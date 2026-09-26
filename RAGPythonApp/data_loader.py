# llama index to load pfs docs and embed them
# creating vectors
# process is like: pdf -> text chunks -> embeddings -> vectors

from sentence_transformers import SentenceTransformer
from llama_index.readers.file import PDFReader
from llama_index.core.node_parser import SentenceSplitter
from dotenv import load_dotenv

load_dotenv()

# Using free Sentence Transformers model instead of OpenAI
# This model is free and runs locally
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
EMBED_DIM = 384  # Dimension for all-MiniLM-L6-v2 model

# chunk_overlap -> how much the end of one chunk overlaps with the start of the next chunk
# hello world my name is tim ->
#  hello world my -> 1 & my name is tim -> 2
#  it is done so that the chunks have relevant data which might be useful for querying the vector db
splitter = SentenceSplitter(chunk_size=1000, chunk_overlap=200)


def load_and_chunk_pdfs(path: str):
    docs = PDFReader().load_data(file=path)
    texts = [d.text for d in docs if getattr(d, "text", None)]
    chunks = []
    for t in texts:
        chunks.extend(splitter.split_text(t))
    return chunks


def embed_texts(texts: list[str]) -> list[list[float]]:
    # Using free Sentence Transformers - no API key needed!
    embeddings = embedding_model.encode(texts, show_progress_bar=True)
    return embeddings.tolist()
