import io
from unittest.mock import patch
import pytest
from app.models.resource import Resource
from app.models.knowledge_source import KnowledgeSource
from app.models.chunk import KnowledgeChunk
from app.extensions import db
from app import create_app
from app.config import Config

def test_guest_quiz_generation(client, app):
    dummy_questions = [
        {"question": "What is the powerhouse of the cell?", "options": ["Mitochondria", "Nucleus", "Ribosome", "Golgi"], "answer_index": 0}
    ]
    with patch('app.services.gemini.generate_quiz_content', return_value=dummy_questions):
        res = client.post('/generate_quiz', data={'topic': 'Cell Biology'}, follow_redirects=True)
        assert res.status_code == 200
        assert b"What is the powerhouse of the cell?" in res.data
        assert b"Guest Mode" in res.data or b"Sign up" in res.data

    with app.app_context():
        assert Resource.query.count() == 0
        assert KnowledgeSource.query.count() == 0
        assert KnowledgeChunk.query.count() == 0


def test_guest_flashcards_generation(client, app):
    dummy_cards = [
        {"question": "What is Mitosis?", "answer": "Cell division resulting in two identical daughter cells."}
    ]
    with patch('app.services.gemini.generate_flashcards', return_value=dummy_cards):
        res = client.post('/generate_flashcards', data={'topic': 'Cell Division'}, follow_redirects=True)
        assert res.status_code == 200
        assert b"What is Mitosis?" in res.data
        assert b"Guest Deck Preview" in res.data

    with app.app_context():
        assert Resource.query.count() == 0


def test_guest_explanation_generation(client, app):
    dummy_explanation = "Gravity is a fundamental interaction that causes mutual attraction between all things with mass."
    with patch('app.services.gemini.generate_explanation', return_value=dummy_explanation):
        res = client.post('/present', data={'topic': 'Gravity'}, follow_redirects=True)
        assert res.status_code == 200
        assert b"Gravity" in res.data

    with app.app_context():
        assert Resource.query.count() == 0


def test_guest_summary_generation(client, app):
    dummy_summary = "This is a concise summary of the provided text."
    with patch('app.services.gemini.generate_summary', return_value=dummy_summary):
        res = client.post('/summarize_text', data={'text': 'Photosynthesis is the process by which plants use sunlight...'}, follow_redirects=True)
        assert res.status_code == 200
        assert b"This is a concise summary" in res.data

    with app.app_context():
        assert Resource.query.count() == 0


def test_guest_rag_attempt_rejected_quiz(client):
    with patch('app.services.gemini.generate_quiz_content') as mock_gen:
        res = client.post('/generate_quiz', data={'topic': 'Gravity', 'knowledge_source_id': '1'}, follow_redirects=True)
        assert res.status_code == 200
        assert b"Sign up to use your own documents" in res.data
        mock_gen.assert_not_called()


def test_guest_rag_attempt_rejected_flashcards(client):
    with patch('app.services.gemini.generate_flashcards') as mock_gen:
        res = client.post('/generate_flashcards', data={'topic': 'Chemistry', 'knowledge_source_id': '1'}, follow_redirects=True)
        assert res.status_code == 200
        assert b"Sign up to use your own documents" in res.data
        mock_gen.assert_not_called()


def test_guest_rag_attempt_rejected_present(client):
    with patch('app.services.gemini.generate_explanation') as mock_gen:
        res = client.post('/present', data={'topic': 'Physics', 'knowledge_source_id': '1'}, follow_redirects=True)
        assert res.status_code == 200
        assert b"Sign up to use your own documents" in res.data
        mock_gen.assert_not_called()


def test_guest_rag_attempt_rejected_summary(client):
    with patch('app.services.gemini.generate_summary') as mock_gen:
        res = client.post('/summarize_text', data={'text': 'Some text', 'knowledge_source_id': '1'}, follow_redirects=True)
        assert res.status_code == 200
        assert b"Sign up to use your own documents" in res.data
        mock_gen.assert_not_called()


def test_pptx_and_pdf_remain_login_required(client):
    res_pptx = client.post('/generate', data={'topic': 'Solar System'})
    assert res_pptx.status_code == 302
    assert '/login' in res_pptx.headers['Location']

    res_pdf = client.post('/generate_pdf', data={'topic': 'Solar System'})
    assert res_pdf.status_code == 302
    assert '/login' in res_pdf.headers['Location']


def test_guest_rate_limiting_enforcement():
    class RateLimitTestConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        WTF_CSRF_ENABLED = False
        SECRET_KEY = 'test-rate-limit-secret'
        RATELIMIT_ENABLED = True
        RATELIMIT_STORAGE_URI = 'memory://'
        SCHEDULER_API_ENABLED = False
        JOBS = []

    rate_app = create_app(RateLimitTestConfig)
    dummy_questions = [{"question": "Q?", "options": ["A", "B", "C", "D"], "answer_index": 0}]

    with rate_app.app_context():
        db.create_all()
        client = rate_app.test_client()

        with patch('app.services.gemini.generate_quiz_content', return_value=dummy_questions):
            # 5 requests should succeed
            for i in range(5):
                res = client.post('/generate_quiz', data={'topic': f'Topic {i}'}, environ_base={'REMOTE_ADDR': '192.168.1.100'})
                assert res.status_code == 200

            # 6th request exceeds 5/hour guest limit
            res = client.post('/generate_quiz', data={'topic': 'Topic 6'}, environ_base={'REMOTE_ADDR': '192.168.1.100'})
            assert res.status_code == 429

        db.session.remove()
        db.drop_all()
