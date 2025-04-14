import datetime
import uuid


class NarrativeThread:
    """Represents a narrative thread in the Cognisphere system."""

    def __init__(self, title, theme="unclassified", description=""):
        self.id = str(uuid.uuid4())
        self.title = title
        self.theme = theme
        self.description = description
        self.creation_time = datetime.utcnow().isoformat()
        self.last_updated = self.creation_time
        self.events = []
        self.status = "active"  # active, resolved, dormant
        self.importance = 0.5

    def add_event(self, content, emotion="neutral", impact=0.5):
        """Add an event to this thread."""
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "content": content,
            "emotion": emotion,
            "impact": impact
        }
        self.events.append(event)
        self.last_updated = event["timestamp"]
        return event["id"]

    def to_dict(self):
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "title": self.title,
            "theme": self.theme,
            "description": self.description,
            "creation_time": self.creation_time,
            "last_updated": self.last_updated,
            "events": self.events,
            "status": self.status,
            "importance": self.importance
        }

    @classmethod
    def from_dict(cls, data):
        """Create from dictionary."""
        thread = cls(
            title=data["title"],
            theme=data["theme"],
            description=data["description"]
        )
        thread.id = data["id"]
        thread.creation_time = data["creation_time"]
        thread.last_updated = data["last_updated"]
        thread.events = data["events"]
        thread.status = data["status"]
        thread.importance = data["importance"]
        return thread