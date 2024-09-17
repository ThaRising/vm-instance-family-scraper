import logging
import typing as t

from src.documents import DocumentFile

from .shared import BaseParser

logger = logging.getLogger(__name__)


def document_to_parser(
    document: DocumentFile, family_document: DocumentFile
) -> t.Optional[BaseParser]:
    from .families import FamilyMarkdownDocumentParser
    from .multi_series import MultiSeriesMarkdownDocumentParser
    from .series import SeriesMarkdownDocumentParser

    logger.debug(
        f"document_to_parser called for document '{document.path.name}' ({document.name})"
    )
    if document.is_multi_series_document:
        ms_parser = MultiSeriesMarkdownDocumentParser(document, family_document)
        if ms_parser.is_public_preview:
            logger.info(
                f"Document '{document.name}' ({document.path}) is public_preview, skipping"
            )
        return ms_parser
    elif document.is_family:
        assert document is family_document
        return FamilyMarkdownDocumentParser(document, family_document)
    else:
        parser = SeriesMarkdownDocumentParser(document, family_document)
        if parser.is_public_preview:
            logger.info(
                f"Document '{document.name}' ({document.path}) is public_preview, skipping"
            )
        return parser
