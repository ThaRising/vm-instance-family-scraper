import copy
import itertools
import logging
import re
import typing as t
from collections import OrderedDict

import panflute

from .abstract import MarkdownDocumentProps
from .documents import DocumentDescriptor, DocumentFile
from .families import SkuFamilyDocument
from .parser import MarkdownDocumentParser, MarkdownDocumentParserDoctype

logger = logging.getLogger(__name__)


class SkuSeriesDocument(MarkdownDocumentParser, MarkdownDocumentProps):
    document: MarkdownDocumentParserDoctype

    def __init__(self, document: DocumentFile, family_document: DocumentFile) -> None:
        super().__init__(document)
        self.family_document = family_document

    @property
    def name(self) -> str:
        document_title = self.document.metadata["title"]
        document_title = t.cast(panflute.Header, document_title)
        document_title_content = self.flatten_list_of_lists(
            [
                re.split(r"/", self.stringify(elem))
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
            index = document_title_string_list.index(self.document_file.path.stem)
            match = re.search(r"^([a-zA-Z0-9]+)-.+$", document_title_content[index])
            assert (
                match
            ), f"A match for the files '{self.document_file.path.stem}' path name could not be found"
            text = match.group(1)
        else:
            text = document_title_content[index]
        return text

    def get_host_specs_document(self) -> "SkuSeriesDocument":
        cls = self.__class__
        header = self.retrieve_elem(
            self.get_header_by_identifier("host-specifications")
        )
        if self.document_file.is_multi_series_document or header is None:
            if not self.document_file.is_multi_series_document:
                logger.info(
                    f"No header found for document '{self.document_file.path.name}'"
                )
            family = SkuFamilyDocument(self.family_document)
            headers_iexact = [
                section
                for section in family.sections
                if self.name.lower() in section.identifier
            ]
            assert headers_iexact
            headers_exact = [
                h
                for h in headers_iexact
                if h.identifier == self.document_file.path.stem
            ]
            headers = headers_exact or headers_iexact
            assert len(headers) == 1
            header = headers[0]
            next_elem = header.next
            while not isinstance(next_elem, panflute.Header):
                if hasattr(next_elem.content, "list"):
                    link = self.retrieve_first_elem_of_type(panflute.Link, next_elem.content.list)  # type: ignore
                    if self.name.lower() in link.url and "specs" in link.url:
                        host_specs_document = DocumentDescriptor(
                            self.family_document.path.resolve().parent / link.url
                        )
                        return cls(
                            host_specs_document.to_document_file(), self.family_document
                        )
                next_elem = next_elem.next
            return self
        header = t.cast(panflute.Header, header)
        link = self.retrieve_first_elem_of_type(panflute.Link, header.next.content.list)  # type: ignore
        host_specs_document = DocumentDescriptor(
            self.document_file.path.resolve().parent / link.url
        )
        return cls(host_specs_document.to_document_file(), self.family_document)

    def get_host_specs_table(self) -> t.List[OrderedDict[str, t.List[str]]]:
        specs_document = self.get_host_specs_document()
        specs_table = specs_document.parse_table_head_column(specs_document.tables[0])
        return specs_table

    def get_associated_instance_names(self) -> t.List[str]:
        if self.document_file.is_multi_series_document:
            table_headers = [
                h for h in self.headers if self.name.lower() in h.identifier
            ]
            assert table_headers
            tables = []
            for header in table_headers:
                # Check if the next element after the header is a table
                if isinstance(header.next, panflute.Table):
                    tables.append(header.next)
                # Check if the previous element before the header after this one is a table
                elif (
                    prev := self.headers[self.headers.index(header) + 1].prev
                ) and isinstance(prev, panflute.Table):
                    tables.append(prev)
            assert tables
            assert all([isinstance(t, panflute.Table) for t in tables])
        else:
            tables = [self.document.tables[0]]
        for table in tables:
            _, listing = self.parse_table_head_row(
                table, lambda v: v.strip().split()[0].lower()
            )
            if "size" in listing.keys():
                return self.flatten_list_of_lists(listing["size"])
        raise ValueError("No valid tables were found")

    def get_host_summary_document(self) -> "SkuSeriesDocument":
        cls = self.__class__
        links = [
            lnk
            for lnk in self.document.links
            if "summary" in (url := lnk.url) and "includes" in url
        ]
        if self.document_file.is_multi_series_document:
            return self
        elif not links:
            logger.info(
                f"No summary document link found for document {self.document_file.path.name}"
            )
            return self
        assert not len(links) > 1
        link = links[0]
        link = t.cast(panflute.Link, link)
        host_summary_document = DocumentDescriptor(
            self.document_file.path.parent / link.url
        )
        return cls(host_summary_document.to_document_file(), self.family_document)

    def get_host_summary(self) -> str:
        def prepare(doc):
            doc.paragraphs = []

        def get_paragraphs(elem, doc):
            if isinstance(elem, panflute.Para):
                doc.paragraphs.append(elem)

        summary_document = self.get_host_summary_document()
        doc = panflute.run_filter(
            get_paragraphs, prepare=prepare, doc=summary_document.document
        )
        doc = t.cast(MarkdownDocumentParserDoctype, doc)
        if summary_document is self:
            index = 0
            next_elem = doc.paragraphs[index]
            while isinstance(next_elem, panflute.Para):
                next_elem = next_elem.next
                index += 1
            summary_paragraphs = doc.paragraphs[:index]
            return " ".join([panflute.stringify(s).strip() for s in summary_paragraphs])
        return self.stringify(doc.paragraphs[0])

    def is_confidential(self) -> bool:
        summary = self.get_host_summary()
        return "confidential" in summary.lower()

    def get_capabilities(self) -> t.List[str]:
        def group_and_format_capabilities(c):
            c_ = [
                list(y)
                for x, y in itertools.groupby(
                    c, lambda z: isinstance(z, panflute.RawInline)
                )
                if not x
            ]
            return [
                " ".join([val for v in capability if (val := self.stringify(v))])
                for capability in c_
            ]

        header = self.retrieve_elem(self.get_header_by_identifier("feature-support"))
        if header:
            capability_list = header.next.content.list
            capabilities = group_and_format_capabilities(capability_list)
        else:
            headers = [
                h
                for h in self.headers[1:]
                if (self.name.lower() in h.identifier and "series" in h.identifier)
            ]
            if not headers:
                header = self.headers[0]
            else:
                header = headers[0]
            next_elem = header.next
            while not isinstance(next_elem, panflute.Header):
                if panflute.stringify(next_elem).lower().count("supported") >= 4:
                    capability_list = (
                        next_elem.content.list
                        if isinstance(next_elem, panflute.Para)
                        else next_elem.next.content.list
                    )
                    break
                next_elem = next_elem.next
            capability_list = next_elem.content.list
            if isinstance(next_elem, panflute.Para):
                capabilities = group_and_format_capabilities(capability_list)
            else:
                capabilities = [self.stringify(c) for c in capability_list]
        if not len(capabilities):
            raise ValueError("No capabilities found")
        capabilities = [c for c in capabilities if c]
        assert all([":" in c for c in capabilities])
        cap_mapping = {}
        for capability in capabilities:
            key, value = capability.split(":")
            cap_mapping[key.strip()] = value.strip()
        # else:
        #    header = self.retrieve_elem(self.get_header_by_identifier("feature-support"))
        #    capability_list = header.next.content.list

        # cap_mapping = {}
        # if not (cap_len := len(capabilities)):
        #     raise ValueError("No capabilities found")
        # elif cap_len > 1:
        #     for capability in capabilities:
        #         cap = [val for v in capability if (val := self.stringify(v))]
        #         cap = [
        #             item or ":"
        #             for sublist in [c.split(":") for c in cap]
        #             for item in sublist
        #         ]
        #         if not cap:
        #             continue
        #         key = " ".join(cap[0 : cap.index(":")])
        #         value = " ".join(cap[cap.index(":") + 1 :])
        #         cap_mapping[key] = value
        # elif cap_len == 1:
        #     cap = [val for v in capabilities[0] if (val := self.stringify(v))]
        #     cap = [[e.strip() for e in c.split(":")] for c in cap]
        #     for key, value in cap:
        #         cap_mapping[key] = value
        for key, value in cap_mapping.items():
            cap_mapping[key] = value.replace(":", "").strip()
        return cap_mapping
