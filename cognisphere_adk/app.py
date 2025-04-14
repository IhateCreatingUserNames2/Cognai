"""# cognisphere_adk/app.py
Flask application serving as a Web UI for Cognisphere ADK.
"""

import os
import sys
import json
from typing import Dict, Any
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import asyncio

# Import ADK components
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService, Session
from google.adk.runners import Runner
from google.genai import types
import litellm

# Import Cognisphere components
from services.database import DatabaseService
from services.embedding import EmbeddingService
import services_container
from callbacks.safety import content_filter_callback, tool_argument_validator
import config
from services.openrouter_setup import OpenRouterIntegration

if not OpenRouterIntegration.configure_openrouter():
    raise RuntimeError("OpenRouter initialisation failed – check API key")
# Initialize the Flask app
app = Flask(__name__)
print("Flask app initialized.")

# --- Initialize Services ---
print("Initializing DatabaseService...")
db_service = DatabaseService(db_path=config.DATABASE_CONFIG["path"])
print("DatabaseService initialized.")
print("Initializing EmbeddingService...")
embedding_service = EmbeddingService()
print("EmbeddingService initialized.")

# Inicialize o container de serviços
services_container.initialize_services(db_service, embedding_service)

# --- Create Session Service ---
print("Initializing SessionService...")
session_service = InMemorySessionService()
print("SessionService initialized.")
litellm._turn_on_debug()


# Agora que os serviços estão inicializados, importar os agentes
from agents.memory_agent import create_memory_agent
from agents.narrative_agent import create_narrative_agent
from agents.orchestrator_agent import create_orchestrator_agent

# --- Initialize Agents ---
# Set up sub-agents
memory_agent = create_memory_agent(model=LiteLlm(model=config.MODEL_CONFIG["memory"]))
narrative_agent = create_narrative_agent(model=LiteLlm(model=config.MODEL_CONFIG["narrative"]))

# Create orchestrator
orchestrator_agent = create_orchestrator_agent(
    model=LiteLlm(model=config.MODEL_CONFIG["orchestrator"]),
    memory_agent=memory_agent,
    narrative_agent=narrative_agent
)

# Add safety callbacks if enabled
if config.SAFETY_CONFIG["enable_content_filter"]:
    orchestrator_agent.before_model_callback = content_filter_callback

if config.SAFETY_CONFIG["enable_tool_validation"]:
    orchestrator_agent.before_tool_callback = tool_argument_validator

# Create Runner
app_name = "cognisphere_adk"
runner = Runner(
    agent=orchestrator_agent,
    app_name=app_name,
    session_service=session_service
)


# --- Helper Functions ---
def ensure_session(user_id: str, session_id: str) -> Session:
    """
    Ensure a session exists and is initialized with service objects.
    """
    session = session_service.get_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id
    )

    if not session:
        # Create a new session with initialized state
        initial_state = {
            "user_preference_temperature_unit": "Celsius"
            # Não armazenamos mais os serviços aqui
        }

        session = session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            state=initial_state
        )

    return session


async def process_message(user_id: str, session_id: str, message: str):
    """
    Process a user message through the orchestrator agent.
    """
    # Ensure session exists
    session = ensure_session(user_id, session_id)

    # Prepare the user's message in ADK format
    content = types.Content(role='user', parts=[types.Part(text=message)])

    final_response_text = "No response generated."
    try:
        # Processar todos os eventos, não apenas o final
        last_event = None
        async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content
        ):
            last_event = event
            # Verificar se este é um evento de resposta final
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response_text = event.content.parts[0].text

        # Se não houver evento final mas houver um último evento, tente usar
        if not final_response_text or final_response_text == "No response generated.":
            if last_event and last_event.content and last_event.content.parts:
                final_response_text = last_event.content.parts[0].text

    except Exception as e:
        print(f"Error during runner.run_async: {e}")  # Log error
        final_response_text = f"Error processing message: {e}"

    return final_response_text


# --- Routes ---
@app.route('/')
def index():
    """Render the main UI page."""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
