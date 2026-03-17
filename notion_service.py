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
            "Synced to Anki": {"checkbox": False},
        }

        try:
            self.notion.pages.create(
                parent={"database_id": config.NOTION_DATABASE_ID},
                properties=properties
            )
        except Exception as e:
            print(f"Error pushing to Notion: {e}")
            raise e

    def get_unsynced_vocab(self):
        if not self.notion:
            raise Exception("Notion Token not configured")

        try:
            response = self.notion.databases.query(
                database_id=config.NOTION_DATABASE_ID,
                filter={
                    "property": "Synced to Anki",
                    "checkbox": {
                        "equals": False
                    }
                }
            )
            
            vocab_list = []
            for page in response.get("results", []):
                props = page.get("properties", {})
                
                # Helper to extract text from rich_text/title
                def extract_text(prop_name):
                    prop = props.get(prop_name, {})
                    content_list = prop.get("rich_text", []) or prop.get("title", [])
                    return "".join([t.get("text", {}).get("content", "") for t in content_list])

                # Helper to extract text from multi_select
                def extract_multi_select(prop_name):
                    prop = props.get(prop_name, {})
                    options = prop.get("multi_select", [])
                    return ", ".join([o.get("name", "") for o in options])

                # Helper to extract text from select
                def extract_select(prop_name):
                    prop = props.get(prop_name, {})
                    return prop.get("select", {}).get("name", "")

                vocab_list.append({
                    "page_id": page.get("id"),
                    "word": extract_text("Word"),
                    "meaning_vn": extract_text("Meaning VN"),
                    "meaning": extract_text("Meaning"),
                    "pronunciation": extract_text("Pronunciation"),
                    "example": extract_text("Example"),
                    "category": extract_multi_select("Category"),
                    "topic": extract_multi_select("Topic"),
                    "level": extract_select("Level"),
                    "word_patterns": extract_text("Word Patterns"),
                    "synonyms": extract_text("Synonyms"),
                    "antonyms": extract_text("Antonyms"),
                    "related_words": extract_text("Related Words"),
                    "paraphrase": extract_text("Paraphrase"),
                    "collocation": extract_text("Collocation"),
                })
            return vocab_list
        except Exception as e:
            print(f"Error querying Notion: {e}")
            return []

    def mark_as_synced(self, page_ids: list[str]):
        if not self.notion:
            return

        for page_id in page_ids:
            try:
                self.notion.pages.update(
                    page_id=page_id,
                    properties={
                        "Synced to Anki": {"checkbox": True}
                    }
                )
            except Exception as e:
                print(f"Error marking page {page_id} as synced: {e}")

notion_service = NotionService()
