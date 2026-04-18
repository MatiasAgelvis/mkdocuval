from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class BaseMetadata:
    title: Optional[str] = None
    author: Optional[str] = None
    book: Optional[str] = None
    year: Optional[str] = None


@dataclass
class ImageRef:
    path: str
    filename: str
    internal_path: Optional[str] = None
    caption: Optional[str] = None
    position: Optional[str] = None
    placeholder_id: Optional[int] = None
    alt_text: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CardMetadata(BaseMetadata):
    page: Optional[str] = None
    raw_marker: Optional[str] = None


@dataclass(kw_only=True)
class Card(BaseMetadata):
    id: str
    page: Optional[str]
    raw_marker: Optional[str]
    content: str
    source_path: str
    source_format: str
    images: List[ImageRef] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["images"] = [image.to_dict() for image in self.images]
        return data
