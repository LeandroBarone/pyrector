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
from os import environ, makedirs, path
from time import sleep


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
        file_path = self.cache_file(prompt, f'{self.cache_dir}/text_', '.txt')
        if path.exists(file_path):
            return file_path

        if not self.client or not self.genai:
            raise ValueError('Google client not loaded')

        response = self.client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=prompt,
        )
        if response.text is None:
            raise ValueError('No text returned from model')

        text = response.text.strip()

        with open(file_path, 'w') as f:
            f.write(text)

        return text


class GoogleImageProvider(WithGoogleClient, GenerativeImageProvider):
    def generate(self, prompt: str) -> str:
        file_path = self.cache_file(prompt, f'{self.cache_dir}/image_', '.png')
        if path.exists(file_path):
            return file_path

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

        for part in response.parts:
            if part.inline_data is not None:
                image = part.as_image()
                if image is None:
                    continue
                image.save(file_path)
                return file_path

        raise ValueError('No image returned from model')


class GoogleVideoProvider(WithGoogleClient, GenerativeVideoProvider):
    def generate(self, prompt: str, duration: float = 4) -> str:
        file_path = self.cache_file(prompt, f'{self.cache_dir}/video_', '.mp4')
        if path.exists(file_path):
            return file_path

        if not self.client or not self.genai:
            raise ValueError('Google client not loaded')

        operation = self.client.models.generate_videos(
            model="veo-3.1-fast-generate-preview",
            prompt=prompt,
            config=self.genai.types.GenerateVideosConfig(
                aspect_ratio='16:9',  # TODO: derive aspect ratio
                duration_seconds=int(duration),
                resolution='720p',
            ),
        )

        while not operation.done:
            print("Waiting for video generation to complete...")
            sleep(5)
            operation = self.client.operations.get(operation)

        if (not operation.response or not operation.response.generated_videos):
            raise ValueError('No video returned from model')

        generated_video = operation.response.generated_videos[0]
        if not generated_video.video:
            raise ValueError('No video returned from model')

        self.client.files.download(file=generated_video.video)
        generated_video.video.save(file_path)

        return file_path


class ElevenLabsAudioProvider(WithElevenLabsClient, GenerativeAudioProvider):
    def generate(self, prompt: str) -> str:
        file_path = self.cache_file(prompt, f'{self.cache_dir}/audio_', '.mp3')
        if path.exists(file_path):
            return file_path

        if not self.client or not self.elevenlabs_client:
            raise ValueError('ElevenLabs client not loaded')

        response = self.client.text_to_sound_effects.convert(
            text=prompt,
        )

        response_bytes = b''.join(response)
        with open(file_path, 'wb') as f:
            f.write(response_bytes)

        return file_path


class ElevenLabsVoiceProvider(WithElevenLabsClient, GenerativeVoiceProvider):
    def generate(self, prompt: str) -> str:
        if not self.client or not self.elevenlabs_client:
            raise ValueError('ElevenLabs client not loaded')

        file_path = self.cache_file(prompt, f'{self.cache_dir}/voice_', '.mp3')
        if path.exists(file_path):
            return file_path

        response = self.client.text_to_speech.convert(
            voice_id='4nLP0u2B3yI0lyzATFnN',  # TODO: make this configurable
            text=prompt,
            model_id='eleven_turbo_v2_5',
        )

        response_bytes = b''.join(response)
        with open(file_path, 'wb') as f:
            f.write(response_bytes)

        return file_path


class ElevenLabsMusicProvider(WithElevenLabsClient, GenerativeMusicProvider):
    def generate(self, prompt: str, duration: float = 30) -> str:
        file_path = self.cache_file(prompt, f'{self.cache_dir}/music_', '.mp3')
        if path.exists(file_path):
            return file_path

        if not self.client or not self.elevenlabs_client:
            raise ValueError('ElevenLabs client not loaded')

        response = self.client.music.compose(
            prompt=prompt,
            model_id='music_v1',
            music_length_ms=int(duration * 1000),
        )

        response_bytes = b''.join(response)
        with open(file_path, 'wb') as f:
            f.write(response_bytes)

        return file_path
