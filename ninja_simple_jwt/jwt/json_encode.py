from typing import Any
from uuid import UUID

from django.core.serializers.json import DjangoJSONEncoder


class TokenUserEncoder(DjangoJSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, UUID):
            return str(o)

        return super().default(o)
