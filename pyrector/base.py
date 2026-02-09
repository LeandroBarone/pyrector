from pyrector.uid import WithUid

from PIL import ImageColor
from moviepy import (
    ColorClip,
    CompositeVideoClip,
    CompositeAudioClip,
    AudioFileClip,
    Effect as MoviepyEffect,
    vfx as MoviepyVFX,
)

import hashlib
import logging
from abc import ABC, abstractmethod
from typing import Literal, Any, Sequence
from dataclasses import dataclass


TRGBTuple = tuple[int, int, int]
TRGBATuple = tuple[int, int, int, float]
TColor = TRGBTuple | TRGBATuple | str
TPercentage = str
TDim = float | TPercentage | Literal['auto']
TTextSize = int | str | Literal['xxs', 'xs', 's', 'm', 'l', 'xl', 'xxl', 'xxxl']
TTextHorizontalAlign = Literal['left', 'center', 'right']
TTextVerticalAlign = Literal['top', 'center', 'bottom']


@dataclass
class FontStyle():
    font_size: int
    text_color: TColor = 'white'
    background_color: TColor | None = None
    stroke_color: TColor | None = None
    stroke_width: int = 0
    interline: int = 4
    text_align: TTextHorizontalAlign = 'left'
    vertical_align: TTextVerticalAlign = 'center'


class Component(WithUid, ABC):
    def __init__(
        self,
        parent: 'Container | None' = None,
    ):
        super().__init__()
        self.parent = parent

    @abstractmethod
    def render(self, *args, **kwargs) -> Any:
        pass

    @property
    def container(self) -> 'Container':
        parent = self.parent
        while True:
            if isinstance(parent, Container):
                return parent
            parent = parent.parent if parent is not None else None
            if parent is None:
                raise ValueError('The component is not associated with a container')

    @property
    def movie(self) -> 'Movie':
        if isinstance(self, Movie):
            return self
        if self.parent:
            return self.parent.movie
        raise ValueError('The component is not associated with a movie container')

    def set_parent(self, parent: 'Container') -> None:
        self.parent = parent

    def count_parents(self) -> int:
        count = 0
        parent = self
        while True:
            parent = getattr(parent, 'parent', None)
            if parent is None:
                break
            count += 1
        return count

    def get_available_providers(self) -> 'list[GenerativeProvider]':
        self.log('getting available providers...')
        providers = []
        for subtype in GenerativeProvider.__subclasses__():
            for provider in subtype.__subclasses__():
                try:
                    provider = provider()
                    providers.append(provider)
                except Exception:
                    continue
        return providers

    def resolve_generative_function(self, generative_function: 'str | GenFunction') -> str:
        if isinstance(generative_function, GenFunction):
            available_providers = self.get_available_providers()
            required_provider = generative_function.required_provider
            try:
                provider = next((p for p in available_providers if isinstance(p, required_provider)))
            except StopIteration:
                raise ValueError(f'No {required_provider.__name__} provider found')
            self.log(f'running {provider.__class__.__name__} prompt="{generative_function.prompt}"')
            result = generative_function.generate(provider)
            self.log(f'result="{result}"')
            return result
        return generative_function

    def log(self, msg: str, level: int = logging.INFO) -> None:
        logger = logging.getLogger()
        parent_label = f' (in {self.parent.uid})' if self.parent is not None else ''
        logger.log(level, f'{self.count_parents() * "  "}{self.uid}{parent_label} says: {str(msg)}')


