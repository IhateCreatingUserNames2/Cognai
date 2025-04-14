#cognisphere/services/database.py
import chromadb
import json
import os

from data_models.narrative import NarrativeThread


class DatabaseService:
    def __init__(self, db_path="./cognisphere_data"): # Adjusted default path
        # No lock needed, initialize directly
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
        
        # Ensure the ChromaDB path exists before initializing
        chroma_db_path = os.path.join(db_path) # Chroma persists directly in the given path
        os.makedirs(chroma_db_path, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=chroma_db_path)
        self.collections = {}
        self.ensure_collection("memories")
        self.ensure_collection("narrative_threads")
        self.ensure_collection("entities")
        self.initialized = True # Mark as initialized

    def ensure_collection(self, name):
        """Ensure a collection exists."""
        try:
            self.collections[name] = self.client.get_collection(name=name)
        except:
            self.collections[name] = self.client.create_collection(name=name)
        return self.collections[name]

    def add_memory(self, memory, embedding):
        """Add a memory to the database."""
        collection = self.collections["memories"]

        # Obter o dicionário de memória
        memory_dict = memory.to_dict()

        # Serializar dados emocionais para JSON se for um dicionário
        if "emotion_data" in memory_dict and isinstance(memory_dict["emotion_data"], dict):
            import json
            memory_dict["emotion_data"] = json.dumps(memory_dict["emotion_data"])

        collection.add(
            ids=[memory.id],
            embeddings=[embedding],
            documents=[memory.content],
            metadatas=[memory_dict]
        )

        return memory.id

    def query_memories(self, query_embedding, n_results=5):
        """Query memories by embedding similarity."""
        collection = self.collections["memories"]
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["metadatas", "documents", "distances"]
        )

        # Desserializar dados de emoção - com verificação melhor de tipos
        import json

        # Verificar a estrutura de dados retornada
        metadatas = results.get("metadatas", [])
        if metadatas and isinstance(metadatas, list):
            # Se for uma lista direta de metadados
            if metadatas and all(isinstance(m, dict) for m in metadatas):
                for metadata in metadatas:
                    if "emotion_data" in metadata and isinstance(metadata["emotion_data"], str):
                        try:
                            metadata["emotion_data"] = json.loads(metadata["emotion_data"])
                        except json.JSONDecodeError:
                            pass
            # Se for uma lista de listas (formato esperado)
            elif metadatas and isinstance(metadatas[0], list):
                for metadata_list in metadatas:
                    for metadata in metadata_list:
                        if isinstance(metadata, dict) and "emotion_data" in metadata and isinstance(
                                metadata["emotion_data"], str):
                            try:
                                metadata["emotion_data"] = json.loads(metadata["emotion_data"])
                            except json.JSONDecodeError:
                                pass

        return results

    def save_thread(self, thread):
        """Save a narrative thread."""
        # Save thread data to a JSON file
        threads_dir = os.path.join(self.db_path, "threads")
        os.makedirs(threads_dir, exist_ok=True)

        file_path = os.path.join(threads_dir, f"{thread.id}.json")
        with open(file_path, "w") as f:
            json.dump(thread.to_dict(), f, indent=2)

        return thread.id

    def get_thread(self, thread_id):
        """Get a narrative thread by ID."""
        file_path = os.path.join(self.db_path, "threads", f"{thread_id}.json")
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                return NarrativeThread.from_dict(data)
        except:
            return None

    def get_all_threads(self):
        """Get all narrative threads."""
        threads_dir = os.path.join(self.db_path, "threads")
        os.makedirs(threads_dir, exist_ok=True)

        threads = []
        for filename in os.listdir(threads_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(threads_dir, filename)
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        threads.append(NarrativeThread.from_dict(data))
                except:
                    continue

        return threads
