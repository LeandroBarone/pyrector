from pyrector.base import (
    GenerativeTextProvider,
    GenerativeImageProvider,
    GenerativeAudioProvider,
    GenerativeVoiceProvider,
    GenerativeMusicProvider,
    GenerativeVideoProvider,
)

import hashlib
from abc import ABC
from os import environ


class WithGoogleClient(ABC):
    genai = None
    client = None

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


class WithElevenLabsClient(ABC):
    elevenlabs = None
    client = None

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


class GoogleTextProvider(WithGoogleClient, GenerativeTextProvider):
    def generate(self, prompt: str) -> str:
        return 'This sentence is a placeholder for a much funnier one.'
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
        return 'media/nerd.jpg'
        if not self.client or not self.genai:
            raise ValueError('Google client not loaded')

        response = self.client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents='A cartoon infographic for flying sneakers',
            config=self.genai.types.GenerateContentConfig(
                response_modalities=['IMAGE'],
                image_config=self.genai.types.ImageConfig(
                    aspect_ratio='1:1',
                ),
            ),
        )
        if response.text is None:
            raise ValueError('No text returned from model')
        return response.text.strip()


class GoogleAudioProvider(WithGoogleClient, GenerativeAudioProvider):
    def generate(self, prompt: str) -> str:
        raise NotImplementedError('#TODO: Implement generate method')


class GoogleVideoProvider(WithGoogleClient, GenerativeVideoProvider):
    def generate(self, prompt: str) -> str:
        return 'media/meeting.mp4'
        if not self.client or not self.genai:
            raise ValueError('Google client not loaded')

        response = self.client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents='A cartoon infographic for flying sneakers',
            config=self.genai.types.GenerateContentConfig(
                response_modalities=['IMAGE'],
                image_config=self.genai.types.ImageConfig(
                    aspect_ratio='1:1',
                ),
            ),
        )
        if response.text is None:
            raise ValueError('No text returned from model')
        return response.text.strip()


class ElevenLabsVoiceProvider(WithElevenLabsClient, GenerativeVoiceProvider):
    def generate(self, prompt: str) -> str:
        return 'media/speech.mp3'
        if not self.client or not self.elevenlabs_client:
            raise ValueError('ElevenLabs client not loaded')

        response = self.client.text_to_speech.convert(
            voice_id='somevoice',
            output_format='mp3_22050_32',
            text=prompt,
            model_id='eleven_turbo_v2_5',
        )

        prompt_hash = hashlib.sha256(prompt.encode('utf-8')).hexdigest()

        # Generating a unique file name for the output MP3 file
        save_file_path = f'media/speech_{prompt_hash}.mp3'

        # Writing the audio to a file
        with open(save_file_path, 'wb') as f:
            for chunk in response:
                if chunk:
                    f.write(chunk)


class ElevenLabsMusicProvider(WithElevenLabsClient, GenerativeMusicProvider):
    def generate(self, prompt: str) -> str:
        return 'media/music.mp3'
