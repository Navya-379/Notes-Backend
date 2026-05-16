import base64
import hashlib
import hmac
import json
import time
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def _json(data: dict[str, Any]) -> bytes:
    return json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")


def create_access_token(user_id: int, expires_in: int = 60 * 60 * 24) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": str(user_id), "iat": int(time.time()), "exp": int(time.time()) + expires_in}
    signing_input = f"{_b64encode(_json(header))}.{_b64encode(_json(payload))}"
    signature = hmac.new(settings.SECRET_KEY.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64encode(signature)}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise exceptions.AuthenticationFailed("Invalid token") from exc

    signing_input = f"{header_b64}.{payload_b64}"
    expected = hmac.new(settings.SECRET_KEY.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    try:
        supplied = _b64decode(signature_b64)
        payload = json.loads(_b64decode(payload_b64))
    except Exception as exc:
        raise exceptions.AuthenticationFailed("Invalid token") from exc

    if not hmac.compare_digest(expected, supplied):
        raise exceptions.AuthenticationFailed("Invalid token")
    if int(payload.get("exp", 0)) < int(time.time()):
        raise exceptions.AuthenticationFailed("Token expired")
    return payload


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth = get_authorization_header(request).decode("utf-8")
        if not auth:
            return None
        parts = auth.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise exceptions.AuthenticationFailed("Authorization header must be Bearer token")

        payload = decode_access_token(parts[1])
        user_model = get_user_model()
        try:
            user = user_model.objects.get(id=payload["sub"], is_active=True)
        except user_model.DoesNotExist as exc:
            raise exceptions.AuthenticationFailed("Invalid token") from exc
        return user, parts[1]
