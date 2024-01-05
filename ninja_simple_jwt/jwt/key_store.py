from typing import IO

from django.core.files.storage import Storage


class LocalDiskKeyStorage(Storage):
    def _save(self, name: str, content: IO) -> str:
        with open(name, "w", encoding="utf-8") as f:
            f.write(content.read().decode())
        return name

    def exists(self, name: str) -> bool:
        """Always overwrite old keys with same filename."""
        return False

    def _open(self, name: str, mode: str = "rb") -> IO:
        return open(name, mode)  # pylint: disable=unspecified-encoding


local_disk_key_storage = LocalDiskKeyStorage()
