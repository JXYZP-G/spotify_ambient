from __future__ import annotations

from dataclasses import dataclass


RGBColor = tuple[int, int, int]


@dataclass(slots=True)
class SpotifyTrack:
    track_id: str
    name: str
    artists: str
    album: str
    artwork_url: str | None
    duration_ms: int
    progress_ms: int
    is_playing: bool
    item_type: str

    @property
    def remaining_seconds(self) -> float:
        return max(0, self.duration_ms - self.progress_ms) / 1000


@dataclass(slots=True)
class SpotifyAmbientData:
    track: SpotifyTrack | None
    palette: list[RGBColor] | None
