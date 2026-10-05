import requests
from flask import current_app

MODELS_TO_TRY = [
    ("v1beta", "models/text-embedding-004"),
    ("v1", "models/text-embedding-004"),
    ("v1beta", "models/embedding-001")
]

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
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_results = None
        
        for version, model_name in MODELS_TO_TRY:
            url = f"https://generativelanguage.googleapis.com/{version}/{model_name}:batchEmbedContents?key={api_key}"
            requests_payload = [
                {
                    "model": model_name,
                    "content": {"parts": [{"text": t}]}
                }
                for t in batch
            ]
            
            try:
                response = requests.post(
                    url,
                    json={"requests": requests_payload},
                    headers={'Content-Type': 'application/json'},
                    timeout=60
                )
                if response.status_code == 200:
                    data = response.json()
                    embeddings = data.get('embeddings', [])
                    if len(embeddings) == len(batch):
                        batch_results = [item.get('values', [0.0] * 768) for item in embeddings]
                        break
            except Exception as e:
                current_app.logger.warning("Batch embedding attempt failed for %s: %s", model_name, e)
                
        if batch_results is not None:
            all_embeddings.extend(batch_results)
        else:
            # Fallback for failed batch: embed one by one
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
    
    for version, model_name in MODELS_TO_TRY:
        url = f"https://generativelanguage.googleapis.com/{version}/{model_name}:embedContent?key={api_key}"
        body = {
            "model": model_name,
            "content": {"parts": [{"text": query}]}
        }
        
        try:
            response = requests.post(
                url,
                json=body,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                values = data.get('embedding', {}).get('values', [])
                if values:
                    return values
        except Exception as e:
            current_app.logger.warning("Single embedding attempt failed for %s: %s", model_name, e)
            
    current_app.logger.error("All embedding attempts failed for query '%s'", query[:50])
    return [0.0] * 768
