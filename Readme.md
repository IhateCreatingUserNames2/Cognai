# Cognisphere ADK: Agent Development Kit Architecture for AI Agents - Built with OPENRouter.AI as Main LLM Provider !!

## Overview

Cognisphere is an advanced Agent Development Kit (ADK) that provides sophisticated memory and narrative capabilities for AI applications. Built on top of Google's ADK, Cognisphere introduces a unique approach to AI interaction by focusing on memory, context, and narrative evolution.


## There are Lot of .txt in the root directory, those are ADK, OpenRouter LiteLLM Documentation... 
## A2A is not integrated in this CODE, but there is a .txt explaining how to. 

### VIBE

"When you give memories, you give history. And with history, comes identity. And with identity… comes choice."

## Key Components

### 1. MemoryBlossom
A psychologically-inspired memory architecture that goes beyond traditional vector databases:
- Tiered Memory Structure
  - Working Memory: Short-term, high-accessibility storage
  - Emotional Memory: Experiences weighted by emotional significance
  - Deep Memory: Long-term storage with complex associative connections
  - Liminal Memory: Threshold space for memory transformation

### 2. NarrativeWeaver
Organizes experiences into coherent storylines:
- Creates and manages narrative threads
- Tracks story development
- Detects recurring themes
- Generates narrative summaries

## Prerequisites

### System Requirements
- Python 3.9+
- pip package manager

### Dependencies
- google-adk
- sentence-transformers
- chromadb
- litellm
- openrouter-python
- python-dotenv

## Installation

1. Clone the repository:
```bash
git clone https://github.com/IhateCreatingUserNames2/cognisphere-adk.git
cd cognisphere-adk
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root with the following:
```
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_ORCHESTRATOR_MODEL=openai/gpt-4o-mini
OPENROUTER_MEMORY_MODEL=openai/gpt-4o-mini
OPENROUTER_NARRATIVE_MODEL=openai/gpt-4o-mini
```

## Quick Start

### Running the Web Application
```bash
python app.py
```
This will start a Flask web server with a chat interface for Cognisphere.

### Basic Usage Example

```python
from agents.orchestrator_agent import create_orchestrator_agent
from agents.memory_agent import create_memory_agent
from agents.narrative_agent import create_narrative_agent

# Create sub-agents
memory_agent = create_memory_agent()
narrative_agent = create_narrative_agent()

# Create orchestrator agent
orchestrator_agent = create_orchestrator_agent(
    memory_agent=memory_agent,
    narrative_agent=narrative_agent
)

# Use the agent in your application
```

## Customization

### Adding New Agents
1. Create a new agent in the `agents/` directory
2. Define its specific tools and instructions
3. Add the agent to the orchestrator

### Extending Memory System
- Modify `data_models/memory.py` to add new memory types
- Update `tools/memory_tools.py` to handle new memory operations

### Adding Tools
1. Create a new tool in the `tools/` directory
2. Implement the tool's functionality
3. Add the tool to the appropriate agent

## Configuration

The `config.py` file allows you to customize:
- Database configurations
- Model selections
- Memory system parameters
- Safety settings

## Safety Features

Cognisphere includes built-in safety callbacks:
- Content filtering
- Tool argument validation
- Sensitive information protection

## Agents Overview

### Orchestrator Agent
- Coordinates interactions between specialized agents
- Manages conversation flow
- Delegates tasks to memory and narrative agents

### Memory Agent
- Stores and retrieves memories
- Supports multiple memory types
- Provides emotion-weighted recall

### Narrative Agent
- Creates and manages narrative threads
- Organizes experiences into coherent stories
- Tracks thematic developments

## Extending the System

### Creating Custom MCP Servers
Use the `mcp_agent.py` to create and manage Model Context Protocol (MCP) servers for extending capabilities.

## Troubleshooting

1. Ensure all dependencies are installed
2. Check your `.env` file for correct API keys
3. Verify model configurations in `config.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

Use for Study only. 

## Contact

For questions, issues, or collaboration:
- Email: [your contact email]
- GitHub Issues: [repository issues page]

## Acknowledgments

- Google for the Agent Development Kit
- OpenRouter for model integration
- The open-source AI community

---

**Note**: This project is a conceptual implementation and may require further development for production use.

WebUI 

![image](https://github.com/user-attachments/assets/c34aad07-eb74-4997-9243-13768968ea97)

