import logging
import os
import re
import signal
import sys
import tempfile
import typing as t
from pathlib import Path

from git import Git

from .documents import DocumentDescriptor
from .documents import DocumentFile

logger = logging.getLogger(__name__)


class DocsSourceRepository:
    def __init__(self, repo_url: str, repo_name: str, repo_relative_path: str) -> None:
        self.repo_url = repo_url
        self.repo_name = repo_name
        self.repo_relative_path = repo_relative_path
        logger.info("Create tempdir")
        self.repo_temp_directory = tempfile.TemporaryDirectory()
        self._register_delete_tempdir()
        self.git = Git()
        self.repo_workdir_abs_path: Path = t.cast(Path, None)
        self.documents: t.Dict[Path, t.Dict[DocumentFile, t.List[DocumentFile]]]

    def cleanup(self) -> None:
        logger.info(f"Cleaning up tempdir '{self.repo_temp_directory.name}'")
        self.repo_temp_directory.cleanup()

    def _cleanup_repo_temp_directory(self, num, _) -> None:
        current_signal = signal.strsignal(num)
        logger.info(f"Detected signal '{current_signal}")
        self.cleanup()
        logger.info(f"Done, exiting with code {num}")
        sys.exit(num)

    def _register_delete_tempdir(self) -> None:
        logger.info("Registering tempdir cleanup for signals 'SIGTERM' and 'SIGINT'")
        signal.signal(signal.SIGTERM, self._cleanup_repo_temp_directory)
        signal.signal(signal.SIGINT, self._cleanup_repo_temp_directory)

    def clone_repository(self, destination_basepath: t.Optional[Path] = None) -> Path:
        repo_path = os.path.join(
            destination_basepath or self.repo_temp_directory.name, self.repo_name
        )
        if destination_basepath:
            logger.info(
                f"'destination_basepath' was set, cloning to '{repo_path}' instead of tempdir"
            )
        logger.info(
            f"Cloning repository '{self.repo_name}' with depth of 1 on branch 'main'"
        )
        self.git.clone("--depth", "1", "--branch", "main", self.repo_url, repo_path)
        self.repo_workdir_abs_path = Path(
            os.path.join(repo_path, self.repo_relative_path)
        )
        logging.info("Done cloning repository")
        return self.repo_workdir_abs_path

    def get_documents(
        self,
    ) -> t.Dict[Path, t.Dict["DocumentFile", t.List["DocumentFile"]]]:
        directories = self._list_sku_series_directories()
        self.documents = {
            dir: self._list_sku_series_documents_for_directory(dir)
            for dir in directories
        }
        return self.documents

    def get_families(
        self,
    ) -> t.Tuple[t.Dict[Path, t.List["DocumentFile"]], t.List["DocumentFile"]]:
        directories = self._list_sku_series_directories()
        results: t.Dict[Path, t.List["DocumentFile"]] = {}
        results_list: t.List["DocumentFile"] = []
        for directory in directories:
            families = self.get_families_for_directory(directory)
            results.setdefault(directory, [])
            results[directory].extend(families)
            results_list.extend(families)
        return results, results_list

    def get_families_for_directory(self, directory: Path) -> t.List["DocumentFile"]:
        _files = [
            entry
            for entry in directory.iterdir()
            if entry.is_file() and entry.name.endswith(".md")
        ]
        files = [DocumentDescriptor(entry) for entry in _files]
        families = [
            entry.to_document_file()
            for entry in files
            if not entry.is_exception and entry.is_family
        ]
        return families

    def _list_sku_series_directories(self) -> t.List[Path]:
        all_subdirectories = [
            entry
            for entry in Path(self.repo_workdir_abs_path).iterdir()
            if entry.is_dir()
        ]
        return [
            entry
            for entry in all_subdirectories
            if re.match(r"^(?!migration)([a-z]*?-[a-z-]+)$", entry.name)
        ]

    @staticmethod
    def flatten_list_of_lists(lst: t.List[t.List[t.Any]]) -> t.List[t.Any]:
        return [item for sublist in lst for item in sublist]

    def _list_sku_series_documents_for_directory(
        self, directory: Path
    ) -> t.Dict["DocumentFile", t.List["DocumentFile"]]:
        _files = [
            entry
            for entry in directory.iterdir()
            if entry.is_file() and entry.name.endswith(".md")
        ]
        files = [DocumentDescriptor(entry) for entry in _files]
        results: t.Dict[DocumentFile, t.List[DocumentFile]] = {}
        families = [
            entry.to_document_file()
            for entry in files
            if not entry.is_exception and entry.is_family
        ]
        for family in families:
            results.setdefault(family, [])
        series = self.flatten_list_of_lists(
            [
                entry_docs
                for entry in files
                if (entry.is_series or entry.is_multi_series)
                and (entry_docs := entry.to_document_files())
            ]
        )
        for s in series:
            family = s.get_associated_family(families)
            results[family].append(s)
        return results
