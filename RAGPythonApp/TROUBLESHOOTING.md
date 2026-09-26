# Troubleshooting Guide

## Timeout Error Fix

The timeout error you experienced has been fixed with improved error handling and service checks.

### What Was Changed

1. **Service Status Checker**: Added automatic service health checks when the app starts
2. **Better Error Messages**: Timeout errors now show detailed information about which services are down
3. **Progress Updates**: The app now shows status updates while waiting for responses
4. **Graceful Error Handling**: All error types are caught and displayed with helpful troubleshooting tips

### How to Use the App

#### Step 1: Start All Services

Run the batch file to start all required services:

```bash
start_services.bat
```

This will open 3 terminal windows:
- **FastAPI Server** (port 8000) - Your backend API
- **Inngest Dev Server** (port 8288) - Event/workflow orchestration
- **Streamlit App** (port 8501) - Your web UI

#### Step 2: Wait for Services to Initialize

Give the services about 10-15 seconds to fully start up.

#### Step 3: Check Service Status

When you open the Streamlit app, you'll see a status check at the top showing:
- ✅ Inngest Dev Server (Running)
- ✅ FastAPI Backend (Running)

If you see ❌ for any service, it means that service didn't start properly.

### Common Issues and Solutions

#### Issue 1: Timeout Error

**Symptoms**: "Timed out waiting for run output"

**Solutions**:
1. Make sure all services are running (`start_services.bat`)
2. Check that Ollama is running if using local LLM:
   ```bash
   ollama serve
   ```
3. Verify the Inngest Dev Server terminal shows your FastAPI app is connected
4. Check FastAPI terminal for any errors

#### Issue 2: Services Won't Start

**Symptoms**: Service status shows ❌

**Solutions**:
1. Close all terminal windows and try again
2. Check if ports 8000 or 8288 are already in use:
   ```bash
   netstat -ano | findstr "8000"
   netstat -ano | findstr "8288"
   ```
3. Kill any processes using those ports if needed
4. Make sure your virtual environment is activated

#### Issue 3: No PDFs to Query

**Symptoms**: Getting empty or unhelpful responses

**Solutions**:
1. First upload and ingest at least one PDF using the upload section
2. Wait for the ingestion to complete (you'll see a success message)
3. Then try asking questions

#### Issue 4: Ollama Not Running

**Symptoms**: Error calling Ollama in the response

**Solutions**:
1. Install Ollama: https://ollama.ai/download
2. Start Ollama:
   ```bash
   ollama serve
   ```
3. Pull the model (default is llama3.2):
   ```bash
   ollama pull llama3.2
   ```

### Verifying Services Manually

#### Check Inngest Dev Server
Open browser: http://localhost:8288

You should see the Inngest dev server UI.

#### Check FastAPI Backend
Open browser: http://localhost:8000/api/inngest

You should see a JSON response from Inngest.

#### Check FastAPI Docs
Open browser: http://localhost:8000/docs

You should see the FastAPI Swagger documentation.

### Still Having Issues?

Check the terminal windows for detailed error messages:
1. **FastAPI Server** - Shows backend errors and Inngest function execution
2. **Inngest Dev Server** - Shows event processing and run status
3. **Streamlit App** - Shows the UI errors

Look for red error messages or stack traces in these windows.
