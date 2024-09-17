import datetime
import functools
import glob
import logging
import os
import re
import signal
import sys
import tempfile
import typing as t
from pathlib import Path

from git import Git, Repo

from .documents import DocumentDescriptor, DocumentFile
from .mixins import ParserUtilityMixin

logger = logging.getLogger(__name__)


class DocsSourceRepository(ParserUtilityMixin):
    def __init__(
        self,
        repo_url: str,
        repo_name: str,
        repo_relative_path: str,
        repo_branch: str = "main",
    ) -> None:
        self.repo_url = repo_url
        self.repo_name = repo_name
        self.repo_relative_path = repo_relative_path
        self.repo_branch = repo_branch
        logger.info("Create tempdir")
        self.repo_temp_directory = tempfile.TemporaryDirectory()
        self._register_delete_tempdir()
        self.git = Git()
        self.repo_workdir_abs_path: Path = t.cast(Path, None)
        self.documents: t.Dict[Path, t.Dict[DocumentFile, t.List[DocumentFile]]]
        self.repo: t.Optional[Repo] = None

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

    def setup_repository(self, repo_path: Path) -> None:
        self.repo = Repo(repo_path)
        logging.info("Created 'Repo' object for Repository")

    def clone_repository(self, destination_basepath: t.Optional[Path] = None) -> Path:
        repo_path = os.path.join(
            destination_basepath or self.repo_temp_directory.name, self.repo_name
        )
        if destination_basepath:
            logger.info(
                f"'destination_basepath' was set, cloning to '{repo_path}' instead of tempdir"
            )
        logger.info(
            f"Cloning repository '{self.repo_name}' on branch '{self.repo_branch}'"
        )
        logger.warning("Beginning cloning, this might take a while...")
        self.git.clone("--branch", self.repo_branch, self.repo_url, repo_path)
        self.repo_workdir_abs_path = Path(
            os.path.join(repo_path, self.repo_relative_path)
        )
        logging.info("Done cloning repository")
        self.setup_repository(Path(repo_path))
        return self.repo_workdir_abs_path

    def get_documents(
        self,
    ) -> t.List["DocumentFile"]:
        """Discover all SKU series documents while splitting all multi-series documents into distinct series"""
        series_names = [
            fd.to_document_files()
            for f in glob.iglob(
                f"{self.repo_workdir_abs_path.parent}/**/*", recursive=True
            )
            if (fd := DocumentDescriptor(Path(f))).is_series or fd.is_multi_series
        ]
        series_documents_list = self.flatten_list_of_lists(series_names)
        series_documents_list = list(set(series_documents_list))
        series_documents_list = list(sorted(series_documents_list, key=lambda doc: f"{doc.path.parts[-2]}/{doc.path.parts[-1]}"))
        series_documents_list = t.cast(t.List["DocumentFile"], series_documents_list)
        return series_documents_list

    def get_all_files(self) -> t.List[Path]:
        files = glob.iglob(
            f"{self.repo_workdir_abs_path.parent}/**/*", recursive=True
        )
        return list(set(files))

    def get_families_and_associated_documents(
        self,
    ) -> t.Dict[Path, t.Dict["DocumentFile", t.List["DocumentFile"]]]:
        pass

    def get_families(
        self,
    ) -> t.Tuple[t.Dict[Path, t.List["DocumentFile"]], t.List["DocumentFile"]]:
        """
        Discover all family documents inside of the working directory of the repository.
        Return these as a mapping of Folders to Families and a flat list of families, both as documents.
        """
        directories = self._list_sku_directories()
        results: t.Dict[Path, t.List["DocumentFile"]] = {}
        results_list: t.List["DocumentFile"] = []
        for directory in directories:
            families = self.get_families_for_directory(directory)
            results.setdefault(directory, [])
            results[directory].extend(families)
            results_list.extend(families)
        return results, results_list

    def get_families_for_directory(self, directory: Path) -> t.List["DocumentFile"]:
        """Return all family documents inside of a specific folder"""
        _files = [
            entry
            for entry in directory.iterdir()
            if entry.is_file() and entry.suffix == ".md"
        ]
        files = [DocumentDescriptor(entry) for entry in _files]
        families = [
            entry.to_document_file()
            for entry in files
            if not entry.is_exception and entry.is_family
        ]
        return families

    def _list_sku_directories(self) -> t.List[Path]:
        """Return a list of all valid SKU folder paths"""
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

    @functools.lru_cache(maxsize=150)
    def last_commit_for_document(
        self, document_file: DocumentFile
    ) -> datetime.datetime:
        assert self.repo
        for commit in self.repo.iter_commits(self.repo_branch):
            commit_files = [Path(c) for c in commit.stats.files.keys()]
            if document_file.path.relative_to(self.repo.working_dir) in commit_files:
                commit_time = datetime.datetime.fromtimestamp(commit.committed_date)
                return commit_time
        raise ValueError("No commit found for file, aborting")
