import logging
import typing as t
import unittest
from pathlib import Path

from src import constants
from src.repository import DocsSourceRepository

logger = logging.getLogger(__name__)


class TestDocsSourceRepository(unittest.TestCase):
    repository: DocsSourceRepository
    directories: t.List[str]

    @classmethod
    def setUpClass(cls) -> None:
        cls.directories = [
            "compute-optimized",
            "memory-optimized",
            "storage-optimized",
            "high-performance-compute",
            "gpu-accelerated",
            "general-purpose",
            "fpga-accelerated",
        ]
        cls.repository = DocsSourceRepository(
            constants.MS_REPOSITORY_URL,
            constants.MS_REPOSITORY_NAME,
            constants.MS_REPOSITORY_PATH,
        )

    def setUp(self) -> None:
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

    def test010_list_sku_series_directories(self):
        self.assertTrue(
            all(
                [
                    d.name in self.directories
                    for d in self.repository._list_sku_series_directories()
                ]
            )
        )

    def test020_list_sku_series_documents_for_directory(self):
        families = self.repository._list_sku_series_documents_for_directory(
            self.repository_workdir
            / self.directories[self.directories.index("memory-optimized")]
        )

    def test030_get_families_for_directory(self):
        families = self.repository.get_families_for_directory(
            self.repository_workdir
            / self.directories[self.directories.index("memory-optimized")]
        )
        self.assertTrue(len(families) > 1)

    def test040_get_families(self):
        families, family_list = self.repository.get_families()
        self.assertTrue(families)
        self.assertTrue(len(family_list) > 1)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.repository.cleanup()
