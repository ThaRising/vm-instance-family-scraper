import datetime
import logging
import re
import typing as t
from collections import OrderedDict
from copy import deepcopy

from src import constants
from src.mixins import FileHashingMixin, MongoDBMixin
from src.parsers.series import SeriesMarkdownDocumentParser

from .shared import AzureType, DescriptionObject

logger = logging.getLogger(__name__)


def SkuTypes(series_parser: SeriesMarkdownDocumentParser):
    instances = series_parser.get_associated_instance_names()
    return [SkuType(series_parser, instance) for instance in instances]


class SkuType(AzureType, FileHashingMixin, MongoDBMixin):
    regex = re.compile(
        r"^(?P<tier>[sS]tandard|[bB]asic)?_?(?P<fam>[A-Z])(?P<subfam>[A-Z]{0,2})(?P<vcpus>\d+)(?P<constr>-\d+)?(?P<addons>[a-z]*)_?(?P<accel>[a-zA-Z\d]+_)?(?P<version>v\d)?(?P<iversion>\d)?$"
    )
    mongodb_collection_name = "sku_types"
    __attrs = (
        "name",
        "name__str",
        "_tier",
        "tier",
        "tier__str",
        "family_id",
        "family_id__str",
        "family_description",
        "family_description__str",
        "_subfamilies",
        "subfamilies",
        "subfamilies__str",
        "vcpus",
        "vcpus__str",
        "constrained_vcpus",
        "constrained_vcpus__str",
        "_addons",
        "addons",
        "addons__str",
        "_accelerator",
        "accelerator",
        "accelerator__str",
        "version",
        "version__str",
        "iversion",
        "iversion__str",
        "last_updated_azure",
    )

    def __init__(
        self, series_parser: SeriesMarkdownDocumentParser, instance_name: str
    ) -> None:
        self.parser = series_parser
        self._id = None

        self.is_confidential = self.parser.is_confidential
        self.instance = instance_name
        instance_attributes = self.regex.search(self.instance)
        assert instance_attributes
        self.instance_attributes = instance_attributes.groupdict()

        self.name: t.Optional[str] = None
        self.name__str: t.Optional[str] = None
        self._tier: t.Optional[str] = None
        self.tier: t.Dict[str, str] = {}
        self.tier__str: t.Optional[str] = None
        self.family_id: t.Optional[str] = None
        self.family_id__str: t.Optional[str] = None
        self.family_description: t.Optional[str] = None
        self.family_description__str: t.Optional[str] = None
        self._subfamilies: t.Optional[str] = None
        self.subfamilies: t.Dict[str, t.Dict[str, str]] = {}
        self.subfamilies__str: t.Optional[str] = None
        self.vcpus: t.Optional[int] = None
        self.vcpus__str: t.Optional[str] = None
        self.constrained_vcpus: t.Optional[int] = None
        self.constrained_vcpus__str: t.Optional[str] = None
        self._addons: t.Optional[str] = None
        self.addons: t.Dict[str, t.Dict[str, str]] = {}
        self.addons__str: t.Optional[str] = None
        self._accelerator: t.Optional[str] = None
        self.accelerator: t.Dict[str, t.Dict[str, str]] = {}
        self.accelerator__str: t.Optional[str] = None
        self.version: t.Optional[int] = None
        self.version__str: t.Optional[str] = None
        self.iversion: t.Optional[str] = None
        self.iversion__str: t.Optional[str] = None
        self.last_updated_azure: t.Optional[datetime.datetime] = None
        self._get_instance_attributes()
        print()

    def serialize(self) -> t.Dict[str, t.Union[int, str, bool, None]]:
        return {k: getattr(self, k) for k in self.__attrs}

    def write_to_database(self) -> bool:
        assert self.name
        return self._write_to_database({"name": self.name})

    def set_last_updated_azure(self, repo) -> None:
        self.last_updated_azure = self.parser.last_updated_timestamp(repo).isoformat()

    def _get_instance_attributes(self) -> None:
        attrs: t.OrderedDict[str, t.Union[str, int, None, t.Dict[str, dict]]] = (
            OrderedDict()
        )
        attrs["name"] = self.instance

        tier = self.instance_attributes["tier"]
        assert tier
        attrs["_tier"] = tier
        tier = {
            tier.capitalize(): DescriptionObject(
                tier.lower(), constants.TIER_MAPPING
            ).serialize()
        }
        attrs["tier"] = tier

        family_id = self.instance_attributes["fam"]
        assert family_id
        attrs["family_id"] = family_id
        family_description = constants.FAMILIES[family_id]
        attrs["family_description"] = family_description

        _subfamilies = self.instance_attributes["subfam"] or None
        subfamilies = OrderedDict()
        if _subfamilies:
            for subfam_id in list(_subfamilies):
                if subfam_id == "C" and self.is_confidential:
                    subfam_id = "_C"
                subfamilies[subfam_id] = DescriptionObject(
                    subfam_id, constants.SUBFAMILIES
                ).serialize()
        attrs["_subfamilies"] = _subfamilies
        attrs["subfamilies"] = subfamilies

        vcpus = self._cast_to_int(self.instance_attributes["vcpus"])
        assert vcpus
        attrs["vcpus"] = vcpus

        constrained_vcpus = self.instance_attributes["constr"]
        if constrained_vcpus:
            constrained_vcpus = re.sub(r"\s|-|_", "", constrained_vcpus)
            constrained_vcpus = self._cast_to_int(constrained_vcpus)
        constrained_vcpus = t.cast(t.Optional[int], constrained_vcpus)
        attrs["constrained_vcpus"] = constrained_vcpus

        _addons = self.instance_attributes["addons"]
        addons = OrderedDict()
        if _addons:
            _addons = re.sub(r"\s|-|_", "", _addons)
            for addon_id in list(_addons):
                addons[addon_id] = DescriptionObject(
                    addon_id, constants.ADDONS_MAPPING
                ).serialize()
        attrs["_addons"] = _addons
        attrs["addons"] = addons

        _accelerator = self.instance_attributes["accel"]
        accelerator = {}
        if _accelerator:
            _accelerator = re.sub(r"\s|-|_", "", _accelerator)
            accelerator = {
                _accelerator: DescriptionObject(
                    _accelerator, constants.SKU_ACCELERATOR_EXPLANATIONS
                ).serialize()
            }
        attrs["_accelerator"] = _accelerator
        attrs["accelerator"] = accelerator

        version = self.instance_attributes["version"] or "v1"
        version = version.replace("v", "")
        attrs["version"] = version
        iversion = self.instance_attributes["iversion"]
        attrs["iversion"] = iversion

        _attrs = deepcopy(attrs)
        for key, value in attrs.items():
            if key.startswith("_"):
                continue
            _attrs[key] = value
            _attrs[f"{key}__str"] = constants.SKU_FIELDS_EXPLANATIONS[key]
        for key, value in _attrs.items():
            setattr(self, key, value)
