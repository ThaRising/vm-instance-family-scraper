import logging
import unittest
from pathlib import Path

from src import constants
from src.azure_types import SkuTypes
from src.documents import DocumentDescriptor
from src.families import SkuFamilyDocument
from src.repository import DocsSourceRepository
from src.series import SkuSeriesDocument

logger = logging.getLogger(__name__)


class TestSkuFamilyDocument(unittest.TestCase):
    repository: DocsSourceRepository

    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = DocsSourceRepository(
            constants.MS_REPOSITORY_URL,
            constants.MS_REPOSITORY_NAME,
            constants.MS_REPOSITORY_PATH,
        )

    def setUp(self) -> None:
        self.cls = DocumentDescriptor
        current_path = Path(__file__).parent
        clone_basepath = current_path / "data"
        if not (clone_basepath / self.repository.repo_name).exists():
            self.repository_workdir = self.repository.clone_repository(clone_basepath)
        else:
            logger.debug("Repo already exists, not cloning again")
            self.repository_workdir = (
                clone_basepath
                / self.repository.repo_name
                / self.repository.repo_relative_path
            )
            self.repository.repo_workdir_abs_path = self.repository_workdir

    def test010_get_children(self):
        _, families = self.repository.get_families()
        for family in families:
            fam = SkuFamilyDocument(family)
            __import__("pprint").pprint(fam.children)

    def test020_export_children_data(self):
        _, families = self.repository.get_families()
        for family in families:
            fam = SkuFamilyDocument(family)
            for series in fam.children:
                sku = SkuSeriesDocument(series, fam.document_file)
                print(sku.name)
                __import__("pprint").pprint(SkuTypes(sku).instance_attributes)
                specs_document = sku.get_host_specs_document()
                specs_table = specs_document.parse_table_head_column(
                    specs_document.tables[0]
                )
                print(sku.get_capabilities())
                print(f"Confidential: {sku.is_confidential()}")
                __import__("pprint").pprint(specs_table)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.repository.cleanup()
