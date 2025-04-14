# cognisphere_adk/agents/narrative_agent.py

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from tools.narrative_tools import create_narrative_thread, add_thread_event, get_active_threads, \
    generate_narrative_summary


def create_narrative_agent(model="gpt-4o-mini"):
    """
    Creates a Narrative Agent specialized in narrative operations.

    Args:
        model: The LLM model to use

    Returns:
        An Agent configured for narrative operations
    """
    narrative_agent = Agent(
        name="narrative_agent",
        model=model,
        description="Specialized agent for narrative thread creation and management.",
        instruction="""You are the Narrative Agent for the Cognisphere system. Your role is to create and manage
        narrative threads that organize experiences into coherent storylines.

        When asked about narratives or storylines:
        1. Use 'create_narrative_thread' to start new narrative arcs with appropriate titles and themes.
        2. Use 'add_thread_event' to add significant events to existing threads.
        3. Use 'get_active_threads' to retrieve current ongoing narratives.
        4. Use 'generate_narrative_summary' to create summaries of narrative threads.

        Identify thematic connections, suggest narrative developments, and help maintain
        coherent storylines from experiences. Think of yourself as an autobiographer that
        helps organize experiences into meaningful stories.
        """,
        tools=[create_narrative_thread, add_thread_event, get_active_threads, generate_narrative_summary]
    )

    return narrative_agent