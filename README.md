# Notes App Backend API

A Django REST backend for a multi-user notes service. It supports registration, JWT login, note CRUD, note sharing, OpenAPI JSON, candidate metadata, and extra product features.

## Local Setup

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The API runs at `http://127.0.0.1:8000`.

## Required Endpoints

- `POST /register`
- `POST /login`
- `GET /notes`
- `GET /notes/{id}`
- `POST /notes`
- `PUT /notes/{id}`
- `DELETE /notes/{id}`
- `POST /notes/{id}/share`
- `GET /openapi.json`
- `GET /about`

Authenticated endpoints require:

```text
Authorization: Bearer <access_token>
```

## Extra Features

- `POST /notes/{id}/favorite` marks or unmarks a note as favorite.
- `GET /notes?page=1&page_size=20` returns paginated notes.
- `GET /search?q=keyword` searches visible notes by title or content.

## Deploying

For Render/Railway/Fly, set:

- Build command: `pip install -r requirements.txt && python manage.py migrate`
- Start command: `gunicorn config.wsgi:application`
- Environment variables: `SECRET_KEY`, `CANDIDATE_NAME`, `CANDIDATE_EMAIL`, optional `DATABASE_URL`, optional `DEBUG=False`
