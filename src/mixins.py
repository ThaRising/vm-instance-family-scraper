import hashlib
import re
import typing as t
from pathlib import Path

import panflute


class FileHashingMixin:
    BUF_SIZE: t.ClassVar[int] = 65536
    _document_hash: "hashlib._Hash"

    def generate_document_hash(self, path: Path) -> "hashlib._Hash":
        sha256 = hashlib.sha256()
        with open(path, "rb") as fin:
            while True:
                data = fin.read(self.BUF_SIZE)
                if not data:
                    break
                sha256.update(data)
        return sha256

    def generate_hash(self, str_or_bytes: t.Union[str, bytes]) -> "hashlib._Hash":
        if not isinstance(str_or_bytes, bytes):
            str_or_bytes = t.cast(str, str_or_bytes)  # type: ignore
            str_or_bytes = str_or_bytes.encode()
        sha256 = hashlib.sha256(str_or_bytes)
        return sha256

    def file_is_different(self, new_file_path: Path) -> bool:
        return (
            self.document_hash == self.generate_document_hash(new_file_path).hexdigest()
        )

    @property
    def document_hash(self) -> str:
        return self._document_hash.hexdigest()

    @document_hash.setter
    def document_hash(self, val: "hashlib._Hash") -> None:
        self._document_hash = val


class ParserUtilityMixin:
    @staticmethod
    def clean_string(elem: str) -> str:
        return re.sub(r"\s{2,}", " ", elem.strip())

    @classmethod
    def stringify(cls, elem):
        if isinstance(elem, str):
            return cls.clean_string(elem)
        val = panflute.stringify(elem)
        val = t.cast(str, val)
        return cls.clean_string(val)

    @classmethod
    def split_strings(cls, elem: str) -> t.List[str]:
        elements = re.split(r"<[a-z]+>|\\n|/", elem)
        elements = [e for e in elements if e]
        elements = [cls.clean_string(e) for e in elements]
        return elements

    @classmethod
    def filter_non_strings(cls, elem: t.List[str]) -> t.List[str]:
        return [e for e in elem if not re.match(r"^[\d,]+<\/sup>$", e)]

    @staticmethod
    def flatten_list_of_lists(lst: t.List[t.List[t.Any]]) -> t.List[t.Any]:
        return [item for sublist in lst for item in sublist]
