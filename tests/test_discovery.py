import glob
from pathlib import Path

from src.documents import DocumentDescriptor
from src.mixins import ParserUtilityMixin
from src.parsers.families import FamilyMarkdownDocumentParser
from src.parsers.utility import document_to_parser

from .shared import BaseTestCase


class TestDocumentDiscovery(BaseTestCase):
    def test010_discover_families(self):
        _, discovered_families_list = self.repository.get_families()
        discovered_families_names = [f.path.name for f in discovered_families_list]
        ls_families_list = [
            Path(f).name
            for f in glob.iglob(
                f"{self.repository.repo_workdir_abs_path.parent}/**/*", recursive=True
            )
            if DocumentDescriptor(Path(f)).is_family
        ]
        self.assertEqual(
            list(sorted(discovered_families_names)), list(sorted(ls_families_list))
        )

    def test020_discover_series(self):
        series_names = [
            fd.to_document_files()
            for f in glob.iglob(
                f"{self.repository.repo_workdir_abs_path.parent}/**/*", recursive=True
            )
            if (fd := DocumentDescriptor(Path(f))).is_series or fd.is_multi_series
        ]
        series_list = ParserUtilityMixin.flatten_list_of_lists((series_names))
        series_list = list(set(series_list))
        series_names_list = list(
            sorted(
                [(doc.identifier, doc, doc.path.parts[-3:]) for doc in series_list],
                key=lambda l: l[0],
            )
        )
        self.assertEqual(len(series_list), len(set(series_names_list)))
        __import__("pprint").pprint(series_names_list)

    def test030_series_family_recognition(self):
        series_documents_list = self.repository.get_documents()
        _, family_documents_list = self.repository.get_families()
        series_to_family_mapping = {
            series_document: series_document.get_associated_family(
                family_documents_list
            )
            for series_document in series_documents_list
        }
        family_to_series_mapping = {
            family_document: FamilyMarkdownDocumentParser(
                family_document, family_document
            ).get_children()
            for family_document in family_documents_list
        }
        family_document_child_series = [
            document
            for series_documents in family_to_series_mapping.values()
            for document in series_documents
        ]
        self.assertNotEqual(
            len(series_to_family_mapping), len(family_document_child_series)
        )
        series_documents_without_direct_parent = len(series_to_family_mapping) - len(
            family_document_child_series
        )
        previous_gen_series = [
            doc
            for doc, family in series_to_family_mapping.items()
            if document_to_parser(doc, family).is_previous_generation
        ]
        self.assertEqual(
            series_documents_without_direct_parent, len(previous_gen_series)
        )
