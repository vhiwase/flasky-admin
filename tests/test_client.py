import unittest
from app import create_app, db
from app.models import Role, User
from base64 import b64encode
import re


class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        # Test redirect to login page functionality for unauthorized users
        response = self.client.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Login' in response.get_data(as_text=True))

    def test_login_and_logout(self):
        # Register users in database
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u1 = User(email='john@example.com', 
                 password='cat',
                  username='john',  
                 confirmed=True,
                 role=r)
        u2 = User(email='adam@example.com', 
                 password='dog',
                  username='adam',  
                 confirmed=False,
                 role=r)
        db.session.add_all([u1, u2])
        db.session.commit()
        
        # log in with the new account with confirmation
        response1 = self.client.post('/auth/login', data={
            'email': 'john@example.com',
            'password': 'cat'
        }, follow_redirects=True)
        self.assertEqual(response1.status_code, 200)
        self.assertTrue(re.search('Training', response1.get_data(as_text=True)))
        
        # log in with the new account without confirmation
        response2 = self.client.post('/auth/login', data={
            'email': 'adam@example.com',
            'password': 'dog'
        }, follow_redirects=True)
        self.assertEqual(response2.status_code, 200)
        self.assertTrue(
            'You have not confirmed your account yet' in response2.get_data(
                as_text=True))

        # send a confirmation token
        user = User.query.filter_by(email='adam@example.com').first()
        token = user.generate_confirmation_token()
        response = self.client.get('/auth/confirm/{}'.format(token),
                                   follow_redirects=True)
        user.confirm(token)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            'You have confirmed your account' in response.get_data(
                as_text=True))
        
        
        # log out
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('You have been logged out' in response.get_data(
            as_text=True))