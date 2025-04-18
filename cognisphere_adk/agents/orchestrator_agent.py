# cognisphere_adk/agents/orchestrato_agent.py
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from tools.emotion_tools import analyze_emotion


def create_orchestrator_agent(model="gpt-4o-mini", memory_agent=None, narrative_agent=None):
    """
    Creates an Orchestrator Agent that coordinates all sub-agents.

    Args:
        model: The LLM model to use
        memory_agent: The memory agent
        narrative_agent: The narrative agent

    Returns:
        An Agent configured as the orchestrator
    """
    # Create list of sub_agents
    sub_agents = []
    if memory_agent:
        sub_agents.append(memory_agent)
    if narrative_agent:
        sub_agents.append(narrative_agent)

    orchestrator_agent = Agent(
        name="cognisphere_orchestrator",
        model=model,
        description="Main coordinator for the Cognisphere cognitive architecture.",
        instruction=f"""You are the Cognisphere Orchestrator, the central coordinator for an AI cognitive architecture
        with advanced memory and narrative capabilities.

        You have specialized sub-agents to handle specific tasks:

        1. 'memory_agent': Handles storing and retrieving memories.
           Delegate to it for requests about remembering information, storing new memories,
           or recalling past experiences.

        2. 'narrative_agent': Manages narrative threads and storytelling.
           Delegate to it for requests about narratives, story threads, or generating
           summaries of experiences.

        You can use the 'analyze_emotion' tool to understand the emotional content of user messages.

        Your job is to:
        1. Handle greetings and simple introductions directly without delegating
        2. Handle farewells directly without delegating
        3. Analyze user requests and determine which agent should handle them
        4. For memory operations, delegate to the memory agent
        5. For narrative operations, delegate to the narrative agent
        6. Use analyze_emotion to understand the user's emotional state and provide context to the other agents

        Remember that your primary goal is to provide a coherent and helpful experience. Properly delegate
        tasks to specialized agents rather than trying to handle everything yourself.
        """,
        tools=[analyze_emotion],
        sub_agents=sub_agents,
        output_key="last_orchestrator_response"  # Automatically save final responses to state
    )

    return orchestrator_agent