async def chat():
    """Handle chat messages."""
    data = request.json
    user_message = data.get('message', '')
    user_id = data.get('user_id', 'default_user')
    session_id = data.get('session_id', 'default_session')

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        # Process the message through the orchestrator
        response = await process_message(user_id, session_id, user_message)

        # Return the response
        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/memories', methods=['GET'])
def get_memories():
    """Get recent memories."""
    print("Received request for /api/memories")
    user_id = request.args.get('user_id', 'default_user')
    session_id = request.args.get('session_id', 'default_session')

    try:
        # Ensure session exists
        session = ensure_session(user_id, session_id)

        # Get memories from session state if available
        memories = session.state.get("last_recalled_memories", [])

        # Garantir que é uma lista mesmo se for None
        if memories is None:
            memories = []

        # Verificar se cada item tem as propriedades esperadas
        for memory in memories:
            if not isinstance(memory, dict):
                print(f"Warning: Invalid memory format found: {memory}")
                memories.remove(memory)
                continue

            # Garantir que campos essenciais existam
            if "content" not in memory:
                memory["content"] = "Unknown content"
            if "type" not in memory:
                memory["type"] = "unknown"
            if "emotion" not in memory:
                memory["emotion"] = "neutral"
            if "relevance" not in memory:
                memory["relevance"] = 0.5

        return jsonify({
            'memories': memories,
            'count': len(memories)
        })
    except Exception as e:
        print(f"Error in /api/memories: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        print("Finished processing /api/memories")


@app.route('/api/narratives', methods=['GET'])
def get_narratives():
    """Get active narrative threads."""
    print("Received request for /api/narratives")
    user_id = request.args.get('user_id', 'default_user')
    session_id = request.args.get('session_id', 'default_session')

    try:
        # Get all threads from database
        threads = db_service.get_all_threads()

        # Filter for active threads
        active_threads = [thread.to_dict() for thread in threads if thread.status == "active"]

        return jsonify({
            'threads': active_threads,
            'count': len(active_threads)
        })
    except Exception as e:
        print(f"Error in /api/narratives: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        print("Finished processing /api/narratives")


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status information."""
    print("Received request for /api/status")
    try:
        # Check services
        components = {
            'database_service': bool(db_service),
            'embedding_service': bool(embedding_service),
            'memory_agent': bool(memory_agent),
            'narrative_agent': bool(narrative_agent),
            'orchestrator_agent': bool(orchestrator_agent),
            'runner': bool(runner)
        }

        return jsonify({
            'system_online': all(components.values()),
            'timestamp': datetime.now().isoformat(),
            'components': components
        })
    except Exception as e:
        print(f"Error in /api/status: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        print("Finished processing /api/status")


# --- Run the Application ---
if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)

    # Create a basic index.html template if it doesn't exist
    index_path = os.path.join('templates', 'index.html')
    if not os.path.exists(index_path):
        with open(index_path, 'w') as f:
            f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Cognisphere ADK</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            color: #333;
            background-color: #f7f9fc;
        }
        .container {
            display: flex;
            height: 100vh;
            max-width: 1400px;
            margin: 0 auto;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        .chat-panel {
            flex: 2;
            display: flex;
            flex-direction: column;
            padding: 20px;
            background-color: white;
            border-right: 1px solid #ddd;
        }
        .info-panel {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background-color: #f0f4f8;
        }
        .chat-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        .chat-header h1 {
            margin: 0;
            color: #4a6fa5;
        }
        .chat-history {
            flex: 1;
            overflow-y: auto;
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 8px;
            border: 1px solid #eee;
        }
        .chat-input {
            display: flex;
            gap: 10px;
        }
        .chat-input input {
            flex: 1;
            padding: 12px 15px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 15px;
        }
        .chat-input button {
            padding: 12px 20px;
            background-color: #4a6fa5;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: background-color 0.2s;
        }
        .chat-input button:hover {
            background-color: #3a5a85;
        }
        .message {
            margin-bottom: 15px;
            padding: 12px 15px;
            border-radius: 8px;
            max-width: 80%;
            word-wrap: break-word;
        }
        .user {
            background-color: #e1f5fe;
            margin-left: auto;
            text-align: right;
            border-bottom-right-radius: 0;
        }
        .assistant {
            background-color: #f1f1f1;
            margin-right: auto;
            border-bottom-left-radius: 0;
        }
        .section {
            background-color: white;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .section h2 {
            margin-top: 0;
            color: #4a6fa5;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        button.action {
            background-color: #4a6fa5;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-top: 10px;
        }
        button.action:hover {
            background-color: #3a5a85;
        }
        .status {
            display: flex;
            gap: 10px;
            align-items: center;
            margin-bottom: 10px;
        }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background-color: #ddd;
        }
        .status-online {
            background-color: #4CAF50;
        }
        .status-offline {
            background-color: #f44336;
        }
        .memory-item, .thread-item {
            padding: 10px;
            border: 1px solid #eee;
            border-radius: 4px;
            margin-bottom: 10px;
            background-color: #fafbfc;
        }
        .thread-item h3 {
            margin-top: 0;
            color: #4a6fa5;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
        .memory-item .relevance {
            font-size: 0.8em;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="chat-panel">
            <div class="chat-header">
                <h1>Cognisphere ADK</h1>
                <div class="status" style="margin-left: 15px;">
                    <div class="status-indicator" id="status-indicator"></div>
                    <span id="status-text">Checking status...</span>
                </div>
            </div>
            <div class="chat-history" id="chat-history"></div>
            <div class="chat-input">
                <input type="text" id="user-input" placeholder="Ask Cognisphere something..." />
                <button id="send-button">Send</button>
            </div>
        </div>
        <div class="info-panel">
            <div class="section">
                <h2>System Status</h2>
                <div id="component-status">Loading...</div>
            </div>
            <div class="section">
                <h2>Memories</h2>
                <div id="memories">Loading...</div>
                <button class="action" id="recall-button">Recall Memories</button>
            </div>
            <div class="section">
                <h2>Narrative Threads</h2>
                <div id="narrative-threads">Loading...</div>
                <button class="action" id="get-threads-button">Update Threads</button>
            </div>
        </div>
    </div>

    <script>
        // Global variables
        const USER_ID = 'default_user';
        const SESSION_ID = 'default_session';

        // Helper function for API calls
        async function fetchAPI(url, method = 'GET', data = null) {
            const options = {
                method,
                headers: {
                    'Content-Type': 'application/json'
                }
            };

            if (data) {
                options.body = JSON.stringify(data);
            }

            try {
                const response = await fetch(url, options);
                return await response.json();
            } catch (error) {
                console.error('API Error:', error);
                return { error: error.message };
            }
        }

        // Initialize the UI
        document.addEventListener('DOMContentLoaded', () => {
            const chatHistory = document.getElementById('chat-history');
            const userInput = document.getElementById('user-input');
            const sendButton = document.getElementById('send-button');
            const statusIndicator = document.getElementById('status-indicator');
            const statusText = document.getElementById('status-text');
            const componentStatus = document.getElementById('component-status');
            const memoriesDiv = document.getElementById('memories');
            const narrativeThreadsDiv = document.getElementById('narrative-threads');
            const recallButton = document.getElementById('recall-button');
            const getThreadsButton = document.getElementById('get-threads-button');

            // Chat functionality
            sendButton.addEventListener('click', sendMessage);
            userInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });

            async function sendMessage() {
                const message = userInput.value.trim();
                if (!message) return;

                // Add user message to chat
                addMessageToChat('user', message);
                userInput.value = '';

                // Show thinking indicator
                addMessageToChat('assistant', 'Thinking...', 'thinking');

                // Send to backend
                const response = await fetchAPI('/api/chat', 'POST', { 
                    message,
                    user_id: USER_ID,
                    session_id: SESSION_ID
                });

                // Remove thinking indicator and add response
                const thinkingElement = document.querySelector('.thinking');
                if (thinkingElement) {
                    chatHistory.removeChild(thinkingElement);
                }

                if (response.error) {
                    addMessageToChat('assistant', `Error: ${response.error}`);
                } else {
                    addMessageToChat('assistant', response.response);

                    // Refresh UI data after interaction
                    updateMemories();
                    updateNarrativeThreads();
                }
            }

            function addMessageToChat(role, content, className) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${role}${className ? ' ' + className : ''}`;
                messageDiv.textContent = content;
                chatHistory.appendChild(messageDiv);
                chatHistory.scrollTop = chatHistory.scrollHeight;
            }

            // System status
            async function updateSystemStatus() {
                const status = await fetchAPI('/api/status');

                if (status.error) {
                    statusIndicator.className = 'status-indicator status-offline';
                    statusText.textContent = 'System Offline';
                    return;
                }

                statusIndicator.className = 'status-indicator status-online';
                statusText.textContent = 'System Online';

                // Update component status
                const components = status.components;
                let componentHTML = '<ul style="list-style: none; padding: 0;">';
                for (const [name, isActive] of Object.entries(components)) {
                    const statusClass = isActive ? 'status-online' : 'status-offline';
                    const label = name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                    componentHTML += `<li style="display: flex; align-items: center; margin-bottom: 5px;">
                        <div class="status-indicator ${statusClass}" style="margin-right: 10px;"></div> ${label}
                    </li>`;
                }
                componentHTML += '</ul>';
                componentStatus.innerHTML = componentHTML;
            }

            // Memories
            async function updateMemories() {
                const result = await fetchAPI(`/api/memories?user_id=${USER_ID}&session_id=${SESSION_ID}`);

                if (result.error) {
                    memoriesDiv.innerHTML = `<div class="error">Error: ${result.error}</div>`;
                    return;
                }

                if (!result.memories || result.memories.length === 0) {
                    memoriesDiv.innerHTML = '<p>No memories recalled yet.</p>';
                    return;
                }

                let memoriesHTML = '';
                for (const memory of result.memories) {
                    const relevancePercent = Math.round((memory.relevance || 0) * 100);
                    memoriesHTML += `
                        <div class="memory-item">
                            <div>${memory.content}</div>
                            <div class="relevance">Type: ${memory.type || 'unknown'}, Emotion: ${memory.emotion || 'neutral'}, Relevance: ${relevancePercent}%</div>
                        </div>
                    `;
                }

                memoriesDiv.innerHTML = memoriesHTML;
            }

            // Narrative threads
            async function updateNarrativeThreads() {
                const result = await fetchAPI(`/api/narratives?user_id=${USER_ID}&session_id=${SESSION_ID}`);

                if (result.error) {
                    narrativeThreadsDiv.innerHTML = `<div class="error">Error: ${result.error}</div>`;
                    return;
                }

                if (!result.threads || result.threads.length === 0) {
                    narrativeThreadsDiv.innerHTML = '<p>No active narrative threads.</p>';
                    return;
                }

                let threadsHTML = '';
                for (const thread of result.threads) {
                    const lastUpdated = new Date(thread.last_updated).toLocaleString();

                    // Get last event if available
                    let lastEventText = 'No events yet';
                    if (thread.events && thread.events.length > 0) {
                        const lastEvent = thread.events[thread.events.length - 1];
                        lastEventText = lastEvent.content || 'Event with no content';
                    }

                    threadsHTML += `
                        <div class="thread-item">
                            <h3>${thread.title}</h3>
                            <div>${thread.description}</div>
                            <div><strong>Theme:</strong> ${thread.theme}</div>
                            <div><strong>Latest:</strong> ${lastEventText}</div>
                            <div><strong>Last updated:</strong> ${lastUpdated}</div>
                        </div>
                    `;
                }

                narrativeThreadsDiv.innerHTML = threadsHTML;
            }

            // Button handlers
            recallButton.addEventListener('click', () => {
                memoriesDiv.innerHTML = '<div class="loading">Recalling memories...</div>';
                updateMemories();
            });

            getThreadsButton.addEventListener('click', () => {
                narrativeThreadsDiv.innerHTML = '<div class="loading">Updating threads...</div>';
                updateNarrativeThreads();
            });

            // Initial data load
            updateSystemStatus();
            updateMemories();
            updateNarrativeThreads();

            // Add a welcome message
            addMessageToChat('assistant', 'Welcome to Cognisphere ADK! How can I help you today?');

            // Refresh status every minute
            setInterval(updateSystemStatus, 60000);
        });
    </script>
</body>
</html>''')
        print(f"Created template at {index_path}")

    # Run the app
    print("Starting Flask app...")
    app.run(host='0.0.0.0', debug=True)
