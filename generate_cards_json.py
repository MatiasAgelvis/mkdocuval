#!/usr/bin/env python3
# coding: utf-8

import argparse
import io
import json
import re
import tempfile
import warnings
import zipfile
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

import mammoth
import pypandoc

from card_models import Card, CardMetadata, ImageRef
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
    return result.value


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
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"(?:\n[ \t]*){2,}", "\n\n", text)
        text = re.sub(r" *\n *", "\n", text)
        return text.strip()


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


def parse_card_marker(marker: str, config: SourceDocumentConfig) -> CardMetadata:
    metadata = CardMetadata(
        title=config.title,
        author=config.author,
        book=config.book,
        year=config.year,
        page=config.extra.get("page"),
        raw_marker=marker.strip() if marker else None,
    )

    if marker:
        if not metadata.year:
            year_match = re.search(r"\b(\d{4}(?:-\d{4})?)\b", marker)
            if year_match:
                metadata.year = year_match.group(1)

        if not metadata.page:
            page_match = re.search(r"[pP]\.?\s*(\d+(?:-\d+)?)", marker)
            if page_match:
                metadata.page = page_match.group(1)
            else:
                page_match = re.search(r":\s*\(?\s*(\d+(?:-\d+)?)(?:\s*y\s*ss)?(?:\D|$)", marker)
                if page_match:
                    metadata.page = page_match.group(1)

        if not metadata.title:
            cleaned = re.sub(r"\(?\d{4}(?:-\d{4})?\)?", "", marker)
            cleaned = re.sub(r"[pP]\.?\s*\d+(?:-\d+)?", "", cleaned)
            cleaned = re.sub(r"[()\[\]]", "", cleaned).strip(" :-–—")
            metadata.title = cleaned or config.title

    return metadata


def split_text_into_cards(text: str, config: SourceDocumentConfig) -> list[tuple[str, str]]:
    regex = re.compile(config.split_pattern, flags=re.IGNORECASE | re.MULTILINE)
    matches = list(regex.finditer(text))
    if not matches:
        warnings.warn(
            f"Split pattern did not match any markers for {config.filename!r}. "
            "Treating document as a single card. Check the regex pattern."
        )
        return [("", text.strip())]

    cards: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        marker = match.group(1)
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        cards.append((marker, text[start:end].strip()))

    if matches[0].start() > 0:
        preamble = text[: matches[0].start()].strip()
        if preamble:
            cards[0] = (cards[0][0], f"{preamble}\n\n{cards[0][1]}")

    return cards


def build_cards_for_source(source_path: Path, config: SourceDocumentConfig, image_root: Path) -> list[Card]:
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
    for index, (marker, content) in enumerate(sections, start=1):
        metadata = parse_card_marker(marker, config)
        card_id = base_id if len(sections) == 1 else f"{base_id}-{index}"
        card_images = [
            image for image in images
            if image.placeholder_id is not None and f"[[IMAGE:{image.placeholder_id}]]" in content
        ]
        cards.append(
            Card(
                id=card_id,
                title=metadata.title,
                author=metadata.author,
                book=metadata.book,
                year=metadata.year,
                page=metadata.page,
                raw_marker=metadata.raw_marker,
                content=content,
                source_path=str(source_path.as_posix()),
                source_format=source_path.suffix.lower().lstrip("."),
                images=card_images,
            )
        )
    return cards


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

    cards: list[Card] = []
    for config, source_path in source_configs:
        if args.verbose:
            print(f"Processing {source_path}")
        cards.extend(build_cards_for_source(source_path, config, image_root))

    output_data = {"cards": [card.to_dict() for card in cards]}
    output_path.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.verbose:
        print(f"Wrote {len(cards)} cards to {output_path}")
        print(f"Images stored under {image_root}")


if __name__ == "__main__":
    main()


