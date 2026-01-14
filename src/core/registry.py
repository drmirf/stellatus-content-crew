"""
Registry system for agents and skills.

Provides auto-discovery and decorator-based registration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar

from src.core.exceptions import DuplicateRegistrationError

if TYPE_CHECKING:
    from src.interfaces.agent_interface import IAgent
    from src.interfaces.skill_interface import ISkill

T = TypeVar("T")


class Registry(Generic[T]):
    """
    Generic registry for managing components.

    Features:
    - Type-safe registration
    - Decorator support for easy registration
    - Category-based filtering
    - Instance caching
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._items: dict[str, type[T]] = {}
        self._instances: dict[str, T] = {}
        self._metadata: dict[str, dict[str, Any]] = {}
        self._categories: dict[str, set[str]] = {}

    def register(
        self,
        name: str | None = None,
        category: str = "default",
        metadata: dict[str, Any] | None = None,
        replace: bool = False,
    ) -> Callable[[type[T]], type[T]]:
        """
        Decorator to register a class in the registry.

        Usage:
            @agent_registry.register(name="research", category="content")
            class ResearchAgent(BaseAgent):
                pass
        """

        def decorator(cls: type[T]) -> type[T]:
            item_name = name or cls.__name__
            self.add(item_name, cls, category, metadata, replace)
            return cls

        return decorator

    def add(
        self,
        name: str,
        cls: type[T],
        category: str = "default",
        metadata: dict[str, Any] | None = None,
        replace: bool = False,
    ) -> None:
        """Add a class to the registry."""
        if name in self._items and not replace:
            raise DuplicateRegistrationError(self.name, name)

        self._items[name] = cls
        self._metadata[name] = metadata or {}
        self._metadata[name]["category"] = category

        if category not in self._categories:
            self._categories[category] = set()
        self._categories[category].add(name)

    def remove(self, name: str) -> None:
        """Remove an item from the registry."""
        if name not in self._items:
            return

        category = self._metadata.get(name, {}).get("category", "default")
        if category in self._categories:
            self._categories[category].discard(name)

        del self._items[name]
        self._metadata.pop(name, None)
        self._instances.pop(name, None)

    def get(self, name: str) -> type[T] | None:
        """Get a registered class by name."""
        return self._items.get(name)

    def get_instance(self, name: str, *args: Any, **kwargs: Any) -> T | None:
        """Get or create a singleton instance."""
        if name not in self._items:
            return None

        if name not in self._instances:
            cls = self._items[name]
            self._instances[name] = cls(*args, **kwargs)

        return self._instances[name]

    def create(self, name: str, *args: Any, **kwargs: Any) -> T | None:
        """Create a new instance (non-singleton)."""
        cls = self._items.get(name)
        if cls is None:
            return None
        return cls(*args, **kwargs)

    def get_metadata(self, name: str) -> dict[str, Any]:
        """Get metadata for a registered item."""
        return self._metadata.get(name, {})

    def list_all(self) -> list[str]:
        """List all registered item names."""
        return list(self._items.keys())

    def list_by_category(self, category: str) -> list[str]:
        """List all items in a specific category."""
        return list(self._categories.get(category, set()))

    def get_categories(self) -> list[str]:
        """Get all available categories."""
        return list(self._categories.keys())

    def has(self, name: str) -> bool:
        """Check if an item is registered."""
        return name in self._items

    def clear(self) -> None:
        """Clear all registered items."""
        self._items.clear()
        self._instances.clear()
        self._metadata.clear()
        self._categories.clear()

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, name: str) -> bool:
        return self.has(name)

    def __iter__(self):
        return iter(self._items.items())


# Global registries
agent_registry: Registry[IAgent] = Registry("Agent")
skill_registry: Registry[ISkill] = Registry("Skill")
