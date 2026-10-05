import io
from unittest.mock import patch
from app.models.knowledge_source import KnowledgeSource

def test_unauthenticated_dashboard_redirects(client):
    res = client.get('/dashboard')
    assert res.status_code == 302
    assert '/login' in res.headers['Location'] or '/' in res.headers['Location']

def test_authenticated_dashboard_access(auth_client):
    res = auth_client.get('/dashboard')
    assert res.status_code == 200
    assert b"Knowledge Base" in res.data or b"Hey, teststudent" in res.data

def test_keep_alive_endpoint(client):
    res = client.get('/keep-alive')
    assert res.status_code == 200
    assert res.json == {"status": "alive"}

def test_knowledge_list_endpoint(auth_client, app, test_user_id):
    with app.app_context():
        from app.extensions import db
        ks = KnowledgeSource(user_id=test_user_id, title="Calculus Chapter 1", chunk_count=3)
        db.session.add(ks)
        db.session.commit()

    res = auth_client.get('/knowledge/')
    assert res.status_code == 200
    data = res.get_json()
    assert 'sources' in data
    assert len(data['sources']) == 1
    assert data['sources'][0]['title'] == "Calculus Chapter 1"
    assert data['sources'][0]['chunk_count'] == 3

def test_knowledge_upload_route(auth_client):
    dummy_text = b"Photosynthesis transforms light into energy. Chloroplasts contain chlorophyll."
    data = {
        'file': (io.BytesIO(dummy_text), 'biology.txt'),
        'title': 'Biology Unit 1'
    }
    
    with patch('app.services.embeddings.embed_texts', return_value=[[0.1]*768, [0.2]*768]):
        res = auth_client.post('/knowledge/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
        assert res.status_code == 200
        assert b"Biology Unit 1" in res.data or b"Successfully indexed" in res.data


def test_quiz_generation_requires_topic(auth_client):
    res = auth_client.post('/generate_quiz', data={'topic': ''}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Topic is required." in res.data


def test_quiz_generation_topic_only(auth_client):
    dummy_questions = [
        {"question": "What is the capital of Italy?", "options": ["Rome", "Milan", "Naples", "Turin"], "answer_index": 0}
    ]
    with patch('app.services.gemini.generate_quiz_content', return_value=dummy_questions):
        res = auth_client.post('/generate_quiz', data={'topic': 'Roman History'}, follow_redirects=True)
        assert res.status_code == 200
        assert b"What is the capital of Italy?" in res.data


def test_quiz_generation_with_rag_knowledge_source(auth_client, app, test_user_id):
    with app.app_context():
        from app.extensions import db
        from app.models.chunk import KnowledgeChunk
        ks = KnowledgeSource(user_id=test_user_id, title="Physics 101", chunk_count=1)
        db.session.add(ks)
        db.session.flush()
        chunk = KnowledgeChunk(source_id=ks.id, content="Newton's second law is F = ma.", chunk_index=0, embedding=[0.1]*768)
        db.session.add(chunk)
        db.session.commit()
        ks_id = ks.id

    dummy_questions = [
        {"question": "What is Newton second law?", "options": ["F=ma", "E=mc^2", "V=IR", "P=IV"], "answer_index": 0}
    ]
    with patch('app.services.retrieval.embed_query', return_value=[0.1]*768), \
         patch('app.services.gemini.generate_quiz_content', return_value=dummy_questions) as mock_gen:
        res = auth_client.post('/generate_quiz', data={
            'topic': 'Second Law of Motion',
            'knowledge_source_id': str(ks_id)
        }, follow_redirects=True)
        assert res.status_code == 200
        assert b"What is Newton second law?" in res.data
        assert mock_gen.called
        # Verify rag_context was passed to Gemini
        call_kwargs = mock_gen.call_args[1]
        assert "Newton's second law is F = ma." in call_kwargs.get('rag_context', '')

