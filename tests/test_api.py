import json
import unittest
from base64 import b64encode

from app import create_app, db
from app.models import Role, User


class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def get_api_headers(self, username, password):
        return {
            "Authorization": "Basic "
            + b64encode((username + ":" + password).encode("utf-8")).decode("utf-8"),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def test_404(self):
        response = self.client.get(
            "/wrong/url", headers=self.get_api_headers("email", "password")
        )
        self.assertEqual(response.status_code, 404)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response["error"], "not found")

    def test_no_auth(self):
        response = self.client.get("/api/v1/users/", content_type="application/json")
        self.assertEqual(response.status_code, 401)

    def test_bad_auth(self):
        # add a user
        r = Role.query.filter_by(name="User").first()
        self.assertIsNotNone(r)
        u = User(email="john@example.com", password="cat", confirmed=True, role=r)
        db.session.add(u)
        db.session.commit()
        # authenticate with bad password
        response = self.client.get(
            "/api/v1/users/", headers=self.get_api_headers("john@example.com", "dog")
        )
        self.assertEqual(response.status_code, 401)

    def test_token_auth(self):
        # add a user
        r = Role.query.filter_by(name="User").first()
        self.assertIsNotNone(r)
        u = User(email="john@example.com", password="cat", confirmed=True, role=r)
        db.session.add(u)
        db.session.commit()

        # issue a request with a bad token
        response = self.client.get(
            "/api/v1/users/", headers=self.get_api_headers("bad-token", "")
        )
        self.assertEqual(response.status_code, 401)

        # get a token
        response = self.client.post(
            "/api/v1/tokens/", headers=self.get_api_headers("john@example.com", "cat")
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get("token"))
        token = json_response["token"]

        # issue a request with the token
        response = self.client.get(
            "/api/v1/users/", headers=self.get_api_headers(token, "")
        )
        self.assertEqual(response.status_code, 200)

    def test_anonymous(self):
        response = self.client.get(
            "/api/v1/users/", headers=self.get_api_headers("", "")
        )
        self.assertEqual(response.status_code, 401)

    def test_unconfirmed_account(self):
        # add an unconfirmed user
        r = Role.query.filter_by(name="User").first()
        self.assertIsNotNone(r)
        u = User(email="john@example.com", password="cat", confirmed=False, role=r)
        db.session.add(u)
        db.session.commit()

        # get list of users with the unconfirmed account
        response = self.client.get(
            "/api/v1/users/", headers=self.get_api_headers("john@example.com", "cat")
        )
        self.assertEqual(response.status_code, 403)

    # def test_posts(self):
    #     # add a user
    #     r = Role.query.filter_by(name='User').first()
    #     self.assertIsNotNone(r)
    #     u = User(email='john@example.com', password='cat', confirmed=True,
    #              role=r)
    #     db.session.add(u)
    #     db.session.commit()

    #     # write an empty post
    #     response = self.client.post(
    #         '/api/v1/posts/',
    #         headers=self.get_api_headers('john@example.com', 'cat'),
    #         data=json.dumps({'body': ''}))
    #     self.assertEqual(response.status_code, 400)

    #     # write a post
    #     response = self.client.post(
    #         '/api/v1/posts/',
    #         headers=self.get_api_headers('john@example.com', 'cat'),
    #         data=json.dumps({'body': 'body of the *blog* post'}))
    #     self.assertEqual(response.status_code, 201)
    #     url = response.headers.get('Location')
    #     self.assertIsNotNone(url)

    #     # get the new post
    #     response = self.client.get(
    #         url,
    #         headers=self.get_api_headers('john@example.com', 'cat'))
    #     self.assertEqual(response.status_code, 200)
    #     json_response = json.loads(response.get_data(as_text=True))
    #     self.assertEqual('http://localhost' + json_response['url'], url)
    #     self.assertEqual(json_response['body'], 'body of the *blog* post')
    #     self.assertEqual(json_response['body_html'],
    #                     '<p>body of the <em>blog</em> post</p>')
    #     json_post = json_response

    #     # get the post from the user
    #     response = self.client.get(
    #         '/api/v1/users/{}/posts/'.format(u.id),
    #         headers=self.get_api_headers('john@example.com', 'cat'))
    #     self.assertEqual(response.status_code, 200)
    #     json_response = json.loads(response.get_data(as_text=True))
    #     self.assertIsNotNone(json_response.get('posts'))
    #     self.assertEqual(json_response.get('count', 0), 1)
    #     self.assertEqual(json_response['posts'][0], json_post)

    #     # get the post from the user as a follower
    #     response = self.client.get(
    #         '/api/v1/users/{}/timeline/'.format(u.id),
    #         headers=self.get_api_headers('john@example.com', 'cat'))
    #     self.assertEqual(response.status_code, 200)
    #     json_response = json.loads(response.get_data(as_text=True))
    #     self.assertIsNotNone(json_response.get('posts'))
    #     self.assertEqual(json_response.get('count', 0), 1)
    #     self.assertEqual(json_response['posts'][0], json_post)

    #     # edit post
    #     response = self.client.put(
    #         url,
    #         headers=self.get_api_headers('john@example.com', 'cat'),
    #         data=json.dumps({'body': 'updated body'}))
    #     self.assertEqual(response.status_code, 200)
    #     json_response = json.loads(response.get_data(as_text=True))
    #     self.assertEqual('http://localhost' + json_response['url'], url)
    #     self.assertEqual(json_response['body'], 'updated body')
    #     self.assertEqual(json_response['body_html'], '<p>updated body</p>')

    def test_users(self):
        # add two users
        user_role = Role.query.filter_by(name="User").first()
        admin_role = Role.query.filter_by(name="Administrator").first()
        self.assertIsNotNone(user_role)
        self.assertIsNotNone(admin_role)
        u1 = User(
            email="john@example.com",
            username="john",
            password="cat",
            confirmed=True,
            role=user_role,
        )
        u2 = User(
            email="susan@example.com",
            username="susan",
            password="dog",
            confirmed=False,
            role=user_role,
        )
        admin = User(
            email="vaibhav@example.com",
            username="vaibhav",
            confirmed=True,
            password="admin123",
        )
        db.session.add_all([u1, u2, admin])
        db.session.commit()

        # get users/ endpoint
        response = self.client.get(
            "/api/v1/users/", headers=self.get_api_headers("john@example.com", "cat")
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(len(json_response["users"]), 3)

        response = self.client.get(
            "/api/v1/users/", headers=self.get_api_headers("john@example.com", "dog")
        )
        self.assertEqual(response.status_code, 401)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response["error"], "unauthorized")
        self.assertEqual(json_response["message"], "Invalid credentials")

        response = self.client.get(
            "/api/v1/users/", headers=self.get_api_headers("susan@example.com", "dog")
        )
        self.assertEqual(response.status_code, 403)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response["error"], "forbidden")
        self.assertEqual(json_response["message"], "Unconfirmed account")

        # get users/{id} endpoint
        response = self.client.get(
            "/api/v1/users/{}".format(u1.id),
            headers=self.get_api_headers("john@example.com", "cat"),
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response["username"], "john")

        response = self.client.get(
            "/api/v1/users/{}".format(u2.id),
            headers=self.get_api_headers("john@example.com", "dog"),
        )
        self.assertEqual(response.status_code, 401)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response["error"], "unauthorized")
        self.assertEqual(json_response["message"], "Invalid credentials")

        response = self.client.get(
            "/api/v1/users/{}".format(u2.id),
            headers=self.get_api_headers("susan@example.com", "dog"),
        )
        self.assertEqual(response.status_code, 403)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response["error"], "forbidden")
        self.assertEqual(json_response["message"], "Unconfirmed account")

        # get add_new_user/ endpoint from unautherized user access
        response = self.client.post(
            "/api/v1/add_new_user/",
            headers=self.get_api_headers("john@example.com", "cat"),
            data=json.dumps(
                {
                    "email": "testuser@example.com",
                    "username": "testuser123",
                    "id": 123,
                    "confirmed": True,
                    "about_me": "user",
                    "location": "jaipur",
                    "name": "Test User",
                }
            ),
        )
        self.assertEqual(response.status_code, 403)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response["error"], "forbidden")
        self.assertEqual(json_response["message"], "Insufficient permissions")

        # get add_new_user/ endpoint from Invalid credentials
        response = self.client.post(
            "/api/v1/add_new_user/",
            headers=self.get_api_headers("john@example.com", "dog"),
            data=json.dumps(
                {
                    "email": "testuser@example.com",
                    "username": "testuser123",
                    "id": 123,
                    "confirmed": True,
                    "about_me": "user",
                    "location": "jaipur",
                    "name": "Test User",
                }
            ),
        )
        self.assertEqual(response.status_code, 401)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response["error"], "unauthorized")
        self.assertEqual(json_response["message"], "Invalid credentials")

        # get add_new_user/ endpoint from Unconfirmed account
        response = self.client.post(
            "/api/v1/add_new_user/",
            headers=self.get_api_headers("susan@example.com", "dog"),
            data=json.dumps(
                {
                    "email": "testuser@example.com",
                    "username": "testuser123",
                    "id": 123,
                    "confirmed": True,
                    "about_me": "I am testing this endpoint!",
                    "location": "jaipur",
                    "name": "Test User",
                }
            ),
        )
        self.assertEqual(response.status_code, 403)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response["error"], "forbidden")
        self.assertEqual(json_response["message"], "Unconfirmed account")

        # get add_new_user/ endpoint from authorized admin access
        response = self.client.post(
            "/api/v1/add_new_user/",
            headers=self.get_api_headers("vaibhav@example.com", "admin123"),
            data=json.dumps(
                {
                    "email": "testuser@example.com",
                    "username": "testuser123",
                    "id": 123,
                    "confirmed": True,
                    "about_me": "I am testing this endpoint!",
                    "location": "jaipur",
                    "name": "Test User",
                }
            ),
        )
        self.assertEqual(response.status_code, 201)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response["email"], "testuser@example.com")
        self.assertEqual(json_response["username"], "testuser123")
        self.assertEqual(json_response["id"], 123)
        self.assertEqual(json_response["confirmed"], True)
        self.assertEqual(json_response["about_me"], "I am testing this endpoint!")
        self.assertEqual(json_response["location"], "jaipur")
        self.assertEqual(json_response["name"], "Test User")
        self.assertEqual(json_response["url"], "/api/v1/users/123")

        # get users/ users_per_page/
        response = self.client.get(
            "/api/v1/users_per_page/",
            headers=self.get_api_headers("john@example.com", "cat"),
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response["count"], 4)
        self.assertEqual(json_response["next_url"], None)
        self.assertEqual(json_response["prev_url"], None)

        response = self.client.get(
            "/api/v1/users_per_page/",
            headers=self.get_api_headers("john@example.com", "dog"),
        )
        self.assertEqual(response.status_code, 401)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response["error"], "unauthorized")
        self.assertEqual(json_response["message"], "Invalid credentials")

        response = self.client.get(
            "/api/v1/users_per_page/",
            headers=self.get_api_headers("susan@example.com", "dog"),
        )
        self.assertEqual(response.status_code, 403)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response["error"], "forbidden")
        self.assertEqual(json_response["message"], "Unconfirmed account")

        # get users/ users_per_page/{per_page}
        per_page = 2

        response = self.client.get(
            "/api/v1/users_per_page/?page={}".format(per_page),
            headers=self.get_api_headers("john@example.com", "cat"),
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response["count"], 4)
        self.assertEqual(json_response["next_url"], None)
        self.assertEqual(json_response["prev_url"], "/api/v1/users_per_page/?page=1")

        response = self.client.get(
            "/api/v1/users_per_page/?page={}".format(per_page),
            headers=self.get_api_headers("john@example.com", "dog"),
        )
        self.assertEqual(response.status_code, 401)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response["error"], "unauthorized")
        self.assertEqual(json_response["message"], "Invalid credentials")

        response = self.client.get(
            "/api/v1/users_per_page/?page={}".format(per_page),
            headers=self.get_api_headers("susan@example.com", "dog"),
        )
        self.assertEqual(response.status_code, 403)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response["error"], "forbidden")
        self.assertEqual(json_response["message"], "Unconfirmed account")