class TimelineComponent(Component, ABC):
    def __init__(
        self,
        start_time: float | None = None,
        end_time: float | None = None,
        duration: float | None = None,
        effects: 'Effect | Sequence[Effect]' = (),
        parent: 'Container | None' = None,
    ):
        super().__init__(parent)
        self._start_time = start_time
        self._end_time = end_time
        self._duration = duration
        self.effects = ()
        self.add_effects(effects)

    def add_effects(self, effects: 'Effect | Sequence[Effect]') -> None:
        if isinstance(effects, Effect):
            effects = (effects,)
        self.effects = (*self.effects, *effects)

    def build_effects(self) -> 'list[MoviepyEffect]':
        built_effects = []
        for ef in self.effects:
            built_effects.append(ef.build())

        return built_effects

    @property
    def start_time(self) -> float:
        return self._start_time if self._start_time is not None else 0

    @property
    def end_time(self) -> float:
        return self._end_time if self._end_time is not None else self.duration

    @property
    def duration(self) -> float:
        relative_duration = self.relative_duration
        if relative_duration:
            return relative_duration

        if self.parent is not None:
            parent_duration = getattr(self.parent, 'duration', None)
            if parent_duration is not None:
                return parent_duration

        return 10

    @property
    def relative_duration(self) -> float:
        if self._end_time and self._duration:
            raise ValueError('Can\'t set both end time and duration')
        elif self._start_time and self._end_time:
            return self._end_time - self._start_time
        elif self._start_time and self._duration:
            return self._duration - self._start_time
        elif self._end_time:
            return self._end_time
        elif self._duration:
            return self._duration

        return 0


