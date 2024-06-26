"""SQLAlchemy models for Warbler."""

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()

db = SQLAlchemy()
dbx = db.session.execute

DEFAULT_IMAGE_URL = (
    "https://icon-library.com/images/default-user-icon/" +
    "default-user-icon-28.jpg")

DEFAULT_HEADER_IMAGE_URL = (
    "https://images.unsplash.com/photo-1519751138087-5bf79df62d5b?ixlib=" +
    "rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=for" +
    "mat&fit=crop&w=2070&q=80")


class Follow(db.Model):
    """Connection of a follower <-> followed_user."""

    __tablename__ = 'follows'

    # Adds constraint: Does not allow you to follow yourself or a non-existent user
    __table_args__ = (
        db.UniqueConstraint("user_being_followed_id", "user_following_id"),
    )

    # Ex: who is the user following following? Andrea, Zach, Joel
    user_being_followed_id = db.mapped_column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
        nullable=False,
    )

    # The user doing the following -> USER followed Andrea
    user_following_id = db.mapped_column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
        nullable=False,
    )

    # Ex: who is the user following following? Andrea, Zach, Joel
    followed_user = db.relationship(
        "User",
        foreign_keys=[user_following_id],
        back_populates="followers_users",
    )

    # The user doing the following -> USER followed Andrea
    following_user = db.relationship(
        "User",
        foreign_keys=[user_being_followed_id],
        back_populates="following_users",
    )


class Like(db.Model):
    """Connection of a user <-> a message."""

    __tablename__ = 'likes'

    user_id = db.mapped_column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
        nullable=False,
    )

    message_id = db.mapped_column(
        db.Integer,
        db.ForeignKey('messages.id', ondelete="cascade"),
        primary_key=True,
        nullable=False,
    )

    user_liking_the_message = db.relationship(
        "User",
        # TODO: this is not needed, because we already specified and SQLalchemy know what to join on
        foreign_keys=[user_id],
        # TODO: rename because it's not technically messages, it's instances of likes
        back_populates="liked_messages",
    )

    message_the_user_liked = db.relationship(
        "Message",
        foreign_keys=[message_id],
        back_populates="users_who_liked",  # TODO: rename because it's still likes
    )


class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.mapped_column(
        db.Integer,
        db.Identity(),
        primary_key=True,
    )

    email = db.mapped_column(
        db.String(50),
        nullable=False,
        unique=True,
    )

    username = db.mapped_column(
        db.String(30),
        nullable=False,
        unique=True,
    )

    image_url = db.mapped_column(
        db.String(255),
        nullable=False,
        default=DEFAULT_IMAGE_URL,
    )

    header_image_url = db.mapped_column(
        db.String(255),
        nullable=False,
        default=DEFAULT_HEADER_IMAGE_URL,
    )

    bio = db.mapped_column(
        db.Text,
        nullable=False,
        default="",
    )

    location = db.mapped_column(
        db.String(30),
        nullable=False,
        default="",
    )

    password = db.mapped_column(
        db.String(100),
        nullable=False,
    )

    ############################################################################
    # Relationships

    messages = db.relationship(
        "Message",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # The users that the User is following.
    following_users = db.relationship(
        "Follow",
        foreign_keys=[Follow.user_following_id],
        back_populates="followed_user",
        cascade="all, delete-orphan",
    )

    # All the users that follow the User.
    followers_users = db.relationship(
        "Follow",
        foreign_keys=[Follow.user_being_followed_id],
        back_populates="following_user",
        cascade="all, delete-orphan",
    )

    # All the messages liked by the User.
    liked_messages = db.relationship(  # TODO: rename this
        "Like",
        # TODO: take this out because there's only one relationship; call it out if it's unexpected
        foreign_keys=[Like.user_id],
        back_populates="user_liking_the_message",
    )

    ############################################################################
    # Lists of Relationships

    @property
    def likes(self):  # : TODO: rename, this is now the liked_messages
        """ Return a list of every message the User liked """
        return [like.message_the_user_liked for like in self.liked_messages]  # : TODO: change name

    @property
    def following(self):
        """ Return a list of everyone the User follows """
        return [follow.following_user for follow in self.following_users]

    @property
    def followers(self):
        """ Return a list of all the followers the User has """
        return [follow.followed_user for follow in self.followers_users]

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    ############################################################################
    # Class Methods

    @classmethod
    def signup(cls, username, email, password, image_url=DEFAULT_IMAGE_URL):
        """Sign up user.

        Hashes password and adds user to session.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            image_url=image_url,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If this can't find matching user (or if password is wrong), returns
        False.
        """

        q = db.select(cls).filter_by(username=username)
        user = dbx(q).scalar_one_or_none()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

    @classmethod
    def is_username_taken(cls, username):
        """ Checks if the username exists in the database already. """

        q = db.select(User.id).where(User.username == username)
        user = dbx(q).first()

        return bool(user)

    @classmethod
    def is_email_taken(cls, email):
        """ Checks if the email exists in the database already. """

        q = db.select(User.id).where(User.email == email)
        user = dbx(q).first()

        return bool(user)

    ############################################################################
    # Follows

    def follow(self, other_user):
        """Follow another user."""

        follow = Follow(
            user_being_followed_id=other_user.id,
            user_following_id=self.id
        )
        db.session.add(follow)

    def unfollow(self, other_user):
        """Stop following another user."""

        q = (db
             .delete(Follow)
             .filter_by(
                 user_being_followed_id=other_user.id,
                 user_following_id=self.id)
             )
        dbx(q)

    def is_followed_by(self, other_user):
        """Is this user followed by `other_user`?"""

        found_user_list = [
            user for user in self.followers if user == other_user]
        return len(found_user_list) == 1

    def is_following(self, other_user):
        """Is this user following `other_user`?"""

        found_user_list = [
            user for user in self.following if user == other_user]
        return len(found_user_list) == 1

    ############################################################################
    # Like

    def like(self, message_id):
        """ Like a message by a user """

        like = Like(
            message_id=message_id,
            user_id=self.id,
        )
        db.session.add(like)

    def unlike(self, message_id):
        """ Unlike a message by a user """

        q = (db
             .delete(Like)
             .filter_by(
                 message_id=message_id,
                 user_id=self.id,)
             )
        dbx(q)

    def is_liked(self, message_id):
        """ Does user like this message? """

        found_likes = [
            liked_msg for liked_msg in self.likes if liked_msg.id == message_id]

        return len(found_likes) == 1


class Message(db.Model):
    """An individual message ("warble")."""

    __tablename__ = 'messages'

    id = db.mapped_column(
        db.Integer,
        db.Identity(),
        primary_key=True,
    )

    text = db.mapped_column(
        db.String(140),
        nullable=False,
    )

    timestamp = db.mapped_column(
        db.DateTime,
        nullable=False,
        default=db.func.current_timestamp(),
    )

    user_id = db.mapped_column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )

    user = db.relationship(
        "User",
        back_populates="messages",
    )

    users_who_liked = db.relationship(
        "Like",
        foreign_keys=[Like.message_id],
        back_populates="message_the_user_liked",
    )
