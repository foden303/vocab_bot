import asyncio
from notion_client import AsyncClient
from config import config


class NotionService:
    # ----------------- Notion Property Constants ----------------- #
    PROP_WORD = "Word"
    PROP_COLLOCATION = "Collocation"
    PROP_TYPE = "Type"
    PROP_CATEGORY = "Category"
    PROP_PRONUNCIATION = "Pronunciation"
    PROP_MEANING_VN = "Meaning VN"
    PROP_MEANING = "Meaning"
    PROP_EXAMPLE = "Example"
    PROP_LEVEL = "Level"
    PROP_TOPIC = "Topic"
    PROP_WORD_PATTERNS = "Word Patterns"
    PROP_SYNONYMS = "Synonyms"
    PROP_ANTONYMS = "Antonyms"
    PROP_RELATED_WORDS = "Related Words"
    PROP_PARAPHRASE = "Paraphrase"
    PROP_COLLOCATION = "Collocation"
    PROP_SYNCED_TO_ANKI = "Synced to Anki"
    PROP_SYNC_AUDIO = "Sync Audio"

    # ----------------- Init ----------------- #
    def __init__(self):
        self.notion = AsyncClient(
            auth=config.NOTION_TOKEN) if config.NOTION_TOKEN else None

    # ----------------- Helpers ----------------- #
    @staticmethod
    def to_str(val) -> str:
        if isinstance(val, list):
            return "\n".join([str(v) for v in val])
        return str(val) if val else ""

    @staticmethod
    def _build_rich_text(content: str) -> list[dict]:
        return [{"text": {"content": content}}]

    @staticmethod
    def _build_multi_select(items: list[str]) -> list[dict]:
        return [{"name": str(i)} for i in items if i]

    # ------------------- Extractors ------------------- #
    @staticmethod
    def _extract_text(prop: dict) -> str:
        content_list = prop.get("rich_text") or prop.get("title") or []
        if not isinstance(content_list, list):
            content_list = []
        return "".join([t.get("text", {}).get("content", "") for t in content_list])

    @staticmethod
    def _extract_multi_select(prop: dict) -> str:
        options = prop.get("multi_select") or []
        if not isinstance(options, list):
            options = []
        return ", ".join([o.get("name", "") for o in options])

    @staticmethod
    def _extract_select(prop: dict) -> str:
        sel = prop.get("select") or {}
        return sel.get("name", "")

    # ------------------- Notion Actions ------------------- #
    async def push_to_notion_collocation_db(self, collocation: dict):
        if not self.notion:
            raise Exception("Notion Token not configured")

        properties = {
            self.PROP_COLLOCATION: {"title": self._build_rich_text(collocation.get("collocation", ""))},
            self.PROP_TYPE: {"rich_text": self._build_rich_text(self.to_str(collocation.get("type", "")))},
            self.PROP_MEANING: {"rich_text": self._build_rich_text(self.to_str(collocation.get("meaning", "")))},
            self.PROP_EXAMPLE: {"rich_text": self._build_rich_text(self.to_str(collocation.get("example", "")))},
            self.PROP_TOPIC: {"multi_select": self._build_multi_select(collocation.get("topic", []))},
            self.PROP_SYNONYMS: {"rich_text": self._build_rich_text(self.to_str(collocation.get("synonyms", [])))},
            self.PROP_SYNCED_TO_ANKI: {"checkbox": False},
            self.PROP_SYNC_AUDIO: {"checkbox": False},
        }

        try:
            await self.notion.pages.create(
                parent={"database_id": config.NOTION_DB_COLLOCATION_ID}, properties=properties)
        except Exception as e:
            print(f"Error pushing to Notion: {e}")
            raise

    async def push_to_notion_word_db(self, vocab: dict):
        if not self.notion:
            raise Exception("Notion Token not configured")

        properties = {
            self.PROP_WORD: {"title": self._build_rich_text(vocab.get("word", ""))},
            self.PROP_CATEGORY: {"multi_select": self._build_multi_select(vocab.get("category", []))},
            self.PROP_PRONUNCIATION: {"rich_text": self._build_rich_text(self.to_str(vocab.get("pronunciation", "")))},
            self.PROP_MEANING_VN: {"rich_text": self._build_rich_text(self.to_str(vocab.get("meaning_vn", "")))},
            self.PROP_MEANING: {"rich_text": self._build_rich_text(self.to_str(vocab.get("meaning", "")))},
            self.PROP_EXAMPLE: {"rich_text": self._build_rich_text(self.to_str(vocab.get("example", "")))},
            self.PROP_LEVEL: {"select": {"name": vocab.get("level") or "Unknown"}},
            self.PROP_TOPIC: {"multi_select": self._build_multi_select(vocab.get("topic", []))},
            self.PROP_WORD_PATTERNS: {"rich_text": self._build_rich_text(self.to_str(vocab.get("patterns", [])))},
            self.PROP_SYNONYMS: {"rich_text": self._build_rich_text(self.to_str(vocab.get("synonyms", [])))},
            self.PROP_ANTONYMS: {"rich_text": self._build_rich_text(self.to_str(vocab.get("antonyms", [])))},
            self.PROP_RELATED_WORDS: {"rich_text": self._build_rich_text(self.to_str(vocab.get("related_words", [])))},
            self.PROP_PARAPHRASE: {"rich_text": self._build_rich_text(self.to_str(vocab.get("paraphrase", [])))},
            self.PROP_COLLOCATION: {"rich_text": self._build_rich_text(self.to_str(vocab.get("collocation", [])))},
            self.PROP_SYNCED_TO_ANKI: {"checkbox": False},
            self.PROP_SYNC_AUDIO: {"checkbox": False},
        }

        try:
            await self.notion.pages.create(
                parent={"database_id": config.NOTION_DB_WORD_ID}, properties=properties)
        except Exception as e:
            print(f"Error pushing to Notion: {e}")
            raise

    async def _query_database(self, checkbox_field: str) -> list[dict]:
        if not self.notion:
            raise Exception("Notion Token not configured")

        try:
            response = await self.notion.databases.query(
                database_id=config.NOTION_DB_WORD_ID,
                filter={"property": checkbox_field,
                        "checkbox": {"equals": False}}
            )

            vocab_list = []
            for page in response.get("results", []):
                props = page.get("properties", {})
                vocab_list.append({
                    "page_id": page.get("id"),
                    "word": self._extract_text(props.get(self.PROP_WORD, {})),
                    "meaning_vn": self._extract_text(props.get(self.PROP_MEANING_VN, {})),
                    "meaning": self._extract_text(props.get(self.PROP_MEANING, {})),
                    "pronunciation": self._extract_text(props.get(self.PROP_PRONUNCIATION, {})),
                    "example": self._extract_text(props.get(self.PROP_EXAMPLE, {})),
                    "category": self._extract_multi_select(props.get(self.PROP_CATEGORY, {})),
                    "level": self._extract_select(props.get(self.PROP_LEVEL, {})),
                    "word_patterns": self._extract_text(props.get(self.PROP_WORD_PATTERNS, {})),
                    "synonyms": self._extract_text(props.get(self.PROP_SYNONYMS, {})),
                    "antonyms": self._extract_text(props.get(self.PROP_ANTONYMS, {})),
                    "related_words": self._extract_text(props.get(self.PROP_RELATED_WORDS, {})),
                    "paraphrase": self._extract_text(props.get(self.PROP_PARAPHRASE, {})),
                    "collocation": self._extract_text(props.get(self.PROP_COLLOCATION, {})),
                })
            return vocab_list
        except Exception as e:
            print(f"Error querying Notion: {e}")
            return []

    async def _query_database_collocation(self, checkbox_field: str) -> list[dict]:
        if not self.notion:
            raise Exception("Notion Token not configured")

        try:
            response = await self.notion.databases.query(
                database_id=config.NOTION_DB_COLLOCATION_ID,
                filter={"property": checkbox_field,
                        "checkbox": {"equals": False}}
            )

            vocab_list = []
            for page in response.get("results", []):
                props = page.get("properties", {})
                vocab_list.append({
                    "page_id": page.get("id"),
                    "collocation": self._extract_text(props.get(self.PROP_COLLOCATION, {})),
                    "type": self._extract_select(props.get(self.PROP_TYPE, {})),
                    "meaning": self._extract_text(props.get(self.PROP_MEANING, {})),
                    "example": self._extract_text(props.get(self.PROP_EXAMPLE, {})),
                    "synonyms": self._extract_text(props.get(self.PROP_SYNONYMS, {})),
                })
            return vocab_list
        except Exception as e:
            print(f"Error querying Notion: {e}")
            return []

    async def _query_database_only_word(self, checkbox_field: str) -> list[dict]:
        if not self.notion:
            raise Exception("Notion Token not configured")

        try:
            response = await self.notion.databases.query(
                database_id=config.NOTION_DB_WORD_ID,
                filter={"property": checkbox_field,
                        "checkbox": {"equals": False}}
            )

            vocab_list = []
            for page in response.get("results", []):
                props = page.get("properties", {})
                vocab_list.append({
                    "page_id": page.get("id"),
                    "word": self._extract_text(props.get(self.PROP_WORD, {})),
                })
            return vocab_list
        except Exception as e:
            print(f"Error querying Notion: {e}")
            return []

    async def get_unsynced_vocab(self) -> list[dict]:
        return await self._query_database(self.PROP_SYNCED_TO_ANKI)

    async def get_unsynced_collocation(self) -> list[dict]:
        return await self._query_database_collocation(self.PROP_SYNCED_TO_ANKI)

    async def get_unsynced_audio(self) -> list[dict]:
        return await self._query_database_only_word(self.PROP_SYNC_AUDIO)

    async def mark_as_synced(self, prop_name: str, page_ids: list[str]):
        """Mark multiple pages as synced in parallel using asyncio.gather."""
        if not self.notion:
            return

        async def _update_one(page_id: str):
            try:
                await self.notion.pages.update(
                    page_id=page_id,
                    properties={prop_name: {"checkbox": True}}
                )
            except Exception as e:
                print(f"Error marking page {page_id} as synced: {e}")

        # Run all updates in parallel
        await asyncio.gather(*[_update_one(pid) for pid in page_ids])


notion_service = NotionService()
