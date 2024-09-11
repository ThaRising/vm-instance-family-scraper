import logging
import re
import typing as t
from collections import OrderedDict

from src import constants
from src.parsers.series import SeriesMarkdownDocumentParser

logger = logging.getLogger(__name__)


class SkuTypes:
    regex = re.compile(
        r"^(?P<tier>[sS]tandard|[bB]asic)?_?(?P<fam>[A-Z])(?P<subfam>[A-Z]{0,2})(?P<vcpus>\d+)(?P<constr>-\d+)?(?P<addons>[a-z]*)_?(?P<accel>[a-zA-Z\d]+_)?(?P<version>v\d)?(?P<iversion>\d)?$"
    )

    def __init__(self, series_parser: SeriesMarkdownDocumentParser) -> None:
        self.parser = series_parser
        self.is_confidential = self.parser.is_confidential
        self.instances = self.parser.get_associated_instance_names()
        self.instance_attributes: t.Dict[str, dict] = {}
        self._instance_attributes = []
        for instance in self.instances:
            self._instance_attributes.append([instance, self.regex.search(instance)])
        self._get_instance_attributes()

    @staticmethod
    def _cast_to_int(val: t.Union[int, str, None]) -> t.Optional[int]:
        if val is None or isinstance(val, int):
            return val
        return int(val)

    def to_dto(self) -> t.Dict[str, dict]:
        return self.instance_attributes

    def _get_instance_attributes(self) -> None:
        for instance_info in self._instance_attributes:
            instance_name, instance_attr_match = instance_info
            instance_name = t.cast(str, instance_name)
            instance_attr_match = t.cast(re.Match, instance_attr_match)
            instance_attrs = instance_attr_match.groupdict()
            tier = instance_attrs["tier"]
            assert tier
            family_id = instance_attrs["fam"]
            assert family_id
            _subfamilies = instance_attrs["subfam"]
            subfamilies = OrderedDict()
            if _subfamilies:
                for subfam_id in list(_subfamilies):
                    if subfam_id == "C" and self.is_confidential:
                        subfam_id = "_C"
                    subfamilies[subfam_id] = constants.SUBFAMILIES[subfam_id]
            vcpus = instance_attrs["vcpus"]
            assert vcpus
            constrained_cpus = instance_attrs["constr"]
            if constrained_cpus:
                constrained_cpus = re.sub(r"\s|-|_", "", constrained_cpus)
            _addons = instance_attrs["addons"]
            addons = OrderedDict()
            if _addons:
                _addons = re.sub(r"\s|-|_", "", _addons)
                for addon_id in list(_addons):
                    addons[addon_id] = constants.ADDONS_MAPPING[addon_id]
            accelerator = instance_attrs["accel"]
            if accelerator:
                accelerator = re.sub(r"\s|-|_", "", accelerator)
            version = instance_attrs["version"] or "v1"
            version = version.replace("v", "")
            _obj = {
                "tier": {
                    "name": tier.capitalize(),
                    "description": constants.TIER_MAPPING[tier.lower()],
                },
                "name": instance_name,
                "family_id": family_id,
                "family_description": constants.FAMILIES[family_id],
                "subfamilies": subfamilies,
                "vcpus": self._cast_to_int(vcpus),
                "constrained_cpus": self._cast_to_int(constrained_cpus),
                "addons": addons,
                "accelerator": accelerator,
                "version": self._cast_to_int(version),
            }
            obj = {}
            for key, value in _obj.items():
                obj[key] = value
                obj[f"{key}__str"] = constants.SKU_FIELDS_EXPLANATIONS[key]
            self.instance_attributes[instance_name] = obj
