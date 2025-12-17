import os
from fastapi import APIRouter, HTTPException
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from google.cloud.firestore_v1.vector import Vector
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict, Any
from pydantic import BaseModel
import logging
import json

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize Firebase
firebase_config = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
if not firebase_config:
    raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON not found in environment variables")

# Parse the JSON string from environment variable
service_account = json.loads(firebase_config)
cred = credentials.Certificate(service_account)
firebase_admin.initialize_app(cred)
db = firestore.client()

# Initialize Google AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=GEMINI_API_KEY)

COLLECTION_NAME = "combined_products"

class SearchRequest(BaseModel):
    query: str

async def generate_embeddings(text: str) -> List[float]:
    """Generate embeddings for the given text using Google Gemini."""
    logger.info(f"Generating embeddings for text: {text[:50]}...")
    try:
        result = genai.embed_content(model="models/text-embedding-004", content=text)
        logger.info(f"Embeddings generated successfully, length: {len(result['embedding'])}")
        return result['embedding']
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")

async def search_products(query: str) -> List[Dict[str, Any]]:
    """Perform vector search in Firestore."""
    logger.info(f"Starting search for query: {query}")
    try:
        # Generate query embedding
        logger.info("Generating query embedding...")
        query_embedding = await generate_embeddings(query)
        logger.info(f"Query embedding generated, length: {len(query_embedding)}")

        # Perform vector search
        logger.info("Performing vector search in Firestore...")
        vector_query = db.collection(COLLECTION_NAME).find_nearest(
            vector_field='embedding',
            query_vector=Vector(query_embedding),  # Wrap in Vector object
            distance_measure=DistanceMeasure.COSINE,  # Use enum, not string
            limit=10
        )

        docs = vector_query.stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            result = {
                'id': doc.id,
                'name': data.get('name'),
                'source': data.get('source'),
                'price': data.get('price'),
                'categories': data.get('categories', []),
                'attributes': data.get('attributes', {}),
                'description': data.get('description'),
                'stock': data.get('stock', {}),
                'image': data.get('image', ''),
                'images': data.get('images', {})
            }
            results.append(result)
        
        logger.info(f"Search completed, found {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

router = APIRouter()

@router.post("/search")
async def search(request: SearchRequest):
    """Search for products based on semantic similarity."""
    logger.info(f"Received search request: {request.query}")
    query = request.query
    if not query:
        logger.warning("Empty query received")
        raise HTTPException(status_code=400, detail="Query parameter is required")

    results = await search_products(query)
    logger.info(f"Returning {len(results)} results for query: {query}")
    return {"query": query, "results": results}