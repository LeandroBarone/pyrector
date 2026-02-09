from pyrector.base import (
    TDim,
    TColor,
    TPercentage,
    TTextSize,
    TTextHorizontalAlign,
    TTextVerticalAlign,
    FontStyle,
    VisualComponent,
    AudioComponent,
    Container,
    Effect,
    GenFunction,
)
from moviepy import (
    TextClip,
    ColorClip,
    ImageClip,
    VideoFileClip,
    CompositeVideoClip,
    AudioFileClip,
)
from pyrector.audio_effects import Volume

import numpy as np
from PIL import Image

from typing import Sequence


class ColorBlock(VisualComponent):
    """
    ColorBlock is a visual component that renders a solid color block.
    Supports transparency.
    """
    def __init__(
        self,
        color: TColor,
        width: TDim = 'auto',
        height: TDim = 'auto',
        left: TDim = 'auto',
        top: TDim = 'auto',
        start_time: float | None = None,
        end_time: float | None = None,
        duration: float | None = None,
        effects: 'Effect | Sequence[Effect]' = (),
        parent: 'Container | None' = None,
    ):
        super().__init__(width, height, left, top, start_time, end_time, duration, effects, parent)
        self.color = color

    def render(self, width: int, height: int, left: int, top: int) -> 'ColorClip':
        self.log(f'rendering color block {width}x{height} @ ({left}, {top}) color={self.color}')
        color = self.color_to_tuple(self.color)

        return (
            ColorClip(size=(width, height), color=color)
            .with_start(self.start_time)
            .with_end(self.end_time)
            .with_effects(self.build_effects())
        )


class ImageFile(VisualComponent):
    def __init__(
        self,
        image_path: 'str | GenFunction',
        width: TDim = 'auto',
        height: TDim = 'auto',
        left: TDim = 'auto',
        top: TDim = 'auto',
        start_time: float | None = None,
        end_time: float | None = None,
        duration: float | None = None,
        effects: 'Effect | Sequence[Effect]' = (),
        parent: 'Container | None' = None,
    ):
        super().__init__(width, height, left, top, start_time, end_time, duration, effects, parent)
        self.image_path = self.resolve_generative_function(image_path)
        self.image = Image.open(self.image_path)

    @staticmethod
    def image_as_array(image_path: str, width: int, height: int) -> 'np.ndarray':
        img = Image.open(image_path)
        img_w, img_h = img.size
        if img_w != width or img_h != height:
            scale = max(width / img_w, height / img_h)
            new_w = round(img_w * scale)
            new_h = round(img_h * scale)
            left = (new_w - width) // 2
            top = (new_h - height) // 2
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            img = img.crop((left, top, left + width, top + height))
        return np.array(img)

    def render(self, width: int, height: int, left: int, top: int) -> 'ImageClip':
        self.log(f'rendering image {width}x{height} @ ({left}, {top}) path="{self.image_path}"')
        img = self.image_as_array(self.image_path, width, height)
        return (
            ImageClip(img)
            .with_position((left, top))
            .with_start(self.start_time)
            .with_end(self.end_time)
            .with_effects(self.build_effects())
        )


class VideoFile(VisualComponent):
    def __init__(
        self,
        video_path: 'str | GenFunction',
        width: TDim = 'auto',
        height: TDim = 'auto',
        left: TDim = 'auto',
        top: TDim = 'auto',
        start_time: float | None = None,
        end_time: float | None = None,
        duration: float | None = None,
        effects: 'Effect | Sequence[Effect]' = [],
        parent: 'Container | None' = None,
    ):
        super().__init__(width, height, left, top, start_time, end_time, duration, effects, parent)
        self.video_path = self.resolve_generative_function(video_path)
        self.video = VideoFileClip(self.video_path, audio=False)

    def crop_self(self, width: int, height: int):
        vid_w, vid_h = self.video.size
        if vid_w == width and vid_h == height:
            return
        scale = max(width / vid_w, height / vid_h)
        new_w = round(vid_w * scale)
        new_h = round(vid_h * scale)
        resized_video = self.video.resized(width=new_w, height=new_h)
        if not isinstance(resized_video, VideoFileClip):
            raise ValueError(f'Resized video is not a VideoFileClip: {type(resized_video)}')
        cropped_video = resized_video.cropped(  # type: ignore
            x_center=new_w // 2,
            y_center=new_h // 2,
            width=width,
            height=height,
        )
        if not isinstance(cropped_video, VideoFileClip):
            raise ValueError(f'Cropped video is not a VideoFileClip: {type(cropped_video)}')
        self.video = cropped_video

    def render(self, width: int, height: int, left: int, top: int) -> 'VideoFileClip':
        self.log(f'Cropping video {width}x{height} @ ({left}, {top}) path="{self.video_path}"')
        self.crop_self(width, height)
        self.log(f'rendering video {width}x{height} @ ({left}, {top}) path="{self.video_path}"')
        return (
            self.video
            .with_position((left, top))
            .with_start(self.start_time)
            .with_end(self.end_time)
            .with_effects(self.build_effects())
        )


