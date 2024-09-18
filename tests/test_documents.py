import logging

from .shared import BaseTestCase, tag

logger = logging.getLogger(__name__)


@tag("document_descriptor")
class TestDocumentDescriptor(BaseTestCase):
    test_files: list

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_files = [
            (
                "memory-optimized/mbsv3-mbdsv3-series.md",
                {
                    "is_series": False,
                    "is_family": False,
                    "is_multi_series": True,
                    "identifiers": ["mbsv3", "mbdsv3"],
                },
            ),
            (
                "memory-optimized/epdsv5-series.md",
                {
                    "is_series": True,
                    "is_family": False,
                    "is_multi_series": False,
                    "identifiers": ["epdsv5"],
                },
            ),
            (
                "memory-optimized/eb-family.md",
                {
                    "is_series": False,
                    "is_family": True,
                    "is_multi_series": False,
                    "identifiers": ["eb"],
                },
            ),
            (
                "memory-optimized/dv2-dsv2-series-memory.md",
                {
                    "is_series": False,
                    "is_family": False,
                    "is_multi_series": False,
                    "identifiers": [],
                },
            ),
        ]
        super().setUpClass()

    def test010_attribute_detection(self):
        for relative_filepath, attrs in self.test_files:
            path = self.repository_workdir / relative_filepath
            doc = self.cls(path)
            doc_identifier = doc.identifier
            self.assertEqual(doc.is_series, attrs["is_series"])
            self.assertEqual(doc.is_family, attrs["is_family"])
            self.assertEqual(doc.is_multi_series, attrs["is_multi_series"])
            self.assertTrue(all(i in doc_identifier for i in attrs["identifiers"]))
            logger.debug(f"Document '{relative_filepath}' passes")

    def test020_to_document_file(self):
        for relative_filepath, attrs in self.test_files:
            path = self.repository_workdir / relative_filepath
            doc = self.cls(path)
            logger.debug(f"Running for document '{relative_filepath}'")
            if attrs["is_family"] or attrs["is_series"]:
                self.assertTrue(doc.to_document_file())
            else:
                with self.assertRaises(AssertionError):
                    doc.to_document_file()

    def test030_to_document_files(self):
        for relative_filepath, attrs in self.test_files:
            path = self.repository_workdir / relative_filepath
            doc = self.cls(path)
            logger.debug(f"Running for document '{relative_filepath}'")
            if attrs["is_family"] or attrs["is_series"]:
                documents = doc.to_document_files()
                self.assertEqual(len(documents), 1)
            elif attrs["is_multi_series"]:
                documents = doc.to_document_files()
                self.assertEqual(len(documents), 2)
            else:
                documents = doc.to_document_files()
                self.assertEqual(len(documents), 0)
