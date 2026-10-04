import requests
from flask import current_app

EMBEDDING_MODEL = "models/text-embedding-004"

def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Batch embed a list of texts using Google Gemini Text Embedding API.
    Returns a list of 768-dimensional float vectors.
    """
    if not texts:
        return []
    
    api_key = current_app.config.get('GEMINI_API_KEY')
    if not api_key:
        current_app.logger.warning("GEMINI_API_KEY is not configured for embeddings.")
        return [[0.0] * 768 for _ in texts]
    
    batch_size = 50
    all_embeddings = []
    
    url = f"https://generativelanguage.googleapis.com/v1beta/{EMBEDDING_MODEL}:batchEmbedContents"
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        requests_payload = [
            {
                "model": EMBEDDING_MODEL,
                "content": {"parts": [{"text": t}]}
            }
            for t in batch
        ]
        
        try:
            response = requests.post(
                url,
                json={"requests": requests_payload},
                headers={
                    'Content-Type': 'application/json',
                    'x-goog-api-key': api_key
                },
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            embeddings = data.get('embeddings', [])
            
            for item in embeddings:
                values = item.get('values', [])
                all_embeddings.append(values)
                
        except Exception as e:
            current_app.logger.exception("Error in batch embeddings: %s", e)
            # Fallback for failed batch items: try individually or fill empty
            for text in batch:
                single_emb = embed_query(text)
                all_embeddings.append(single_emb)
                
    return all_embeddings

def embed_query(query: str) -> list[float]:
    """
    Embed a single search query string using Gemini Text Embedding API.
    Returns a 768-dimensional float vector.
    """
    if not query or not query.strip():
        return [0.0] * 768
    
    api_key = current_app.config.get('GEMINI_API_KEY')
    if not api_key:
        current_app.logger.warning("GEMINI_API_KEY is not configured for embedding query.")
        return [0.0] * 768
    
    url = f"https://generativelanguage.googleapis.com/v1beta/{EMBEDDING_MODEL}:embedContent"
    body = {
        "content": {"parts": [{"text": query}]}
    }
    
    try:
        response = requests.post(
            url,
            json=body,
            headers={
                'Content-Type': 'application/json',
                'x-goog-api-key': api_key
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data.get('embedding', {}).get('values', [0.0] * 768)
    except Exception as e:
        current_app.logger.exception("Error embedding query '%s': %s", query[:50], e)
        return [0.0] * 768
