import hashlib
import typing as t

import panflute

from ..documents import DocumentFile
from .series import SeriesMarkdownDocumentParser


class MultiSeriesMarkdownDocumentParser(SeriesMarkdownDocumentParser):
    """
    Parses a SKU series similarly to a SeriesParser but first reduces the document,
    to only include content for the series the provided 'document_file.identifier' specifies
    """

    def __init__(
        self, document_file: DocumentFile, family_document_file: DocumentFile
    ) -> None:
        assert document_file.is_multi_series_document
        super().__init__(document_file, family_document_file)
        self.reduce_document()

    def do_document_hashing(self) -> "hashlib._Hash":
        return self.generate_hash(self.stringify(self.document))

    def reduce_document(self) -> None:
        headers = [
            h
            for h in self.document.headers
            if (self.name.lower() in h.identifier and any([s in h.identifier for s in ("series", "memory")]))
        ]
        self.logger.debug("'reduce_document' called, creating new Document")
        new_document = panflute.Doc(metadata=self.document.metadata, format="markdown")
        for header in headers:
            new_document.content.append(header)
            next_elem = header.next
            while bool(next_elem) and not isinstance(next_elem, panflute.Header):
                next_elem = t.cast(t.Type[panflute.Element], next_elem)
                new_document.content.append(next_elem)
                next_elem = next_elem.next
        new_document = self.prepare_document(new_document)
        self.document = new_document
        self._document_hash = self.do_document_hashing()
