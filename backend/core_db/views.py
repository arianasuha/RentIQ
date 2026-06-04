from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from .serializers import UserRegistrationSerializer

User = get_user_model()

class UserRegistrationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    Handles user registration. Only exposes POST /register/.
    Bypasses token requirements so anyone can sign up.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny] 

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
                
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"detail": "Account created successfully.", "user": serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers
        )