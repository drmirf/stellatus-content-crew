"""
Event system for inter-component communication.

Provides a publish-subscribe pattern for loose coupling between components.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Coroutine, Union
from uuid import uuid4


class EventType(Enum):
    """Standard event types in the system."""

    # Agent events
    AGENT_STARTED = auto()
    AGENT_COMPLETED = auto()
    AGENT_FAILED = auto()

    # Skill events
    SKILL_STARTED = auto()
    SKILL_COMPLETED = auto()
    SKILL_FAILED = auto()

    # Pipeline events
    PIPELINE_STARTED = auto()
    PIPELINE_STAGE_STARTED = auto()
    PIPELINE_STAGE_COMPLETED = auto()
    PIPELINE_COMPLETED = auto()
    PIPELINE_FAILED = auto()

    # RAG events
    RAG_INGESTION_STARTED = auto()
    RAG_INGESTION_COMPLETED = auto()
    RAG_QUERY_STARTED = auto()
    RAG_QUERY_COMPLETED = auto()

    # Content events
    CONTENT_CREATED = auto()
    CONTENT_REVISED = auto()
    CONTENT_APPROVED = auto()

    # Custom events
    CUSTOM = auto()


@dataclass
class Event:
    """Represents an event in the system."""

    type: Union[EventType, str]
    data: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "type": self.type.name if isinstance(self.type, EventType) else self.type,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
        }


# Type alias for event handlers
EventHandler = Union[Callable[[Event], Coroutine[Any, Any, None]], Callable[[Event], None]]


class EventBus:
    """
    Central event bus for the content crew system.

    Features:
    - Async and sync handler support
    - Wildcard subscriptions
    - Event history
    """

    def __init__(self, max_history: int = 1000) -> None:
        self._handlers: dict[Union[EventType, str], list[tuple[int, EventHandler]]] = {}
        self._wildcard_handlers: list[tuple[int, EventHandler]] = []
        self._history: list[Event] = []
        self._max_history = max_history

    def subscribe(
        self,
        event_type: EventType | str | None,
        handler: EventHandler,
        priority: int = 0,
    ) -> Callable[[], None]:
        """Subscribe to an event type."""
        if event_type is None:
            self._wildcard_handlers.append((priority, handler))
            self._wildcard_handlers.sort(key=lambda x: -x[0])
            return lambda: self._wildcard_handlers.remove((priority, handler))

        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append((priority, handler))
        self._handlers[event_type].sort(key=lambda x: -x[0])

        return lambda: self._handlers[event_type].remove((priority, handler))

    def on(
        self,
        event_type: EventType | str | None = None,
        priority: int = 0,
    ) -> Callable[[EventHandler], EventHandler]:
        """Decorator to subscribe to an event type."""

        def decorator(handler: EventHandler) -> EventHandler:
            self.subscribe(event_type, handler, priority)
            return handler

        return decorator

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        handlers = self._handlers.get(event.type, [])
        all_handlers = sorted(
            handlers + self._wildcard_handlers,
            key=lambda x: -x[0],
        )

        for _, handler in all_handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"Error in event handler: {e}")

    def get_history(
        self,
        event_type: EventType | str | None = None,
        limit: int = 100,
    ) -> list[Event]:
        """Get event history, optionally filtered by type."""
        history = self._history
        if event_type is not None:
            history = [e for e in history if e.type == event_type]
        return history[-limit:]

    def clear_history(self) -> None:
        """Clear event history."""
        self._history.clear()


# Global event bus instance
event_bus = EventBus()
