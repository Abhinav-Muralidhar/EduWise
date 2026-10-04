import pytest
from unittest.mock import patch
from app.extensions import db
from app.models.user import User
from app.models.knowledge_source import KnowledgeSource
from app.models.chunk import KnowledgeChunk
from app.services.retrieval import cosine_similarity, get_relevant_chunks

def test_cosine_similarity_identical():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert abs(cosine_similarity(v1, v2) - 1.0) < 1e-5

def test_cosine_similarity_orthogonal():
    v1 = [1.0, 0.0, 0.0]
    v2 = [0.0, 1.0, 0.0]
    assert abs(cosine_similarity(v1, v2) - 0.0) < 1e-5

def test_cosine_similarity_empty():
    assert cosine_similarity([], []) == 0.0
    assert cosine_similarity([1.0], [1.0, 2.0]) == 0.0

def test_get_relevant_chunks_and_user_isolation(app):
    with app.app_context():
        # Create user 1 and user 2
        u1 = User(username="alice", email="alice@test.com", password="hash_password")
        u2 = User(username="bob", email="bob@test.com", password="hash_password")
        db.session.add_all([u1, u2])
        db.session.commit()

        # Mock embeddings: 768 dimensions
        emb_quantum = [0.9] * 384 + [0.1] * 384
        emb_history = [0.1] * 384 + [0.9] * 384

        # Alice uploads Quantum Physics
        ks_alice = KnowledgeSource(user_id=u1.id, title="Quantum Mechanics", chunk_count=1)
        db.session.add(ks_alice)
        db.session.flush()

        chunk_alice = KnowledgeChunk(
            source_id=ks_alice.id,
            content="Schrodinger equation describes how quantum state changes over time.",
            chunk_index=0,
            embedding=emb_quantum
        )
        db.session.add(chunk_alice)

        # Bob uploads History
        ks_bob = KnowledgeSource(user_id=u2.id, title="World War II", chunk_count=1)
        db.session.add(ks_bob)
        db.session.flush()

        chunk_bob = KnowledgeChunk(
            source_id=ks_bob.id,
            content="The Battle of Midway was a decisive naval battle in the Pacific.",
            chunk_index=0,
            embedding=emb_history
        )
        db.session.add(chunk_bob)
        db.session.commit()

        # When Alice queries for Quantum with an embedding close to quantum
        with patch('app.services.retrieval.embed_query', return_value=emb_quantum):
            results = get_relevant_chunks(user_id=u1.id, query="quantum state equation", k=5)
            assert len(results) == 1
            assert "Schrodinger" in results[0]['content']
            assert results[0]['source_title'] == "Quantum Mechanics"
            assert results[0]['similarity'] > 0.8

        # When Bob queries, he should ONLY see his WWII chunks, NOT Alice's quantum chunks
        with patch('app.services.retrieval.embed_query', return_value=emb_quantum):
            results_bob = get_relevant_chunks(user_id=u2.id, query="quantum physics", k=5)
            assert len(results_bob) == 1
            assert "Battle of Midway" in results_bob[0]['content']
            # Bob's results must NEVER contain Alice's content
            assert not any("Schrodinger" in r['content'] for r in results_bob)
