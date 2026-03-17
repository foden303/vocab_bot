import os
import requests
import re
from config import config

class AudioService:
    def __init__(self):
        self.base_url = "https://www.oxfordlearnersdictionaries.com/definition/english/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def download_oxford_audio(self, word):
        """
        Attempts to download the US English pronunciation audio for a word from Oxford Learner's Dictionary.
        Saves it to config.SOUNDS_DIR as {word}.mp3.
        """
        url = f"{self.base_url}{word.lower()}"
        save_path = os.path.join(config.SOUNDS_DIR, f"{word.lower()}.mp3")

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                # Try with a common suffix or search if needed, but simple direct link is a good start
                return False, f"Word not found (Status {response.status_code})"

            # Search for US audio first, then UK
            # Pattern: data-src-mp3="https://www.oxfordlearnersdictionaries.com/media/english/us_pron/...mp3"
            # We look for the 'pron-us' class or similar
            
            # Specific targeting for US pronunciation
            # Oxford usually puts US audio in a container with class 'phons-us'
            
            # Find all potential audio blocks
            # We look for the data-src-mp3 attribute specifically in the US phonetic section if possible
            # But a robust way is to find all mp3 links and strictly filter for 'us_pron'
            mp3_links = re.findall(r'data-src-mp3="([^"]+)"', response.text)
            
            target_url = None
            if mp3_links:
                # Filter strictly for 'us_pron' as requested by the user
                us_links = [l for l in mp3_links if "us_pron" in l]
                if us_links:
                    target_url = us_links[0]
                else:
                    return False, "US audio pronunciation not found for this word"

            if not target_url:
                return False, "Audio link not found on page"

            # Download the mp3
            audio_response = requests.get(target_url, headers=self.headers, timeout=10)
            if audio_response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(audio_response.content)
                return True, save_path
            else:
                return False, f"Failed to download audio content (Status {audio_response.status_code})"

        except Exception as e:
            print(f"Error downloading audio for {word}: {e}")
            return False, str(e)

audio_service = AudioService()
