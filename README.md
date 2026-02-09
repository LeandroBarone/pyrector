# pyrector

A thin, opinionated Python library for building short-form videos (social ads, promos, stories) via a declarative API. Define a tree of visual and audio components under a root `Movie`; layout and timing are handled with sensible defaults. Generative media (text, image, audio, video) plugs in via `Gen*` types and configurable providers.

![pyrector example](https://raw.githubusercontent.com/LeandroBarone/pyrector/main/demo.mp4)

# Changelog

## 0.1.0 (2026-02-08)

- Initial release.

# Features

- **Declarative composition**: Build videos as a tree of containers and components (boxes, rows, columns, scenes).
- **Layout and timing**: Position and size with percentages or pixels; control duration and when each element appears.
- **Generative media**: Use `GenText`, `GenImage`, `GenVideo`, `GenVoice`, `GenAudio`, `GenMusic` with pluggable providers (e.g. Google, ElevenLabs).
- **Effects**: Fade, slide, and other visual/audio effects applied per component.
- **One entry point**: Call `movie.build('output.mp4')` to render.

# Installation

```bash
pip install pyrector
```

# Hello World

```python
import pyrector as pg

movie = pg.Movie([
    pg.AudioFile('music.mp3'),
    pg.AudioFile('hello_world.mp3'),
    pg.ImageFile('bg.jpg'),
    pg.Text('Hello, World!', font_size='xl'),
], width=720, height=1080, fps=30)
movie.build('hello_world.mp4')
```

# Full example

```python
import pyrector as pg

scene1 = pg.Scene(
    [
        pg.Row(
            [
                pg.Box(
                    components=[
                        pg.ImageFile(pg.GenImage('a red apple'), effects=[pg.FadeIn(duration=0.5)]),
                    ],
                    width='50%',
                    height='50%',
                ),
                pg.Col(
                    [
                        pg.ColorBlock('navy'),
                        pg.Text('Hello', font_size='l', effects=[pg.SlideOutTop(duration=0.5)]),
                    ],
                    percentage=50,
                ),
            ]
        ),
    ],
    duration=3,
    width=720,
    height=720,
    fps=30,
)

scene2 = pg.Scene(
    [
        pg.VideoFile(pg.GenVideo('sunset clip'), effects=[pg.FadeIn(duration=0.5)]),
        pg.AudioFile(pg.GenVoice('Welcome to the show'), volume=0.9),
    ],
    duration=5,
)

scene3 = pg.Scene(
    [
        pg.TextBlock([pg.Text(pg.GenText('Closing line'))]),
        pg.ColorBlock('#333', width='100%', height=80, left=0, top='80%'),
    ],
    duration=2,
)

movie = pg.Movie(
    [scene1, scene2, scene3],
    width=720,
    height=720,
    fps=30,
)
movie.build('short_movie.mp4')
```

# API reference

The API is organized into: **containers** (layout), **components** (visual and audio), **generative functions** (Gen*), and **effects**.

## Containers (layout)

### Movie

Root container. Same structure as **Scene**; use it as the top-level entry and call `.build(file_path)` to render to a video file.

```python
Movie(
    components: Component | Sequence[Component] = (),
    width: int = 720,
    height: int = 720,
    duration: float | None = None,
    effects: Effect | Sequence[Effect] = (),
    fps: int = 30,
    bg_color: tuple[int, int, int] = (0, 0, 0),
)
```

| Parameter | Description |
|-----------|-------------|
| **components** | One or more child components (typically **Scene**). |
| **width** | Output video width in pixels. |
| **height** | Output video height in pixels. |
| **duration** | Total duration in seconds; can be derived from children if not set. |
| **effects** | see: **Box** |
| **fps** | Frames per second for the output video. |
| **bg_color** | Background color as RGB tuple `(r, g, b)`. |

**Methods:** `build(file_path: str)`: Renders the movie to the given file path.

### Box

A **Box** is a container used to group other components spatially. Containers of any type (Box, Row, Col, Scene) can be nested inside.

```python
Box(
    width: TDim = 'auto',
    height: TDim = 'auto',
    left: TDim = 'auto',
    top: TDim = 'auto',
    components: Component | Sequence[Component] = (),
    start_time: float | None = None,
    end_time: float | None = None,
    duration: float | None = None,
    effects: Effect | Sequence[Effect] = (),
)
```

| Parameter | Description |
|-----------|-------------|
| **width** | Width: number (px), `'auto'`, or e.g. `'50%'`. **TDim**. |
| **height** | Height: number (px), `'auto'`, or percentage string. **TDim**. |
| **left** | Horizontal position from the left edge. **TDim**. |
| **top** | Vertical position from the top edge. **TDim**. |
| **components** | Child components to place inside the box. |
| **start_time** | Start time in seconds. |
| **end_time** | End time in seconds. |
| **duration** | Length in seconds. Can not be set together with **end_time**. |
| **effects** | Single effect or list; applied in order when rendering. |

### Scene

A **Scene** groups components that are rendered at the same time. Multiple scenes within a container are rendered one after the other, in the order they are defined. Component times inside a Scene are relative to the start of that scene. Multiple scenes can be rendered at the same time if they live in different containers. Duration can be set manually; otherwise it is derived in this order: (1) sum of its Scene children’s durations, (2) duration of its longest child (audio, video, etc.), (3) parent container’s duration, or (4) 10s if none of the above apply.

```python
Scene(
    components: Component | Sequence[Component] = (),
    width: int = 720,
    height: int = 720,
    duration: float | None = None,
    effects: Effect | Sequence[Effect] = (),
    fps: int = 30,
    bg_color: tuple[int, int, int] = (0, 0, 0),
)
```

| Parameter | Description |
|-----------|-------------|
| **components** | One or more child components (e.g. **Row**, **Col**, **Box**, **VideoFile**, **Text**). |
| **width** | Scene width in pixels. |
| **height** | Scene height in pixels. |
| **duration** | Length of this scene in seconds. |
| **effects** | see: **Box** |
| **fps** | Frames per second for this scene. |
| **bg_color** | Background color as RGB tuple. |

### Row

A **Row** occupies a **percentage** of its parent container’s **height**. Sibling rows stack vertically; each row’s **percentage** is its share of the parent’s height (total should be ≤ 100%). The row’s **components** are rendered inside that slot. A container may have rows or columns (possibly together with other components like **Box**), but not both rows and columns. A row spans the full width of its parent. Rows (and **Col**s) do not have `width`, `height`, `left`, or `top`; use empty **Row** or **Col** to create space between others.

```python
Row(
    components: Component | Sequence[Component] = (),
    percentage: float = 50,
    start_time: float | None = None,
    end_time: float | None = None,
    duration: float | None = None,
    effects: Effect | Sequence[Effect] = (),
)
```

| Parameter | Description |
|-----------|-------------|
| **components** | Child components rendered inside this row’s slot. |
| **percentage** | This row’s share of the **parent’s height** (0–100). Sibling rows’ percentages should sum to ≤ 100. |
| **start_time**, **end_time**, **duration** | see: **Box** |
| **effects** | see: **Box** |

### Col

A **Col** occupies a **percentage** of its parent container’s **width**. Sibling columns sit side by side; each column’s **percentage** is its share of the parent’s width (total should be ≤ 100%). The column’s **components** are rendered inside that slot. Same rules as **Row**: a container may have rows or columns (and other components), but not both rows and columns; total percentage per container cannot exceed 100%. A column spans the full height of its parent. Cols (and Rows) do not have `width`, `height`, `left`, or `top`; use empty **Col** or **Row** for spacing.

```python
Col(
    components: Component | Sequence[Component] = (),
    percentage: float = 50,
    start_time: float | None = None,
    end_time: float | None = None,
    duration: float | None = None,
    effects: Effect | Sequence[Effect] = (),
)
```

| Parameter | Description |
|-----------|-------------|
| **components** | Child components rendered inside this column’s slot. |
| **percentage** | This column’s share of the **parent’s width** (0–100). Sibling columns’ percentages should sum to ≤ 100. |
| **start_time**, **end_time**, **duration** | see: **Box** |
| **effects** | see: **Box** |

## Components

### ColorBlock

Solid color block. Supports transparency via **TColor** (e.g. RGBA).

```python
ColorBlock(
    color: TColor,
    width: TDim = 'auto',
    height: TDim = 'auto',
    left: TDim = 'auto',
    top: TDim = 'auto',
    start_time: float | None = None,
    end_time: float | None = None,
    duration: float | None = None,
    effects: Effect | Sequence[Effect] = (),
)
```

| Parameter | Description |
|-----------|-------------|
| **color** | **TColor**: RGB tuple `(r,g,b)`, RGBA tuple, or color string (e.g. `'white'`, `'#333'`). |
| **width**, **height**, **left**, **top** | see: **Box** |
| **start_time**, **end_time**, **duration** | see: **Box** |
| **effects** | see: **Box** |

### ImageFile

Image from a file path or from a generative function (e.g. `GenImage`). The image is scaled/cropped to fit the given size.

```python
ImageFile(
    image_path: str | GenFunction,
    width: TDim = 'auto',
    height: TDim = 'auto',
    left: TDim = 'auto',
    top: TDim = 'auto',
    start_time: float | None = None,
    end_time: float | None = None,
    duration: float | None = None,
    effects: Effect | Sequence[Effect] = (),
)
```

| Parameter | Description |
|-----------|-------------|
| **image_path** | File path string or generative function (e.g. `pg.GenImage('a red apple')`). |
| **width**, **height**, **left**, **top** | see: **Box** |
| **start_time**, **end_time**, **duration** | see: **Box** |
| **effects** | see: **Box** |

### VideoFile

Video from path or generative function (e.g. `GenVideo`). Loaded without audio by default. Sizing behavior is the same as **ImageFile**.

```python
VideoFile(
    video_path: str | GenFunction,
    width: TDim = 'auto',
    height: TDim = 'auto',
    left: TDim = 'auto',
    top: TDim = 'auto',
    start_time: float | None = None,
    end_time: float | None = None,
    duration: float | None = None,
    effects: Effect | Sequence[Effect] = (),
)
```

| Parameter | Description |
|-----------|-------------|
| **video_path** | File path or generative function (e.g. `pg.GenVideo('sunset clip')`). |
| **width**, **height**, **left**, **top** | see: **Box** |
| **start_time**, **end_time**, **duration** | see: **Box** |
| **effects** | see: **Box** |

### TextBlock

Container that stacks **Text** components vertically. Does not use **Text** alignment or background; use **ColorBlock** for backgrounds.

```python
TextBlock(
    components: Text | Sequence[Text] = (),
    vertical_spacing: TDim = 'auto',
    start_time: float | None = None,
    end_time: float | None = None,
    duration: float | None = None,
    effects: Effect | Sequence[Effect] = (),
)
```

| Parameter | Description |
|-----------|-------------|
| **components** | One or more **Text** components. |
| **vertical_spacing** | Space between lines: pixel number, `'auto'` (= `'100%'`), or percentage string (e.g. `'80%'`). **TDim**. |
| **start_time**, **end_time**, **duration** | see: **Box** |
| **effects** | see: **Box** |

### Text

Text label or caption. **text** can be a string or a generative function (e.g. `GenText`). **font_size** can be an int (pixels) or a size name relative to movie height.

```python
Text(
    text: str | GenFunction,
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
    effects: Effect | Sequence[Effect] = (),
)
```

| Parameter | Description |
|-----------|-------------|
| **text** | String or generative function (e.g. `pg.GenText('Closing line')`). |
| **font_size** | **TTextSize**: int (pixels) or size name `'xxs'`, `'xs'`, `'s'`, `'m'`, `'l'`, `'xl'`, `'xxl'` (scaled from movie height). |
| **font_color** | **TColor** (see: **ColorBlock**). |
| **background_color** | **TColor** or `None`. |
| **stroke_color** | **TColor** for text outline, or `None`. |
| **stroke_width** | Outline width in pixels; 0 disables. |
| **interline** | Extra spacing between lines (pixels). |
| **text_align** | Horizontal alignment of text within the line: e.g. `'left'`, `'center'`, `'right'`. |
| **horizontal_align** | Horizontal alignment of the text block in its container. |
| **vertical_align** | Vertical alignment of the text block: e.g. `'top'`, `'center'`, `'bottom'`. |
| **font_style** | **FontStyle** dataclass to override several text properties at once. |
| **width**, **height**, **left**, **top** | see: **Box** |
| **start_time**, **end_time**, **duration** | see: **Box** |
| **effects** | see: **Box** |

### AudioFile

Audio from path or generative function (e.g. `GenAudio`, `GenVoice`). Duration is taken from the file or from explicit **duration** / **start_time** / **end_time**.

```python
AudioFile(
    audio_path: str | GenFunction,
    volume: float = 1.0,
    start_time: float | None = None,
    end_time: float | None = None,
    duration: float | None = None,
    effects: Effect | Sequence[Effect] = (),
)
```

| Parameter | Description |
|-----------|-------------|
| **audio_path** | File path or generative function (e.g. `pg.GenVoice('Welcome to the show')`). |
| **volume** | Playback volume multiplier (0.0–1.0 or higher). |
| **start_time**, **end_time**, **duration** | see: **Box** |
| **effects** | see: **Box** |

## Generative functions

Used wherever a path or string is expected (e.g. `ImageFile(image_path=pg.GenImage('...'))`). At build time they are resolved by an available provider (e.g. Google, ElevenLabs). All take a single **prompt** string.

| Class | Use as | Typical provider |
|-------|--------|-------------------|
| **GenText**(prompt: str) | `Text(text=...)` | GenerativeTextProvider (e.g. Google) |
| **GenImage**(prompt: str) | `ImageFile(image_path=...)` | GenerativeImageProvider (e.g. Google) |
| **GenAudio**(prompt: str) | `AudioFile(audio_path=...)` | GenerativeAudioProvider |
| **GenVoice**(prompt: str) | `AudioFile(audio_path=...)` | GenerativeVoiceProvider (e.g. ElevenLabs) |
| **GenMusic**(prompt: str) | `AudioFile(audio_path=...)` | GenerativeMusicProvider (e.g. ElevenLabs) |
| **GenVideo**(prompt: str) | `VideoFile(video_path=...)` | GenerativeVideoProvider (e.g. Google) |

## Effects

**Visual** (from `pyrector.visual_effects`):

| Effect | Parameters | Description |
|--------|------------|-------------|
| **FadeIn** | duration: float = 1 | Fade in over given seconds. |
| **FadeOut** | duration: float = 1 | Fade out over given seconds. |
| **Painting** | saturation: float = 1.4, black: float = 0.006 | Painting-style look. |
| **SlideInTop**, **SlideInBottom**, **SlideInLeft**, **SlideInRight** | duration: float = 1 | Slide in from the given edge. |
| **SlideOutTop**, **SlideOutBottom**, **SlideOutLeft**, **SlideOutRight** | duration: float = 1 | Slide out toward the given edge. |
| **TimeMirror** | - | No parameters. |

**Audio** (from `pyrector.audio_effects`):

| Effect | Parameters | Description |
|--------|------------|-------------|
| **Volume** | factor: float = 1.0 | Multiply volume by factor. |

## Type notes

- **TColor**: RGB tuple `(r, g, b)`, RGBA tuple, or color name/hex string (e.g. `'white'`, `'#333'`).
- **TDim**: Number (pixels), `'auto'`, or percentage string (e.g. `'50%'`).
- **TTextSize**: Int (pixels) or size name `'xxs'`…`'xxl'`; names are scaled from movie height.
