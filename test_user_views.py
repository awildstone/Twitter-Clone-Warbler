"""User View tests."""
# FLASK_ENV=production python3 -m unittest test_user_views.py

import os
from unittest import TestCase
from models import db, connect_db, Message, User, Follows, Likes

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
            
            res = c.post("/users/follow/45", follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(Follows.query.all()), 1)
            self.assertIn(b"@birbsrcool", res.data)

    
    def test_add_follow_no_auth(self):
        """ Does add_follow(follow_id) prevent an unauthed user from adding a new follow? """

        with self.client as c:

            res = c.post("/users/follow/45", follow_redirects=True)

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
            
            res = c.post("/users/stop-following/31", follow_redirects=True)

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
            
            res = c.post("/users/stop-following/31", follow_redirects=True)

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

    def test_delete_user(self):
        """ Can the authed user delete themself? """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id

            res = c.post("/users/delete", follow_redirects=True)

            all_users = User.query.all()

            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(all_users), 3)
    
    def test_user_add_like(self):
        """ Can an authed user add a new like? """

        #create new test message
        msg = Message(text="Test message for user 2!", user_id=self.user2.id)
        msg.id = 5
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id

            res = c.post("/users/add_like/5", follow_redirects=True)

            user1 = User.query.get(10)

            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(user1.likes), 1)
            self.assertEqual(user1.likes[0].id, 5)
            self.assertEqual(user1.likes[0].user_id, 22)

    def test_user_add_like_no_auth(self):
        """ Does add_like(message_id) prevent a unauthed user from adding a like? """

        #create new test message
        msg = Message(text="Test message for user 2!", user_id=self.user2.id)
        msg.id = 5
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            res = c.post("/users/add_like/5", follow_redirects=True)

            all_likes = Likes.query.all()

            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(all_likes), 0)


    def test_user_remove_like(self):
        """ Can an authed user remove one of their likes? """

        #create test messages
        msg1 = Message(text="Test message for user 2!", user_id=self.user2.id)
        msg1.id = 2
        msg2 = Message(text="Another message for user 2!", user_id=self.user2.id)
        msg2.id = 3

        db.session.add_all([msg1, msg2])
        db.session.commit()

        #create test likes

        like1 = Likes(user_id=self.user1.id, message_id=msg1.id)
        like2 = Likes(user_id=self.user1.id, message_id=msg2.id)

        db.session.add_all([like1, like2])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id

            res = c.post("/users/remove_like/2", follow_redirects=True)

            user1 = User.query.get(10)

            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(user1.likes), 1)
            self.assertEqual(user1.likes[0].id, 3)
            self.assertEqual(user1.likes[0].user_id, 22)




