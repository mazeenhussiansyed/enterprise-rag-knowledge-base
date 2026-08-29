from __future__ import annotations

import re
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from pypdf import PdfReader

from .errors import DocumentParseError, UnsupportedDocumentError, UnsafeDocumentError
from .models import ParsedPage


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".markdown"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
WORD_NAMESPACE = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def sanitize_filename(filename: str) -> str:
    normalized = filename.replace("\\", "/")
    if not normalized or Path(normalized).name != normalized:
        raise UnsafeDocumentError("filename must not contain a directory path")
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", normalized).strip("._")
    if not safe:
        raise UnsafeDocumentError("filename has no safe characters")
    return safe


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def validate_document(path: str | Path) -> tuple[Path, str]:
    source = Path(path)
    if not source.exists() or not source.is_file():
        raise UnsafeDocumentError(f"document does not exist: {source}")
    size = source.stat().st_size
    if size == 0:
        raise UnsafeDocumentError("document is empty")
    if size > MAX_FILE_SIZE_BYTES:
        raise UnsafeDocumentError(
            f"document exceeds the {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB limit"
        )

    extension = source.suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise UnsupportedDocumentError(
            f"unsupported extension {extension or '<none>'}; allowed: {sorted(ALLOWED_EXTENSIONS)}"
        )

    sanitized_name = sanitize_filename(source.name)
    if extension == ".pdf":
        with source.open("rb") as handle:
            if handle.read(5) != b"%PDF-":
                raise UnsafeDocumentError("PDF signature is invalid")
    if extension == ".docx":
        if not zipfile.is_zipfile(source):
            raise UnsafeDocumentError("DOCX archive is invalid")
        with zipfile.ZipFile(source) as archive:
            if "word/document.xml" not in archive.namelist():
                raise UnsafeDocumentError("DOCX is missing word/document.xml")
    return source, sanitized_name


def _parse_pdf(path: Path) -> list[ParsedPage]:
    try:
        reader = PdfReader(path)
        if reader.is_encrypted and reader.decrypt("") == 0:
            raise UnsafeDocumentError("encrypted PDF requires a password")
        pages = [
            ParsedPage(page_number=index, text=normalize_text(page.extract_text() or ""))
            for index, page in enumerate(reader.pages, start=1)
        ]
    except UnsafeDocumentError:
        raise
    except Exception as exc:
        raise DocumentParseError(f"could not parse PDF: {path.name}") from exc
    return [page for page in pages if page.text]


def _docx_tokens(paragraph: ElementTree.Element) -> list[str | None]:
    tokens: list[str | None] = []
    for element in paragraph.iter():
        if element.tag == f"{WORD_NAMESPACE}t":
            tokens.append(element.text or "")
        elif element.tag == f"{WORD_NAMESPACE}tab":
            tokens.append("\t")
        elif element.tag == f"{WORD_NAMESPACE}br":
            break_type = element.attrib.get(f"{WORD_NAMESPACE}type", "textWrapping")
            tokens.append(None if break_type == "page" else "\n")
        elif element.tag == f"{WORD_NAMESPACE}lastRenderedPageBreak":
            tokens.append(None)
    return tokens


def _parse_docx(path: Path) -> list[ParsedPage]:
    try:
        with zipfile.ZipFile(path) as archive:
            root = ElementTree.fromstring(archive.read("word/document.xml"))
    except Exception as exc:
        raise DocumentParseError(f"could not parse DOCX: {path.name}") from exc

    page_parts: list[list[str]] = [[]]
    for paragraph in root.iter(f"{WORD_NAMESPACE}p"):
        for token in _docx_tokens(paragraph):
            if token is None:
                page_parts.append([])
            else:
                page_parts[-1].append(token)
        page_parts[-1].append("\n")

    pages = [
        ParsedPage(page_number=index, text=normalize_text("".join(parts)))
        for index, parts in enumerate(page_parts, start=1)
    ]
    return [page for page in pages if page.text]


def _parse_text(path: Path) -> list[ParsedPage]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DocumentParseError("TXT and Markdown documents must use UTF-8") from exc
    normalized = normalize_text(text)
    return [ParsedPage(page_number=1, text=normalized)] if normalized else []


def parse_document(path: str | Path) -> tuple[str, list[ParsedPage]]:
    source, sanitized_name = validate_document(path)
    extension = source.suffix.lower()
    if extension == ".pdf":
        pages = _parse_pdf(source)
    elif extension == ".docx":
        pages = _parse_docx(source)
    else:
        pages = _parse_text(source)
    if not pages:
        raise DocumentParseError(f"no extractable text found in {source.name}")
    return sanitized_name, pages
