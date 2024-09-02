import typing as t

import panflute

from .abstract import MarkdownDocumentProps
from .documents import DocumentDescriptor
from .documents import DocumentFile
from .parser import MarkdownDocumentParser
from .parser import MarkdownDocumentParserDoctype


class SkuFamilyDocument(MarkdownDocumentParser, MarkdownDocumentProps):
    document: MarkdownDocumentParserDoctype

    def __init__(self, document: DocumentFile) -> None:
        super().__init__(document)
        self.sections = list(self.get_sections())
        self.children: t.List[DocumentFile] = self.get_children()
        print()

    @property
    def name(self) -> str:
        return self.document_file.identifier.upper()

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

    def get_children(self) -> t.List[DocumentFile]:
        children = []
        for section in self.sections:
            link = section.next.next.content.list[0]
            assert isinstance(link, panflute.Link)
            path = self.document_path.parent / link.url
            children.append(DocumentDescriptor(path).to_document_files())
        children = self.flatten_list_of_lists(children)
        return children
