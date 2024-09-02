import io
import logging
import re
import typing as t
from collections import OrderedDict

import panflute
import pypandoc

from .documents import DocumentFile

logger = logging.getLogger(__name__)


class MarkdownDocumentParserDoctype(panflute.Doc):
    links: t.List[panflute.Link]
    tables: t.List[panflute.Table]
    headers: t.List[panflute.Header]
    paragraphs: t.List[panflute.Para]


class MarkdownDocumentParser:
    def __init__(self, document: DocumentFile) -> None:
        self.document_file = document
        self.document_path = self.document_file.path
        logger.debug(f"Reading document {self.document_file}")
        logger.debug(f"Reading path {self.document_path}")
        data = self.parse_file()
        self.document = panflute.load(io.StringIO(data))
        self.document = t.cast(
            MarkdownDocumentParserDoctype,
            panflute.run_filter(self.action, prepare=self.prepare, doc=self.document),
        )

    def parse_file(self):
        try:
            data = pypandoc.convert_file(self.document_path, "json")
        except RuntimeError as e:
            logger.warning(f"Error parsing file {self.document_path}: {e}")
            logger.warning(e.args)
            if "yaml parse exception" in e.args[0].lower():
                logger.warning("Attempting to fix YAML parse exception")
                with open(self.document_path, "r") as fin:
                    _lines = fin.readlines()
                lines = []
                occurences_of_dashes = 0
                for line in _lines:
                    if line.startswith("---") and occurences_of_dashes < 2:
                        occurences_of_dashes += 1
                    elif line.startswith("---") and occurences_of_dashes >= 2:
                        occurences_of_dashes += 1
                        continue
                    lines.append(line)
                with open(self.document_path, "w") as fout:
                    fout.writelines(lines)
                return self.parse_file()
            raise e
        return data

    @property
    def links(self):
        return self.document.links

    @property
    def tables(self):
        return self.document.tables

    @property
    def headers(self):
        return self.document.headers

    @staticmethod
    def action(elem, doc):
        if isinstance(elem, panflute.Link):
            doc.links.append(elem)
        if isinstance(elem, panflute.Table):
            doc.tables.append(elem)
        if isinstance(elem, panflute.Header):
            doc.headers.append(elem)

    @staticmethod
    def prepare(doc):
        doc.links = []
        doc.tables = []
        doc.headers = []

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

    def retrieve_first_elem_of_type(self, elem_type, elements):
        return [elem for elem in elements if isinstance(elem, elem_type)][0]

    def retrieve_all_elems_of_type(self, elem_type, elements):
        return [elem for elem in elements if isinstance(elem, elem_type)]

    def get_header_by_identifier(self, identifier: str):
        def action(elem, doc):
            if isinstance(elem, panflute.Header) and elem.identifier == identifier:
                raise StopIteration(elem)

        return action

    @staticmethod
    def clean_string(elem: str) -> str:
        return re.sub(r"\s{2,}", " ", elem.strip())

    @classmethod
    def stringify(cls, elem):
        val = panflute.stringify(elem)
        val = t.cast(str, val)
        return cls.clean_string(val)

    @classmethod
    def split_strings(cls, elem: str) -> t.List[str]:
        elements = re.split(r"<[a-z]+>|\\n", elem)
        elements = [e for e in elements if e]
        elements = [cls.clean_string(e) for e in elements]
        return elements

    @classmethod
    def filter_non_strings(cls, elem: t.List[str]) -> t.List[str]:
        return [e for e in elem if not re.match(r"^[\d,]+<\/sup>$", e)]

    @classmethod
    def parse_table(
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

    @staticmethod
    def flatten_list_of_lists(lst: t.List[t.List[t.Any]]) -> t.List[t.Any]:
        return [item for sublist in lst for item in sublist]

    @classmethod
    def parse_table_head_row(
        cls, table: panflute.Table, clean_header_vals_fn=None
    ) -> t.Tuple[t.List[OrderedDict[str, str]], t.Dict[str, t.List[str]]]:
        header_values, body_values = cls.parse_table(table)
        if clean_header_vals_fn:
            header_values = [clean_header_vals_fn(val) for val in header_values]
        tbl = [
            OrderedDict({k: v for k, v in zip(header_values, row)})
            for row in body_values
        ]
        listing = OrderedDict(
            {
                val: [row[i] for row in body_values]
                for i, val in enumerate(header_values)
            }
        )
        return tbl, listing

    @classmethod
    def parse_table_head_column(
        cls, table: panflute.Table, clean_header_vals_fn=None
    ) -> OrderedDict[str, t.List[str]]:
        header_values, body_values = cls.parse_table(table)
        if clean_header_vals_fn:
            header_values = [clean_header_vals_fn(val) for val in header_values]
        tbl = OrderedDict({row[0][0]: row[1:] for row in body_values})
        return tbl
