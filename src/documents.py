import logging
import os
import re
import typing as t
from pathlib import Path

from .mixins import FileHashingMixin

logger = logging.getLogger(__name__)


class DocumentDescriptor:
    EXCEPTION_FILES = ["dv2-dsv2-series-memory.md", "nccadsh100v5-series.md"]
    series_regex = re.compile(r"^([a-z\d]+)-?(v\d)?-series(?:\.md)?$")
    multi_series_regex = re.compile(
        r"^([a-z\d]+)-(?!v\d)([a-z\d]+)(?:-[a-z]*?)?-series(?:\.md)?$"
    )
    family_regex = re.compile(r"^([a-z]+)-family\.[a-z]{1,3}$")

    def __init__(self, path: Path) -> None:
        self.path = path
        name = self.path.name
        self.is_series = bool(self.series_regex.match(name))
        series_name_match = t.cast(re.Match, self.series_regex.search(name))
        self.series_name = series_name_match.group(1) if self.is_series else None
        if self.is_series and (name_suffix := series_name_match.group(2)):
            self.series_name = self.series_name + name_suffix
        self.is_family = bool(self.family_regex.match(name))
        self.family_name = None
        if self.is_family:
            assert not self.is_series
            family_name = self.family_regex.search(name)
            family_name = t.cast(re.Match, family_name)
            self.family_name = family_name.group(1)
        self.is_multi_series = bool(self.multi_series_regex.match(name))
        self.series_names = None
        if self.is_multi_series:
            assert not self.is_series
            assert not self.is_family
            series_names = self.multi_series_regex.search(name)
            series_names = t.cast(re.Match, series_names)
            self.series_names = [series_names.group(1), series_names.group(2)]

    def __repr__(self) -> str:
        return self.path.name

    @property
    def is_exception(self) -> bool:
        is_exception = self.path.name in self.EXCEPTION_FILES
        if is_exception:
            logger.info(
                f"File '{os.path.join(*self.path.parts[-3:])}' matches EXCEPTION_FILES"
            )
        return is_exception

    @property
    def identifier(self) -> t.List[str]:
        if self.is_exception:
            return []
        if self.is_family:
            return [t.cast(str, self.family_name)]
        elif self.is_series and not self.is_multi_series:
            return [t.cast(str, self.series_name)]
        elif not self.is_series and self.is_multi_series:
            return t.cast(t.List[str], self.series_names)
        else:
            return [self.path.name.replace(".md", "")]

    def to_document_file(
        self, identifier_: t.Optional[t.List[str]] = None
    ) -> "DocumentFile":
        assert not self.is_exception
        identifier = identifier_ or self.identifier
        assert len(identifier) == 1
        return DocumentFile(
            self.path,
            self.is_series or self.is_multi_series,
            self.is_family,
            self.is_multi_series,
            identifier[0],
        )

    def to_document_files(self) -> t.List["DocumentFile"]:
        if self.is_exception:
            return []
        identifier = self.identifier
        return [self.to_document_file([id_]) for id_ in identifier]


class DocumentFile(FileHashingMixin):
    def __init__(
        self,
        path: Path,
        is_series: bool,
        is_family: bool,
        is_multi_series_document: bool,
        identifier: str,
    ) -> None:
        self.path = path
        self.is_series = is_series
        self.is_family = is_family
        self.is_multi_series_document = is_multi_series_document
        self.identifier = identifier
        self._document_hash = self.generate_document_hash(self.path)

    @property
    def name(self) -> str:
        return self.path.name

    def __repr__(self) -> str:
        if not self.is_family:
            return f"{self.identifier} ({self.name})"
        return self.name

    @property
    def series_name(self) -> t.Optional[str]:
        return self.identifier if self.is_series else None

    @property
    def family_name(self) -> t.Optional[str]:
        return self.identifier if self.is_family else None

    @t.overload
    def get_associated_family(
        self, family_paths: t.Sequence["DocumentFile"]
    ) -> "DocumentFile": ...

    @t.overload
    def get_associated_family(self, family_paths: t.Sequence[Path]) -> Path: ...

    def get_associated_family(
        self, family_paths: t.Sequence[t.Union["DocumentFile", Path]]
    ) -> t.Union["DocumentFile", Path]:
        """Get the document of the family associated with this SKU series document"""
        cls = self.__class__
        assert len(family_paths)
        if not (input_was_native := isinstance(family_paths[0], cls)):
            family_paths = t.cast(t.Sequence[Path], family_paths)
            family_paths = [
                DocumentDescriptor(f).to_document_file() for f in family_paths
            ]
        family_paths = t.cast(t.Sequence[DocumentFile], family_paths)
        if not self.is_series:
            return self if input_was_native else self.path
        assert all([f.is_family for f in family_paths])
        sorted_family_paths = sorted(
            family_paths, key=lambda entry: len(entry.path.name), reverse=True
        )
        for family in sorted_family_paths:
            family_name = t.cast(str, family.family_name)
            series_name = t.cast(str, self.series_name)
            if series_name.startswith(family_name):
                if input_was_native:
                    return family
                else:
                    return family.path
        raise Exception("No matching family present")
