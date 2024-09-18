import copy
import typing as t

from src.azure_types.instances import SkuTypes
from src.azure_types.series import AzureSkuSeriesType
from src.database import MongoDB
from src.documents import DocumentDescriptor, DocumentFile
from src.mixins import ParserUtilityMixin
from src.parsers.utility import document_to_parser

from .shared import BaseTestCase, tag


@tag("series_type")
class TestSeriesTypes(BaseTestCase):
    mongodb: MongoDB

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.mongodb = MongoDB()

    def setUp(self) -> None:
        super().setUp()
        self.documents = ParserUtilityMixin.flatten_list_of_lists(
            [
                DocumentDescriptor(f).to_document_files()
                for f in self.documents_path.iterdir()
            ]
        )
        self.mongodb.drop()

    def tearDown(self):
        super().tearDown()
        self.mongodb.drop()

    def test010_azure_sku_series_database_write(self):
        _, families = self.repository.get_families()
        for document in self.documents[:10]:
            document = t.cast(DocumentFile, document)
            family_document = document.get_associated_family(families)
            parser = document_to_parser(document, family_document)
            family_parser = document_to_parser(family_document, family_document)
            series_type = AzureSkuSeriesType(parser, family_parser)
            changed = series_type.write_to_database()
            _id = copy.copy(series_type._id)
            self.assertTrue(changed)
            changed = series_type.write_to_database()
            self.assertFalse(changed)
            series_type.memory_gb_min = 68
            changed = series_type.write_to_database()
            new_id = copy.copy(series_type._id)
            self.assertTrue(changed)
            self.assertEquals(_id, new_id)

    def test020_azure_sku_series(self):
        _, families = self.repository.get_families()
        for document in self.documents:
            document = t.cast(DocumentFile, document)
            family_document = document.get_associated_family(families)
            parser = document_to_parser(document, family_document)
            family_parser = document_to_parser(family_document, family_document)
            series_type = AzureSkuSeriesType(parser, family_parser)
            # series_type.set_last_updated_azure(self.repository)
            dto = series_type.serialize()
            self.assertTrue(dto)
            __import__("pprint").pprint(dto)
            changed = series_type.write_to_database()
            self.assertTrue(changed)

    def test030_azure_sku_types(self):
        _, families = self.repository.get_families()
        for document in self.documents:
            document = t.cast(DocumentFile, document)
            family_document = document.get_associated_family(families)
            parser = document_to_parser(document, family_document)
            # family_parser = document_to_parser(family_document, family_document)
            sku_types = SkuTypes(parser)
            for sku_type in sku_types:
                # sku_type.set_last_updated_azure(self.repository)
                dto = sku_type.serialize()
                self.assertTrue(dto)
                __import__("pprint").pprint(dto)
                changed = sku_type.write_to_database()
                self.assertTrue(changed)
