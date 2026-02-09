from pyrector.base import AudioEffect

import moviepy


class Volume(AudioEffect):
    def __init__(self, factor: float = 1.0):
        super().__init__()
        self.factor = factor

    def build(self) -> 'moviepy.Effect':
        return moviepy.afx.MultiplyVolume(factor=self.factor)
