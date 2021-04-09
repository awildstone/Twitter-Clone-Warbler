"""User View tests."""
# FLASK_ENV=production python3 -m unittest test_user_views.py

import os
from unittest import TestCase
from models import db, connect_db, Message, User

#set DB environment to test DB
os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY
#disable WTForm CSRF validation
app.config['WTF_CSRF_ENABLED'] = False

db.create_all()

class UserViewTestCase(TestCase):
    """Test views for user."""

    def setUp(self):
        """Create test client, add sample data."""
        db.create_all()

        self.client = app.test_client()

        self.user1 = User.signup(username="testuser1", email="test1@test.com", password="testuser1", image_url=None)
        self.user1.id = 10
        self.user2 = User.signup(username="testuser2", email="test2@test.com", password="testuser2", image_url=None)
        self.user2.id = 22
        self.user3 = User.signup(username="ilovecats", email="catlover@test.com", password="password1", image_url=None)
        self.user3.id = 31
        self.user4 = User.signup(username="birbsrcool", email="chirp@test.com", password="secret", image_url=None)
        self.user4.id = 45

        db.session.commit()
    
    def tearDown(self):
        """ Rollback any failed sessions & drop tables. """

        db.session.rollback()
        db.session.remove()
        db.drop_all()


    def test_show_users(self):
        """ Does list_users() show all users? """

        with self.client as c:
            res = c.get("/users")
            
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'@testuser1', res.data)
            self.assertIn(b'@testuser2', res.data)
            self.assertIn(b'@ilovecats', res.data)
            self.assertIn(b'@birbsrcool', res.data)
    
    def test_search_users(self):
        """ Does search only show users that match query? """

        with self.client as c:
            res = c.get("/users?q=test")

            self.assertEqual(res.status_code, 200)
            self.assertIn(b'@testuser1', res.data)
            self.assertIn(b'@testuser2', res.data)
            self.assertNotIn(b'@ilovecats', res.data)
            self.assertNotIn(b'@birbsrcool', res.data)