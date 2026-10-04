import math
from sqlalchemy import text as sql_text
from flask import current_app
from app.extensions import db
from app.models.knowledge_source import KnowledgeSource
from app.models.chunk import KnowledgeChunk
from app.services.embeddings import embed_query

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Calculate cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def get_relevant_chunks(user_id: int, query: str, source_id: int = None, k: int = 5) -> list[dict]:
    """
    Retrieve the top-k most relevant chunks from the user's knowledge base.
    Uses pgvector's cosine distance operator (<=>) on PostgreSQL,
    and falls back to Python cosine similarity on SQLite.
    
    Strictly scoped to `user_id` to prevent cross-user data leakage.
    """
    if not query or not query.strip():
        return []
    
    query_embedding = embed_query(query)
    
    # Determine DB dialect
    dialect_name = db.session.bind.dialect.name if db.session.bind else 'sqlite'
    
    # 1. PostgreSQL + pgvector execution path
    if dialect_name == 'postgresql':
        try:
            vector_str = f"[{','.join(str(x) for x in query_embedding)}]"
            query_sql = """
                SELECT c.content, c.chunk_index, ks.title, ks.id AS source_id,
                       1 - (c.embedding <=> :embedding) AS similarity
                FROM knowledge_chunk c
                JOIN knowledge_source ks ON c.source_id = ks.id
                WHERE ks.user_id = :user_id
            """
            params = {
                'embedding': vector_str,
                'user_id': user_id,
                'k': k
            }
            if source_id:
                query_sql += " AND ks.id = :source_id"
                params['source_id'] = int(source_id)
                
            query_sql += " ORDER BY c.embedding <=> :embedding LIMIT :k"
            
            results = db.session.execute(sql_text(query_sql), params).fetchall()
            
            return [
                {
                    'content': r.content,
                    'source_title': r.title,
                    'source_id': r.source_id,
                    'chunk_index': r.chunk_index,
                    'similarity': round(float(r.similarity), 4) if r.similarity is not None else 0.0
                }
                for r in results
            ]
        except Exception as e:
            current_app.logger.warning("Postgres pgvector query failed, falling back to in-memory search: %s", e)
    
    # 2. SQLite / In-Memory Fallback Path
    sources_query = KnowledgeSource.query.filter_by(user_id=user_id)
    if source_id:
        sources_query = sources_query.filter_by(id=int(source_id))
    
    sources = sources_query.all()
    if not sources:
        return []
    
    source_map = {s.id: s.title for s in sources}
    source_ids = list(source_map.keys())
    
    chunks = KnowledgeChunk.query.filter(KnowledgeChunk.source_id.in_(source_ids)).all()
    if not chunks:
        return []
    
    scored_chunks = []
    for chunk in chunks:
        emb = chunk.embedding
        if isinstance(emb, str):
            import json
            try:
                emb = json.loads(emb)
            except Exception:
                emb = []
        
        sim = cosine_similarity(query_embedding, emb) if emb else 0.0
        scored_chunks.append({
            'content': chunk.content,
            'source_title': source_map.get(chunk.source_id, 'Source'),
            'source_id': chunk.source_id,
            'chunk_index': chunk.chunk_index,
            'similarity': round(sim, 4)
        })
    
    # Sort by similarity descending and return top k
    scored_chunks.sort(key=lambda x: x['similarity'], reverse=True)
    return scored_chunks[:k]
