# pyright: reportAttributeAccessIssue=false
# mypy: disable-error-code="attr-defined"
import abc
import logging
import math
import re
import typing as t

from src import constants


class DescriptionObject:
    keys = ("description", "verbose_description")

    def __init__(
        self, name: str, choices: t.Union[t.Dict[str, str], t.Dict[str, t.List[str]]]
    ) -> None:
        self.description = choices[name]
        if isinstance(self.description, str):
            self.description = [self.description]

    def serialize(self) -> t.Dict[str, str]:
        return {self.keys[i]: v for i, v in enumerate(self.description)}


class AzureType(abc.ABC):
    __attrs: t.ClassVar[t.Sequence[str]]
    regex: t.ClassVar[re.Pattern]
    logger: t.ClassVar[logging.Logger] = logging.getLogger(__name__)

    _id: t.Optional[str]
    mongodb_database_name: t.ClassVar[str] = constants.MONGODB_DATABASE_NAME
    mongodb_collection_name: t.ClassVar[str]
    mongodb_hostname: t.ClassVar[str] = constants.MONGODB_HOSTNAME
    mongodb_username: t.ClassVar[str] = constants.MONGODB_USERNAME
    mongodb_password: t.ClassVar[str] = constants.MONGODB_PASSWORD

    @abc.abstractmethod
    def serialize(self) -> t.Dict[str, t.Union[int, str, bool, None]]:
        """Convert the internal data of this Azure Type into a JSON serializable representation"""
        raise NotImplementedError

    def _write_to_database(self, filter: t.Dict[str, str]) -> bool:
        changed = False
        document = self.serialize()
        documents_count = self.collection.count_documents(filter)
        assert (
            documents_count <= 1
        ), f"Duplicate documents for name '{self.name}' found, exiting"
        if not documents_count:
            # If no documents were found, insert a new one
            changed = True
            _id = self.collection.insert_one(self.serialize()).inserted_id
        else:
            # If a document was found, check if it is different from the current state
            existing_document = self.collection.find_one(filter)
            assert existing_document
            # Remove the _id key because it is not present in the serialized document and would otherwise always return a change
            _id = existing_document.pop("_id")
            changed = (
                self.generate_hash(existing_document).hexdigest()
                != self.generate_hash(document).hexdigest()
            )
            if changed:
                # If the existing document and the state of this instance differ, replace the current document
                self.collection.replace_one({"_id": _id}, document)
        _id = str(_id)
        self._id = _id
        return changed

    @abc.abstractmethod
    def write_to_database(self) -> bool:
        """
        Write the serialized data of this object to the database if it has changed
        Sets the instance attribute '_id' to the ID returned by find or insert

        Return True if a write occured (and the objects were thus different) and False if not
        """
        raise NotImplementedError

    @classmethod
    def _cast_to_int(cls, val: t.Union[int, str, None]) -> t.Optional[int]:
        if val is None or isinstance(val, int):
            return val
        if cls._is_float(val):
            return math.floor(float(val))
        return int(val)

    @staticmethod
    def _is_float(val: str) -> bool:
        try:
            float(val)
        except ValueError:
            return False
        else:
            return True
