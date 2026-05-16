from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from .models import Note


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, max_length=128, write_only=True)

    def validate_email(self, value: str) -> str:
        email = value.strip().lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def create(self, validated_data):
        email = validated_data["email"]
        return get_user_model().objects.create_user(
            username=email,
            email=email,
            password=validated_data["password"],
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs["email"].strip().lower()
        user = authenticate(username=email, password=attrs["password"])
        if user is None:
            raise serializers.ValidationError("Invalid email or password")
        attrs["user"] = user
        return attrs


class NoteSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)

    class Meta:
        model = Note
        fields = ["id", "title", "content", "is_favorite", "created_at", "updated_at"]
        read_only_fields = ["id", "is_favorite", "created_at", "updated_at"]


class NoteWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["title", "content"]

    def validate_title(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title cannot be blank.")
        return value


class ShareNoteSerializer(serializers.Serializer):
    share_with_email = serializers.EmailField()

    def validate_share_with_email(self, value: str) -> str:
        return value.strip().lower()


class FavoriteNoteSerializer(serializers.Serializer):
    is_favorite = serializers.BooleanField()
