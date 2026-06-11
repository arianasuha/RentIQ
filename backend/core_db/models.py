"""
Database models.
"""
from django.db import models
from django.utils.text import slugify
from django.core.validators import MaxValueValidator, MinValueValidator
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

        user = self.model(email=self.normalize_email(email), **extra_fields)
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
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r"^\S+$",  # No whitespace allowed
                message="Username cannot contain spaces",
                code="invalid_username",
            )
        ],
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
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

        super().save(*args, **kwargs)

    def __str__(self):
        """String representation of the user object."""
        return self.email


class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, max_length=50, blank=True)
    is_approved = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.slug != slugify(self.name):
            self.name = self.name.strip().title()
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name if self.is_approved else f"{self.name} (Pending)"

    class Meta:
        ordering = ['name']

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, max_length=255, blank=True)

    genres = models.ManyToManyField(
        'Genre',
        related_name='books',
        blank=True
    )

    class Meta:
        unique_together = ('title', 'author')

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f'{self.title} {self.author}')

            new_slug = base_slug
            counter = 1
            while Book.objects.filter(slug=new_slug).exists():
                new_slug = f'{base_slug}-{counter}'
                counter += 1

            self.slug = new_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.title} by {self.author}'


class ReviewPost(models.Model):
    reviewer = models.ForeignKey('User',on_delete=models.CASCADE)
    review_title = models.CharField(max_length=150, blank=True, null=True)
    book = models.ForeignKey('Book', on_delete=models.CASCADE, related_name='reviews')
    review_image = models.ImageField(
        upload_to='review_images/',
        blank=True,
        null=True,
    )
    review_content = models.TextField()
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Rating must be between 1 and 5 stars.'
    )
    review_date = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, max_length=255, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            # 1. Fallback logic: Use review_title OR book.title
            title_to_slugify = self.review_title if self.review_title else f"Review of {self.book.title}"

            base_slug = slugify(title_to_slugify)
            unique_slug_base = f'{base_slug}-by-{self.reviewer.slug}'

            # 2. Collision detection
            final_slug = unique_slug_base
            counter = 1
            while ReviewPost.objects.filter(slug=final_slug).exists():
                final_slug = f'{unique_slug_base}-{counter}'
                counter += 1

            self.slug = final_slug

        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-review_date']
        constraints = [
            models.UniqueConstraint(
                fields=['reviewer', 'book'],
                name='unique_review_per_user_per_book'
            )
        ]



class Reaction(models.Model):
    class ReactionTypes(models.TextChoices):
        LOVE = 'LOVE', 'Love'
        LIKE = 'LIKE', 'Like'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review_post = models.ForeignKey(ReviewPost, on_delete=models.CASCADE, related_name='reactions')
    reaction_type = models.CharField(max_length=7, choices=ReactionTypes.choices)

    class Meta:
        # Crucial for APIs: prevents duplicate likes
        constraints = [
            models.UniqueConstraint(fields=['user', 'review_post'], name='unique_user_reaction')
        ]

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review_post = models.ForeignKey(ReviewPost, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
