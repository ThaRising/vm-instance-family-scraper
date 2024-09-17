import logging
import signal
import time
import typing as t
from pathlib import Path

from src import constants
from src.azure_types.instances import SkuTypes
from src.parsers.series import SeriesMarkdownDocumentParser
from src.parsers.utility import document_to_parser
from src.repository import DocsSourceRepository

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.warning("Starting main process")
    try:
        repository = DocsSourceRepository(
            constants.MS_REPOSITORY_URL,
            constants.MS_REPOSITORY_NAME,
            constants.MS_REPOSITORY_PATH,
        )
        clone_path = Path(repository.repo_temp_directory.name) / Path(
            repository.repo_name
        )
        repository_workdir = repository.clone_repository()
        documents = repository.get_documents()
        _, families = repository.get_families()
        for document in documents:
            family_document = document.get_associated_family(families)
            parser = document_to_parser(document, family_document)
            parser = t.cast(SeriesMarkdownDocumentParser, parser)
            dto = parser.to_type
            if dto:
                dto.set_last_updated_azure(repository)
                __import__("pprint").pprint(dto.to_dto())
            sku_types = SkuTypes(parser)
            __import__("pprint").pprint(sku_types.to_dto())
    except Exception as e:
        repository.cleanup()
        signal.alarm(1)
        time.sleep(1)
        raise e
