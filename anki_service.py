import requests
import os
import re
from config import config

class AnkiService:
    def __init__(self):
        self.url = config.ANKI_CONNECT_URL
        self.template_dir = os.path.join(os.path.dirname(__file__), "templates")

    def _load_template(self, filename):
        path = os.path.join(self.template_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error loading template {filename}: {e}")
            return ""

    def _render(self, template, data):
        # Simple placeholder replacement {{field}}
        # Also supports simple {{#field}}...{{/field}} for conditional blocks
        rendered = template
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, str(value if value else ""))
            
            # Simple conditional: {{#key}}...{{/key}}
            start_tag = f"{{{{#{key}}}}}"
            end_tag = f"{{{{/{key}}}}}"
            if start_tag in rendered and end_tag in rendered:
                if value:
                    # Keep content, remove tags
                    rendered = rendered.replace(start_tag, "").replace(end_tag, "")
                else:
                    # Remove tags and content between them
                    pattern = re.escape(start_tag) + ".*?" + re.escape(end_tag)
                    rendered = re.sub(pattern, "", rendered, flags=re.DOTALL)
        
            # Inverted conditional: {{^key}}...{{/key}}
            inv_start_tag = f"{{{{^{key}}}}}"
            if inv_start_tag in rendered and end_tag in rendered:
                if not value:
                    # Keep content, remove tags
                    rendered = rendered.replace(inv_start_tag, "").replace(end_tag, "")
                else:
                    # Remove tags and content between them
                    pattern = re.escape(inv_start_tag) + ".*?" + re.escape(end_tag)
                    rendered = re.sub(pattern, "", rendered, flags=re.DOTALL)

        # Clean up any remaining tags and placeholders
        rendered = re.sub(r"\{\{\#.*?\}\}", "", rendered)
        rendered = re.sub(r"\{\{\^.*?\}\}", "", rendered)
        rendered = re.sub(r"\{\{\/.*?\}\}", "", rendered)
        rendered = re.sub(r"\{\{.*?\}\}", "", rendered)
        return rendered

    def _invoke(self, action, **params):
        try:
            response = requests.post(self.url, json={
                "action": action,
                "version": 6,
                "params": params
            }, timeout=3)
            return response.json()
        except Exception as e:
            print(f"Error connecting to AnkiConnect: {e}")
            return {"error": str(e)}

    def is_connected(self):
        try:
            res = self._invoke("version")
            return res.get("result") is not None
        except:
            return False

    def _store_media(self, filename, filepath):
        import base64
        try:
            with open(filepath, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")
            
            return self._invoke("storeMediaFile", filename=filename, data=data)
        except Exception as e:
            print(f"Error storing media file {filename}: {e}")
            return {"error": str(e)}

    def add_note(self, item):
        word = item.get("word", "")
        sound_filename = f"{word}.mp3"
        sound_path = os.path.join(config.SOUNDS_DIR, sound_filename)
        
        # Check if sound file exists and sync it
        if os.path.exists(sound_path):
            self._store_media(sound_filename, sound_path)
            item["sound"] = f"[sound:{sound_filename}]"
        else:
            item["sound"] = ""

        front_tpl = self._load_template("front.html")
        back_tpl = self._load_template("back.html")
        
        front = self._render(front_tpl, item)
        back = self._render(back_tpl, item)

        params = {
            "note": {
                "deckName": config.ANKI_DECK_NAME,
                "modelName": config.ANKI_MODEL_NAME,
                "fields": {
                    "Front": front,
                    "Back": back
                },
                "options": {
                    "allowDuplicate": False,
                    "duplicateScope": "deck"
                },
                "tags": ["vocab_bot"]
            }
        }
        
        return self._invoke("addNote", **params)

    def sync_to_anki(self, vocab_list: list[dict]):
        results = []
        for item in vocab_list:
            res = self.add_note(item)
            if res.get("error"):
                results.append({"page_id": item["page_id"], "success": False, "error": res["error"]})
            else:
                results.append({"page_id": item["page_id"], "success": True, "note_id": res["result"]})
        return results

anki_service = AnkiService()
