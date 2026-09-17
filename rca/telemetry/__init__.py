"""Read-only telemetry adapters used by deterministic discovery."""

from .inventory import (
    ALLOWED_SOURCE_FAMILIES,
    InventoryBudgetExceeded,
    INVENTORY_SCHEMA_VERSION,
    inventory,
)

__all__ = [
    "ALLOWED_SOURCE_FAMILIES",
    "InventoryBudgetExceeded",
    "INVENTORY_SCHEMA_VERSION",
    "inventory",
]
