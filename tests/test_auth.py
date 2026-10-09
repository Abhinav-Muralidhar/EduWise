import pytest
from app.models.user import User
from app.extensions import db

def test_login_case_insensitive_username(client, test_user_id):
    # test_user_id fixture creates user 'teststudent' with password 'password123'
    # Try uppercase username
    res = client.post('/login', data={
        'username_or_email': 'TestStudent',
        'password': 'password123'
    }, follow_redirects=False)
    assert res.status_code == 302
    assert '/dashboard' in res.headers['Location']

    # Try ALL CAPS username
    res2 = client.post('/login', data={
        'username_or_email': 'TESTSTUDENT',
        'password': 'password123'
    }, follow_redirects=False)
    assert res2.status_code == 302
    assert '/dashboard' in res2.headers['Location']


def test_login_case_insensitive_email(client, test_user_id):
    # Try mixed-case email
    res = client.post('/login', data={
        'username_or_email': 'Student@Example.Com',
        'password': 'password123'
    }, follow_redirects=False)
    assert res.status_code == 302
    assert '/dashboard' in res.headers['Location']


def test_signup_case_insensitive_duplicate_prevention(client, test_user_id):
    # Trying to sign up with existing username in uppercase
    res = client.post('/signup', data={
        'username': 'TESTSTUDENT',
        'email': 'newunique@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert b"Username or Email already exists" in res.data

    # Trying to sign up with existing email in uppercase
    res2 = client.post('/signup', data={
        'username': 'newuser123',
        'email': 'STUDENT@EXAMPLE.COM',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert b"Username or Email already exists" in res2.data


def test_signup_validation(client):
    # Password too short (< 8)
    res = client.post('/signup', data={
        'username': 'validuser',
        'email': 'valid@example.com',
        'password': '123',
        'confirm_password': '123'
    }, follow_redirects=True)
    assert b"Password must be at least 8 characters" in res.data

    # Passwords do not match
    res = client.post('/signup', data={
        'username': 'validuser',
        'email': 'valid@example.com',
        'password': 'password123',
        'confirm_password': 'mismatchpassword'
    }, follow_redirects=True)
    assert b"Passwords do not match" in res.data


def test_password_reset_token_hashed_and_single_use(client, app, test_user_id):
    import hashlib
    from datetime import datetime, timedelta, timezone

    plain_token = "secure-random-reset-token-xyz"
    token_hash = hashlib.sha256(plain_token.encode('utf-8')).hexdigest()

    with app.app_context():
        user = User.query.get(test_user_id)
        user.reset_token = token_hash
        user.reset_token_expiry = datetime.now(timezone.utc) + timedelta(minutes=15)
        db.session.commit()

    # 1. Plain token in URL matches hashed token in DB
    res_get = client.get(f'/reset-password/{plain_token}')
    assert res_get.status_code == 200
    assert b"Reset Password" in res_get.data

    # 2. Reset the password
    res_post = client.post(f'/reset-password/{plain_token}', data={
        'password': 'newpassword123',
        'confirm_password': 'newpassword123'
    }, follow_redirects=False)
    assert res_post.status_code == 302
    assert '/login' in res_post.headers['Location']

    # 3. Token is single-use and cleared from DB, session_version incremented
    with app.app_context():
        user = User.query.get(test_user_id)
        assert user.reset_token is None
        assert user.reset_token_expiry is None
        assert user.session_version == 2

    # 4. Reusing the token fails
    res_reuse = client.get(f'/reset-password/{plain_token}', follow_redirects=False)
    assert res_reuse.status_code == 302
    assert '/forgot-password' in res_reuse.headers['Location']


def test_delete_account_cascades_sources_chunks_resources(client, app, test_user_id):
    from app.models.resource import Resource
    from app.models.knowledge_source import KnowledgeSource
    from app.models.chunk import KnowledgeChunk

    with app.app_context():
        # Create resources, knowledge sources, and knowledge chunks
        res = Resource(user_id=test_user_id, resource_type='pdf', topic='Biology Notes')
        db.session.add(res)
        
        ks = KnowledgeSource(user_id=test_user_id, title='Cell Biology', chunk_count=2)
        db.session.add(ks)
        db.session.flush()

        c1 = KnowledgeChunk(source_id=ks.id, content='Mitochondria is the powerhouse of the cell', chunk_index=0)
        c2 = KnowledgeChunk(source_id=ks.id, content='Chloroplasts perform photosynthesis', chunk_index=1)
        db.session.add_all([c1, c2])
        db.session.commit()

        ks_id = ks.id

    # Authenticate client
    with client.session_transaction() as sess:
        sess['user_id'] = test_user_id
        sess['username'] = "teststudent"
        sess['session_version'] = 1

    # Delete account with correct password
    delete_res = client.post('/profile/delete-account', data={'password': 'password123'}, follow_redirects=False)
    assert delete_res.status_code == 302
    assert '/login' in delete_res.headers['Location']

    # Verify everything was deleted in DB
    with app.app_context():
        assert User.query.get(test_user_id) is None
        assert Resource.query.filter_by(user_id=test_user_id).count() == 0
        assert KnowledgeSource.query.filter_by(user_id=test_user_id).count() == 0
        assert KnowledgeChunk.query.filter_by(source_id=ks_id).count() == 0


def test_session_version_rejection_after_password_change(client, app, test_user_id):
    # Simulate a logged-in user on Browser 1 (session_version = 1)
    # and Browser 2 (session_version = 1)
    with client.session_transaction() as sess:
        sess['user_id'] = test_user_id
        sess['username'] = "teststudent"
        sess['session_version'] = 1

    # Access protected route before password change
    res_before = client.get('/dashboard')
    assert res_before.status_code == 200

    # User changes password on Browser 1
    change_res = client.post('/profile/change-password', data={
        'current_password': 'password123',
        'new_password': 'brandnewpassword123',
        'confirm_password': 'brandnewpassword123'
    }, follow_redirects=True)
    assert change_res.status_code == 200
    assert b"Password updated successfully!" in change_res.data

    with app.app_context():
        user = User.query.get(test_user_id)
        assert user.session_version == 2

    # Browser 1's session was updated to session_version = 2 and continues to work
    res_browser1 = client.get('/dashboard')
    assert res_browser1.status_code == 200

    # Simulate Browser 2 (stale session with session_version = 1)
    with client.session_transaction() as sess:
        sess['user_id'] = test_user_id
        sess['username'] = "teststudent"
        sess['session_version'] = 1  # stale

    res_stale = client.get('/dashboard', follow_redirects=False)
    assert res_stale.status_code == 302
    assert '/login' in res_stale.headers['Location']
