"""
Test script to verify Qdrant Cloud connection
Run this after setting up your QDRANT_URL and QDRANT_API_KEY in .env
"""

from dotenv import load_dotenv
import os
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
import sys


def test_qdrant_connection():
    # Load environment variables
    load_dotenv()

    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")

    if not url or not api_key:
        print("❌ Error: QDRANT_URL and QDRANT_API_KEY must be set in .env file")
        print("\nPlease add these to your .env file:")
        print("QDRANT_URL=https://your-cluster-url.cloud.qdrant.io:6333")
        print("QDRANT_API_KEY=your-api-key-here")
        return False

    try:
        print("🔄 Connecting to Qdrant Cloud...")
        print(f"   URL: {url}")

        # Initialize client
        client = QdrantClient(url=url, api_key=api_key, timeout=30)

        # Test connection
        collections = client.get_collections()
        print(f"✅ Connected successfully!")
        print(f"📊 Existing collections: {collections}")

        # Create a test collection
        test_collection = "test_collection"
        print(f"\n🔄 Creating test collection '{test_collection}'...")

        if not client.collection_exists(test_collection):
            client.create_collection(
                collection_name=test_collection,
                vectors_config=VectorParams(size=128, distance=Distance.COSINE),
            )
            print(f"✅ Test collection '{test_collection}' created successfully!")
        else:
            print(f"ℹ️  Collection '{test_collection}' already exists")

        # Get collection info
        info = client.get_collection(test_collection)
        print(f"📈 Collection info: {info}")

        print("\n🎉 All tests passed! Your Qdrant Cloud setup is working correctly!")
        return True

    except Exception as e:
        print(f"❌ Error connecting to Qdrant Cloud: {e}")
        print("\nPlease check:")
        print("1. Your QDRANT_URL is correct")
        print("2. Your QDRANT_API_KEY is correct")
        print("3. Your internet connection is working")
        print("4. Your cluster is running in Qdrant Cloud dashboard")
        return False


if __name__ == "__main__":
    success = test_qdrant_connection()
    sys.exit(0 if success else 1)
