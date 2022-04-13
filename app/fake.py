from random import randint
from sqlalchemy.exc import IntegrityError
from faker import Faker
from . import db
from .models import User

def users(count=100):
    fake = Faker()
    i = 0
    while i < count:
        u = User(email=fake.email(),
                 username=fake.user_name(),
                 password='password',
                 confirmed=True,
                 name=fake.name(),
                 location=fake.city(),
                 about_me=fake.text(),
                 member_since=fake.past_date())
        db.session.add(u)
        # The event that a duplicate is generated, the database session 
        # commit will throw an IntegrityError exception. The exception
        # is handled by rolling back the session to cancel that
        # duplicate user. 
        try:
            db.session.commit()
            i += 1
        except IntegrityError:
            db.session.rollback()