from pyrector.base import VisualEffect, AnimatedEffect

import moviepy


class FadeIn(AnimatedEffect):
    def build(self) -> 'moviepy.Effect':
        return moviepy.vfx.CrossFadeIn(duration=self.duration)


class FadeOut(AnimatedEffect):
    def build(self) -> 'moviepy.Effect':
        return moviepy.vfx.CrossFadeOut(duration=self.duration)


class Painting(VisualEffect):
    def __init__(self, saturation: float = 1.4, black: float = 0.006):
        super().__init__()
        self.saturation = saturation
        self.black = black

    def build(self) -> 'moviepy.Effect':
        return moviepy.vfx.Painting(self.saturation, self.black)


class SlideInTop(AnimatedEffect):
    def build(self) -> 'moviepy.Effect':
        return moviepy.vfx.SlideIn(duration=self.duration, side='top')


class SlideInBottom(AnimatedEffect):
    def build(self) -> 'moviepy.Effect':
        return moviepy.vfx.SlideIn(duration=self.duration, side='bottom')


class SlideInLeft(AnimatedEffect):
    def build(self) -> 'moviepy.Effect':
        return moviepy.vfx.SlideIn(duration=self.duration, side='left')


class SlideInRight(AnimatedEffect):
    def build(self) -> 'moviepy.Effect':
        return moviepy.vfx.SlideIn(duration=self.duration, side='right')


class SlideOutTop(AnimatedEffect):
    def build(self) -> 'moviepy.Effect':
        return moviepy.vfx.SlideOut(duration=self.duration, side='top')


class SlideOutBottom(AnimatedEffect):
    def build(self) -> 'moviepy.Effect':
        return moviepy.vfx.SlideOut(duration=self.duration, side='bottom')


class SlideOutLeft(AnimatedEffect):
    def build(self) -> 'moviepy.Effect':
        return moviepy.vfx.SlideOut(duration=self.duration, side='left')


class SlideOutRight(AnimatedEffect):
    def build(self) -> 'moviepy.Effect':
        return moviepy.vfx.SlideOut(duration=self.duration, side='right')


class TimeMirror(VisualEffect):
    def build(self) -> 'moviepy.Effect':
        return moviepy.vfx.TimeMirror()
