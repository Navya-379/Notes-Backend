from django.urls import path

from .views import (
    AboutView,
    FavoriteNoteView,
    LoginView,
    NoteDetailView,
    NotesView,
    OpenAPIView,
    RegisterView,
    SearchView,
    ShareNoteView,
)

urlpatterns = [
    path("register", RegisterView.as_view()),
    path("login", LoginView.as_view()),
    path("notes", NotesView.as_view()),
    path("notes/<int:note_id>", NoteDetailView.as_view()),
    path("notes/<int:note_id>/share", ShareNoteView.as_view()),
    path("notes/<int:note_id>/favorite", FavoriteNoteView.as_view()),
    path("search", SearchView.as_view()),
    path("about", AboutView.as_view()),
    path("openapi.json", OpenAPIView.as_view()),
]
