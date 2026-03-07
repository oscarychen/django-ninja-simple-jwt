from typing import Any

from django.core.management.base import BaseCommand

from ninja_simple_jwt.jwt.key_creation import make_and_save_key_pair


class Command(BaseCommand):
    help = "Create JWT key pair based on JWT_ALGORITHM setting."

    def handle(self, *args: Any, **kwargs: Any) -> None:
        private_key_path, public_key_path = make_and_save_key_pair()
        print(f"Key pair created: \n {private_key_path}\n {public_key_path}")
