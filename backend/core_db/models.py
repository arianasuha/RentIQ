"""
Database models.
"""
from django.db import models
from django.utils.text import slugify
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return a new user."""
        if not email:
            raise ValueError('Users must have an email address.')

        try:
            validate_email(email)
        except ValidationError:
            raise ValueError('The provided email is not a valid format.')

        user = self.model(email=self.normalize_email(email).lower(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return superuser."""
        if password is None:
            raise TypeError('Superusers must have a password.')

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        user = self.create_user(email, password, **extra_fields)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    """Custom User class in the system."""
    class Meta:
        ordering = ["email"]
        
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=255, unique=True)
    username = models.CharField(
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z0-9_-]+$",
                message="Username can only contain letters, numbers, underscores, and hyphens.",
                code="invalid_username",
            )
        ],
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    trust_score = models.IntegerField(default=0)
    image_url = models.ImageField(upload_to='user_images/', blank=True, null=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def set_password(self, raw_password):
        """Validates raw password before hashing"""
        if not raw_password:
            raise ValidationError("Password is required.")
        
        validate_password(raw_password, user=self)
        
        super().set_password(raw_password)

    def save(self, *args, **kwargs):
        if not self.pk and not self.slug:
            base_slug = slugify(self.email.split('@')[0])
            
            if not base_slug:
                base_slug = 'user'

            new_slug = base_slug
            counter = 1
            while self.__class__.objects.filter(slug=new_slug).exists():
                new_slug = f'{base_slug}-{counter}'
                counter += 1

            self.slug = new_slug
            
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """String representation of the user object."""
        return self.email
