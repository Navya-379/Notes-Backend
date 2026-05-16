import os

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import JWTAuthentication, create_access_token
from .models import Note
from .serializers import (
    FavoriteNoteSerializer,
    LoginSerializer,
    NoteSerializer,
    NoteWriteSerializer,
    RegisterSerializer,
    ShareNoteSerializer,
)


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"message": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({"access_token": create_access_token(serializer.validated_data["user"].id)})


class AuthenticatedView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def visible_notes(self):
        return Note.objects.filter(Q(owner=self.request.user) | Q(shared_with=self.request.user)).distinct()

    def owned_note(self, note_id):
        return get_object_or_404(Note, id=note_id, owner=self.request.user)

    def visible_note(self, note_id):
        return get_object_or_404(self.visible_notes(), id=note_id)


class NotesView(AuthenticatedView):
    def get(self, request):
        queryset = self.visible_notes()
        page = request.query_params.get("page")
        page_size = request.query_params.get("page_size", "20")
        if page is not None:
            try:
                page_number = max(int(page), 1)
                size = min(max(int(page_size), 1), 100)
            except ValueError:
                return Response({"detail": "page and page_size must be integers"}, status=400)
            start = (page_number - 1) * size
            items = queryset[start : start + size]
            return Response(
                {
                    "count": queryset.count(),
                    "page": page_number,
                    "page_size": size,
                    "results": NoteSerializer(items, many=True).data,
                }
            )
        return Response(NoteSerializer(queryset, many=True).data)

    def post(self, request):
        serializer = NoteWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = serializer.save(owner=request.user)
        return Response(NoteSerializer(note).data, status=status.HTTP_201_CREATED)


class NoteDetailView(AuthenticatedView):
    def get(self, request, note_id):
        return Response(NoteSerializer(self.visible_note(note_id)).data)

    def put(self, request, note_id):
        note = self.owned_note(note_id)
        serializer = NoteWriteSerializer(note, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(NoteSerializer(note).data)

    def delete(self, request, note_id):
        self.owned_note(note_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShareNoteView(AuthenticatedView):
    def post(self, request, note_id):
        note = self.owned_note(note_id)
        serializer = ShareNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["share_with_email"]
        user_model = get_user_model()
        try:
            share_with = user_model.objects.get(email__iexact=email)
        except user_model.DoesNotExist:
            return Response({"detail": "User to share with was not found"}, status=status.HTTP_404_NOT_FOUND)
        if share_with == request.user:
            return Response({"detail": "You cannot share a note with yourself"}, status=status.HTTP_400_BAD_REQUEST)
        note.shared_with.add(share_with)
        return Response({"message": "Note shared successfully"})


class FavoriteNoteView(AuthenticatedView):
    def post(self, request, note_id):
        note = self.owned_note(note_id)
        serializer = FavoriteNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note.is_favorite = serializer.validated_data["is_favorite"]
        note.save(update_fields=["is_favorite", "updated_at"])
        return Response(NoteSerializer(note).data)


class SearchView(AuthenticatedView):
    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response({"detail": "q query parameter is required"}, status=400)
        notes = self.visible_notes().filter(Q(title__icontains=query) | Q(content__icontains=query))
        return Response(NoteSerializer(notes, many=True).data)


class AboutView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(
            {
                "name": os.getenv("CANDIDATE_NAME", "Navya"),
                "email": os.getenv("CANDIDATE_EMAIL", "navya@example.com"),
                "my features": {
                    "Favorite notes": "Users can mark their own important notes as favorites and see that state in note responses. I chose it because real note apps need a quick way to highlight high-priority notes.",
                    "Paginated notes": "GET /notes supports page and page_size query parameters for larger accounts.",
                    "Search": "GET /search?q=keyword finds accessible notes by title or content.",
                },
            }
        )


class OpenAPIView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        base_schema = {
            "openapi": "3.0.0",
            "info": {"title": "Notes App API", "version": "1.0.0"},
            "paths": {
                "/register": {"post": {"summary": "Register a new user", "responses": {"201": {"description": "Created"}}}},
                "/login": {"post": {"summary": "Login and receive a JWT token", "responses": {"200": {"description": "OK"}, "401": {"description": "Unauthorized"}}}},
                "/notes": {"get": {"summary": "List notes visible to the authenticated user"}, "post": {"summary": "Create a note"}},
                "/notes/{id}": {"get": {"summary": "Get a note"}, "put": {"summary": "Update an owned note"}, "delete": {"summary": "Delete an owned note"}},
                "/notes/{id}/share": {"post": {"summary": "Share an owned note with another user"}},
                "/notes/{id}/favorite": {"post": {"summary": "Mark or unmark an owned note as favorite"}},
                "/search": {"get": {"summary": "Search visible notes by title or content"}},
                "/about": {"get": {"summary": "Candidate and feature information"}},
                "/openapi.json": {"get": {"summary": "OpenAPI schema"}},
            },
        }
        return Response(base_schema)
