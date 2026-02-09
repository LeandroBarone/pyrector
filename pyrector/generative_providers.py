from pyrector.base import (
    GenerativeTextProvider,
    GenerativeImageProvider,
    GenerativeAudioProvider,
    GenerativeVoiceProvider,
    GenerativeMusicProvider,
    GenerativeVideoProvider,
)

from PIL import Image

import hashlib
from abc import ABC
from os import environ, makedirs


class WithGoogleClient(ABC):
    genai = None
    client = None
    cache_dir = '_gencache'

    def __init__(self):
        self.lazy_load()

    @classmethod
    def lazy_load(cls):
        if cls.genai is None:
            if environ.get('GOOGLE_API_KEY') is None:
                raise ValueError('GOOGLE_API_KEY is not set')
            import google.genai
            cls.genai = google.genai
            cls.client = google.genai.Client(api_key=environ['GOOGLE_API_KEY'])
            makedirs(cls.cache_dir, exist_ok=True)


class WithElevenLabsClient(ABC):
    elevenlabs = None
    client = None
    cache_dir = '_gencache'

    def __init__(self):
        self.lazy_load()

    @classmethod
    def lazy_load(cls):
        if cls.elevenlabs is None:
            if environ.get('ELEVENLABS_API_KEY') is None:
                raise ValueError('ELEVENLABS_API_KEY is not set')
            import elevenlabs
            import elevenlabs.client
            cls.elevenlabs = elevenlabs
            cls.elevenlabs_client = elevenlabs.client
            cls.client = elevenlabs.client.ElevenLabs(api_key=environ['ELEVENLABS_API_KEY'])
            makedirs('_gencache', exist_ok=True)


class GoogleTextProvider(WithGoogleClient, GenerativeTextProvider):
    def generate(self, prompt: str) -> str:
        if not self.client or not self.genai:
            raise ValueError('Google client not loaded')

        response = self.client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=prompt,
        )
        if response.text is None:
            raise ValueError('No text returned from model')
        return response.text.strip()


class GoogleImageProvider(WithGoogleClient, GenerativeImageProvider):
    def generate(self, prompt: str) -> str:
        if not self.client or not self.genai:
            raise ValueError('Google client not loaded')

        response = self.client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=prompt,
            config=self.genai.types.GenerateContentConfig(
                response_modalities=['IMAGE'],
                image_config=self.genai.types.ImageConfig(
                    aspect_ratio='1:1',  # TODO: derive aspect ratio
                ),
            ),
        )
        if response.parts is None:
            raise ValueError('No content returned from model')

        prompt_hash = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
        file_path = f'{self.cache_dir}/image_{prompt_hash}.png'

        for part in response.parts:
            if part.inline_data is not None:
                image = part.as_image()
                if image is None:
                    continue
                image.save(file_path)
                return file_path

        raise ValueError('No image returned from model')


class ElevenLabsVoiceProvider(WithElevenLabsClient, GenerativeVoiceProvider):
    def generate(self, prompt: str) -> str:
        if not self.client or not self.elevenlabs_client:
            raise ValueError('ElevenLabs client not loaded')

        response = self.client.text_to_speech.convert(
            voice_id='4nLP0u2B3yI0lyzATFnN',  # TODO: make this configurable
            text=prompt,
            model_id='eleven_turbo_v2_5',
        )

        prompt_hash = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
        file_path = f'{self.cache_dir}/speech_{prompt_hash}.mp3'

        with open(file_path, 'wb') as f:
            for chunk in response:
                if chunk:
                    f.write(chunk)

        return file_path


class ElevenLabsMusicProvider(WithElevenLabsClient, GenerativeMusicProvider):
    def generate(self, prompt: str) -> str:
        if not self.client or not self.elevenlabs_client:
            raise ValueError('ElevenLabs client not loaded')

        response = self.client.music.compose(
            prompt=prompt,
            model_id='music_v1',
        )

        prompt_hash = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
        file_path = f'{self.cache_dir}/music_{prompt_hash}.mp3'

        with open(file_path, 'wb') as f:
            for chunk in response:
                if chunk:
                    f.write(chunk)

        return file_path
