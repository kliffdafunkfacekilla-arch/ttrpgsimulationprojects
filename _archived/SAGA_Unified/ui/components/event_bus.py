from collections import defaultdict
from typing import Callable, Any

class EventBus:
    """
    Synchronous Event Bus for decoupled UI components.
    
    This is the central nervous system of the SAGA Unified architecture,
    enabling event-driven communication between all subsystems.
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
                    import traceback
                    print(f"[EventBus] Error in callback for {event_type}: {e}")
                    traceback.print_exc()

    def unsubscribe(self, event_type: str, callback: Callable[[Any], None]):
        """Remove a callback from event type subscribers."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass  # Callback not in list

    def clear_subscribers(self, event_type: str = None):
        """Clear all subscribers for an event type, or all events if None."""
        if event_type:
            self._subscribers[event_type].clear()
        else:
            self._subscribers.clear()