class TextBlock(Container):
    """
    TextBlock is a container that lays out Text components vertically.
    Property `vertical_spacing` can be:
        - a float or int, the spacing in pixels
        - 'n%', a percentage of the line height (such as 80% to 140%)
        - 'auto', equals to '100%'
    Text children have their own font size and style, except:
        - text alignments are ignored
        - background color is ignored, use a ColorBlock instead
    """
    def __init__(
        self,
        components: 'Text | Sequence[Text]' = [],
        vertical_spacing: TDim = 'auto',
        start_time: float | None = None,
        end_time: float | None = None,
        duration: float | None = None,
        effects: 'Effect | Sequence[Effect]' = [],
        parent: 'Container | None' = None
    ):
        super().__init__(components, start_time, end_time, duration, effects, parent)
        self._vertical_spacing = vertical_spacing

    def get_bottom_spacing(self, font_size: int) -> int:
        if self._vertical_spacing == 'auto':
            return 0
        elif isinstance(self._vertical_spacing, (float, int)):
            return int(self._vertical_spacing)
        elif isinstance(self._vertical_spacing, TPercentage):
            p = float(self._vertical_spacing.strip('%')) / 100
            return int(p * font_size) - font_size
        raise ValueError(f'Invalid vertical spacing: {self._vertical_spacing}')

    def render(
        self,
        width: int,
        height: int,
        left: int,
        top: int,
        offset_time: float = 0,
        extra_d_for_next_fadein: float = 0,
    ) -> 'CompositeVideoClip | None':
        rendered_components = []
        row_top = 0
        bottom_spacing = 0
        for component in self.components:
            if not isinstance(component, Text):
                raise ValueError(f'TextBlock can only contain Text components, got {type(component)}')

            comp_top = row_top

            self.log(f'rendering {component.uid} row_top={comp_top})')
            rendered_component = component.render_as_label(width, row_top)
            rendered_components.append(rendered_component)
            component_font_size = component.font_size
            text_height = rendered_component.h + int(component.font_size / 2)  # fix inconsistent vertical margins

            base_bottom_spacing = int(0 - component_font_size * 2)  # lines are almost touching
            bottom_spacing = base_bottom_spacing + self.get_bottom_spacing(component_font_size)
            row_top += text_height + bottom_spacing

            self.log(f'text_height={text_height} component_font_size={component_font_size} row_top={row_top}')

        if not rendered_components:
            self.log('rendering empty container')
            return None

        total_height = row_top - bottom_spacing
        centered_top = int((height - total_height) / 2)
        self.log(f'building composite video clip {width}x{total_height} @ ({left}, {centered_top})')
        return (
            CompositeVideoClip(rendered_components, size=(width, total_height))
            .with_position((left, centered_top))
            .with_start(self.start_time)
            .with_end(self.end_time)
            .with_duration(self.duration)
            .with_effects(self.build_effects())
        )


