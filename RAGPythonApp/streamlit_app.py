import asyncio
from pathlib import Path
import time

import streamlit as st
import inngest
from dotenv import load_dotenv
import os
import requests

load_dotenv(override=True)


def run_async(coro):
    """Helper to run async functions in Streamlit"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def _inngest_api_base() -> str:
    # Local dev server default; configurable via env
    return os.getenv("INNGEST_API_BASE", "http://127.0.0.1:8288/v1")


def check_services() -> dict:
    """Check if required services are running"""
    status = {
        "inngest": False,
        "fastapi": False,
        "inngest_url": _inngest_api_base(),
        "fastapi_url": "http://127.0.0.1:8000",
    }

    # Check Inngest dev server
    try:
        resp = requests.get(f"{_inngest_api_base().rstrip('/v1')}/health", timeout=5)
        status["inngest"] = resp.status_code == 200
    except:
        pass

    # Check FastAPI server (try both localhost and 127.0.0.1)
    for url in [
        "http://127.0.0.1:8000/api/inngest",
        "http://localhost:8000/api/inngest",
    ]:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                status["fastapi"] = True
                status["fastapi_url"] = url.replace("/api/inngest", "")
                break
        except:
            continue

    return status


st.set_page_config(page_title="RAG Ingest PDF", page_icon="📄", layout="centered")

# Service status check removed - silent operation


@st.cache_resource
def get_inngest_client() -> inngest.Inngest:
    return inngest.Inngest(app_id="rag_app", is_production=False)


def save_uploaded_pdf(file) -> Path:
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    file_path = uploads_dir / file.name
    file_bytes = file.getbuffer()
    file_path.write_bytes(file_bytes)
    return file_path


async def send_rag_ingest_event(pdf_path: Path) -> str:
    """Send ingest event via direct HTTP POST to Inngest Dev Server"""
    import uuid

    event_id = f"01{uuid.uuid4().hex[:24].upper()}"
    event_payload = {
        "name": "/rag/ingest_pdf",
        "data": {
            "pdf_path": str(pdf_path.resolve()),
            "source_id": pdf_path.name,
        },
        "id": event_id,
        "ts": int(time.time() * 1000),
    }

    try:
        resp = requests.post(
            "http://localhost:8288/e/rag_app", json=event_payload, timeout=5
        )
        resp.raise_for_status()
        # Inngest returns the actual event ID it created
        result = resp.json()
        actual_event_id = result.get("ids", [event_id])[0]
        return actual_event_id
    except Exception as e:
        st.error(f"Failed to send event: {e}")
        return None


def fetch_runs(event_id: str) -> list[dict]:
    url = f"{_inngest_api_base()}/events/{event_id}/runs"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])
    except requests.RequestException as e:
        st.error(f"Failed to fetch runs from Inngest API: {e}")
        return []


def wait_for_run_output(
    event_id: str, timeout_s: float = 120.0, poll_interval_s: float = 0.5
) -> dict:
    start = time.time()
    last_status = None
    iteration = 0

    while True:
        iteration += 1
        runs = fetch_runs(event_id)

        if runs:
            run = runs[0]
            status = run.get("status")
            last_status = status or last_status

            # Status updates removed - silent polling

            if status in ("Completed", "Succeeded", "Success", "Finished"):
                output = run.get("output")
                # The Inngest dev server can briefly report status="Completed"
                # before the run's output is actually persisted/queryable (a
                # race condition in its REST API). Only treat the run as truly
                # done once output is present; otherwise keep polling.
                if output is not None:
                    return output
            if status in ("Failed", "Cancelled"):
                error_msg = run.get("error", "Unknown error")
                raise RuntimeError(f"Function run {status}: {error_msg}")

        if time.time() - start > timeout_s:
            # Provide helpful error message
            services = check_services()
            error_details = [
                f"Timed out waiting for run output (last status: {last_status})",
                f"\nEvent ID: {event_id}",
                f"Total runs found: {len(runs)}",
                f"\nService Status:",
                f"  - Inngest Dev Server: {'✅ Running' if services['inngest'] else '❌ Not Running'}",
                f"  - FastAPI Backend: {'✅ Running' if services['fastapi'] else '❌ Not Running'}",
                f"\nPlease ensure all services are running. Use start_services.bat to start them.",
            ]
            raise TimeoutError("\n".join(error_details))

        time.sleep(poll_interval_s)


st.title("Upload a PDF to Ingest")
uploaded = st.file_uploader("Choose a PDF", type=["pdf"], accept_multiple_files=False)

if uploaded is not None:
    try:
        with st.spinner("Processing PDF..."):
            path = save_uploaded_pdf(uploaded)
            # Send the event and get event ID
            event_id = run_async(send_rag_ingest_event(path))

            if event_id:
                with st.spinner("Ingesting..."):
                    # Wait for the ingestion to complete
                    output = wait_for_run_output(event_id, timeout_s=60.0)
                    st.success(
                        f"✅ {path.name} is ready! You can now ask questions about it."
                    )
            else:
                st.error(
                    "Failed to send ingestion event. Check the error message above."
                )
    except TimeoutError as e:
        st.error("⏱️ **Ingestion Timed Out**")
        st.error(str(e))
    except Exception as e:
        st.error(f"❌ Error during ingestion: {str(e)}")

    st.caption("You can upload another PDF if you like.")

st.divider()
st.title("Ask a question about your PDFs")


async def send_rag_query_event(question: str, top_k: int) -> str:
    """Send query event via direct HTTP POST to Inngest Dev Server"""
    import uuid

    event_id = f"01{uuid.uuid4().hex[:24].upper()}"
    event_payload = {
        "name": "/rag/query_pdf_ai",
        "data": {
            "question": question,
            "top_k": top_k,
        },
        "id": event_id,
        "ts": int(time.time() * 1000),
    }

    try:
        resp = requests.post(
            "http://localhost:8288/e/rag_app", json=event_payload, timeout=5
        )
        resp.raise_for_status()
        # Inngest returns the actual event ID it created
        result = resp.json()
        actual_event_id = result.get("ids", [event_id])[0]
        return actual_event_id
    except Exception as e:
        st.error(f"Failed to send event: {e}")
        return None


with st.form("rag_query_form"):
    question = st.text_input("Your question")
    top_k = st.number_input(
        "How many chunks to retrieve", min_value=1, max_value=20, value=5, step=1
    )
    submitted = st.form_submit_button("Ask")

    if submitted and question.strip():
        try:
            with st.spinner("Sending event and generating answer..."):
                # Fire-and-forget event to Inngest for observability/workflow
                event_id = run_async(send_rag_query_event(question.strip(), int(top_k)))
                # Poll the local Inngest API for the run's output with longer timeout for LLM processing
                output = wait_for_run_output(
                    event_id, timeout_s=180.0
                )  # 3 minutes for Ollama
                answer = output.get("answer", "")
                sources = output.get("sources", [])

            st.subheader("Answer")
            st.write(answer or "(No answer)")

        except TimeoutError as e:
            st.error("⏱️ **Request Timed Out**")
            st.error(str(e))
            st.info("💡 **Troubleshooting Tips:**")
            st.markdown(
                """
            1. Check that all services are running (run `start_services.bat`)
            2. Verify Ollama is running if using local LLM
            3. Check the FastAPI and Inngest Dev Server terminal windows for errors
            4. Try uploading and ingesting a PDF first if you haven't
            """
            )

        except RuntimeError as e:
            st.error("❌ **Function Execution Failed**")
            st.error(str(e))

        except Exception as e:
            st.error("❌ **Unexpected Error**")
            st.error(f"Error: {str(e)}")
            st.caption("Check the terminal windows for more details.")
