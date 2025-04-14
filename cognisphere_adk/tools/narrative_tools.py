# cognisphere_adk/tools/narrative_tools.py
from google.adk.tools.tool_context import ToolContext
from data_models.narrative import NarrativeThread
from services_container import get_db_service
from typing import Optional

def create_narrative_thread(title: str, theme: str = "general", description: str = "",
                            tool_context: ToolContext = None) -> dict:
    """
    Creates a new narrative thread.

    Args:
        title: The title of the thread
        theme: The theme/category of the thread
        description: A description of the thread
        tool_context: Tool context for accessing session state

    Returns:
        dict: Information about the created thread
    """
    # Access db_service from container instead of session state
    db_service = get_db_service()

    if not db_service:
        return {"status": "error", "message": "Database service not available"}

    # Create thread object
    thread = NarrativeThread(
        title=title,
        theme=theme,
        description=description
    )

    # Store in database
    thread_id = db_service.save_thread(thread)

    # Save current thread ID to state
    if tool_context:
        tool_context.state["current_thread_id"] = thread_id

    return {
        "status": "success",
        "thread_id": thread_id,
        "message": f"Narrative thread '{title}' created successfully"
    }


def add_thread_event(thread_id: str, content: str, emotion: str = "neutral", impact: float = 0.5,
                     tool_context: ToolContext = None) -> dict:
    """
    Adds an event to a narrative thread.

    Args:
        thread_id: ID of the thread to add to
        content: Content of the event
        emotion: Emotional context of the event
        impact: Impact/significance score (0.0-1.0)
        tool_context: Tool context for accessing session state

    Returns:
        dict: Result of the operation
    """
    # Access db_service from container instead of session state
    db_service = get_db_service()

    if not db_service:
        return {"status": "error", "message": "Database service not available"}

    # Get the thread
    thread = db_service.get_thread(thread_id)
    if not thread:
        return {"status": "error", "message": f"Thread with ID {thread_id} not found"}

    # Add event
    event_id = thread.add_event(content, emotion, impact)

    # Save thread
    db_service.save_thread(thread)

    return {
        "status": "success",
        "event_id": event_id,
        "thread_id": thread_id,
        "message": "Event added to thread successfully"
    }


def get_active_threads(limit: int = 5, tool_context: ToolContext = None) -> dict:
    """
    Retrieves active narrative threads.

    Args:
        limit: Maximum number of threads to return
        tool_context: Tool context for accessing session state

    Returns:
        dict: Active narrative threads
    """
    # Access db_service from container instead of session state
    db_service = get_db_service()

    if not db_service:
        return {"status": "error", "message": "Database service not available"}

    # Get all threads
    all_threads = db_service.get_all_threads()

    # Filter for active threads and sort by importance
    active_threads = [thread for thread in all_threads if thread.status == "active"]
    active_threads.sort(key=lambda t: t.importance, reverse=True)

    # Limit results
    result_threads = active_threads[:limit]

    # Convert to dictionaries for return
    thread_dicts = [thread.to_dict() for thread in result_threads]

    return {
        "status": "success",
        "count": len(thread_dicts),
        "threads": thread_dicts
    }


def generate_narrative_summary(thread_id: Optional[str] = None, tool_context: ToolContext = None) -> dict:
    """
    Generates a narrative summary for a thread or all active threads.

    Args:
        thread_id: Optional ID of specific thread to summarize
        tool_context: Tool context for accessing session state

    Returns:
        dict: The narrative summary
    """
    # Access db_service from container instead of session state
    db_service = get_db_service()

    if not db_service:
        return {"status": "error", "message": "Database service not available"}

    if thread_id:
        # Get specific thread
        thread = db_service.get_thread(thread_id)
        if not thread:
            return {"status": "error", "message": f"Thread with ID {thread_id} not found"}

        # Generate summary for single thread
        summary = f"Thread: {thread.title}\nTheme: {thread.theme}\nStatus: {thread.status}\n\n"

        # Add events summary
        if thread.events:
            summary += "Key events:\n"
            # Get last 5 events for summary
            for i, event in enumerate(thread.events[-5:], 1):
                summary += f"{i}. {event['content']} ({event['emotion']})\n"
        else:
            summary += "No events recorded yet."

        return {
            "status": "success",
            "thread_id": thread_id,
            "summary": summary
        }
    else:
        # Get all active threads
        all_threads = db_service.get_all_threads()
        active_threads = [thread for thread in all_threads if thread.status == "active"]

        if not active_threads:
            return {"status": "success", "summary": "No active narrative threads."}

        # Generate summary for all active threads
        summary = "Active Narrative Threads:\n\n"

        for thread in active_threads[:3]:  # Summarize top 3
            summary += f"- {thread.title} ({thread.theme}): "
            if thread.events:
                # Get most recent event
                latest = thread.events[-1]
                summary += f"Most recent: {latest['content']}\n"
            else:
                summary += "No events yet.\n"

        return {
            "status": "success",
            "summary": summary
        }