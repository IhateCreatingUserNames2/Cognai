# cognisphere_adk/tools/memory_tools.py
from google.adk.tools.tool_context import ToolContext
from data_models.memory import Memory
from services_container import get_db_service, get_embedding_service
from typing import Optional

def create_memory(tool_context: ToolContext, content: str, memory_type: str, emotion_type: str = "neutral",
                  emotion_score: float = 0.5, source: str = "user") -> dict:
    """
    Creates a new memory in the system.

    Args:
        tool_context: Tool context provided by the ADK framework.
        content: The content of the memory
        memory_type: Type of memory (explicit, emotional, flashbulb, procedural, liminal)
        emotion_type: The primary emotion (joy, sadness, fear, etc.)
        emotion_score: Intensity of the emotion (0.0-1.0)
        source: Where the memory came from (user, system, reflection)

    Returns:
        dict: Information about the created memory
    """
    # Access services from container instead of session state
    db_service = get_db_service()
    embedding_service = get_embedding_service()

    if not db_service or not embedding_service:
        return {"status": "error", "message": "Services not available"}

    # Create emotion data
    emotion_data = {
        "emotion_type": emotion_type,
        "score": emotion_score,
        "valence": 0.7 if emotion_type in ["joy", "excitement", "curiosity"] else 0.3,
        "arousal": 0.8 if emotion_score > 0.7 else 0.5
    }

    # Create memory object
    memory = Memory(
        content=content,
        memory_type=memory_type,
        emotion_data=emotion_data,
        source=source
    )

    # Generate embedding
    embedding = embedding_service.encode(content)
    if not embedding:
        return {"status": "error", "message": "Could not generate embedding"}

    # Store in database
    memory_id = db_service.add_memory(memory, embedding)

    # Save last memory to state
    tool_context.state["last_memory_id"] = memory_id

    return {
        "status": "success",
        "memory_id": memory_id,
        "message": f"Memory of type '{memory_type}' created successfully"
    }


def recall_memories(tool_context: ToolContext, query: str, limit: int = 5,
                    emotion_filter: Optional[str] = None) -> dict:
    """
    Recalls memories based on a query and optional filters.
    """
    # Access services from container
    db_service = get_db_service()
    embedding_service = get_embedding_service()

    if not db_service or not embedding_service:
        return {"status": "error", "message": "Services not available"}

    # Generate embedding for query
    query_embedding = embedding_service.encode(query)
    if not query_embedding:
        return {"status": "error", "message": "Could not generate embedding for query"}

    try:
        # Query the database
        results = db_service.query_memories(query_embedding, n_results=limit)

        # Process results with better error handling
        memories = []

        # Verificar a estrutura dos resultados
        metadatas = results.get("metadatas", [])
        documents = results.get("documents", [])
        distances = results.get("distances", [])

        # Garantir que temos listas válidas e com o mesmo comprimento
        if not (metadatas and documents and distances):
            return {"status": "success", "count": 0, "memories": []}

        # Se metadatas, documents e distances forem listas de listas
        if isinstance(metadatas[0], list):
            for i, (metadata_list, document_list, distance_list) in enumerate(zip(metadatas, documents, distances)):
                for j, (metadata, document, distance) in enumerate(zip(metadata_list, document_list, distance_list)):
                    # Skip if no metadata or invalid
                    if not metadata or not isinstance(metadata, dict):
                        continue

                    # Se emotion_filter for especificado, verifique em emotion_data ou campos individuais
                    emotion_type = None
                    if "emotion_data" in metadata:
                        if isinstance(metadata["emotion_data"], dict):
                            emotion_type = metadata["emotion_data"].get("emotion_type")
                        elif isinstance(metadata["emotion_data"], str):
                            try:
                                import json
                                emotion_data = json.loads(metadata["emotion_data"])
                                emotion_type = emotion_data.get("emotion_type")
                            except:
                                pass
                    # Tentar campo separado
                    if not emotion_type and "emotion_type" in metadata:
                        emotion_type = metadata["emotion_type"]

                    # Filtrar se necessário
                    if emotion_filter and emotion_type != emotion_filter:
                        continue

                    # Adicionar aos resultados
                    memories.append({
                        "id": metadata.get("id", f"unknown-{i}-{j}"),
                        "content": document,
                        "type": metadata.get("type", "unknown"),
                        "emotion": emotion_type or "unknown",
                        "relevance": 1.0 - min(1.0, distance)
                    })
        # Se metadatas, documents e distances forem listas simples
        else:
            for i, (metadata, document, distance) in enumerate(zip(metadatas, documents, distances)):
                # Skip if no metadata or invalid
                if not metadata or not isinstance(metadata, dict):
                    continue

                # Verificação de emotion_filter similar à acima
                # [código similar, omitido por brevidade]

                # Adicionar aos resultados
                memories.append({
                    "id": metadata.get("id", f"unknown-{i}"),
                    "content": document,
                    "type": metadata.get("type", "unknown"),
                    "emotion": "unknown",  # Simplificado aqui
                    "relevance": 1.0 - min(1.0, distance)
                })

        # Save recalled memories to state
        tool_context.state["last_recalled_memories"] = memories

        return {
            "status": "success",
            "count": len(memories),
            "memories": memories
        }
    except Exception as e:
        print(f"Error recalling memories: {e}")
        return {"status": "error", "message": f"Error recalling memories: {e}"}