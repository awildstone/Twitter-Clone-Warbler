"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python3 -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()
    
    def tearDown(self):
        """ Rollback any failed sessions & drop tables. """
        db.session.rollback()
        db.session.remove()
        db.drop_all()


    def test_add_message(self):
        """ Can messages_add() add a message? """

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")
    
    def test_add_msg_without_session(self):
        """ Does messages_add() prevent adding a message without a valid user session? """
        with self.client as c:
            res = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(Message.query.all()), 0)
            self.assertIn(b'Access unauthorized.', res.data)

    def test_add_msg_invalid_user(self):
        """ Does messages_add() prevent adding a message with an invalid user? """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 99
        
            res = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(Message.query.all()), 0)
            self.assertIn(b'Access unauthorized.', res.data)
    
    def test_view_add_message_form(self):
        """ Can messages_add() show the add message form? """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
        
            res = c.get("/messages/new")

            self.assertEqual(res.status_code, 200)
            self.assertIn(b'<form method="POST">', res.data)
            self.assertIn(b'<button class="btn btn-outline-success btn-block">Add my message!</button>', res.data)
    
    def test_view_msg(self):
        """ Does messages_show(message_id) show the details for a specific msg? """
        
        #create a test msg
        new_msg = Message(id=7, text="My Test MSG", user_id=self.testuser.id)
        db.session.add(new_msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            msg = Message.query.get(7)
            res = c.get(f"/messages/{msg.id}")

            self.assertEqual(res.status_code, 200)
            self.assertIn(b'My Test MSG', res.data)
            self.assertIn(b'@testuser', res.data)
    
    def test_view_invalid_msg(self):
        """ Does messages_show(message_id) handle request for an invalid msg? """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            res = c.get("/messages/99")

            self.assertEqual(res.status_code, 404)
            self.assertIn(b"404 Not Found", res.data)
    
    
    def test_delete_msg(self):
        """ Does messages_destroy(message_id) delete a specific msg? """

        #create a test msg
        new_msg = Message(id=10, text="My Test MSG", user_id=self.testuser.id)
        db.session.add(new_msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            res = c.post("/messages/10/delete", data={}, follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(Message.query.all()), 0)
    
    def test_delete_msg_invalid_user(self):
        """ Does messages_destroy(message_id) prevent deleting a msg when the user is invalid? """
        #create a test msg & unauthorized user
        new_msg = Message(id=10, text="My Test MSG", user_id=self.testuser.id) #test user created this msg
        wrong_user = User.signup(username="faker", email="faker@test.com", password="fakeuser", image_url=None)
        wrong_user.id = 12

        db.session.add_all([new_msg, wrong_user])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 12 #current user is wrong_user
            
            res = c.post("/messages/10/delete", data={}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(Message.query.all()), 1)
            self.assertIn(b"Access unauthorized.", res.data)
    
    def test_delete_msg_no_auth(self):
        """ Does messages_destroy(message_id) prevent deleting msg with no user authentication? """

        new_msg = Message(id=10, text="My Test MSG", user_id=self.testuser.id)
        db.session.add(new_msg)
        db.session.commit()

        with self.client as c:
            
            res = c.post("/messages/10/delete", data={}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(Message.query.all()), 1)
            self.assertIn(b"Access unauthorized.", res.data)

