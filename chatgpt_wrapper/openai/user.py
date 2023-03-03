import logging
import hashlib
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from chatgpt_wrapper.openai.orm import Orm, User
import chatgpt_wrapper.debug as debug

class UserManagement:
    def __init__(self, database_uri):
        self.engine = create_engine(database_uri)
        session = sessionmaker(bind=self.engine)
        self.session = session()
        self.orm = Orm(database_uri, logging.WARNING)

    def find_user_by_id(self, user_id):
        user = self.session.get(User, user_id)
        return user

    def find_user_by_username_or_email(self, username_or_email):
        identifier = username_or_email.lower()
        user = self.session.query(User).filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()
        return user

    def hash_password(self, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        return hashed_password

    def register(self, username, email, password, default_model='default', preferences={}):
        # Lowercase username and email
        username = username.lower()
        if email:
            email = email.lower()
        if password:
            self.hash_password(password)
        # Check if the username or email is equal to the email of an existing user.
        existing_user = self.session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            return False, "Username or email is already in use."

        self.orm.add_user(username, password, email, default_model, preferences)

        return True, "User successfully registered."

    def login(self, identifier, password):
        # Lowercase identifier
        identifier = identifier.lower()

        # Get the user with the specified identifier (username or email)
        user = self.find_user_by_username_or_email(identifier)
        if not user:
            return False, "Username or email not found."

        # Hash the password and compare it to the hashed password in the database
        if self.hash_password(password) != user.password:
            return False, "Incorrect password."

        # Update the last login time
        user.last_login_time = datetime.datetime.utcnow()
        self.session.commit()
        self.session.refresh(user)
        self.session.close()

        return True, "Login successful."

    def logout(self, user_id):
        # Logout functionality is usually implemented on the frontend, so this method can be left blank
        pass

    def edit(self, user_id, username=None, email=None, password=None, default_model=None):

        # Get the user with the specified user_id
        user = self.find_user_by_id(user_id)
        if not user:
            return False, "User not found."

        # Check if the new username or email is equal to the email of an existing user
        if username:
            username = username.lower()
            existing_user = self.session.query(User).filter(User.email == username).first()
            if existing_user:
                return False, "Username cannot be the same as an existing user's email."
            user.username = username

        if email:
            email = email.lower()
            existing_user = self.session.query(User).filter(User.username == email).first()
            if existing_user:
                return False, "Email cannot be the same as an existing user's username."
            user.email = email

        if password:
            # Hash the password before saving
            user.password = self.hash_password(password)

        if default_model:
            user.default_model = default_model

        self.session.commit()
        self.session.close()

        return True, "User successfully edited."

    def delete(self, user_id):
        # Get the user with the specified user_id
        user = self.find_user_by_id(user_id)
        if not user:
            return False, "User not found."

        # Delete the user
        self.session.delete(user)
        self.session.commit()
        self.session.close()

        return True, "User successfully deleted."
