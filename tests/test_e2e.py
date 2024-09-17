import typing as t

from src.azure_types.instances import SkuTypes
from src.parsers.series import SeriesMarkdownDocumentParser
from src.parsers.utility import document_to_parser

from .shared import BaseTestCase, tag


@tag("e2e")
class TestEndToEnd(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.documents = self.repository.get_documents()
        _, self.families = self.repository.get_families()

    def test010_end_to_end(self):
        self.repository.generate_last_commit_index()
        for document in self.documents:
            family_document = document.get_associated_family(self.families)
            parser = document_to_parser(document, family_document)
            parser = t.cast(SeriesMarkdownDocumentParser, parser)
            dto = parser.to_type
            if dto:
                dto.set_last_updated_azure(self.repository)
                __import__("pprint").pprint(dto.to_dto())
            sku_types = SkuTypes(parser)
            __import__("pprint").pprint(sku_types.to_dto())
