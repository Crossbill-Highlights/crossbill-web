"""Common domain type aliases."""

from typing import Any

# JSON-serialized form of pydantic-ai ModelMessage list.
# The typed form (list[ModelMessage]) lives only in the infrastructure AI adapter;
# all other layers use this serialized representation for storage and transport.
SerializedMessageHistory = list[dict[str, Any]]
