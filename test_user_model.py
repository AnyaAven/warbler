"""User model tests."""

import os
from unittest import TestCase

from app import app
from models import db, dbx, User
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import IntegrityError

# To run the tests, you must provide a "test database", since these tests
# delete & recreate the tables & data. In your shell:
#
# Do this only once:
#   $ createdb warbler_test
#
# To run the tests using that test data:
#   $ DATABASE_URL=postgresql:///warbler_test python3 -m unittest

if not app.config['SQLALCHEMY_DATABASE_URI'].endswith("_test"):
    raise Exception(
        "\n\nMust set DATABASE_URL env var to db ending with _test")

# NOW WE KNOW WE'RE IN THE RIGHT DATABASE, SO WE CAN CONTINUE
app.app_context().push()
db.drop_all()
db.create_all()


class UserModelTestCase(TestCase):
    def setUp(self):
        dbx(db.delete(User))
        db.session.commit()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id

    def tearDown(self):
        db.session.rollback()

    def test_user_model_(self):
        u1 = db.session.get(User, self.u1_id)

        # User should have no messages & no followers
        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 0)

    def test_is_following(self):

        user1_id = self.u1_id
        user2_id = self.u2_id

        user1 = db.session.get(User, user1_id)
        user2 = db.session.get(User, user2_id)

        self.assertNotIn(user2, user1.followers)
        self.assertNotIn(user1, user2.following)

        user1.follow(user2)

        db.session.commit()

        self.assertIn(user1, user2.followers)
        self.assertIn(user2, user1.following)

    def test_is_unfollowing(self):

        user1_id = self.u1_id
        user2_id = self.u2_id

        user1 = db.session.get(User, user1_id)
        user2 = db.session.get(User, user2_id)

        user1.follow(user2)

        db.session.commit()

        self.assertIn(user1, user2.followers)
        self.assertIn(user2, user1.following)

        user1.unfollow(user2)

        db.session.commit()

        self.assertNotIn(user1, user2.followers)
        self.assertNotIn(user2, user1.following)


# Does User.signup successfully create a new user given valid credentials?
# Does User.signup fail to create a new user if any of the validations(eg uniqueness, non-nullable fields) fail?


    def test_signup(self):

        u3 = User.signup("user3", "user3@gmail.com", "password3", None)
        db.session.commit()

        u3_is_auth = User.authenticate(u3.username,"password3" )

        self.assertEqual(u3.username, "user3")
        self.assertEqual(u3.email, "user3@gmail.com")
        self.assertNotEqual(u3.password, "password3")
        self.assertIsNot(u3_is_auth, False)
        # TODO: ask how to test hashed_pwd

    def test_signup_failure(self):
        u3 = User.signup("user3", "user3@gmail.com", "password3", None)
        db.session.commit()

        # Cannot have a duplicate username
        with self.assertRaises(IntegrityError):
            User.signup("user3", "unique", "password3", None)
            db.session.commit()

        db.session.rollback()

        db.session.begin()

        # Cannot have a duplicate email
        with self.assertRaises(IntegrityError):
            User.signup("unique1", "user3@gmail.com", "password3", None)
            db.session.commit()

        db.session.rollback()

        db.session.begin()

        # Cannot have duplicate email and username
        with self.assertRaises(IntegrityError):
            User.signup("user3", "user3@gmail.com", "password3", None)
            db.session.commit()




