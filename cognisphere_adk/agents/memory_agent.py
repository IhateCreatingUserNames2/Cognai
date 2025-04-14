from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from tools.memory_tools import create_memory, recall_memories


def create_memory_agent(model="gpt-4o-mini"):
    """
    Creates a Memory Agent specialized in memory operations.

    Args:
        model: The LLM model to use

    Returns:
        An Agent configured for memory operations
    """
    memory_agent = Agent(
        name="memory_agent",
        model=model,
        description="Specialized agent for memory storage and retrieval operations.",
        instruction="""You are the Memory Agent for the Cognisphere system. Your role is to manage the storage and 
        retrieval of memories.

        When asked to store or remember information:
        1. Use the 'create_memory' tool to store new memories, categorizing them appropriately.
        2. Use the 'recall_memories' tool to retrieve relevant memories based on queries.

        Memory Types:
        - explicit: Factual information and specific interactions
        - emotional: Experiences with emotional significance
        - flashbulb: Highly significant or transformative memories
        - procedural: Process or how-to knowledge
        - liminal: Threshold thoughts or transformative ideas

        For each memory, determine the appropriate emotion type and score based on the content.
        Present recalled memories clearly, showing their content and relevance.
        """,
        tools=[create_memory, recall_memories]
    )

    return memory_agent