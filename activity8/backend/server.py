import os
import time
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types

# Vector DB & Parsing Imports
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue
from llama_index.core import Document
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding

# Load the .env file immediately before initializing any clients
from dotenv import load_dotenv
load_dotenv()

# Initialize FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# qdrant_client = QdrantClient(url="http://localhost:6333") 


# Initialize SDK Clients (Reads GEMINI_API_KEY from .env)
gemini_client = genai.Client()

# Initialize LlamaIndex Google GenAI Embedder for Gemini embeddings
embed_model = GoogleGenAIEmbedding(model_name="gemini-embedding-2")

# Initialize Qdrant Client (In-memory mode prevents Windows portalocker permission conflicts)
print("Connecting to Qdrant...")

qdrant_client = QdrantClient(location=":memory:")

COLLECTION_NAME = "uploaded_documents"

# Ensure collection exists for 768-dimension Gemini embeddings
if not qdrant_client.collection_exists(COLLECTION_NAME):
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
    )
    print(f"Collection '{COLLECTION_NAME}' initialized.")


def extract_embedding_vector(response):
    if hasattr(response, "embeddings") and response.embeddings is not None:
        embeddings = response.embeddings
        if isinstance(embeddings, list) and embeddings:
            first = embeddings[0]
            if isinstance(first, list):
                return first
            if hasattr(first, "values"):
                return first.values
            if isinstance(first, dict) and "values" in first:
                return first["values"]
            return first
        if hasattr(embeddings, "values"):
            return embeddings.values
        return embeddings

    if hasattr(response, "embedding") and response.embedding is not None:
        embedding = response.embedding
        if isinstance(embedding, list):
            return embedding
        if hasattr(embedding, "values"):
            return embedding.values
        if isinstance(embedding, dict) and "values" in embedding:
            return embedding["values"]
        return embedding

    raise ValueError("Unable to extract an embedding vector from Gemini response")


def split_large_text_safely(text: str, max_chars: int = 1500) -> list[str]:
    """
    Slices large text files into solid blocks by character counts without 
    triggering hundreds of sentence-level embedding calls.
    """
    # Break text up into paragraphs first
    paragraphs = text.split("\n")
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # If adding this paragraph exceeds our chunk target limit, save current block
        if len(current_chunk) + len(para) > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            current_chunk += "\n" + para if current_chunk else para
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

def process_and_index_text_file(file_name: str, raw_text: str):
    """
    Ingests large text bodies, chunks them safely by blocks, 
    and handles potential rate limits gracefully with execution pauses.
    """
    print(f"Processing text file contents for: {file_name}")
    
    # 1. Break text into massive content blocks instead of hundreds of sentences
    chunks = split_large_text_safely(raw_text, max_chars=1500)
    print(f"\nProcessing '{file_name}': Safely grouped document into {len(chunks)} large vector blocks.")
    
    # 2. Vectorize chunks and upsert to database
    points = []
    for i, chunk in enumerate(chunks):
        print(f"-> Vectorizing segment {i+1}/{len(chunks)}")
        
        response = gemini_client.models.embed_content(
            model="gemini-embedding-001",
            contents=chunk,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
        )
        
        vector = extract_embedding_vector(response)
        
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "text": chunk,
                "file_name": file_name,
                "timestamp": time.time()
            }
        )
        points.append(point)
        
        # Delay execution for 600ms per vector to stay safely within Free Tier limits
        time.sleep(0.6)
        
    if points:
        qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
        print(f"Successfully indexed all segments for '{file_name}'.")
    return len(chunks)



@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Frontend client connected via WebSocket.")
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                # Detect if incoming payload is a file upload vs standard chat message
                if len(data) > 300 and (" " in data or "\n" in data) and not data.endswith("?"):
                    await websocket.send_text("✦ Processing and chunking your file into the vector database...")
                    num_chunks = process_and_index_text_file(
                        file_name="Uploaded_Document.txt", 
                        raw_text=data
                    )
                    await websocket.send_text(f"✦ Success! File stored cleanly across {num_chunks} vector nodes. You can now ask questions about it.")
                
                else:
                    # Interpret data strings as standard chat queries
                    # 1. Fetch user query embedding vector (FIXED: Unified model target string)
                    query_vector_resp = gemini_client.models.embed_content(
                        model="gemini-embedding-001", 
                        contents=data,
                        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
                    )
                    
                    query_vector = extract_embedding_vector(query_vector_resp)
                    
                    # 2. Search Qdrant for context using your updated query_points API endpoint
                    search_results = qdrant_client.query_points(
                        collection_name=COLLECTION_NAME,
                        query=query_vector,
                        limit=3
                    ).points
                    
                    # Log to your backend terminal so you can verify matches during testing
                    print(f"[RAG System Log] Found {len(search_results)} relevant document nodes.")
                    
                    context = "\n---\n".join([res.payload["text"] for res in search_results])
                    
                    # 3. Construct Augmented Prompt incorporating your strict rubric rules
                                        # 3. RELAXED PROMPT: Allows Gemini to use its general knowledge for any question
                    system_prompt = (
                        "You are an advanced AI assistant powered by a RAG system.\n\n"
                        "INSTRUCTIONS:\n"
                        "1. First, look at the provided Context below. If the user's question relates "
                        "to the uploaded document data, use that context to give a highly accurate answer.\n"
                        "2. If the user's question is completely unrelated to the Context (e.g., asking about coding, "
                        "history, or general knowledge like 'Who is JSON'), do NOT say you don't know. Simply ignore the "
                        "context and use your general LLM knowledge to answer their question fully and helpfully.\n\n"
                        f"Context:\n{context}"
                    )

                    
                    # 4. Generate response from Gemini and send back to chat.jsx
                    response = gemini_client.models.generate_content(
                        model="gemini-3.1-flash-lite",
                        contents=data,
                        config=types.GenerateContentConfig(system_instruction=system_prompt)
                    )

                    reply_text = None
                    if hasattr(response, "text"):
                        reply_text = response.text
                    elif hasattr(response, "content"):
                        reply_text = response.content
                    elif getattr(response, "candidates", None):
                        first_candidate = response.candidates[0]
                        reply_text = getattr(first_candidate, "content", None) or getattr(first_candidate, "text", None)

                    if not reply_text:
                        reply_text = str(response)

                    await websocket.send_text(reply_text)
                            
            except Exception as internal_error:
                print(f"Internal loop processing error: {internal_error}")
                await websocket.send_text(f"⚠️ Backend Error: {str(internal_error)}")
                        
    except WebSocketDisconnect:
        print("Frontend client disconnected.")



if __name__ == "__main__":
    import uvicorn
    # Set reload=False to ensure clean single-process allocation on Windows
    uvicorn.run("server:app", host="localhost", port=8000, reload=False)
