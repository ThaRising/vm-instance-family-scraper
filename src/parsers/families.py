import hashlib
import typing as t
from functools import lru_cache
from pathlib import Path
import re

import panflute

from src.documents import DocumentDescriptor, DocumentFile

from .shared import BaseParser


class FamilyMarkdownDocumentParser(BaseParser):
    def __init__(
        self, document_file: DocumentFile, family_document_file: DocumentFile
    ) -> None:
        assert document_file.is_family
        assert document_file is family_document_file
        super().__init__(document_file, family_document_file)
        self.sections = list(self.get_sections())

    @property
    def name(self) -> str:
        return self.document_file.identifier.upper()

    def do_document_hashing(self) -> "hashlib._Hash":
        return self.generate_document_hash(self.path)

    def get_sections(self) -> t.Generator[panflute.Header, None, None]:
        start_header = [
            h for h in self.document.headers if h.identifier == "series-in-family"
        ]
        assert len(start_header) == 1
        start_index = self.document.headers.index(start_header[0]) + 1
        for header in self.document.headers[start_index:]:
            identifier = header.identifier
            if (
                "series" in identifier
                and "previous-gen" not in identifier
                and not isinstance(header.next, panflute.Header)
            ):
                yield header

    @lru_cache(maxsize=1)
    def get_children(self) -> t.List[DocumentFile]:
        children = []
        for section in self.sections:
            link = section.next.next.content.list[0]  # type: ignore
            assert isinstance(link, panflute.Link)
            path = self._path.parent / link.url
            if not path.resolve().exists():
                path = Path(*[p for p in path.parts if p != ".."])
            if not path.resolve().exists():
                _file_identifier = re.search(r"^(?P<main>[a-zA-Z-\d]+)\s?(?P<version>v\d)-series$", self.stringify(section))
                file_identifier = f"{_file_identifier.group('main')}{_file_identifier.group('version') or ''}"
                file_identifier = re.sub(r"\s|-|_", "", file_identifier).lower()
                path = path.parent / f"{file_identifier}-series.md"
            assert path.resolve().exists()
            children.append(DocumentDescriptor(path).to_document_files())
        _children = self.flatten_list_of_lists(children)
        return _children
