from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import zipfile

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from enterprise_rag import (
    DocumentMetadata,
    IngestionLedger,
    IngestionService,
    ParsedPage,
    build_chunks,
    parse_document,
    sanitize_filename,
)
from enterprise_rag.errors import UnsafeDocumentError, VersionConflictError


DOCX_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Vendor onboarding requires security due diligence.</w:t></w:r></w:p>
    <w:p><w:r><w:br w:type="page"/><w:t>Legal approves contract liability clauses.</w:t></w:r></w:p>
  </w:body>
</w:document>
"""


def make_pdf(path: Path, text: str) -> None:
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_reference = writer._add_object(font)
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject(
                {NameObject("/F1"): font_reference}
            )
        }
    )
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = DecodedStreamObject()
    stream.set_data(f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("latin-1"))
    page[NameObject("/Contents")] = writer._add_object(stream)
    with path.open("wb") as handle:
        writer.write(handle)


def metadata(version: str = "1.0") -> DocumentMetadata:
    return DocumentMetadata(
        document_id="VM-STD",
        title="Vendor Management Standard",
        version=version,
        effective_date="2026-08-20",
        department="Procurement",
        roles=("procurement", "legal"),
    )


class ParserTests(unittest.TestCase):
    def test_parses_pdf_docx_txt_and_markdown(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            txt = root / "remote access.txt"
            txt.write_text("Remote access requires an approved VPN.", encoding="utf-8")
            markdown = root / "policy.md"
            markdown.write_text("# Data Quality\nCompleteness is measured daily.", encoding="utf-8")
            docx = root / "vendor.docx"
            with zipfile.ZipFile(docx, "w") as archive:
                archive.writestr("word/document.xml", DOCX_XML)
            pdf = root / "incident.pdf"
            make_pdf(pdf, "Report security incidents immediately.")

            txt_name, txt_pages = parse_document(txt)
            md_name, md_pages = parse_document(markdown)
            docx_name, docx_pages = parse_document(docx)
            pdf_name, pdf_pages = parse_document(pdf)

            self.assertEqual(txt_name, "remote_access.txt")
            self.assertIn("approved VPN", txt_pages[0].text)
            self.assertEqual(md_name, "policy.md")
            self.assertIn("Data Quality", md_pages[0].text)
            self.assertEqual(docx_name, "vendor.docx")
            self.assertEqual(len(docx_pages), 2)
            self.assertIn("liability clauses", docx_pages[1].text)
            self.assertEqual(pdf_name, "incident.pdf")
            self.assertIn("security incidents", pdf_pages[0].text)

    def test_rejects_path_traversal_and_false_pdf(self) -> None:
        with self.assertRaises(UnsafeDocumentError):
            sanitize_filename("../../secret.pdf")

        with TemporaryDirectory() as directory:
            fake_pdf = Path(directory) / "fake.pdf"
            fake_pdf.write_text("This is not a PDF", encoding="utf-8")
            with self.assertRaises(UnsafeDocumentError):
                parse_document(fake_pdf)


class ChunkingTests(unittest.TestCase):
    def test_uses_500_character_windows_with_50_character_overlap(self) -> None:
        text = "A" * 1100
        chunks = build_chunks(
            [ParsedPage(page_number=7, text=text)],
            metadata(),
            checksum="a" * 64,
            source_file="policy.txt",
            chunk_size=500,
            overlap=50,
        )

        self.assertEqual(len(chunks), 3)
        self.assertEqual(
            [(chunk.char_start, chunk.char_end) for chunk in chunks],
            [(0, 500), (450, 950), (900, 1100)],
        )
        self.assertTrue(all(chunk.page_number == 7 for chunk in chunks))
        self.assertTrue(all(chunk.roles == ("procurement", "legal") for chunk in chunks))
        self.assertTrue(all(chunk.checksum == "a" * 64 for chunk in chunks))


class LineageTests(unittest.TestCase):
    def test_duplicate_conflict_and_new_version_paths(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "vendor policy.txt"
            ledger_path = root / "ledger.json"
            output_root = root / "ingested"
            service = IngestionService(ledger_path=ledger_path, output_root=output_root)

            source.write_text("Vendor due diligence is required before onboarding.", encoding="utf-8")
            created = service.ingest(source, metadata("1.0"))
            duplicate = service.ingest(source, metadata("1.0"))

            self.assertEqual(created.status, "created")
            self.assertEqual(created.chunk_count, 1)
            self.assertTrue(Path(created.chunks_path).exists())
            self.assertEqual(duplicate.status, "duplicate")
            self.assertEqual(duplicate.checksum, created.checksum)

            source.write_text(
                "Vendor due diligence and legal approval are required before onboarding.",
                encoding="utf-8",
            )
            with self.assertRaises(VersionConflictError):
                service.ingest(source, metadata("1.0"))

            version_two = service.ingest(source, metadata("2.0"))
            self.assertEqual(version_two.status, "new_version")
            self.assertNotEqual(version_two.checksum, created.checksum)

            ledger = IngestionLedger(ledger_path).load()
            versions = ledger["documents"]["VM-STD"]["versions"]
            self.assertEqual(len(versions), 2)
            self.assertFalse(versions[0]["active"])
            self.assertTrue(versions[1]["active"])
            self.assertEqual(versions[1]["version"], "2.0")


if __name__ == "__main__":
    unittest.main()
