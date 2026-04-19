#!/usr/bin/env python3
# coding: utf-8

import argparse
import io
import json
import re
import tempfile
import warnings
import zipfile
from dataclasses import asdict, dataclass, field
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional

from anomalies import (
    SourceBuildResult,
    collect_card_length_anomalies,
    print_card_length_anomalies,
)

import mammoth
import pypandoc

from card_models import BaseMetadata, Card, ImageRef
from source_documents import SourceDocumentConfig, find_source_configs

SUPPORTED_INPUT_EXTENSIONS = {".odt", ".docx"}


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def convert_odt_to_docx_bytes(odt_path: Path) -> bytes:
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / f"{odt_path.stem}.docx"
        pypandoc.convert_file(str(odt_path), "docx", outputfile=str(output_path))
        return output_path.read_bytes()


def extract_raw_text_from_docx_bytes(docx_bytes: bytes) -> str:
    with io.BytesIO(docx_bytes) as docx_file:
        result = mammoth.extract_raw_text(docx_file)
    return normalize_whitespace(result.value)


def get_image_extension(content_type: str) -> str:
    if "/" in content_type:
        ext = content_type.split("/", 1)[1].split(";", 1)[0]
    else:
        ext = content_type
    if ext == "jpeg":
        ext = "jpg"
    return ext


class HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str]]) -> None:
        if tag == "img":
            attrs_dict = dict(attrs)
            src = attrs_dict.get("src", "")
            if src.startswith("IMAGE_PLACEHOLDER_"):
                self.parts.append(src.replace("IMAGE_PLACEHOLDER_", "[[IMAGE:").rstrip("/") + "]]")
        elif tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"p", "div", "li", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def get_text(self) -> str:
        text = unescape("".join(self.parts))
        text = normalize_whitespace(text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"(?:\n[ \t]*){2,}", "\n\n", text)
        text = re.sub(r" *\n *", "\n", text)
        return text.strip()


def normalize_whitespace(text: str) -> str:
    text = text.replace("\u00A0", " ")
    text = text.replace("\u202F", " ")
    return text


@dataclass(frozen=True)
class BookGroupKey:
    title: Optional[str]
    author: Optional[str]
    book: Optional[str]
    year: Optional[str]


@dataclass
class BookGroup(BaseMetadata):
    cards: list[Card] = field(default_factory=list)


@dataclass
class CardSection:
    content: str
    marker: Optional[str] = None
    page: Optional[str] = None
    year: Optional[str] = None


def html_to_plain_text(html: str) -> str:
    parser = HTMLTextExtractor()
    parser.feed(html)
    parser.close()
    return parser.get_text()


def extract_text_and_images_from_docx_bytes(docx_bytes: bytes, image_dir: Path) -> tuple[str, list[ImageRef]]:
    images: list[ImageRef] = []
    image_dir.mkdir(parents=True, exist_ok=True)

    def image_handler(image):
        placeholder_id = len(images) + 1
        extension = get_image_extension(image.content_type)
        filename = f"image-{placeholder_id}.{extension}"
        target_path = image_dir / filename
        with image.open() as image_file, target_path.open("wb") as output_file:
            output_file.write(image_file.read())

        images.append(
            ImageRef(
                path=str(target_path.as_posix()),
                filename=filename,
                internal_path=None,
                caption=image.alt_text or None,
                placeholder_id=placeholder_id,
                alt_text=image.alt_text or None,
            )
        )
        return {"src": f"IMAGE_PLACEHOLDER_{placeholder_id}"}

    with io.BytesIO(docx_bytes) as docx_file:
        result = mammoth.convert_to_html(docx_file, convert_image=mammoth.images.img_element(image_handler))

    text = html_to_plain_text(result.value)
    return text, images


