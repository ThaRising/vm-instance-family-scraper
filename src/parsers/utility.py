import logging

from src.documents import DocumentFile

from .shared import BaseParser

logger = logging.getLogger(__name__)


def document_to_parser(
    document: DocumentFile, family_document: DocumentFile
) -> BaseParser:
    from .families import FamilyMarkdownDocumentParser
    from .multi_series import MultiSeriesMarkdownDocumentParser
    from .series import SeriesMarkdownDocumentParser

    logger.debug(
        f"document_to_parser called for document '{document.path.name}' ({document.name})"
    )
    if document.is_multi_series_document:
        return MultiSeriesMarkdownDocumentParser(document, family_document)
    elif document.is_family:
        assert document is family_document
        return FamilyMarkdownDocumentParser(document, family_document)
    else:
        return SeriesMarkdownDocumentParser(document, family_document)
