import typing as t

from src.documents import DocumentDescriptor, DocumentFile
from src.mixins import ParserUtilityMixin
from src.parsers.utility import document_to_parser

from .shared import BaseTestCase, tag


@tag("series")
class TestSeriesDocumentParsers(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.documents = ParserUtilityMixin.flatten_list_of_lists(
            [
                DocumentDescriptor(f).to_document_files()
                for f in self.documents_path.iterdir()
            ]
        )

    def test010_host_summary(self):
        _, families = self.repository.get_families()
        for document in self.documents:
            document = t.cast(DocumentFile, document)
            family_document = document.get_associated_family(families)
            parser = document_to_parser(document, family_document)
            self.assertTrue(parser.host_summary)

    def test020_host_specs(self):
        _, families = self.repository.get_families()
        for document in self.documents:
            document = t.cast(DocumentFile, document)
            family_document = document.get_associated_family(families)
            parser = document_to_parser(document, family_document)
            print(parser.host_specs_table)
            self.assertTrue(parser.host_specs_table)

    def test030_host_specs(self):
        _, families = self.repository.get_families()
        for document in self.documents:
            document = t.cast(DocumentFile, document)
            family_document = document.get_associated_family(families)
            parser = document_to_parser(document, family_document)
            print(parser.get_associated_instance_names())

    def test040_host_specs(self):
        _, families = self.repository.get_families()
        for document in self.documents:
            document = t.cast(DocumentFile, document)
            family_document = document.get_associated_family(families)
            parser = document_to_parser(document, family_document)
            print(parser.capabilities)
