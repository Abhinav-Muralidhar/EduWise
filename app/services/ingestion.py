import os
from flask import current_app
from app.extensions import db
from app.models.knowledge_source import KnowledgeSource
from app.models.chunk import KnowledgeChunk
from app.utils.text import extract_text
from app.services.chunking import chunk_text
from app.services.embeddings import embed_texts

def ingest_knowledge_source(user_id: int, file_storage, title: str = None) -> KnowledgeSource:
    """
    Ingest a document into the user's RAG knowledge base:
    1. Extract raw text from PDF/DOCX/TXT
    2. Chunk the text with sentence-aware boundaries
    3. Generate 768-dim embeddings using Gemini Embeddings API
    4. Store KnowledgeSource and KnowledgeChunks in database
    """
    filename = file_storage.filename or "Uploaded Document"
    ext = os.path.splitext(filename)[1].lower().replace('.', '')
    source_type = ext if ext in ['pdf', 'docx', 'txt'] else 'txt'
    
    if not title or not title.strip():
        title = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title()
        
    # 1. Extract text
    raw_text = extract_text(file_storage)
    if not raw_text or len(raw_text.strip()) < 10:
        raise ValueError("Could not extract sufficient readable text from this file. Please ensure the file is not empty or image-only scanned.")
    
    # 2. Chunk text
    chunks = chunk_text(raw_text)
    if not chunks:
        raise ValueError("Text could not be chunked into valid segments.")
        
    current_app.logger.info("Extracted %d characters and created %d chunks for '%s'", len(raw_text), len(chunks), title)
    
    # 3. Generate embeddings
    embeddings = embed_texts(chunks)
    
    # 4. Save to Database
    source = KnowledgeSource(
        user_id=user_id,
        title=title,
        source_type=source_type,
        chunk_count=len(chunks)
    )
    db.session.add(source)
    db.session.flush()  # Generate source.id
    
    for idx, (content, emb) in enumerate(zip(chunks, embeddings)):
        chunk_obj = KnowledgeChunk(
            source_id=source.id,
            content=content,
            chunk_index=idx,
            embedding=emb
        )
        db.session.add(chunk_obj)
        
    db.session.commit()
    return source
