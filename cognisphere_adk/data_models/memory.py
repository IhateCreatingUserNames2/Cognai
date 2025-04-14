import datetime
import uuid


class Memory:
    """Represents a memory entry in the Cognisphere system."""

    def __init__(self, content, memory_type, emotion_data=None, source="user"):
        self.id = str(uuid.uuid4())
        self.content = content
        self.type = memory_type  # explicit, emotional, flashbulb, etc.
        self.creation_time = datetime.time().isoformat()
        self.emotion_data = emotion_data or {
            'emotion_type': 'neutral',
            'score': 0.5,
            'valence': 0.5,
            'arousal': 0.5
        }
        self.source = source

    def to_dict(self):
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "content": self.content,
            "type": self.type,
            "creation_time": self.creation_time,
            "emotion_data": self.emotion_data,
            "source": self.source
        }

    @classmethod
    def from_dict(cls, data):
        """Create from dictionary."""
        memory = cls(
            content=data["content"],
            memory_type=data["type"],
            emotion_data=data.get("emotion_data"),
            source=data.get("source", "user")
        )
        memory.id = data["id"]
        memory.creation_time = data["creation_time"]
        return memory