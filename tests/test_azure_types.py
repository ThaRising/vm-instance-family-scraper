import typing as t

from src.azure_types.instances import SkuTypes
from src.azure_types.series import AzureSkuSeriesType
from src.documents import DocumentDescriptor, DocumentFile
from src.mixins import ParserUtilityMixin
from src.parsers.utility import document_to_parser

from .shared import BaseTestCase, tag


@tag("series_type")
class TestSeriesTypes(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.documents = ParserUtilityMixin.flatten_list_of_lists(
            [
                DocumentDescriptor(f).to_document_files()
                for f in self.documents_path.iterdir()
            ]
        )

    def test010_azure_sku_series(self):
        _, families = self.repository.get_families()
        for document in self.documents:
            document = t.cast(DocumentFile, document)
            family_document = document.get_associated_family(families)
            parser = document_to_parser(document, family_document)
            family_parser = document_to_parser(family_document, family_document)
            series_type = AzureSkuSeriesType(parser, family_parser)
            dto = series_type.to_dto()
            self.assertTrue(dto)
            __import__("pprint").pprint(dto)

    def test020_azure_sku_types(self):
        _, families = self.repository.get_families()
        for document in self.documents:
            document = t.cast(DocumentFile, document)
            family_document = document.get_associated_family(families)
            parser = document_to_parser(document, family_document)
            family_parser = document_to_parser(family_document, family_document)
            sku_type = SkuTypes(parser)
            dto = sku_type.to_dto()
            self.assertTrue(dto)
            __import__("pprint").pprint(dto)
