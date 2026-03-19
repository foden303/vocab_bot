import os
import re
import aiohttp
from config import config


class AudioService:
    def __init__(self):
        self.base_url = "https://www.oxfordlearnersdictionaries.com/definition/english/"
        self.forvo_base = "https://forvo.com/search/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    async def download_audio(self, word: str):
        word = word.strip().lower()

        # >= 2 word → Forvo (disabled)
        if len(word.split()) >= 2:
            return False, "Phrase audio not found, please download manually"

        # 1 word → Oxford
        success, path = await self._download_oxford_audio(word)
        if success:
            return True, path

        return False, "Word audio not found, please download manually"

    async def _download_oxford_audio(self, word):
        """
        Attempts to download the US English pronunciation audio for a word
        from Oxford Learner's Dictionary using aiohttp (non-blocking).
        """
        url = f"{self.base_url}{word.lower()}"
        save_path = os.path.join(config.SOUNDS_DIR, f"{word.lower()}.mp3")

        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                # Fetch the dictionary page
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        return False, "Word not found"

                    html = await response.text()

                # Find all mp3 links
                mp3_links = re.findall(r'data-src-mp3="([^"]+)"', html)

                target_url = None
                if mp3_links:
                    us_links = [l for l in mp3_links if "us_pron" in l]
                    if us_links:
                        target_url = us_links[0]
                    else:
                        return False, "US audio pronunciation not found for this word"

                if not target_url:
                    return False, "Audio link not found on page"

                # Download the mp3
                async with session.get(target_url, timeout=aiohttp.ClientTimeout(total=10)) as audio_response:
                    if audio_response.status == 200:
                        content = await audio_response.read()
                        with open(save_path, "wb") as f:
                            f.write(content)
                        return True, save_path
                    else:
                        return False, f"Failed to download audio content (Status {audio_response.status})"

        except Exception as e:
            print(f"Error downloading audio for {word}: {e}")
            return False, str(e)


audio_service = AudioService()