class Text(VisualComponent):
    def __init__(
        self,
        text: 'str | GenFunction',
        font_size: TTextSize = 'm',
        font_color: TColor = 'white',
        background_color: TColor | None = None,
        stroke_color: TColor | None = None,
        stroke_width: int = 0,
        interline: int = 4,
        text_align: TTextHorizontalAlign = 'center',
        horizontal_align: TTextHorizontalAlign = 'center',
        vertical_align: TTextVerticalAlign = 'center',
        font_style: FontStyle | None = None,
        width: TDim = 'auto',
        height: TDim = 'auto',
        left: TDim = 'auto',
        top: TDim = 'auto',
        start_time: float | None = None,
        end_time: float | None = None,
        duration: float | None = None,
        effects: 'Effect | Sequence[Effect]' = [],
        parent: 'Container | None' = None,
    ):
        super().__init__(width, height, left, top, start_time, end_time, duration, effects, parent)
        self.text = self.resolve_generative_function(text)
        self._font_size = font_size
        self.font_color = font_color
        self.background_color = background_color
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
        self.interline = interline
        self.text_align = text_align
        self.vertical_align = vertical_align
        self._font_style = font_style

    @property
    def font_size(self) -> int:
        font_size = self._font_style.font_size if self._font_style else self._font_size

        if isinstance(font_size, int):
            return font_size

        base_font_size = round(self.movie.height / 24)
        step_up = round(base_font_size / 2)
        step_down = round(base_font_size / 10)

        if font_size == 'xxs':
            return round(base_font_size - step_down * 3)
        elif font_size == 'xs':
            return round(base_font_size - step_down * 2)
        elif font_size == 's':
            return round(base_font_size - step_down)
        elif font_size == 'm':
            return base_font_size
        elif font_size == 'l':
            return round(base_font_size + step_up)
        elif font_size == 'xl':
            return round(base_font_size + step_up * 2)
        elif font_size == 'xxl':
            return round(base_font_size + step_up * 3)
        else:
            raise ValueError(f'Invalid text size: {font_size}')

    @property
    def font_style_kwargs(self) -> 'dict':
        if self._font_style:
            style = self._font_style
            return {
                'font_size': style.font_size,
                'color': style.text_color,
                'bg_color': self.color_to_tuple(style.background_color) if style.background_color else None,
                'stroke_color': self.color_to_tuple(style.stroke_color) if style.stroke_color else None,
                'stroke_width': style.stroke_width,
                'interline': style.interline,
                'text_align': style.text_align,
                'vertical_align': style.vertical_align,
            }
        else:
            return {
                'font_size': self.font_size,
                'color': self.color_to_tuple(self.font_color),
                'bg_color': self.color_to_tuple(self.background_color) if self.background_color else None,
                'stroke_color': self.color_to_tuple(self.stroke_color) if self.stroke_color else None,
                'stroke_width': self.stroke_width,
                'interline': self.interline,
                'text_align': self.text_align,
                'vertical_align': self.vertical_align,
            }

    def render(self, width: int, height: int, left: int, top: int) -> 'TextClip':
        self.log(f'rendering text {width}x{height} @ ({left}, {top}) label="{self.text}"')
        font_size = self.font_size
        size = (width - font_size * 2, height - font_size * 2)
        margin = (font_size, font_size)

        return (
            TextClip(
                text=self.text,
                margin=margin,
                size=size,
                method='caption',
                **self.font_style_kwargs,
            )
            .with_start(self.start_time)
            .with_end(self.end_time)
            .with_duration(self.duration)
            .with_effects(self.build_effects())
        )

    def render_as_label(self, width: int, row_top: int) -> 'TextClip':
        self.log(f'rendering text @ {row_top} label="{self.text}"')
        font_size = self.font_size
        size = (width - font_size * 2, None)
        margin = (font_size, font_size)

        styles = self.font_style_kwargs
        del styles['text_align']
        del styles['vertical_align']

        return (TextClip(
            text=self.text,
            size=size,
            margin=margin,
            method='label',
            **styles,
            text_align='center',
            horizontal_align='center',
            vertical_align='center',
        )
            .with_position((0, row_top))
            .with_start(self.start_time)
            .with_end(self.end_time)
            .with_duration(self.duration)
            .with_effects(self.build_effects())
        )


class AudioFile(AudioComponent):
    def __init__(
        self,
        audio_path: 'str | GenFunction',
        volume: float = 1.0,
        start_time: float | None = None,
        end_time: float | None = None,
        duration: float | None = None,
        effects: 'Effect | Sequence[Effect]' = [],
        parent: 'Container | None' = None,
    ):
        super().__init__(volume, start_time, end_time, duration, effects, parent)
        self.audio_path = self.resolve_generative_function(audio_path)
        self.audio = AudioFileClip(self.audio_path)

    def render(self) -> 'AudioFileClip':
        self.log(f'rendering audio path="{self.audio_path}"')
        audio = self.audio
        built_effects = self.build_effects()
        if self.volume != 1:
            built_effects.insert(0, Volume(factor=self.volume).build())
        return (
            audio
            .with_start(self.start_time)
            .with_end(self.end_time)
            .with_duration(self.duration)
            .with_effects(built_effects)
        )

    @property
    def duration(self) -> float:
        return self.relative_duration or self.audio.duration

    @property
    def relative_duration(self) -> float:
        return super().relative_duration or self.audio.duration
