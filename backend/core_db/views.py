from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_spectacular.utils import (
    extend_schema,
    OpenApiExample,
    OpenApiResponse,
)
from backend.mixins import http_method_mixin
from backend.schema_serializers import (
    ErrorResponseSerializer, 
    UserCreateRequestSerializer,
    UserUpdateRequestSerializer
)
from .serializers import (
    UserDetailSerializer, 
    UserListSerializer, 
    UserRetrieveSerializer
)


User = get_user_model()

def check_create_request_data(request):
    """Check if create request data is valid."""

    current_user = request.user
    if "is_superuser" in request.data:
        return Response(
            {
                "error": "You do not have permission to create a superuser. Contact Developer."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    if "is_staff" in request.data and not current_user.is_superuser:
        return Response(
            {"error": "You do not have permission to create an admin user."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if "slug" in request.data or "is_active" in request.data:
        return Response(
            {"error": "Forbidden fields cannot be updated."},
            status=status.HTTP_403_FORBIDDEN,
        )

    password = request.data.get("password")
    if not password:
        return Response(
            {"error": "Password is required."}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not request.data.get("c_password"):
        return Response(
            {"error": "Please confirm your password."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    c_password = request.data.pop("c_password")
    if password != c_password:
        return Response(
            {"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST
        )

    return current_user

def check_update_request_data(user_instance, request):
    """Check if update request data is valid."""

    current_user = request.user

    if current_user.id != user_instance.id and not current_user.is_superuser:
        return Response(
            {"error": "You do not have permission to update this user."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if "email" in request.data:
        return Response(
            {"error": "You cannot update the email field."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if (
        "slug" in request.data  
        or "is_active" in request.data
        or "is_staff" in request.data
        or "is_superuser" in request.data
    ):
        return Response(
            {"error": "Forbidden fields cannot be updated."},
            status=status.HTTP_403_FORBIDDEN,
        )

    password = request.data.get("password")
    if password:
        if not request.data.get("c_password"):
            return Response(
                {"error": "Please confirm your password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        c_password = request.data.pop("c_password")
        if password != c_password:
            return Response(
                {"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST
            )

    return current_user

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        """Dynamically return the serializer class based on the action."""
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'retrieve':
            return UserRetrieveSerializer
        return UserDetailSerializer

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action == "create":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):  
        """Queryset for User View."""
        if self.action == "list":
            if self.request.user.is_staff:
                return get_user_model().objects.all()
            return get_user_model().objects.none()

        if self.action == "retrieve":
            if self.request.user.is_staff:
                return get_user_model().objects.all()
            
            return get_user_model().objects.filter(pk=self.request.user.pk)

        if self.request.user.is_superuser:
            return get_user_model().objects.all()
        return get_user_model().objects.filter(pk=self.request.user.pk)
    
    @extend_schema(
        summary="Create New User",
        description="Registers a new user account. Does not require authentication.",
        tags=["User Management"],
        request=UserCreateRequestSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=UserDetailSerializer,
                description="User created successfully. Returns a success message.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=ErrorResponseSerializer,
                description=(
                    "Bad Request. "
                    "Occurs on missing required fields, invalid data format, or duplicate email.",
                ),
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Forbidden. User does not have staff or superuser privileges.",
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                name="Successful User Creation",
                response_only=True,
                status_codes=["201"],
                value={"success": "User created successfully."},
            ),
            OpenApiExample(
                name="Creating Admin as a User Error",
                response_only=True,
                status_codes=["403"],
                value={"error": "You do not have permission to create an admin user."},
            ),
            OpenApiExample(
                name="Updating Forbidden fields.",
                response_only=True,
                status_codes=["403"],
                value={"error": "Forbidden fields cannot be updated."},
            ),
            OpenApiExample(
                name="Password Confirmation Error",
                response_only=True,
                status_codes=["400"],
                value={"error": "Please confirm your password."},
            ),
            OpenApiExample(
                name="Password Matching Error",
                response_only=True,
                status_codes=["400"],
                value={"error": "Passwords do not match."},
            ),
            OpenApiExample(
                name="Email Already Exists Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "email": [
                            "User with this email already exists.",
                        ]
                    }
                },
            ),
            OpenApiExample(
                name="Invalid Email Address Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "email": [
                            "Enter a valid email address.",
                        ]
                    }
                },
            ),
            OpenApiExample(
                name="Password Complexity Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "password": [
                            "Password must be at least 8 characters.",
                            "Password must contain at least one uppercase letter.",
                            "Password must contain at least one number.",
                            "Password must contain at least one special character.",
                        ]
                    }
                },
            ),
        ],
    )
    
    def create(self, request, *args, **kwargs):  
        """Create new user and send email verification link."""

        check_integrity = check_create_request_data(request)

        if isinstance(check_integrity, Response):
            return check_integrity
        
        response = super().create(request, *args, **kwargs)

        if response.status_code != status.HTTP_201_CREATED:
            return response

        return Response(
            {"success": "User profile created successfully."},
            status=status.HTTP_201_CREATED,
        )

    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Retrieve Single User Details",
        description="Returns the details of a specific user by ID.",
        tags=["User Management"],
        request=None,
        responses={
            status.HTTP_200_OK: UserRetrieveSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: ErrorResponseSerializer,
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response=ErrorResponseSerializer,
                description=(
                    "Not Found. "
                    "The user ID does not exist "
                    "or the authenticated user does not have permission to view it.",
                ),
            ),
        },
        examples=[
            OpenApiExample(
                name="Not Found Error",
                response_only=True,
                status_codes=["404"],
                value={"error": "Not found."},
            ),
            OpenApiExample(
                name="Forbidden Access",
                response_only=True,
                status_codes=["403"],
                value={"error": "You do not have permission to perform this action."},
            ),
            OpenApiExample(
                name="Unauthorized Access",
                response_only=True,
                status_codes=["401"],
                value={"error": "You are not authenticated."},
            ),
        ],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    
    def update(self, request, *args, **kwargs):
        """Allow only users to update their own profile. SuperUser can update any profile.
        Patch method allowed, Put method not allowed"""

        not_allowed_method = http_method_mixin(request, *args, **kwargs)

        if not_allowed_method:
            return not_allowed_method

        user = self.get_object()

        check_integrity = check_update_request_data(user, request)

        if isinstance(check_integrity, Response):
            return check_integrity

        response = super().update(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            user.refresh_from_db()
            retrieve_serializer = UserRetrieveSerializer(
                user,
                context=self.get_serializer_context(),
            )
            return Response(
                {
                    "success": "User profile updated successfully.",
                    "data": retrieve_serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        return response
    
    @extend_schema(
        summary="Update User Profile (Partial)",
        description="Partially updates an existing user profile (PATCH method).",
        tags=["User Management"],
        request=UserUpdateRequestSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=UserRetrieveSerializer,
                description="User profile updated successfully. Returns the updated user object.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Bad Request. Occurs on invalid field values or data integrity errors.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unauthorized. User is not authenticated.",
            ),
            status.HTTP_403_FORBIDDEN: ErrorResponseSerializer,
            status.HTTP_404_NOT_FOUND: ErrorResponseSerializer,
            status.HTTP_405_METHOD_NOT_ALLOWED: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                name="Success",
                response_only=True,
                status_codes=["200"],
                value={
                    "success": "User profile updated successfully.",
                    "data": {
                        "id": 1,
                        "slug": "updateduser",
                        "first_name": "Updated",
                        "last_name": "User",
                        "username": "updateduser",
                        "email": "1b8Xu@example.com",
                    },
                },
            ),
            OpenApiExample(
                name="Method Not Allowed",
                response_only=True,
                status_codes=["405"],
                value={"error": "PUT operation not allowed."},
            ),
            OpenApiExample(
                name="Unauthorized User Update Error",
                response_only=True,
                status_codes=["401"],
                value={"error": "You are not authenticated."},
            ),
            OpenApiExample(
                name="Not Found Error",
                response_only=True,
                status_codes=["404"],
                value={"error": "Not found."},
            ),
            OpenApiExample(
                name="Unauthorized User Update Error",
                response_only=True,
                status_codes=["403"],
                value={"error": "You do not have permission to update this user."},
            ),
            OpenApiExample(
                name="Updating Email field",
                response_only=True,
                status_codes=["403"],
                value={"error": "You cannot update the email field."},
            ),
            OpenApiExample(
                name="Updating Forbidden fields.",
                response_only=True,
                status_codes=["403"],
                value={"error": "Forbidden fields cannot be updated."},
            ),
            OpenApiExample(
                name="Username Already Exists Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {"username": ["User with this username already exists."]}
                },
            ),
            OpenApiExample(
                name="Username Too Short Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "username": ["Username must be at least 6 characters long."]
                    }
                },
            ),
            OpenApiExample(
                name="Password Confirmation Error",
                response_only=True,
                status_codes=["400"],
                value={"error": "Please confirm your password."},
            ),
            OpenApiExample(
                name="Password Matching Error",
                response_only=True,
                status_codes=["400"],
                value={"error": "Passwords do not match."},
            ),
            OpenApiExample(
                name="Password Complexity Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "password": [
                            "Password must be at least 8 characters.",
                            "Password must contain at least one uppercase letter.",
                            "Password must contain at least one number.",
                            "Password must contain at least one special character.",
                        ]
                    }
                },
            ),
        ],
    )
    
    def partial_update(self, request, *args, **kwargs):
        """Partially updates an existing user profile (PATCH method)."""
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


    @extend_schema(
        summary="Delete User Profile",
        description="Deletes a user profile by ID.",
        tags=["User Management"],
        request=None,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {"success": {"type": "string"}},
                },
                description="User Profile Deleted Successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: ErrorResponseSerializer,
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response=ErrorResponseSerializer,
                description=("User ID Not Found or Does not exist. "),
            ),
        },
        examples=[
            OpenApiExample(
                name="Successful User Deletion",
                response_only=True,
                status_codes=["200"],
                value={"success": "User Profile Deleted Successfully."},
            ),
            OpenApiExample(
                name="Unauthorized User Delete Error",
                response_only=True,
                status_codes=["401"],
                value={"error": "You are not authenticated."},
            ),
            OpenApiExample(
                name="User ID Not Found Error",
                response_only=True,
                status_codes=["404"],
                value={"error": "User ID Not Found or Does not exist."},
            ),
            OpenApiExample(
                name="Forbidden User Delete Error",
                response_only=True,
                status_codes=["403"],
                value={"error": "You are not authorized to delete this user."},
            ),
            OpenApiExample(
                name="Superuser Delete Error",
                response_only=True,
                status_codes=["403"],
                value={"error": "You cannot delete superusers."},
            ),
        ],
    )
    def destroy(self, request, *args, **kwargs):
        """Allow user to delete their own profile and superuser to delete normal or staff users"""
        current_user = self.request.user
        user_to_delete = self.get_object()

        if not current_user.is_superuser and current_user.id != user_to_delete.id:
            return Response(
                {"error": "You are not authorized to delete this user."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if user_to_delete.is_superuser:
            return Response(
                {"error": "You cannot delete superusers"},
                status=status.HTTP_403_FORBIDDEN,
            )


        email = user_to_delete.email
        response = super().destroy(request, *args, **kwargs)

        if response.status_code == status.HTTP_204_NO_CONTENT:
            return Response(
                {"success": f"User {email} deleted successfully."},
                status=status.HTTP_200_OK,
            )

        return response
