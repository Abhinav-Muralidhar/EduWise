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
