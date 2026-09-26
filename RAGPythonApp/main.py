import logging
from fastapi import FastAPI
import inngest
import inngest.fast_api
from inngest.experimental import ai
from dotenv import load_dotenv
import uuid
import os
import datetime
from data_loader import load_and_chunk_pdfs, embed_texts
from vector_db import QdrantStorage
from custom_types import (
    RAGChunkAndSrc,
    RAGUpsertResult,
    RAGSearchResult,
    RAGQueryResult,
)

# override=True ensures values in .env always win over stale/stray OS-level
# environment variables (e.g. a leftover QDRANT_URL from local Docker testing).
load_dotenv(override=True)

# inngest.PydanticSerializer() -> supports pydantic typing

inngest_client = inngest.Inngest(
    app_id="rag_app",
    logger=logging.getLogger("uvicorn"),
    is_production=False,
    serializer=inngest.PydanticSerializer(),
)

# inngest function - to connect to inngest development server
# so instead of sending data to our api server it will send the request to inngest server


# decorator
@inngest_client.create_function(
    fn_id="RAG: Ingest PDF",
    trigger=inngest.TriggerEvent(event="/rag/ingest_pdf"),  # to trigger any event
)

# when someone triggers event="/rag/ingest_pdf", we get context of that event in below ctx: ingext.Context
async def rag_ingest_pdf(ctx: inngest.Context):
    def _load(ctx: inngest.Context) -> RAGChunkAndSrc:
        pdf_path = ctx.event.data["pdf_path"]
        source_id = ctx.event.data.get("source_id", pdf_path)
        chunks = load_and_chunk_pdfs(pdf_path)
        return RAGChunkAndSrc(chunk=chunks, source_id=source_id)

    def _upsert(chunks_and_src: RAGChunkAndSrc) -> RAGUpsertResult:
        chunks = chunks_and_src.chunk
        source_id = chunks_and_src.source_id
        vectors = embed_texts(chunks)
        ids = [
            str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source_id}-{i}"))
            for i in range(len(chunks))
        ]
        payloads = [
            {"source": source_id, "text": chunks[i]} for i in range(len(chunks))
        ]
        QdrantStorage().upsert(ids, vectors, payloads)
        return RAGUpsertResult(ingested=len(chunks))

    chunks_and_src = await ctx.step.run(
        "load-and-chunk", lambda: _load(ctx), output_type=RAGChunkAndSrc
    )
    ingested = await ctx.step.run(
        "embed-and-upsert", lambda: _upsert(chunks_and_src), output_type=RAGUpsertResult
    )
    return ingested.model_dump()  # converts to json or python dictionary


@inngest_client.create_function(
    fn_id="RAG: Query PDF", trigger=inngest.TriggerEvent(event="/rag/query_pdf_ai")
)
async def rag_query_pdf_ai(ctx: inngest.Context):
    def _search(question: str, top_k: int = 5):
        query_vec = embed_texts([question])[0]
        store = QdrantStorage()
        found = store.search(query_vec, top_k)
        return RAGSearchResult(context=found["Context:-"], sources=found["Sources:-"])

    question = ctx.event.data["question"]
    top_k = int(ctx.event.data.get("top_k", 5))

    found = await ctx.step.run(
        "embed-and-search",
        lambda: _search(question, top_k),
        output_type=RAGSearchResult,
    )

    # Format each context chunk with better spacing
    context_items = [f"{i+1}. {chunk}" for i, chunk in enumerate(found.context)]
    context_block = "\n\n".join(context_items)

    # OpenAI LLM integration (commented out - requires API credits)
    # user_content = (
    #     "Use the following context to answer the question.\n\n"
    #     f"Context:\n{context_block}\n\n"
    #     f"\n\nQuestion: {question}"
    #     "Answer concisely using the context above."
    # )
    #
    # adapter = ai.OpenAIAdapter(
    #     auth_keys=os.getenv("OPENAI_API_KEY"),
    #     model="gpt-4o-mini",
    # )
    #
    # res = await ctx.step.ai.infer(
    #     "llm-answer",
    #     adapter=adapter,
    #     body={
    #         "max-tokens": 1024,
    #         "temperature": 0.2,
    #         "messages": [
    #             {"role": "system", "content": "You answer questions only using the provided context."},
    #             {"role": "user", "content": user_content}
    #         ]
    #     }
    # )
    # answer = res["choices"][0]["message"]["content"].strip()
    # answer = f"""Question: {question}
    # Ollama LLM integration (local LLM)
    async def _generate_answer():
        import requests
        import time

        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        model = os.getenv("OLLAMA_MODEL", "llama3.2")

        print(f"[DEBUG] Using Ollama at: {ollama_url} with model: {model}")

        # Limit context to avoid very long prompts (take only first 3 chunks)
        limited_context = found.context[:3]
        context_text = "\n\n".join(
            [f"{i+1}. {chunk}" for i, chunk in enumerate(limited_context)]
        )

        prompt = f"""Answer the question directly as if you know the information yourself. Do NOT use phrases like "according to the context", "based on the information provided", "the context shows", or similar. Just give a straightforward answer.

Context:
{context_text}

Question: {question}

Give a direct, concise answer (2-3 sentences maximum):"""

        # Retry logic with model preloading
        max_retries = 2
        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] Attempt {attempt + 1}/{max_retries}")

                # Preload model on first attempt
                if attempt == 0:
                    print(f"[DEBUG] Preloading model...")
                    warmup = requests.post(
                        f"{ollama_url}/api/generate",
                        json={"model": model, "prompt": "Hi", "stream": False},
                        timeout=30,
                    )
                    if warmup.status_code == 200:
                        print(f"[DEBUG] Model preloaded")
                    time.sleep(0.5)

                response = requests.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 150,
                            "top_p": 0.9,
                            "top_k": 40,
                        },
                    },
                    timeout=120,
                )

                print(f"[DEBUG] Response status: {response.status_code}")

                if response.status_code == 404:
                    if attempt < max_retries - 1:
                        print(f"[WARN] 404 error, retrying...")
                        time.sleep(2)
                        continue

                response.raise_for_status()
                result = response.json()
                answer_text = result.get("response", "").strip()

                if answer_text and len(answer_text) >= 10:
                    print(f"[DEBUG] Generated answer: {len(answer_text)} chars")
                    return answer_text

            except requests.Timeout:
                return f"⏱️ The AI model took too long to respond. Here's what I found:\n\n{context_text}"
            except Exception as e:
                print(f"[ERROR] Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return f"❌ Error: {str(e)}\n\nRelevant information found:\n{context_text}"
                time.sleep(2)

        # Fallback if all retries exhausted
        return f"Unable to generate answer. Here are the relevant excerpts:\n\n{context_text}"

    answer = await ctx.step.run("llm-answer", _generate_answer)

    return {
        "answer": answer,
        "sources": found.sources,
        "num_contexts": len(found.context),
    }
    # return RAGQueryResult(answer=answer, sources=found.sources, num_contexts=len(found.context)).model_dump()


app = FastAPI()
# main: app
# main -> main.py
# app -> FastAPI instance

inngest.fast_api.serve(app, inngest_client, [rag_ingest_pdf, rag_query_pdf_ai])