def normalize_capture(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    normalized = value.strip()
    if normalized.startswith("(") and normalized.endswith(")"):
        normalized = normalized[1:-1].strip()
    return normalized or None


def split_text_into_cards(text: str, config: SourceDocumentConfig) -> list[CardSection]:
    regex = re.compile(config.split_pattern, flags=re.IGNORECASE | re.MULTILINE)
    matches = list(regex.finditer(text))
    if not matches:
        warnings.warn(
            f"Split pattern did not match any markers for {config.filename!r}. "
            "Treating document as a single card. Check the regex pattern."
        )
        return [CardSection(content=text.strip())]

    cards: list[CardSection] = []
    for index, match in enumerate(matches):
        groups = match.groupdict()
        marker = normalize_capture(groups.get("marker")) or match.group(0).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        cards.append(
            CardSection(
                marker=marker,
                page=normalize_capture(groups.get("page")),
                year=normalize_capture(groups.get("year")),
                content=text[start:end].strip(),
            )
        )

    if matches[0].start() > 0:
        preamble = text[: matches[0].start()].strip()
        if preamble:
            cards[0].content = f"{preamble}\n\n{cards[0].content}"

    return cards


def build_cards_for_source(source_path: Path, config: SourceDocumentConfig, image_root: Path) -> SourceBuildResult:
    if source_path.suffix.lower() == ".odt":
        docx_bytes = convert_odt_to_docx_bytes(source_path)
    elif source_path.suffix.lower() == ".docx":
        docx_bytes = source_path.read_bytes()
    else:
        raise ValueError(f"Unsupported file type: {source_path}")

    output_image_dir = image_root / slugify(Path(config.filename).stem)
    raw_text, images = extract_text_and_images_from_docx_bytes(docx_bytes, output_image_dir)
    sections = split_text_into_cards(raw_text, config)

    cards: list[Card] = []
    base_id = slugify(Path(config.filename).stem)
    for index, section in enumerate(sections, start=1):
        card_id = base_id if len(sections) == 1 else f"{base_id}-{index}"
        card_images = [
            image for image in images
            if image.placeholder_id is not None and f"[[IMAGE:{image.placeholder_id}]]" in section.content
        ]
        cards.append(
            Card(
                id=card_id,
                title=config.title,
                author=config.author,
                book=config.book,
                year=section.year or config.year,
                page=section.page or config.extra.get("page"),
                raw_marker=section.marker,
                content=section.content,
                source_path=str(source_path.as_posix()),
                source_format=source_path.suffix.lower().lstrip("."),
                images=card_images,
            )
        )
    return SourceBuildResult(source_path=source_path, cards=cards)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a JSON card collection from ODT/DOCX source files."
    )
    parser.add_argument(
        "--source-dir",
        default="ODT",
        help="Directory containing source ODT or DOCX files.",
    )
    parser.add_argument(
        "--output-json",
        default="cards.json",
        help="Path for the generated JSON collection.",
    )
    parser.add_argument(
        "--image-dir",
        default="cards_images",
        help="Directory to store extracted images.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress information.",
    )
    parser.add_argument(
        "--report-anomalies",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Print a list of suspiciously short or long cards after generation.",
    )
    parser.add_argument(
        "--anomaly-sigma",
        type=float,
        default=4.0,
        help="Z-score threshold used to flag card lengths as outliers once they are also extreme relative to their source mean.",
    )
    parser.add_argument(
        "--anomaly-min-chars",
        type=int,
        default=25,
        help="Always flag cards at or below this many characters.",
    )
    parser.add_argument(
        "--anomaly-max-chars",
        type=int,
        default=100_000,
        help="Always flag cards at or above this many characters.",
    )
    parser.add_argument(
        "--anomaly-source-share",
        type=float,
        default=0.12,
        help="Flag cards that consume at least this share of a source's generated characters.",
    )
    parser.add_argument(
        "--anomaly-relative-ratio",
        type=float,
        default=4.0,
        help="Require a z-score outlier to also be this many times larger than the source mean, or this many times smaller for short-card detection.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_dir = Path(args.source_dir)
    output_path = Path(args.output_json)
    image_root = Path(args.image_dir)

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    source_configs = find_source_configs(source_dir)
    if not source_configs:
        raise SystemExit(f"No configured source files found in {source_dir}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image_root.mkdir(parents=True, exist_ok=True)

    books: list[BookGroup] = []
    group_index: dict[BookGroupKey, BookGroup] = {}
    source_results: list[SourceBuildResult] = []
    total_cards = 0

    for config, source_path in source_configs:
        if args.verbose:
            print(f"Processing {source_path}")
        source_result = build_cards_for_source(source_path, config, image_root)
        source_results.append(source_result)
        for card in source_result.cards:
            key = BookGroupKey(card.title, card.author, card.book, card.year)
            if key not in group_index:
                group = BookGroup(card.title, card.author, card.book, card.year)
                books.append(group)
                group_index[key] = group
            group_index[key].cards.append(card)
            total_cards += 1

    output_data = {"books": [asdict(group) for group in books]}
    output_path.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")

    anomalies = collect_card_length_anomalies(
        source_results,
        sigma_threshold=args.anomaly_sigma,
        min_chars=args.anomaly_min_chars,
        max_chars=args.anomaly_max_chars,
        source_share_threshold=args.anomaly_source_share,
        relative_ratio_threshold=args.anomaly_relative_ratio,
    )

    if args.verbose:
        print(f"Wrote {total_cards} cards to {output_path}")
        print(f"Images stored under {image_root}")

    if args.report_anomalies:
        print_card_length_anomalies(anomalies)
    elif args.verbose and not anomalies:
        print("No card-length anomalies detected.")


if __name__ == "__main__":
    main()


