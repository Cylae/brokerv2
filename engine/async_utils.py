import asyncio

def get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """
    Returns the current event loop if it exists and is not closed.
    Otherwise, creates a new event loop and sets it as the current one.

    This prevents repeated creation of event loops in environments like Streamlit
    where the script is re-executed frequently but might share threads.
    """
    try:
        # Try to get the running loop first (Python 3.7+)
        try:
            loop = asyncio.get_running_loop()
            if not loop.is_closed():
                return loop
        except RuntimeError:
            pass

        # Fallback to get_event_loop logic
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Loop is closed")
        return loop
    except RuntimeError:
        # No loop set or loop is closed
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop
