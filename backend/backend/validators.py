from django.core.exceptions import ValidationError

class PasswordComplexityValidator:
    def validate(self, password, user=None):
        errors = []
        if len(password) < 8:
            errors.append("Password must contain at least eight characters.")

        has_upper = any(char.isupper() for char in password)
        has_lower = any(char.islower() for char in password)
        has_digit = any(char.isdigit() for char in password)

        has_special = any(not char.isalnum() for char in password)

        if not has_upper:
            errors.append("Password must contain at least one uppercase character.")
        if not has_lower:
            errors.append("Password must contain at least one lowercase character.")
        if not has_digit:
            errors.append("Password must contain at least one digit.")
        if not has_special:
            errors.append("Password must contain at least one special character.")

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return (
            "Your password must contain at least 8 characters, including "
            "uppercase, lowercase, digits, and special characters."
        )