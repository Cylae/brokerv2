import asyncio
import pytest
from engine.async_utils import get_or_create_event_loop

def test_get_or_create_event_loop_creates_new():
    """
    Test that it creates a new loop if none exists.
    We need to ensure no loop is set initially for this thread.
    """
    # Save current loop to restore later
    try:
        current_loop = asyncio.get_event_loop()
    except RuntimeError:
        current_loop = None

    # Clear current loop
    asyncio.set_event_loop(None)

    loop = get_or_create_event_loop()
    assert isinstance(loop, asyncio.AbstractEventLoop)
    assert not loop.is_closed()

    # Verify it is set as current
    assert asyncio.get_event_loop() is loop

    # Cleanup
    if current_loop:
        asyncio.set_event_loop(current_loop)
    else:
        asyncio.set_event_loop(None)

def test_get_or_create_event_loop_reuses_existing():
    """
    Test that it reuses the existing loop.
    """
    # Create a fresh loop and set it
    loop1 = asyncio.new_event_loop()
    asyncio.set_event_loop(loop1)

    loop2 = get_or_create_event_loop()
    assert loop1 is loop2

    # Cleanup
    loop1.close()
    asyncio.set_event_loop(None)

def test_get_or_create_event_loop_handles_closed():
    """
    Test that it creates a new loop if the existing one is closed.
    """
    loop1 = asyncio.new_event_loop()
    asyncio.set_event_loop(loop1)
    loop1.close()

    loop2 = get_or_create_event_loop()
    assert loop2 is not loop1
    assert not loop2.is_closed()

    # Cleanup
    loop2.close()
    asyncio.set_event_loop(None)

def test_get_or_create_event_loop_running_loop():
    """
    Test that it returns the running loop if there is one.
    """
    loop1 = asyncio.new_event_loop()
    asyncio.set_event_loop(loop1)

    # We must start the loop and test from within it to get an active running loop
    async def get_loop_from_inside():
        return get_or_create_event_loop()

    loop2 = loop1.run_until_complete(get_loop_from_inside())
    assert loop1 is loop2

    loop1.close()
    asyncio.set_event_loop(None)
