import pytest
from saga_engine.core.bus import EventBus

def test_subscribe_valid_channel():
    """Verify that subscribing to a valid channel works correctly."""
    bus = EventBus()
    callback_called = False

    def test_callback(payload):
        nonlocal callback_called
        callback_called = True

    bus.subscribe("STATE_UPDATE", test_callback)
    bus.publish("STATE_UPDATE", {"test": "data"})

    assert callback_called is True
    assert test_callback in bus.subscribers["STATE_UPDATE"]

def test_subscribe_invalid_channel(capsys):
    """Verify that subscribing to an invalid channel prints an error message."""
    bus = EventBus()

    def test_callback(payload):
        pass

    invalid_channel = "INVALID_CHANNEL"
    bus.subscribe(invalid_channel, test_callback)

    # Check stdout for the expected error message
    captured = capsys.readouterr()
    expected_error = f"[BUS ERROR] Unrecognized event channel: {invalid_channel}"
    assert expected_error in captured.out
    assert invalid_channel not in bus.subscribers

def test_publish_success():
    """Verify that publishing to multiple subscribers works."""
    bus = EventBus()
    results = []

    def cb1(p): results.append(1)
    def cb2(p): results.append(2)

    bus.subscribe("PLAYER_ACTION", cb1)
    bus.subscribe("PLAYER_ACTION", cb2)

    bus.publish("PLAYER_ACTION", {})

    assert 1 in results
    assert 2 in results
    assert len(results) == 2

def test_publish_invalid_channel():
    """Verify that publishing to an invalid channel does nothing (no crash)."""
    bus = EventBus()
    # This should not raise any exception
    bus.publish("NON_EXISTENT", {"data": 123})
