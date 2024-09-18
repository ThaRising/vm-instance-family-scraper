import glob
import hashlib
import typing as t
from functools import cached_property
from pathlib import Path

import panflute

from src import constants
from src.azure_types.capabilities import (
    AzureSkuCapabilities,
    CapabilitiesElement
)
from src.documents import DocumentDescriptor, DocumentFile
from src.parsers.families import FamilyMarkdownDocumentParser

from .shared import BaseParser


class SafeDocumentHash:
    def do_document_hashing(self) -> "hashlib._Hash":
        return self.generate_hash(self.stringify(self.document))  # type: ignore


class SeriesMarkdownDocumentParser(BaseParser):
    def __init__(
        self, document_file: DocumentFile, family_document_file: DocumentFile
    ) -> None:
        super().__init__(document_file, family_document_file)
        self.family_document_parser = FamilyMarkdownDocumentParser(
            self.family_document_file, self.family_document_file
        )

    def __exit__(self, *args, **kwargs) -> None:
        super().__exit__(*args, **kwargs)
        self.logger.debug("Finalizing lifecycle of family parser")
        self.family_document_parser.finalize()

    @cached_property
    def to_type(self):
        from src.azure_types.series import AzureSkuSeriesType

        if self.is_public_preview:
            return None
        return AzureSkuSeriesType(self, self.family_document_parser)

    def do_document_hashing(self) -> "hashlib._Hash":
        return self.generate_hash(self.stringify(self.document))

    @property
    def is_confidential(self) -> bool:
        return "confidential" in self.host_summary.lower()

    @property
    def is_public_preview(self) -> bool:
        return "public preview" in self.stringify(self.document.headers[0]).lower()

    @property
    def is_previous_generation(self) -> bool:
        return self.document_file.identifier not in [
            doc.identifier for doc in self.family_document_parser.get_children()
        ]

    def _get_host_specs_table(
        self, table
    ) -> t.OrderedDict[str, t.OrderedDict[str, str]]:
        return self.parse_table_colhead_rowhead(table)

    def is_alternative_host_specs_table(self, table) -> bool:
        if not any(
            [
                k in table.keys()
                for k in (
                    "Processor",
                    "Memory",
                    "Local Storage",
                    "Remote Storage",
                    "Network",
                )
            ]
        ):
            return True
        return False

    def _host_specs_table_file(self, host_specs_table) -> t.Optional[Path]:
        if self.is_alternative_host_specs_table(host_specs_table):
            reverse_folder_index = list(reversed(self._path.parts)).index(
                constants.MS_REPOSITORY_PATH.split("/")[-2]
            )
            folder_path_parts = self._path.parts[:-reverse_folder_index]
            folder_path = Path(*folder_path_parts)
            assert folder_path.exists()
            files = [
                Path(file) for file in glob.iglob(f"{folder_path}/**/*", recursive=True)
            ]
            host_specs_filename = f"{self._path.stem}-specs.md"
            file_index = [filepath.name for filepath in files].index(
                host_specs_filename
            )
            file = files[file_index]
            assert file.exists()
            return file
        return None

    def _host_specs_table(self) -> t.OrderedDict[str, t.OrderedDict[str, str]]:
        self.logger.debug(
            f"host_specs_table called for document '{self.path.name}' ({self.name})"
        )
        if not self.is_previous_generation:
            self.logger.debug("host_specs_table -> is_previous_generation is True")
            all_links = self.family_document_parser.document.links
            parser = self._get_linked_doc_parser_from_family_page(
                all_links, link_identifier="specs"
            )
            with parser:
                host_specs_table = parser.document.tables[0]
            return self._get_host_specs_table(host_specs_table)
        if (
            not self.document_file.is_multi_series_document
            and self.document_file.is_series
        ):
            self.logger.debug("host_specs_table -> is_series is True")
            all_links = self.document.links
            parser = self._get_linked_doc_parser_from_family_page(
                all_links, link_identifier="specs"
            )
            with parser:
                host_specs_table = parser.document.tables[0]
            return self._get_host_specs_table(host_specs_table)
        self.logger.debug("host_specs_table -> Default Case")
        return self._get_host_specs_table(self.document.tables[0])

    @cached_property
    def host_specs_table(self) -> t.OrderedDict[str, t.OrderedDict[str, str]]:
        table = self._host_specs_table()
        assert table
        alternate_table_file = self._host_specs_table_file(table)
        if alternate_table_file:
            alternate_specs_document = DocumentDescriptor(alternate_table_file)
            cls = self.base_parser_factory(SafeDocumentHash)
            parser = cls(
                alternate_specs_document.to_document_file(), self.family_document_file
            )
            with parser:
                host_specs_table = parser.document.tables[0]
            return self._get_host_specs_table(host_specs_table)
        return table

    def _get_host_summary(self, parser) -> str:
        paragraphs = []
        if not parser.document.headers:
            paragraphs = parser.document.paragraphs
        else:
            next_elem = parser.document.headers[0].next
            while isinstance(next_elem, panflute.Para):
                paragraphs.append(next_elem)
                next_elem = next_elem.next
        return "\n".join([self.stringify(para) for para in paragraphs])

    @property
    def host_summary(self) -> str:
        if not self.is_previous_generation:
            all_links = self.family_document_parser.document.links
            parser = self._get_linked_doc_parser_from_family_page(
                all_links, link_identifier="summary"
            )
            with parser:
                return self._get_host_summary(parser)
        return self._get_host_summary(self)

    def _paragraph_is_capabilities(self, content: str) -> bool:
        keywords_present = all(
            [s in content for s in ("storage", "generation", "premium", "supported")]
        )
        return keywords_present

    def _parse_capabilities(
        self, capabilities_elem
    ) -> t.OrderedDict[str, t.Union[bool, int, str]]:
        capabilities = CapabilitiesElement(self, capabilities_elem)
        cap = AzureSkuCapabilities(capabilities.to_dto())
        return cap.to_dto()

    @property
    def capabilities(self):
        capabilities_header = self.retrieve_elem(
            self.get_header_by_identifier("feature-support")
        )
        if capabilities_header:
            capabilities_list = capabilities_header.next.content
            return self._parse_capabilities(capabilities_list)
        else:
            next_elem = self.document.headers[0].next
            while next_elem:
                content = self.stringify(next_elem).lower()
                if self._paragraph_is_capabilities(content):
                    break
                next_elem = next_elem.next
            if next_elem:
                content = self.stringify(next_elem).lower()
                assert self._paragraph_is_capabilities(content)
                return self._parse_capabilities(next_elem)
            else:
                capabilities_dto = CapabilitiesElement.from_special_case_elements(
                    self.document, self
                )
                cap = AzureSkuCapabilities(capabilities_dto)
                return cap.to_dto()

    def _get_linked_doc_parser_from_family_page(
        self, all_links: t.List[panflute.Link], link_identifier: str
    ):
        matching_links = [
            link
            for link in all_links
            if link_identifier in (url := link.url)
            and "includes" in url
            and "series" in url
            and self.name.lower().replace("_", "") in url
        ]
        assert matching_links
        # If more than one matching link is found, this indicates that the name of the series is short
        # so we sort by the shortest link-value to ensure the most precise match
        matching_links = list(
            sorted(matching_links, key=lambda link: len(self.stringify(link)))
        )
        link = matching_links[0]
        host_summary_document = DocumentDescriptor(
            self.family_document_file.path.parent / link.url
        )
        cls = self.base_parser_factory(SafeDocumentHash)
        parser = cls(
            host_summary_document.to_document_file(), self.family_document_file
        )
        return parser

    def get_associated_instance_names(self) -> t.List[str]:
        self.logger.debug(
            f"get_associated_instance_names called for document '{self.path.name}' ({self.name})"
        )
        tables = self.document.tables
        assert tables
        instances = []
        for table in tables:
            _, body_values = self._parse_table(table)
            first_row_values = [b[0][0] for b in body_values]
            instances.append(first_row_values)
        instances = sorted(instances, key=lambda e: len(e))
        return list(instances[0])
