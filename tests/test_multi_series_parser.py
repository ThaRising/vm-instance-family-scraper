import logging
from pathlib import Path

from src.documents import DocumentDescriptor
from src.parsers.multi_series import MultiSeriesMarkdownDocumentParser

from .shared import BaseTestCase, tag

logger = logging.getLogger(__name__)


@tag("multi_series")
class TestSkuFamilyDocument(BaseTestCase):

    def setUp(self) -> None:
        super().setUp()
        current_path = Path(__file__).parent
        self.files = (current_path / "data" / "documents").iterdir()

    def test010_reduce_document(self):
        _, families = self.repository.get_families()
        for document in self.files:
            docs = DocumentDescriptor(document).to_document_files()
            for doc in docs:
                family_document = doc.get_associated_family(families)
                if not doc.is_multi_series_document:
                    continue
                multi_series_parser = MultiSeriesMarkdownDocumentParser(
                    doc, family_document
                )
                multi_series_parser.reduce_document()
