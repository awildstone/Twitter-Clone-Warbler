"""Message model tests."""
# FLASK_ENV=production python3 -m unittest test_message_model.py

import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Likes

#set environment to test database
os.environ['DATABASE_URL'] = "postgresql:///warbler-test"
# import app after setting DB
from app import app

#create initial tables
db.create_all()


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """ Create test users and test messages. """
        db.create_all()

        #users 
        user1 = User.signup("test1@test.com", "testuser1", "password1", None)
        user2 = User.signup("test2@test.com", "testuser2", "password2", None)
    
        db.session.commit()

        #get users & save as class instances
        self.user1 = User.query.get(1)
        self.user2 = User.query.get(2)

        #messages
        message1 = Message(text="User1 post a message!")
        self.user1.messages.append(message1)

        message2 = Message(text="User2 typed a funny!")
        self.user2.messages.append(message2)

        db.session.commit()

        #get messages & save as class instances
        self.message1 = Message.query.get_or_404(1)
        self.message2 = Message.query.get_or_404(2)

        self.client = app.test_client()
    
    def tearDown(self):
        """ Rollback any failed sessions & drop tables. """

        db.session.rollback()
        db.session.remove()
        db.drop_all()
    
    def test_message_model(self):
        """ Does the Model work? """

        new_message = Message(text="I love cats!", user_id=self.user2.id)
        db.session.add(new_message)
        db.session.commit()

        messages = Message.query.all()
        self.assertEqual(len(messages), 3)
        self.assertEqual(len(self.user2.messages), 2)
        self.assertEqual(self.user2.messages[1].text, "I love cats!")
    
    def test_associate_correct_user(self):
        """ Does the Message Model associate the message with the correct user? """

        self.assertEqual(self.message1.user_id, self.user1.id)
        self.assertEqual(self.message2.user_id, self.user2.id)
        self.assertEqual(self.message1.user, self.user1)
        self.assertEqual(self.message2.user, self.user2)
        self.assertEqual(self.user1.messages[0].text, "User1 post a message!")
        self.assertEqual(self.user2.messages[0].text, "User2 typed a funny!")
    
    def test_create_new_message_valid_user(self):
        """ Does the Message Model create a new message with a valid user? """

        message = Message(text="User1 did it again!", user_id=self.user1.id)
        db.session.add(message)
        db.session.commit()

        messages = Message.query.all()

        self.assertEqual(len(messages), 3)
        self.assertIsInstance(message, Message)
        self.assertEqual(message.text, "User1 did it again!")
        self.assertEqual(message.user_id, self.user1.id)
        self.assertEqual(self.message1.user, self.user1)

    
    def test_create_new_message_fake_user(self):
        """ Does the Message model fail to create a new message without a valid user? """

        fakeuser = User()

        message = Message(text="User1 did it again!", user_id=fakeuser.id)
        db.session.add(message)

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

        db.session.rollback()
        messages = Message.query.all()
        self.assertEqual(len(messages), 2)
        self.assertIsNone(message.id)
        self.assertIsNone(message.timestamp)
        self.assertIsNone(message.user_id)
    
    def test_new_likes(self):
        """ Does the Model add new likes? """

        new_user = User.signup("newuser", "newuser@gmail.com", "password123", None)
        db.session.add(new_user)
        db.session.commit()

        new_msg = Message(text="A new message from a new user", user_id=new_user.id)
        db.session.add(new_msg)
        db.session.commit()

        new_user.likes.append(new_msg)
        db.session.commit()

        likes = Likes.query.all()
        self.assertEqual(len(likes), 1)
        self.assertEqual(likes[0].user_id, new_user.id)
        self.assertEqual(likes[0].message_id, new_msg.id)


    def test_associate_user_likes(self):
        """ Does the Model associate likes with correct user? """

        testlike1 = self.user1.likes.append(self.message2)
        testlike2 = self.user2.likes.append(self.message1)
        db.session.commit()

        likes = Likes.query.all()

        self.assertEqual(len(likes), 2)
        self.assertEqual(likes[0].user_id, self.user1.id)
        self.assertEqual(likes[1].user_id, self.user2.id)

    
    def test_associate_message_likes(self):
        """ Does the Model associate likes with correct message? """

        testlike1 = self.user2.likes.append(self.message2)
        testlike2 = self.user2.likes.append(self.message1)
        db.session.commit()

        likes = Likes.query.all()
        self.assertEqual(len(likes), 2)
        self.assertEqual(likes[0].message_id, self.message2.id)
        self.assertEqual(likes[1].message_id, self.message1.id)

