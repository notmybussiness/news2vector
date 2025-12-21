"""Milvus vector database client for storing and searching news embeddings."""

from typing import List, Dict, Optional, Any
from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility,
)
from loguru import logger

from ..config import settings


class MilvusClient:
    """
    Client for Milvus vector database operations.

    Handles collection creation, data insertion, and vector search.
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        collection_name: str = None,
    ):
        """
        Initialize Milvus client.

        Args:
            host: Milvus host (default from settings)
            port: Milvus port (default from settings)
            collection_name: Collection name (default from settings)
        """
        self.host = host or settings.milvus_host
        self.port = port or settings.milvus_port
        self.collection_name = collection_name or settings.collection_name
        self._collection: Optional[Collection] = None
        self._connected = False

    def connect(self) -> None:
        """Connect to Milvus server."""
        if self._connected:
            return

        logger.info(f"Connecting to Milvus at {self.host}:{self.port}")
        connections.connect(
            alias="default",
            host=self.host,
            port=self.port,
        )
        self._connected = True
        logger.info("Connected to Milvus")

    def disconnect(self) -> None:
        """Disconnect from Milvus server."""
        if self._connected:
            connections.disconnect("default")
            self._connected = False
            logger.info("Disconnected from Milvus")

    def create_collection(self, drop_if_exists: bool = False) -> Collection:
        """
        Create the news collection with schema from PRD.

        Schema:
        - news_id: Int64 (PK, auto-generated)
        - embedding: FloatVector(768)
        - original_text: VarChar(2000)
        - title: VarChar(512)
        - published_at: VarChar(20)
        - url: VarChar(1024)
        """
        self.connect()

        if utility.has_collection(self.collection_name):
            if drop_if_exists:
                logger.warning(f"Dropping existing collection: {self.collection_name}")
                utility.drop_collection(self.collection_name)
            else:
                logger.info(f"Collection exists: {self.collection_name}")
                self._collection = Collection(self.collection_name)
                return self._collection

        # Define schema
        fields = [
            FieldSchema(
                name="news_id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True,
                description="Unique identifier for the chunk",
            ),
            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=settings.embedding_dimension,
                description="Vector output from ko-sroberta model",
            ),
            FieldSchema(
                name="original_text",
                dtype=DataType.VARCHAR,
                max_length=2000,
                description="The actual text chunk content",
            ),
            FieldSchema(
                name="title",
                dtype=DataType.VARCHAR,
                max_length=512,
                description="News article title",
            ),
            FieldSchema(
                name="published_at",
                dtype=DataType.VARCHAR,
                max_length=20,
                description="Date string (YYYY-MM-DD HH:mm)",
            ),
            FieldSchema(
                name="url",
                dtype=DataType.VARCHAR,
                max_length=1024,
                description="Source link for citation",
            ),
        ]

        schema = CollectionSchema(
            fields=fields,
            description="Storage for chunked news articles and their vector embeddings",
        )

        logger.info(f"Creating collection: {self.collection_name}")
        self._collection = Collection(
            name=self.collection_name,
            schema=schema,
            consistency_level="Bounded",
        )

        # Create index
        self._create_index()

        return self._collection

    def _create_index(self) -> None:
        """Create IVF_FLAT index on embedding field."""
        if self._collection is None:
            return

        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "L2",
            "params": {"nlist": 1024},
        }

        logger.info("Creating index on embedding field")
        self._collection.create_index(
            field_name="embedding",
            index_params=index_params,
        )
        logger.info("Index created successfully")

    def get_collection(self) -> Collection:
        """Get or create the collection."""
        if self._collection is None:
            self.create_collection()
        return self._collection

    def insert(
        self,
        embeddings: List[List[float]],
        texts: List[str],
        titles: List[str],
        published_dates: List[str],
        urls: List[str],
    ) -> List[int]:
        """
        Insert data into the collection.

        Args:
            embeddings: List of embedding vectors
            texts: List of text chunks
            titles: List of article titles
            published_dates: List of publication dates
            urls: List of article URLs

        Returns:
            List of inserted IDs
        """
        collection = self.get_collection()
        collection.load()

        data = [
            embeddings,
            texts,
            titles,
            published_dates,
            urls,
        ]

        logger.info(f"Inserting {len(embeddings)} records")
        result = collection.insert(data)
        collection.flush()

        logger.info(f"Inserted {len(result.primary_keys)} records")
        return result.primary_keys

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        output_fields: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            output_fields: Fields to include in results

        Returns:
            List of search results with metadata
        """
        collection = self.get_collection()
        collection.load()

        output_fields = output_fields or [
            "original_text",
            "title",
            "published_at",
            "url",
        ]

        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10},
        }

        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=output_fields,
        )

        hits = []
        for hit in results[0]:
            hits.append(
                {
                    "id": hit.id,
                    "distance": hit.distance,
                    "score": 1
                    / (1 + hit.distance),  # Convert L2 distance to similarity
                    **hit.entity.to_dict(),
                }
            )

        return hits

    def count(self) -> int:
        """Get the number of entities in the collection."""
        collection = self.get_collection()
        return collection.num_entities

    def check_url_exists(self, url: str) -> bool:
        """Check if a URL already exists in the collection."""
        collection = self.get_collection()
        collection.load()

        results = collection.query(
            expr=f'url == "{url}"',
            output_fields=["news_id"],
            limit=1,
        )

        return len(results) > 0
