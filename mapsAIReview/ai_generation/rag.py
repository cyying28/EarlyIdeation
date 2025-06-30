import os
import uuid
import cohere
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PointStruct, SearchParams, Filter, 
    FieldCondition, MatchValue, PayloadSchemaType
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RagTools:
    def __init__(self, collection_name, cohere_api=None, embedding_model="embed-multilingual-v3.0"):
        # Define database and embeddings        
        self.COLLECTION_NAME = collection_name
        self.COHERE_API = cohere_api or os.getenv("COHERE_API_KEY")
        self.EMBEDDING_MODEL = embedding_model
        
        if not self.COHERE_API:
            raise ValueError("Cohere API key not provided and COHERE_API_KEY not found in environment variables")
        
        # Set up clients
        self.co = cohere.Client(self.COHERE_API)
        
        # Get Qdrant credentials from environment or use defaults
        qdrant_url = os.getenv("QDRANT_URL", "https://ba7af8b2-0ea7-4a32-a152-e49e25585277.us-west-2-0.aws.cloud.qdrant.io")
        qdrant_api_key = os.getenv("QDRANT_API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.5VM9o_YgtD2u7rd2rdLCX9lhFkhC6gDcKLuuEm6agCk")
        
        self.qdrant = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key
        )

    def create_collection(self):
        """
        Make a new collection if name is not found in qdrant already
        """
        try:
            existing_collections = [c.name for c in self.qdrant.get_collections().collections]
            if self.COLLECTION_NAME not in existing_collections:
                self.qdrant.recreate_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
                )
                
                self.qdrant.create_payload_index(
                    collection_name=self.COLLECTION_NAME,
                    field_name="address",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                print(f"Successfully created collection with name {self.COLLECTION_NAME}")
            else:
                print(f"Collection {self.COLLECTION_NAME} already exists")
        except Exception as e:
            print(f"Error creating collection: {e}")
            raise

    def embed_texts(self, texts: list[str], input_type="search_document") -> list[list[float]]:
        """
        Use Cohere embedding to get embeddings for a list of strings/reviews
        """
        try:
            response = self.co.embed(
                texts=texts,
                model=self.EMBEDDING_MODEL,
                input_type=input_type
            )
            return response.embeddings
        except Exception as e:
            print(f"Error creating embeddings: {e}")
            raise

    def upload_documents(self, documents: list[dict]):
        """
        Expects a list of dicts with keys 'id', 'snippet', and 'details'.
        Stores both in the payload for each vector.
        """
        if not documents:
            print("No documents to upload")
            return
            
        try:
            texts = [doc["snippet"] for doc in documents]
            vectors = self.embed_texts(texts, input_type="search_document")
            
            points = [
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vec,
                    # Will return review and the index
                    payload={
                        # ID + Address = unique identifier
                        "id": doc["id"],
                        "address": doc["address"],
                        "details": doc["details"],
                        "snippet": doc["snippet"],
                    }
                )
                for doc, vec in zip(documents, vectors)
            ]
            self.qdrant.upsert(collection_name=self.COLLECTION_NAME, points=points)
            print(f"Successfully uploaded {len(documents)} documents to vector database")
        except Exception as e:
            print(f"Error uploading documents: {e}")
            raise

    def retrieve_similar_reviews(self, restaurant_addr: str, query: str, max_results=35, threshold=0.50):
        """
        Retrieves from Cohere most relevant reviews based on query, then filters out reviews
        that are not similar enough to the query based on the threshold.
        """
        try:
            query_vector = self.embed_texts([query], input_type="search_query")[0]
            
            # Must match addresses --> this way you can use one collection and query for the restaurant intended
            filter_ = Filter(
                must=[
                    FieldCondition(
                        key="address",
                        match=MatchValue(value=restaurant_addr)
                    )
                ]
            )

            # Get more results than needed so we can properly filter by threshold
            search_limit = min(100, max_results * 3)  # Get 3x more results for better filtering
            
            raw_results = self.qdrant.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=query_vector,
                limit=search_limit,
                search_params=SearchParams(hnsw_ef=128, exact=False),
                query_filter=filter_
            )

            # Return both text and index for better downstream utility
            filtered = [
                {
                    "id": hit.payload["id"],
                    "address": hit.payload["address"],
                    "details": hit.payload["details"],
                    "snippet": hit.payload["snippet"],
                    "score": hit.score
                }
                for hit in raw_results
                if hit.score >= threshold
            ]
            
            print(f"Vector search returned {len(raw_results)} results")
            print(f"Found {len(filtered)} relevant reviews (similarity >= {threshold})")
            if len(filtered) >= max_results:
                print(f"⚠️  Hit maximum limit of {max_results} reviews - consider raising threshold for more selectivity")
            return filtered[:max_results]
            
        except Exception as e:
            print(f"Error retrieving similar reviews: {e}")
            return []

# if __name__ == "__main__":
#     create_collection()

#     # Step 1: Upload documents
#     docs = [
#         "Qdrant is a vector database that supports similarity search.",
#         "Cohere provides powerful embeddings via API.",
#         "Retrieval-Augmented Generation combines search with language models.",
#         "Cosine similarity is commonly used in vector search systems.",
#         "Embedding models map text to high-dimensional vectors."
#     ]
#     upload_documents(docs)

#     # Step 2: Query
#     query = "How does vector similarity work?"
#     results = retrieve_similar_documents(query, max_results=20, threshold=0.75)

#     print("\nRetrieved Documents:")
#     for i, r in enumerate(results, 1):
#         print(f"{i}. {r}")
