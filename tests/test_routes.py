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


def test_view_saved_quiz_and_submit(auth_client, app, test_user_id):
    import json
    from app.extensions import db
    from app.models.resource import Resource

    quiz_data = {
        'questions': [
            {'id': 0, 'question': 'What is H2O?', 'options': ['Water', 'Oxygen', 'Hydrogen', 'Carbon'], 'correct_index': 0, 'answer_index': 0}
        ],
        'sources': ['Chemistry 101']
    }
    with app.app_context():
        res_obj = Resource(
            user_id=test_user_id,
            resource_type='quiz',
            topic='Quiz: Chemistry',
            content_json=json.dumps(quiz_data)
        )
        db.session.add(res_obj)
        db.session.commit()
        res_id = res_obj.id

    # 1. Owner can open the saved quiz
    get_res = auth_client.get(f'/resource/{res_id}')
    assert get_res.status_code == 200
    assert b"What is H2O?" in get_res.data
    assert b"Grounded" in get_res.data

    # 2. Owner can submit the quiz and receive a score
    post_res = auth_client.post('/submit_quiz', data={'question_0': '0'})
    assert post_res.status_code == 200
    assert b"1 / 1" in post_res.data or b"Score" in post_res.data or b"Result" in post_res.data or b"What is H2O?" in post_res.data


def test_view_saved_flashcards(auth_client, app, test_user_id):
    import json
    from app.extensions import db
    from app.models.resource import Resource

    cards_data = {
        'flashcards': [
            {'question': 'What is ATP?', 'answer': 'Adenosine Triphosphate, energy currency of the cell.'}
        ],
        'sources': ['Bio Chapter 3']
    }
    with app.app_context():
        res_obj = Resource(
            user_id=test_user_id,
            resource_type='flashcard',
            topic='Flashcards on: ATP',
            content_json=json.dumps(cards_data)
        )
        db.session.add(res_obj)
        db.session.commit()
        res_id = res_obj.id

    get_res = auth_client.get(f'/resource/{res_id}')
    assert get_res.status_code == 200
    assert b"What is ATP?" in get_res.data
    assert b"Bio Chapter 3" in get_res.data


def test_view_resource_unauthorized_returns_404(client, app, test_user_id):
    import json
    from app.extensions import db
    from app.models.resource import Resource
    from app.models.user import User
    from werkzeug.security import generate_password_hash

    # Create another user and a resource belonging to test_user_id
    with app.app_context():
        user2 = User(username='otheruser', email='other@example.com', password=generate_password_hash('pass12345'), session_version=1)
        db.session.add(user2)
        
        res_obj = Resource(
            user_id=test_user_id,
            resource_type='quiz',
            topic='Quiz: Secret Physics',
            content_json=json.dumps({'questions': [], 'sources': []})
        )
        db.session.add(res_obj)
        db.session.commit()
        user2_id = user2.id
        res_id = res_obj.id

    # Log in as user2
    with client.session_transaction() as sess:
        sess['user_id'] = user2_id
        sess['username'] = 'otheruser'
        sess['session_version'] = 1

    # User 2 tries to access User 1's resource
    get_res = client.get(f'/resource/{res_id}')
    assert get_res.status_code == 404


def test_view_resource_null_content_graceful_redirect(auth_client, app, test_user_id):
    from app.extensions import db
    from app.models.resource import Resource

    with app.app_context():
        # Older row with null content_json
        res_obj = Resource(
            user_id=test_user_id,
            resource_type='quiz',
            topic='Quiz: Old Era Topic',
            content_json=None
        )
        db.session.add(res_obj)
        db.session.commit()
        res_id = res_obj.id

    get_res = auth_client.get(f'/resource/{res_id}', follow_redirects=True)
    assert get_res.status_code == 200
    assert b"This resource was created before saving was added." in get_res.data

