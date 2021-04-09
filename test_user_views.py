"""User View tests."""
# FLASK_ENV=production python3 -m unittest test_user_views.py

import os
from unittest import TestCase
from models import db, connect_db, Message, User, Follows

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
    
    def test_show_user_profile(self):
        """ Does users_show(user_id) display a user's profile? """

        with self.client as c:
            res = c.get(f"/users/{self.user3.id}")

            self.assertEqual(res.status_code, 200)
            self.assertIn(b'@ilovecats', res.data)
    
    def test_view_user_following(self):
        """ Can authed user view list of users being followed by a user? """
        #setup test follows
        f1 = Follows(user_being_followed_id=self.user2.id, user_following_id=self.user1.id)
        f2 = Follows(user_being_followed_id=self.user3.id, user_following_id=self.user1.id)
        f3 = Follows(user_being_followed_id=self.user4.id, user_following_id=self.user1.id)

        db.session.add_all([f1, f2, f3])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id
            
            res = c.get(f"/users/{self.user1.id}/following")

            self.assertEqual(res.status_code, 200)
            self.assertIn(b'@testuser2', res.data)
            self.assertIn(b'@ilovecats', res.data)
            self.assertIn(b'@birbsrcool', res.data)
    
    def test_view_user_following_not_auth(self):
        """ Does show_following(user_id) prevent unauthed users from vieweing the user's follow list? """

        #setup test follows
        f1 = Follows(user_being_followed_id=self.user2.id, user_following_id=self.user1.id)
        f2 = Follows(user_being_followed_id=self.user3.id, user_following_id=self.user1.id)
        f3 = Follows(user_being_followed_id=self.user4.id, user_following_id=self.user1.id)

        db.session.add_all([f1, f2, f3])
        db.session.commit()

        with self.client as c:
            res = c.get(f"/users/{self.user1.id}/following", follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Access unauthorized.', res.data)


    def test_view_user_followers(self):
        """ Can authed user view a user's followers? """

        #setup test follows
        f1 = Follows(user_being_followed_id=self.user1.id, user_following_id=self.user2.id)
        f2 = Follows(user_being_followed_id=self.user1.id, user_following_id=self.user3.id)
        f3 = Follows(user_being_followed_id=self.user1.id, user_following_id=self.user4.id)

        db.session.add_all([f1, f2, f3])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id
            
            res = c.get(f"/users/{self.user1.id}/followers")

            self.assertEqual(res.status_code, 200)
            self.assertIn(b'@testuser2', res.data)
            self.assertIn(b'@ilovecats', res.data)
            self.assertIn(b'@birbsrcool', res.data)
    

    def test_view_user_followers_not_auth(self):
        """ Does users_followers(user_id) prevent an unauthed user from viewing the user's followers? """

        #setup test follows
        f1 = Follows(user_being_followed_id=self.user1.id, user_following_id=self.user2.id)
        f2 = Follows(user_being_followed_id=self.user1.id, user_following_id=self.user3.id)
        f3 = Follows(user_being_followed_id=self.user1.id, user_following_id=self.user4.id)

        db.session.add_all([f1, f2, f3])
        db.session.commit()

        with self.client as c:
            res = c.get(f"/users/{self.user1.id}/followers", follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Access unauthorized.', res.data)


    def test_add_follow(self):
        """ Can an authed user add a new follow? """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id
            
            res = c.post("/users/follow/45", data={}, follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(Follows.query.all()), 1)
            self.assertIn(b"@birbsrcool", res.data)

    
    def test_add_follow_no_auth(self):
        """ Does add_follow(follow_id) prevent an unauthed user from adding a new follow? """

        with self.client as c:

            res = c.post("/users/follow/45", data={}, follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Access unauthorized.", res.data)

    def test_stop_follow(self):
        """ Can an authed user stop following a user? """

        #setup test follows
        f1 = Follows(user_being_followed_id=self.user2.id, user_following_id=self.user1.id)
        f2 = Follows(user_being_followed_id=self.user3.id, user_following_id=self.user1.id)
        f3 = Follows(user_being_followed_id=self.user4.id, user_following_id=self.user1.id)

        db.session.add_all([f1, f2, f3])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id
            
            res = c.post("/users/stop-following/31", data={}, follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(Follows.query.all()), 2)
            self.assertIn(b"@testuser2", res.data)
            self.assertIn(b"@birbsrcool", res.data)
            self.assertNotIn(b"@ilovecats", res.data)


    def test_stop_follow_no_auth(self):
        """ Does stop_following(follow_id) prevent an unauthed user from un-following a user? """

        #setup test follows
        f1 = Follows(user_being_followed_id=self.user2.id, user_following_id=self.user1.id)
        f2 = Follows(user_being_followed_id=self.user3.id, user_following_id=self.user1.id)
        f3 = Follows(user_being_followed_id=self.user4.id, user_following_id=self.user1.id)

        db.session.add_all([f1, f2, f3])
        db.session.commit()

        with self.client as c:
            
            res = c.post("/users/stop-following/31", data={}, follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(Follows.query.all()), 3)
            self.assertIn(b"Access unauthorized.", res.data)

    def test_edit_profile(self):
        """ Can an authed user edit profile? """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id
            
            res = c.post("/users/profile", data={"username": "im#1", "email": "num@one.com", "image_url": "/static/images/default-pic.png", "header_image_url": "/static/images/warbler-hero.jpg", "bio": "I'm #1!!", "location": "Denver", "password": "testuser1"}, follow_redirects=True)
            
            updated_user = User.query.get(self.user1.id)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(updated_user.username, "im#1")
            self.assertEqual(updated_user.email, "num@one.com")

    
    def test_edit_profile_no_auth(self):
        """ Is an unauthed user prevented from editing a profile? """

        with self.client as c:
            res = c.post("/users/profile", data={"username": "im#1", "email": "num@one.com", "image_url": "/static/images/default-pic.png", "header_image_url": "/static/images/warbler-hero.jpg", "bio": "I'm #1!!", "location": "Denver", "password": "testuser1"}, follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Access unauthorized.", res.data)
    
    def test_user_add_like(self):
        """ Can an authed user add a new like? """