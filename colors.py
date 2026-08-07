from __future__ import annotations

from io import BytesIO
import colorsys
import math

from PIL import Image, ImageOps

from .models import RGBColor


def _distance(a: RGBColor, b: RGBColor) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b, strict=True)))


def _score(color: RGBColor, count: int) -> float:
    r, g, b = (value / 255 for value in color)
    _, saturation, value = colorsys.rgb_to_hsv(r, g, b)

    # Prefer frequent, vivid, usable ambient colors.
    return count * (0.35 + saturation * 1.25) * (0.35 + value)


def _usable(color: RGBColor) -> bool:
    r, g, b = color
    maximum = max(color)
    minimum = min(color)
    brightness = (r + g + b) / 3
    saturation = maximum - minimum

    if brightness < 18:
        return False
    if brightness > 242 and saturation < 22:
        return False
    if saturation < 12:
        return False
    return True


def extract_palette(image_bytes: bytes, color_count: int = 3) -> list[RGBColor]:
    with Image.open(BytesIO(image_bytes)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        image.thumbnail((180, 180), Image.Resampling.LANCZOS)

        quantized = image.quantize(
            colors=24,
            method=Image.Quantize.MEDIANCUT,
            dither=Image.Dither.NONE,
        ).convert("RGB")

        counted = quantized.getcolors(maxcolors=180 * 180) or []

    candidates: list[tuple[float, RGBColor]] = []
    for count, raw_color in counted:
        color: RGBColor = tuple(raw_color)  # type: ignore[assignment]
        if _usable(color):
            candidates.append((_score(color, count), color))

    candidates.sort(reverse=True, key=lambda item: item[0])

    chosen: list[RGBColor] = []
    for _, color in candidates:
        if all(_distance(color, existing) >= 70 for existing in chosen):
            chosen.append(color)
        if len(chosen) >= color_count:
            break

    if not chosen:
        chosen = [(80, 30, 120)]

    while len(chosen) < color_count:
        base = chosen[len(chosen) % len(chosen)]
        r, g, b = base
        if len(chosen) == 1:
            derived = (min(255, int(r * 1.25 + 15)), min(255, int(g * 0.8 + 10)), min(255, int(b * 1.1 + 10)))
        else:
            derived = (g, b, r)
        chosen.append(derived)

    return chosen[:color_count]
