import logging
import signal
import time
import typing as t
from pathlib import Path
from urllib.parse import quote_plus

from pymongo import MongoClient

from src import constants
from src.azure_types.instances import SkuTypes
from src.parsers.series import SeriesMarkdownDocumentParser
from src.parsers.utility import document_to_parser
from src.repository import DocsSourceRepository

logger = logging.getLogger(__name__)


def get_mongo_collection(name: str):
    user = "root"
    password = "root"
    host = "localhost"
    uri = "mongodb://%s:%s@%s" % (quote_plus(user), quote_plus(password), host)
    client = MongoClient(uri)
    database_name = "ms_instance_family_scraper"
    logger.warning(f"Connecting to MongoDB Database '{database_name}'")
    database = client[database_name]
    return database[name]


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
        repository.generate_last_commit_index()
        documents = repository.get_documents()
        _, families = repository.get_families()
        sku_series_collection = get_mongo_collection("sku_series")
        sku_types_collection = get_mongo_collection("sku_types")
        for document in documents:
            family_document = document.get_associated_family(families)
            parser = document_to_parser(document, family_document)
            parser = t.cast(SeriesMarkdownDocumentParser, parser)
            with parser as parser:
                dto = parser.to_type
                if dto:
                    dto.set_last_updated_azure(repository)
                    __import__("pprint").pprint(dto.to_dto())
                    sku_series_collection.insert_one(dto.to_dto())
                sku_types = SkuTypes(parser)
                __import__("pprint").pprint(sku_types.to_dto())
                for sku_type in sku_types.to_dto().values():
                    sku_types_collection.insert_one(dict(sku_type))
    except Exception as e:
        repository.cleanup()
        signal.alarm(1)
        time.sleep(1)
        raise e
