import typing as t

from src import constants
import logging

from .mixins import MongoDBMixin


class MongoDB(MongoDBMixin):
    mongodb_database_name: t.ClassVar[str] = constants.MONGODB_DATABASE_NAME
    mongodb_hostname: t.ClassVar[str] = constants.MONGODB_HOSTNAME
    mongodb_username: t.ClassVar[str] = constants.MONGODB_USERNAME
    mongodb_password: t.ClassVar[str] = constants.MONGODB_PASSWORD

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
