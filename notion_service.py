from notion_client import Client
from config import config

class NotionService:
    def __init__(self):
        self.notion = Client(auth=config.NOTION_TOKEN) if config.NOTION_TOKEN else None

    def to_str(self, val):
        if isinstance(val, list):
            return "\n".join([str(v) for v in val])
        return str(val) if val else ""

    def push_to_notion(self, vocab: dict):
        if not self.notion:
            raise Exception("Notion Token not configured")

        properties = {
            "Word": {"title": [{"text": {"content": vocab.get("word", "")}}]},
            "Category": {"multi_select": [{"name": str(t)} for t in vocab.get("category", []) if t]},
            "Pronunciation": {"rich_text": [{"text": {"content": self.to_str(vocab.get("pronunciation", ""))}}]},
            "Meaning VN": {"rich_text": [{"text": {"content": self.to_str(vocab.get("meaning_vn", ""))}}]},
            "Meaning": {"rich_text": [{"text": {"content": self.to_str(vocab.get("meaning", ""))}}]},
            "Example": {"rich_text": [{"text": {"content": self.to_str(vocab.get("example", ""))}}]},
            "Level": {"select": {"name": vocab.get("level") or "Unknown"}},
            "Topic": {"multi_select": [{"name": str(t)} for t in vocab.get("topic", []) if t]},
            "Word Patterns": {"rich_text": [{"text": {"content": self.to_str(vocab.get("patterns", []))}}]},
            "Synonyms": {"rich_text": [{"text": {"content": self.to_str(vocab.get("synonyms", []))}}]},
            "Antonyms": {"rich_text": [{"text": {"content": self.to_str(vocab.get("antonyms", []))}}]},
            "Related Words": {"rich_text": [{"text": {"content": self.to_str(vocab.get("related_words", []))}}]},
            "Paraphrase": {"rich_text": [{"text": {"content": self.to_str(vocab.get("paraphrase", []))}}]},
            "Collocation": {"rich_text": [{"text": {"content": self.to_str(vocab.get("collocation", []))}}]},
        }

        try:
            self.notion.pages.create(
                parent={"database_id": config.NOTION_DATABASE_ID},
                properties=properties
            )
        except Exception as e:
            print(f"Error pushing to Notion: {e}")
            raise e

notion_service = NotionService()
