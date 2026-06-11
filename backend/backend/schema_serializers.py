from rest_framework import serializers

class ErrorResponseSerializer(serializers.Serializer):  # pylint: disable=W0223
    """Standard error response structure (HTTP 400, 429, 500)."""

    error = serializers.CharField(
        help_text="A descriptive error message explaining the failure or status."
    )

class UserCreateRequestSerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer defining the expected fields for user creation (POST request body).
    """

    email = serializers.EmailField(
        required=True, help_text="User's unique email address."
    )
    username = serializers.CharField(
        required=False,
        help_text="Unique username for the user. Must be at least 6 characters long.",
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        help_text="Mandatory password, must meet complexity requirements.",
    )
    c_password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        help_text="Mandatory password, must meet complexity requirements.",
    )
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    is_staff = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Designates whether the user is a staff member.",
    )


class UserUpdateRequestSerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer defining the fields accepted for user profile updates (PATCH request body).
    All fields are optional for partial updates.
    """
    username = serializers.CharField(
        required=False,
        help_text="Unique username for the user. Must be at least 6 characters long.",
    )
    password = serializers.CharField(
        required=False,
        write_only=True,
        style={"input_type": "password"},
        help_text="New password (optional). Must meet complexity requirements if provided.",
    )
    c_password = serializers.CharField(
        required=False,
        write_only=True,
        style={"input_type": "password"},
        help_text="Mandatory password, must meet complexity requirements.",
    )
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
