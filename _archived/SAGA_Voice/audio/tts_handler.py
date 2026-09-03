import os
import threading
import asyncio
import edge_tts
import pygame

class TTSHandler:
    def __init__(self):
        # We use a British Male narrator voice from Azure (Edge TTS)
        self.voice = "en-GB-RyanNeural"
        
        # Pygame mixer is extremely lightweight for just playing an MP3
        pygame.mixer.init()
        
    def speak(self, text: str):
        print(f"\n[AI NARRATOR]: {text}\n")
        # Edge TTS requires an asyncio loop to generate the file
        asyncio.run(self._async_speak(text))

    async def _async_speak(self, text: str):
        # Handle empty strings gracefully to prevent corrupt MP3s
        if not text or not text.strip():
            print("[STT/TTS Warning]: Empty text provided, skipping audio generation.")
            return

        # Generate the audio
        communicate = edge_tts.Communicate(text, self.voice)
        audio_file = "temp_speech.mp3"
        await communicate.save(audio_file)
        
        # Play it synchronously using Pygame
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        
        # Wait until finished
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
        # Clean up
        pygame.mixer.music.unload()
        try:
            os.remove(audio_file)
        except OSError:
            pass

    def speak_async(self, text: str):
        """Fires off the speech in a background thread."""
        t = threading.Thread(target=self.speak, args=(text,), daemon=True)
        t.start()
        return t