class VisualComponent(TimelineComponent, ABC):
    def __init__(
        self,
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
        super().__init__(start_time, end_time, duration, effects, parent)
        self._width = width
        self._height = height
        self._left = left
        self._top = top

    def add_effects(self, effects: 'Effect | Sequence[Effect]') -> None:
        super().add_effects(effects)
        for effect in self.effects:
            if isinstance(effect, VisualEffect):
                effect.component = self

    @staticmethod
    def color_to_tuple(color: TColor, ignore_alpha: bool = False) -> 'TRGBTuple | TRGBATuple':
        if isinstance(color, tuple) and len(color) >= 3:
            return color[:3] if ignore_alpha else color
        color_tuple = ImageColor.getrgb(color)
        return color_tuple[:3] if ignore_alpha else color_tuple

    def dim_to_int(self, dim: TDim, axis: Literal['h', 'v']) -> int:
        if isinstance(dim, (int, float)):
            return round(dim)
        elif dim == 'auto':
            if axis == 'h':
                return self.container.width
            elif axis == 'v':
                return self.container.height
        elif '%' in dim:
            if axis == 'h':
                return round(self.container.width * float(dim.replace('%', '')) / 100)
            elif axis == 'v':
                return round(self.container.height * float(dim.replace('%', '')) / 100)
        raise ValueError(f'Invalid dimension: {dim} for axis {axis}')

    @property
    def width(self) -> int:
        return self.dim_to_int(self._width, 'h')

    @property
    def height(self) -> int:
        return self.dim_to_int(self._height, 'v')

    @property
    def left(self) -> int:
        return self.dim_to_int(self._left, 'h')

    @property
    def top(self) -> int:
        return self.dim_to_int(self._top, 'v')


class AudioComponent(TimelineComponent, ABC):
    def __init__(
        self,
        volume: float = 1.0,
        start_time: float | None = None,
        end_time: float | None = None,
        duration: float | None = None,
        effects: 'Effect | Sequence[Effect]' = (),
        parent: 'Container | None' = None,
    ):
        super().__init__(start_time, end_time, duration, effects, parent)
        self.volume = volume

    @abstractmethod
    def render(self, *args, **kwargs) -> 'AudioFileClip':
        pass


class GenerativeComponent(ABC):
    @abstractmethod
    def generate(self) -> Any:
        pass


class Container(TimelineComponent, ABC):
    def __init__(
        self,
        components: 'Component | Sequence[Component]' = (),
        start_time: float | None = None,
        end_time: float | None = None,
        duration: float | None = None,
        effects: 'Effect | Sequence[Effect]' = (),
        parent: 'Container | None' = None
    ):
        super().__init__(start_time, end_time, duration, effects, parent)
        self.components: 'tuple[Component, ...]' = ()
        self.add_components(components)

    @property
    def width(self) -> int:
        return self.container.width

    @property
    def height(self) -> int:
        return self.container.height

    @property
    def duration(self) -> float:
        if self._duration is not None:
            return self._duration

        scene_durations = sum((c.duration for c in self.components if isinstance(c, Scene)), 0)
        if scene_durations:
            self._duration = scene_durations
            return scene_durations

        first_duration = self.find_first_component_with_duration()
        if first_duration:
            self._duration = first_duration
            return first_duration

        if self.movie._duration is not None:
            return self.movie._duration

        raise ValueError('The container does not have a duration')

    def add_components(self, components: 'Component | Sequence[Component]') -> None:
        if isinstance(components, Component):
            components = (components,)
        self.components = (*self.components, *components)
        for component in components:
            component.set_parent(self)

    def validate(self) -> None:
        if self.duration is None:
            raise ValueError('A container must have or inherit a duration')

        rows = [component for component in self.components if isinstance(component, Row)]
        cols = [component for component in self.components if isinstance(component, Col)]

        if rows and cols:
            raise ValueError('A container can only have rows or cols, not both')

        total_hr = sum([row.percentage for row in rows])
        if total_hr > 100:
            raise ValueError('The total height of the rows must be 100% or less')

        total_vr = sum([col.percentage for col in cols])
        if total_vr > 100:
            raise ValueError('The total width of the cols must be 100% or less')

    def render(
        self,
        width: int,
        height: int,
        left: int,
        top: int,
        offset_time: float = 0,
        extra_d_for_next_fadein: float = 0,
    ) -> 'CompositeVideoClip | None':
        self.validate()

        rendered_visual_components = []
        rendered_audio_components = []

        total_time = 0

        row_top = 0
        col_left = 0

        i = 0
        while i < len(self.components):
            component = self.components[i]

            comp_width = width
            comp_height = height
            comp_left = 0
            comp_top = 0

            if isinstance(component, Row):
                comp_height = round(height * component.percentage / 100)
                comp_top = row_top
                row_top += comp_height
            if isinstance(component, Col):
                comp_width = round(width * component.percentage / 100)
                comp_left = col_left
                col_left += comp_width
            elif isinstance(component, Box):
                comp_width = component.width
                comp_height = component.height
                comp_left = component.left
                comp_top = component.top

            if isinstance(component, Scene) and component.duration is not None:
                comp_offset = total_time
                total_time += component.duration
                next_component = self.components[i + 1] if i + 1 < len(self.components) else None
                extra_d_for_next_fadein = self.check_next_component_for_fadeins(next_component)

                self.log(f'rendering {component.uid} {comp_offset}-{comp_offset + component.duration}s')
                rendered_visual_components.append(
                    component.render(comp_width, comp_height, comp_left, comp_top, comp_offset, extra_d_for_next_fadein)
                )
            elif isinstance(component, AudioComponent):
                self.log(f'rendering {component.uid}')
                rendered_audio_components.append(component.render())
            else:
                self.log(f'rendering {component.uid} {comp_width}x{comp_height} @ ({comp_left}, {comp_top})')
                rendered_visual_components.append(component.render(comp_width, comp_height, comp_left, comp_top))

            i += 1

        if not rendered_visual_components:
            self.log('rendering empty container')
            return None

        rendered_visual_components = [c for c in rendered_visual_components if c]
        built_effects = self.build_effects()

        if extra_d_for_next_fadein:
            freeze_effect = MoviepyVFX.Freeze(
                t=self.duration - 0.001,
                freeze_duration=extra_d_for_next_fadein
            )
            built_effects.append(freeze_effect)

        result = (
            CompositeVideoClip(rendered_visual_components, size=(width, height))
            .with_position((left, top))
            .with_start(self.start_time + offset_time)
            .with_end(self.end_time + offset_time)
            .with_duration(self.duration)
            .with_effects(built_effects)
        )

        if rendered_audio_components:
            children_audio_clips: 'list[CompositeAudioClip]' = []
            for rvc in rendered_visual_components:
                if isinstance(rvc, CompositeVideoClip):
                    if rvc.audio:
                        children_audio_clips.append(rvc.audio)
                        rvc.audio = None
            if children_audio_clips:
                self.log(f'reattaching {len(children_audio_clips)} audio clips from children to self')
                rendered_audio_components.extend(children_audio_clips)

            self.log(f'building audio with {len(rendered_audio_components)} clips')
            built_audio = (
                CompositeAudioClip(rendered_audio_components)
                .with_start(self.start_time + offset_time)
                .with_end(self.end_time + offset_time)
                .with_duration(self.duration)
            )

            return result.with_audio(built_audio)
        else:
            return result

    def find_first_component_with_duration(self) -> float:
        if self.relative_duration:
            return self.relative_duration
        for component in self.components:
            if isinstance(component, Container):
                return component.find_first_component_with_duration()
            elif isinstance(component, TimelineComponent):
                if component.relative_duration:
                    return component.relative_duration
        return 0

    @staticmethod
    def check_next_component_for_fadeins(next_component: Component | None = None) -> float:
        if not next_component or not isinstance(next_component, TimelineComponent):
            return 0
        effs = next_component.effects
        next_fadein = next((ef for ef in effs if ef.__class__.__name__ == 'FadeIn'), None)
        if next_fadein:
            return int(getattr(next_fadein, 'duration', 0))
        return 0

    def debug_show_children(self, indent: int = 0) -> None:
        self.log(self.uid)
        for component in self.components:
            if isinstance(component, Container):
                component.debug_show_children(indent + 2)
            else:
                component.log(component.uid)


class Box(VisualComponent, Container):
    """
    A Box is a container that is used to group other components spatially.
    Containers of any type (Box, Row, Col, Scene) can be nested.
    """
    def __init__(
        self,
        width: TDim = 'auto',
        height: TDim = 'auto',
        left: TDim = 'auto',
        top: TDim = 'auto',
        components: 'Component | Sequence[Component]' = [],
        start_time: float | None = None,
        end_time: float | None = None,
        duration: float | None = None,
        effects: 'Effect | Sequence[Effect]' = [],
        parent: 'Container | None' = None
    ):
        super().__init__(width, height, left, top, start_time, end_time, duration, effects, parent)


class Row(Container):
    """
    Col and Row are containers that are used to layout components spatially side by side or vertically.
    Containers of any type (Box, Row, Col, Scene) can be nested.
    See Col for more information.
    """
    def __init__(
        self,
        components: 'Component | Sequence[Component]' = [],
        percentage: float = 50,
        start_time: float | None = None,
        end_time: float | None = None,
        duration: float | None = None,
        effects: 'Effect | Sequence[Effect]' = [],
        parent: 'Container | None' = None
    ):
        super().__init__(components, start_time, end_time, duration, effects, parent)
        self.percentage = percentage

    @property
    def height(self) -> int:
        return round(self.container.height * self.percentage / 100)


class Col(Container):
    """
    Col and Row are containers that are used to layout components spatially side by side or vertically.
    Containers of any type (Box, Row, Col, Scene) can be nested.
    A container can have rows or columns together with other components.
    A container can't have both rows and columns.
    Columns and rows occupy a `percentage` of their container's width or height.
    The total percentage within a container can not be greater than 100%.
    Columns occupy the full height of the container, rows occupy the full width.
    Rows and columns don't have width, height, left, top.
    Use empty rows or columns to create space between other rows or columns.
    """
    def __init__(
        self,
        components: 'Component | Sequence[Component]' = [],
        percentage: float = 50,
        start_time: float | None = None,
        end_time: float | None = None,
        duration: float | None = None,
        effects: 'Effect | Sequence[Effect]' = [],
        parent: 'Container | None' = None
    ):
        super().__init__(components, start_time, end_time, duration, effects, parent)
        self.percentage = percentage

    @property
    def width(self) -> int:
        return round(self.container.width * self.percentage / 100)


class Scene(Container):
    """
    A Scene is a container that groups components that should be rendered at the same time.
    Multiple scenes within a container are rendered one after the other, in the order they are defined.
    Times of components within a Scene are relative to the start of the Scene.
    Two scenes can be rendered at the same time as long as they are in different containers.
    The duration of a Scene can be set manually, otherwise it is automatically calculated by:
        - the sum of the durations of its Scene children, or
        - the duration of its longest child (audio, video, etc.), or
        - the duration of its parent container, or
        - 10s if no other duration is set
    """
    def __init__(
        self,
        components: 'Component | Sequence[Component]' = (),
        width: int = 720,
        height: int = 720,
        duration: float | None = None,
        effects: 'Effect | Sequence[Effect]' = (),
        fps: int = 30,
        bg_color: TColor = 'black',
    ):
        super().__init__(components, duration=duration, effects=effects)

        self._width = width
        self._height = height
        self.fps = fps
        self.bg_color = bg_color

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def build(self, file_path: str = 'output.mp4') -> None:
        self.log(f'building movie {self.width}x{self.height} @ fps={self.fps} length={self.duration}')
        background_color = VisualComponent.color_to_tuple(self.bg_color)
        movie = CompositeVideoClip([
            ColorClip(size=(self.width, self.height), duration=self.duration, color=background_color),
            self.render(self.width, self.height, 0, 0)
        ])

        movie.write_videofile(file_path, fps=self.fps)


class Movie(Scene):
    pass


class Effect(WithUid, ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def build(self) -> 'MoviepyEffect':
        pass


class VisualEffect(Effect, ABC):
    def __init__(self):
        super().__init__()
        self.component: 'VisualComponent | None' = None


class AudioEffect(Effect, ABC):
    def __init__(self):
        super().__init__()
        self.component: 'AudioComponent | None' = None


class AnimatedEffect(VisualEffect, ABC):
    def __init__(self, duration: float = 1):
        super().__init__()
        self.duration = duration


class GenerativeProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, *args, **kwargs) -> str:
        pass

    @classmethod
    def cache_file(cls, prompt: str, prefix: str, suffix: str) -> str:
        if not prompt:
            raise ValueError('Prompt is required')

        digest = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
        return f'{prefix}{digest}{suffix}'


class GenerativeTextProvider(GenerativeProvider, ABC):
    pass


class GenerativeImageProvider(GenerativeProvider, ABC):
    pass


class GenerativeAudioProvider(GenerativeProvider, ABC):
    pass


class GenerativeMusicProvider(GenerativeProvider, ABC):
    pass


class GenerativeVoiceProvider(GenerativeProvider, ABC):
    pass


class GenerativeVideoProvider(GenerativeProvider, ABC):
    pass


class GenFunction(ABC):
    required_provider: type[GenerativeProvider]

    def __init__(self, prompt: str):
        self.prompt = prompt

    def generate(self, provider: GenerativeProvider) -> str:
        return provider.generate(self.prompt)


class GenText(GenFunction):
    required_provider = GenerativeTextProvider


class GenImage(GenFunction):
    required_provider = GenerativeImageProvider


class GenAudio(GenFunction):
    required_provider = GenerativeAudioProvider


class GenMusic(GenFunction):
    required_provider = GenerativeMusicProvider

    def __init__(self, prompt: str, duration: float = 30):
        super().__init__(prompt)
        self.duration = duration

    def generate(self, provider: GenerativeProvider) -> str:
        return provider.generate(self.prompt, self.duration)


class GenVideo(GenFunction):
    required_provider = GenerativeVideoProvider

    def __init__(self, prompt: str, duration: float = 30):
        super().__init__(prompt)
        self.duration = duration

    def generate(self, provider: GenerativeProvider) -> str:
        return provider.generate(self.prompt, self.duration)


class GenVoice(GenFunction):
    required_provider = GenerativeVoiceProvider
