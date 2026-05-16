from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class NotesApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def register_and_login(self, email: str) -> str:
        response = self.client.post(
            "/register",
            {"email": email, "password": "password123"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        response = self.client.post(
            "/login",
            {"email": email, "password": "password123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["access_token"]

    def authorize(self, token: str):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_user_can_crud_note(self):
        token = self.register_and_login("owner@example.com")
        self.authorize(token)

        response = self.client.post("/notes", {"title": "One", "content": "Body"}, format="json")
        self.assertEqual(response.status_code, 201)
        note_id = response.json()["id"]

        response = self.client.get(f"/notes/{note_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "One")

        response = self.client.put(f"/notes/{note_id}", {"title": "Two", "content": "Updated"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["content"], "Updated")

        response = self.client.delete(f"/notes/{note_id}")
        self.assertEqual(response.status_code, 204)

    def test_shared_user_can_read_but_not_update_note(self):
        owner_token = self.register_and_login("owner@example.com")
        viewer_token = self.register_and_login("viewer@example.com")
        self.authorize(owner_token)

        response = self.client.post("/notes", {"title": "Shared", "content": "Visible"}, format="json")
        note_id = response.json()["id"]
        response = self.client.post(
            f"/notes/{note_id}/share",
            {"share_with_email": "viewer@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        self.authorize(viewer_token)
        response = self.client.get(f"/notes/{note_id}")
        self.assertEqual(response.status_code, 200)
        response = self.client.put(f"/notes/{note_id}", {"title": "Hack", "content": "No"}, format="json")
        self.assertEqual(response.status_code, 404)

    def test_duplicate_registration_and_bad_login_are_handled(self):
        self.register_and_login("person@example.com")
        response = self.client.post(
            "/register",
            {"email": "person@example.com", "password": "password123"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            "/login",
            {"email": "person@example.com", "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["message"], "Invalid email or password")

    def test_auth_and_validation_edges_are_handled(self):
        response = self.client.get("/notes")
        self.assertEqual(response.status_code, 403)

        token = self.register_and_login("edge@example.com")
        self.authorize(token)

        response = self.client.post("/notes", {"title": "   ", "content": "Body"}, format="json")
        self.assertEqual(response.status_code, 400)
        response = self.client.post("/notes", {"title": "Title", "content": "   "}, format="json")
        self.assertEqual(response.status_code, 400)

        response = self.client.get("/search")
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            "/notes",
            {"title": "Private", "content": "Only owner can share"},
            format="json",
        )
        note_id = response.json()["id"]
        response = self.client.post(
            f"/notes/{note_id}/share",
            {"share_with_email": "missing@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_about_and_openapi_are_public(self):
        self.client.credentials()
        self.assertEqual(self.client.get("/about").status_code, 200)
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["openapi"], "3.0.0")

    def tearDown(self):
        get_user_model().objects.all().delete()
