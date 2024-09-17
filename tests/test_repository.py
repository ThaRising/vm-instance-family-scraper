import typing as t

from .shared import BaseTestCase, tag


@tag("repository")
class TestDocsSourceRepository(BaseTestCase):
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
        super().setUpClass()

    def test010_list_sku_directories(self):
        self.assertTrue(
            all(
                [
                    d.name in self.directories
                    for d in self.repository._list_sku_directories()
                ]
            )
        )

    def test020_list_sku_series_documents_for_directory(self):
        families = self.repository._list_sku_series_documents_for_directory(
            self.repository_workdir
            / self.directories[self.directories.index("memory-optimized")]
        )
        self.assertTrue(families)

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

    def test050_get_file_changed_timestamp(self):
        documents = self.repository.get_documents()
        for document in documents[:10]:
            timestamp = self.repository.last_commit_for_document(document)
            print(timestamp)
            self.assertTrue(timestamp)
        # Ensure the lru_cache is working
        for document in documents[:10]:
            timestamp = self.repository.last_commit_for_document(document)
            print(timestamp)
            self.assertTrue(timestamp)

    def test060_get_file_changed_index(self):
        self.repository.generate_last_commit_index()
