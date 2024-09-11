import copy
import hashlib
import logging
import re
import signal
import sys
import tempfile
import typing as t
from collections import OrderedDict
from io import StringIO
from pathlib import Path

import panflute
import pypandoc

from src.documents import DocumentFile
from src.mixins import FileHashingMixin, ParserUtilityMixin


class DocumentType(panflute.Doc):
    links: t.List[panflute.Link]
    tables: t.List[panflute.Table]
    headers: t.List[panflute.Header]
    paragraphs: t.List[panflute.Para]


T = t.TypeVar("T", bound="BaseParser")


class BaseParser(FileHashingMixin, ParserUtilityMixin):
    __interned: t.ClassVar[t.List["BaseParser"]] = []
    _signals_registered: t.ClassVar[bool] = False
    logger: logging.Logger = logging.getLogger(
        __name__
    )  # will later be overwritten at the instance level

    @classmethod
    def base_parser_factory(cls, extend_from_cls) -> t.Type["BaseParser"]:
        def walk_bases(bases):
            if not bases:
                return None
            for c in bases:
                if c.__name__ == "BaseParser":
                    return c
                else:
                    return walk_bases(c.__bases__)

        base_cls = walk_bases(cls.__bases__)
        base_cls = t.cast(t.Type["BaseParser"], base_cls)

        class ExtendedBaseParser(extend_from_cls, base_cls):
            pass

        return ExtendedBaseParser

    def __new__(cls, *args, **kwargs):
        logger = logging.getLogger(__name__)
        instance = super().__new__(cls)
        instance.logger = logger
        cls._register_delete_tempdir()
        return instance

    def __init__(
        self, document_file: DocumentFile, family_document_file: DocumentFile
    ) -> None:
        self.document_file = document_file
        self.family_document_file = family_document_file
        self._path = self.document_file.path
        # Create temporary file to save data from document cleanup
        self.file = tempfile.NamedTemporaryFile(delete=False, suffix=".md")
        self.path = Path(self.file.name)
        # Add the file to class-wide list of instances to be cleaned up after the program ends
        self.__class__.__interned.append(self)
        # Clean the document (saving it as a variable, not writing to disk just yet)
        self.content: t.Sequence[str] = self.clean_document()
        # Generate the current hash of the unmodified base-file
        # Depending on the implementation of the subclass this might be non-representative at this point
        self._document_hash = self.generate_document_hash(self._path)
        # ... but a value is needed for the below methods change-detection so we can write to disk
        self.commit_to_tempfile()
        # Now the document itself is parsed from the temporary file that has just been updated
        document = self.parse_file_to_document()
        self.document = self.prepare_document(document)
        self.logger.debug("Document parser initialization complete")
        self._document_hash = self.do_document_hashing()

    def do_document_hashing(self) -> "hashlib._Hash":
        """Generate a representative hash value for the parsed document"""
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.name} ({self.path.name})"

    def __enter__(self: T) -> T:
        return self

    def __exit__(self, *args, **kwargs) -> None:
        self.cleanup()
        cls = self.__class__
        cls.__interned.pop(cls.__interned.index(self))

    def cleanup(self) -> None:
        self.path.unlink(missing_ok=True)

    @classmethod
    def _cleanup_cls(cls, num, _) -> None:
        current_signal = signal.strsignal(num)
        cls.logger.info(f"Detected signal '{current_signal}'")
        cls.logger.info(f"Cleaning up {len(cls.__interned)} temporary document objects")
        for instance in cls.__interned:
            instance.cleanup()
        if num == signal.SIGALRM:
            cls.logger.info("Caught SIGALRM, not exiting")
            return
        cls.logger.info(f"Done, exiting with code {num}")
        sys.exit(0)

    @classmethod
    def _register_delete_tempdir(cls) -> None:
        if cls._signals_registered:
            return
        cls.logger.info(
            "Registering temporary documents cleanup for signals 'SIGTERM' and 'SIGINT'"
        )
        signal.signal(signal.SIGTERM, cls._cleanup_cls)
        signal.signal(signal.SIGINT, cls._cleanup_cls)
        # Register this Signal to cleanup after testing
        signal.signal(signal.SIGALRM, cls._cleanup_cls)

    @property
    def name(self) -> str:
        document_title = self.document.metadata["title"]
        document_title = t.cast(panflute.Header, document_title)
        document_title_content = self.flatten_list_of_lists(
            [
                re.split(r"/|-", self.stringify(elem))
                for elem in document_title.content.list
            ]
        )
        document_title_string_list = [
            s.lower() for s in copy.deepcopy(document_title_content)
        ]
        try:
            # Try first matching by the documents file identifier (good for multi document files with long names)
            index = document_title_string_list.index(self.document_file.identifier)
        except ValueError:
            # For very short names (e.g. just 'm' for 'm-series')
            # try matching by the files name witout extensions instead
            try:
                index = document_title_string_list.index(self.document_file.path.stem)
            except ValueError:
                # Special Case for VM series with accelerators in their names
                document_title_string_list = [s.replace("_", "") for s in document_title_string_list]
                index = document_title_string_list.index(self.document_file.path.stem.split("-")[0])
            match = re.search(r"^([a-zA-Z0-9_]+)-?(?:.+)?$", document_title_content[index])
            assert (
                match
            ), f"A match for the files '{self.document_file.path.stem}' path name could not be found"
            text = match.group(1)
        else:
            text = document_title_content[index]
        return text

    def commit_to_tempfile(self) -> bool:
        self.logger.debug(
            f"Writing {len(self.content)} lines from file '{self._path.name}' to '{self.path.name}'"
        )
        content_bytes = [line.encode() for line in self.content]
        self.file.writelines(content_bytes)
        del content_bytes
        if hasattr(self, "document"):
            hash = self.do_document_hashing()
        else:
            hash = self.generate_document_hash(self.path)
        has_changed = self.document_hash == hash.hexdigest()
        self.document_hash = hash
        return has_changed

    def update_from_tempfile(self) -> None:
        content = self.file.readlines()
        if not content:
            self.file.seek(0)
            content = self.file.readlines()
        self.content = [line.decode() for line in content]

    def parse_file_to_document(self) -> panflute.Doc:
        self.logger.debug("Setting file handle to 0 (start)")
        self.file.seek(0)
        self.logger.debug(f"Converting file '{self.path.name}' to Document")
        data = pypandoc.convert_file(self.path, "json")
        document = panflute.load(StringIO(data))
        del data
        return document

    def prepare_document(self, document: panflute.Doc) -> DocumentType:
        def action(elem, doc):
            if isinstance(elem, panflute.Link):
                doc.links.append(elem)
            if isinstance(elem, panflute.Table):
                doc.tables.append(elem)
            if isinstance(elem, panflute.Header):
                doc.headers.append(elem)
            if isinstance(elem, panflute.Para):
                doc.paragraphs.append(elem)

        def prepare(doc):
            doc.links = []
            doc.tables = []
            doc.headers = []
            doc.paragraphs = []

        self.logger.debug("Prepare document called")
        document = t.cast(
            DocumentType,
            panflute.run_filter(action, prepare=prepare, doc=document),
        )
        return document

    def clean_document(self) -> t.List[str]:
        with open(self._path, "r") as fin:
            _lines = fin.readlines()
        lines = []
        occurences_of_dashes = 0
        next_symbol: t.Optional[str] = None
        for line in _lines:
            if next_symbol and line.lstrip().startswith(next_symbol):
                continue
            elif next_symbol and not line.lstrip().startswith(next_symbol):
                next_symbol = None
            if line.startswith("---") and occurences_of_dashes < 2:
                occurences_of_dashes += 1
            elif line.startswith("---") and occurences_of_dashes >= 2:
                occurences_of_dashes += 1
                continue
            if re.match(r"^<sup>\d</sup>", line.lstrip()):
                continue
            elif line.startswith("**Applies to:** :heavy_check_mark:"):
                continue
            elif line == "> [!NOTE]":
                next_symbol = ">"
                continue
            lines.append(line)
        del _lines
        return lines

    @classmethod
    def _parse_table(
        cls, table: panflute.Table
    ) -> t.Tuple[t.List[str], t.List[t.List[str]]]:
        header_values = [
            re.split(r"\s{2,}|\\n|<[a-z]+>", cls.stringify(cell))[0].strip()
            for cell in table.head.content.list[0].content.list
        ]
        _body_values = [
            [cls.stringify(e) for e in t_.content.list]
            for t_ in table.content.list[0].content.list
        ]
        body_values = []
        for list_of_values in _body_values:
            vals = []
            for value in list_of_values:
                out = cls.split_strings(value)
                vals.append(cls.filter_non_strings(out))
            body_values.append(vals)
        return header_values, body_values

    @classmethod
    def parse_table_rowhead_by_rows(
        cls, table: panflute.Table
    ) -> t.Sequence[t.OrderedDict[str, str]]:
        header_values, body_values = cls._parse_table(table)
        return [
            OrderedDict({k: v for k, v in zip(header_values, row)})
            for row in body_values
        ]

    @classmethod
    def parse_table_rowhead_by_columns(
        cls, table: panflute.Table
    ) -> t.OrderedDict[str, t.Sequence[str]]:
        header_values, body_values = cls._parse_table(table)
        return OrderedDict(
            {
                val: [row[i] for row in body_values]
                for i, val in enumerate(header_values)
            }
        )

    @classmethod
    def parse_table_colhead_rowhead(cls, table: panflute.Table):
        header_values, body_values = cls._parse_table(table)
        entries = OrderedDict()
        # Exclude the header columns key for the header row
        header_values = header_values[1:]
        for row in body_values:
            entries[row[0][0]] = OrderedDict(
                {head_key: row_value for head_key, row_value in zip(header_values, row[1:])}
            )
        return entries

    def retrieve_elem(self, filter_fn):
        try:
            panflute.run_filter(filter_fn, doc=self.document)
        except (StopIteration, RuntimeError) as e:
            if isinstance(e, RuntimeError):
                e = e.__cause__
            if not getattr(e, "value", None):
                raise ValueError from e
            return e.value
        else:
            return None

    def get_header_by_identifier(self, identifier: str):
        def action(elem, doc):
            if isinstance(elem, panflute.Header) and elem.identifier == identifier:
                raise StopIteration(elem)

        return action
