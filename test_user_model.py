"""User model tests."""

# run these tests like:
#
#    FLASK_ENV=production python3 -m unittest test_user_model.py

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

class UserModelTestCase(TestCase):
    """Test views for user."""

    def setUp(self):
        """Create test client, add sample data."""

        db.create_all()

        user1 = User.signup("test1@test.com", "testuser1", "password1", None)
        id1 = 1
        user1.id = 1
        user2 = User.signup("test2@test.com", "testuser2", "password2", None)
        id2 = 2
        user2.id = 2

        db.session.commit()

        #get user instances from DB & save as class instances
        self.user1 = User.query.get(id1)
        self.user2 = User.query.get(id2)

        self.client = app.test_client()
    

    def tearDown(self):
        """ Rollback any failed sessions & drop tables. """

        db.session.rollback()
        db.session.remove()
        db.drop_all()

######## User Model tests ##########
    def test_user_model(self):
        """Does basic model work?"""

        # User should have no messages & no followers
        self.assertEqual(len(self.user1.messages), 0)
        self.assertEqual(len(self.user1.followers), 0)
        #should be instance of User
        self.assertIsInstance(self.user1, User)
    

    def test_user_repr(self):
        """ Does the repr method work as expected? """

        self.assertEqual(repr(self.user1), f"<User #{self.user1.id}: {self.user1.username}, {self.user1.email}>")
        self.assertEqual(repr(self.user2), f"<User #{self.user2.id}: {self.user2.username}, {self.user2.email}>")
    
######## Following tests ##########
    def test_user_following(self):
        """ Does is_following successfully detect when user1 is following user2? """

        new_follower = Follows(
        user_being_followed_id = self.user2.id,
        user_following_id = self.user1.id)

        db.session.add(new_follower)
        db.session.commit()

        self.assertTrue(self.user1.is_following(self.user2))


    def test_user_not_following(self):
        """ Does is_following successfully detect when user1 is not following user2? """

        self.assertFalse(self.user1.is_following(self.user2))


    def test_user_followed_by(self):
        """ Does is_followed_by successfully detect when user1 is followed by user2 """

        new_follower = Follows(
        user_being_followed_id = self.user1.id,
        user_following_id = self.user2.id)

        db.session.add(new_follower)
        db.session.commit()

        self.assertTrue(self.user1.is_followed_by(self.user2))
    

    def test_user_not_followed(self):
        """ Does is_followed_by successfully detect when user1 is not followed by user2 """

        self.assertFalse(self.user1.is_followed_by(self.user2))

######## Signup tests ##########
    def test_signup_user_valid(self):
        """ Does User.signup() successfully create a new user given valid credentials? """

        user = User.signup('newusername', 'newuser@gmail.com', 'password123', None)

        user.id = 7
        db.session.commit()

        self.assertIsInstance(user, User)
        self.assertEqual(user.id, 7)
        self.assertEqual(user.username, 'newusername')
        self.assertEqual(user.email, 'newuser@gmail.com')
    

    def test_signup_user_duplicate_username(self):
        """ Does User.create fail to create a new user if athe username already exists? """

        user = User.signup('testuser1', 'newuser@gmail.com', 'password123', None)

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

        db.session.rollback()
        self.assertIsNone(user.id)

    
    def test_signup_user_invalid_username(self):
        """ Does User.create fail to create a new user if the username is invalid? """

        user = User.signup(None, 'newuser@gmail.com', 'password123', None)

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
        
        db.session.rollback()
        self.assertIsNone(user.id)
    

    def test_signup_user_invalid_email(self):
        """ Does User.create fail to create a new user if the email is invalid? """

        user = User.signup('newuserusername', None, 'password123', None)

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

        db.session.rollback()
        self.assertIsNone(user.id)


    def test_signup_user_invalid_password(self):
        """ Does User.create fail to create a new user if the password is invalid? """

        with self.assertRaises(ValueError) as context:
            user = User.signup('newuserusername', 'newuser@gmail.com', None, None)
        
        with self.assertRaises(ValueError) as context:
            user = User.signup('newuserusername', 'newuser@gmail.com', "", None)

######## Authenticate tests ##########
    def test_user_authenticate_valid(self):
        """ Does User.authenticate successfully return a user when given a valid username and password? """

        user = User.authenticate(self.user1.username, 'password1')
        db.session.commit()
        self.assertIsInstance(user, User)
    

    def test_user_authenticate_username_invalid(self):
        """ Does User.authenticate fail to return a user when the username is invalid? """

        user = User.authenticate('testuser11', 'password1')
        self.assertFalse(user)
    

    def test_user_authenticate_password_invalid(self):
        """ Does User.authenticate fail to return a user when the password is invalid? """

        user = User.authenticate(self.user2.username, 'password1')
        self.assertFalse(user)