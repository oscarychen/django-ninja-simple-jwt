from typing import Any, Optional, Union
from uuid import UUID

from django.contrib.auth import get_user_model

# Type alias for Django primary keys
# Supports int (most common), UUID objects, and str (for UUID strings from JWT or string PKs)
PrimaryKey = Union[int, UUID, str]

User = get_user_model()  # type: ignore[assignment]


class TokenUser:
    """
    Stateless user representation for JWT authentication.

    This class is designed to work with Django ORM queries by providing
    a pk property and _meta attribute so Django treats it like a model instance.
    """

    def __init__(self, user_id: PrimaryKey | None = None, email: str | None = None, roles: list[str] | None = None):
        self.id = user_id
        self.email = email
        self.roles = roles or []
        self.is_authenticated = True
        # Add _meta attribute so Django's ForeignKey.get_prep_value() recognizes this as model-like
        # When Django sees hasattr(value, '_meta'), it extracts value.pk instead of passing
        # the object directly to the field's to_python() method
        # _meta.model is needed for Django's check_rel_lookup_compatibility()
        self._meta = type("Meta", (), {"model": User})()

    @property
    def pk(self) -> PrimaryKey | None:
        """
        Primary key property for Django ORM compatibility.
        This allows TokenUser instances to be used in Django ORM queries like:
        MyModel.objects.filter(related_user=token_user)

        Works with any primary key type (int, UUID, str, etc.).
        For UUID primary keys, the value may be a string (from JWT) or UUID object.
        Django ORM will handle the conversion automatically.
        """
        # If id is a UUID string, return it as-is (Django ORM handles string UUIDs)
        # If it's already a UUID object, return it
        return self.id

    def __getattribute__(self, name: str) -> Any:
        """
        Override attribute access to make TokenUser work with Django's UUIDField.to_python().
        When Django's UUIDField tries to use the TokenUser object directly (e.g., calling .replace()),
        we delegate to the string representation of our id.
        """
        # First, try normal attribute access
        try:
            return super().__getattribute__(name)
        except AttributeError:
            # If attribute doesn't exist and it's a string method that Django's UUIDField might call,
            # delegate to the string representation of our id
            if name in ("replace", "strip", "lower", "upper", "startswith", "endswith", "split", "find", "index"):
                id_value = super().__getattribute__("id")
                if id_value is None:
                    id_str = ""
                else:
                    id_str = str(id_value)
                return getattr(id_str, name)
            raise

    def __repr__(self) -> str:
        """Return a developer-friendly representation for debugging."""
        return f"TokenUser(id={self.id})"

    def __int__(self) -> int:
        """Convert to int for compatibility with integer primary keys."""
        if self.id is None:
            return 0
        # Check for UUID objects or UUID strings
        if isinstance(self.id, UUID) or (isinstance(self.id, str) and self._is_uuid_string(self.id)):
            raise TypeError("Cannot convert TokenUser with UUID primary key to int. Use .pk or .id instead.")
        try:
            return int(self.id)
        except (ValueError, TypeError) as e:
            raise TypeError(
                f"Cannot convert TokenUser with {type(self.id).__name__} primary key to int. Use .pk or .id instead."
            ) from e

    @staticmethod
    def _is_uuid_string(value: str) -> bool:
        """Check if a string is a valid UUID format."""
        try:
            UUID(value)
            return True
        except (ValueError, AttributeError):
            return False

    def __str__(self) -> str:
        """
        Return string representation of the primary key value.
        This allows Django ORM to extract the actual ID value when converting to UUID/int/etc.
        Django's UUIDField.to_python() may call str() on the object, so we need to return the actual ID.
        """
        if self.id is None:
            return ""
        # Return the string representation of the ID value itself
        # This allows Django to parse it as UUID/int when used in queries
        return str(self.id)

    @property
    def is_anonymous(self) -> bool:
        return False

    def has_perm(self, perm: str, obj: Optional[object] = None) -> bool:  # pylint: disable=unused-argument
        # Optional: simple role→permission mapping
        # For stateless users, permissions are typically handled at the application level
        return False

    def has_perms(self, perm_list: list[str], obj: Optional[object] = None) -> bool:
        return all(self.has_perm(p, obj) for p in perm_list)

    def has_module_perms(self, app_label: str) -> bool:  # pylint: disable=unused-argument
        # For stateless users, module permissions are typically handled at the application level
        return False
