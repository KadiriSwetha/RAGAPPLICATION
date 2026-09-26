# Qdrant Cloud Setup Guide

## Step 1: Create a Free Qdrant Cloud Account

1. Go to **https://cloud.qdrant.io/**
2. Click **"Sign Up"** and create a free account
3. Verify your email

## Step 2: Create a Cluster

1. After logging in, click **"Create Cluster"**
2. Choose:
   - **Free Tier** (1GB, perfect for testing)
   - Select a **region** closest to you
   - Give it a name (e.g., "rag-app-cluster")
3. Click **"Create"** and wait a few minutes for provisioning

## Step 3: Get Your Credentials

1. Once the cluster is ready, click on it
2. You'll see:
   - **Cluster URL** (looks like: `https://xxxxx.us-east.aws.cloud.qdrant.io:6333`)
   - **API Key** (click "Generate API Key" if not shown)

## Step 4: Add Credentials to Your .env File

Open your `.env` file and add:

```env
QDRANT_URL=https://your-cluster-url.cloud.qdrant.io:6333
QDRANT_API_KEY=your-api-key-here
```

## Step 5: Test the Connection

Run this test script:

```python
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

# Test connection
print("Collections:", client.get_collections())
print("✅ Connected to Qdrant Cloud successfully!")
```

## Your Updated vector_db.py

The `vector_db.py` file has been updated to automatically:

- Use Qdrant Cloud if `QDRANT_URL` and `QDRANT_API_KEY` are set in `.env`
- Fall back to local Docker (`http://localhost:6333`) if credentials are not provided

## Benefits of Qdrant Cloud

✅ No Docker installation needed
✅ No local setup required
✅ Free tier with 1GB storage
✅ High availability
✅ Automatic backups
✅ Works from anywhere

## Alternative: Docker Cloud Services

If you still want to use Docker in the cloud later:

- **Docker Playground**: https://labs.play-with-docker.com/ (temporary instances)
- **Google Cloud Run**: Deploy containerized apps
- **AWS ECS/Fargate**: Managed container service
- **Azure Container Instances**: Quick container deployment
