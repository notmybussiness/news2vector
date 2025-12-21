"""
Milvus Collection Initialization Script

Creates the stock_news_v1 collection with proper schema.
"""

from pymilvus import connections, utility
import sys
import os

# Add parent directory to path for local imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data-pipeline"))

from src.storage import MilvusClient
from src.config import settings


def main():
    print("=" * 60)
    print("Milvus Collection Initialization")
    print("=" * 60)

    client = MilvusClient()

    try:
        client.connect()
        print(f"✓ Connected to Milvus at {settings.milvus_host}:{settings.milvus_port}")

        # Check if collection exists
        exists = utility.has_collection(settings.collection_name)
        print(f"Collection '{settings.collection_name}' exists: {exists}")

        if exists:
            response = input("Drop and recreate? (y/N): ").strip().lower()
            if response == "y":
                client.create_collection(drop_if_exists=True)
                print(f"✓ Collection recreated")
            else:
                print("Skipping collection creation")
        else:
            client.create_collection()
            print(f"✓ Collection created: {settings.collection_name}")

        # Show collection info
        collection = client.get_collection()
        print(f"\nCollection Info:")
        print(f"  Name: {collection.name}")
        print(f"  Entities: {collection.num_entities}")
        print(f"  Schema: {collection.schema}")

    finally:
        client.disconnect()
        print("\n✓ Disconnected from Milvus")


if __name__ == "__main__":
    main()
