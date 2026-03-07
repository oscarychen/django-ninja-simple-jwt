import warnings
from typing import Any

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Deprecated: use make_jwt_key instead. Create JWT key pair."

    def handle(self, *args: Any, **kwargs: Any) -> None:
        warnings.warn(
            "make_rsa is deprecated, use make_jwt_key instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        call_command("make_jwt_key")
