from collections import defaultdict
from typing import Callable, Any

class EventBus:
    """
    Synchronous Event Bus for decoupled UI components.
    """
    def __init__(self):
        self._subscribers = defaultdict(list)

    def subscribe(self, event_type: str, callback: Callable[[Any], None]):
        """Register a callback for a specific event type."""
        self._subscribers[event_type].append(callback)

    def publish(self, event_type: str, payload: Any = None):
        """Notify all subscribers of an event."""
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(payload)
                except Exception as e:
                    print(f"[EventBus] Error in callback for {event_type}: {e}")
