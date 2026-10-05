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
