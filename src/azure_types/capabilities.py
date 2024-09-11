import itertools
import logging
import re
import typing as t
from collections import OrderedDict, defaultdict
from copy import copy

import panflute

logger = logging.getLogger(__name__)


class CapabilitiesElement:
    def __init__(
        self,
        parent_parser,
        element: t.Union[panflute.Para, panflute.ListContainer, panflute.BulletList],
    ) -> None:
        self.parent_parser = parent_parser
        self.element = element
        self.content = self.contentgetter()
        self.content_types = self.count_type_occurences()
        self.capabilities: t.OrderedDict[str, str] = OrderedDict()
        self._parser_fn = ""
        parser_fn = self.determine_parser()
        self.capabilities = parser_fn()
        self.capabilities["cap_confidential_compute_capable"] = (
            parent_parser.is_confidential
        )

    def to_dto(self) -> t.OrderedDict[str, str]:
        return self.capabilities

    def tostr(self, val) -> str:
        return self.parent_parser.stringify(val)

    def contentgetter(self):
        if isinstance(self.element, panflute.Para):
            return self.element.content.list
        elif isinstance(self.element, panflute.BulletList):
            return self.element.content.list
        elif isinstance(self.element, panflute.ListContainer):
            return self.element.list
        else:
            raise ValueError(f"Unsupported element type: {type(self.element)}")

    def count_type_occurences(self):
        type_counts = defaultdict(int)
        if isinstance(self.content[0], list):
            for line in self.content:
                for elem in line:
                    type_counts[type(elem).__name__] += 1
        else:
            for line in self.content:
                type_counts[type(line).__name__] += 1
        return type_counts

    def determine_parser(self):
        match self.element:
            case panflute.Para() | panflute.ListContainer():
                if "<br>" in (
                    content := self.tostr(self.element).strip().rstrip("<br>")
                ):
                    self._parser_fn = self._parse_split_by_br.__name__
                    return lambda: self._parse_split_by_br(content)
                else:
                    self._parser_fn = self._parse_group_by_rawinline.__name__
                    return self._parse_group_by_rawinline
            case panflute.BulletList():
                self._parser_fn = self._parse_bullet_list.__name__
                return self._parse_bullet_list

    def _parse_list(self):
        pass

    def _parse_split_by_br(self, content):
        lines = content.split("<br>")
        lines = [lstrp for l in lines if (lstrp := l.strip())]
        capabilities = OrderedDict(
            {v[0].strip(): v[1].strip() for v in [l.split(":") for l in lines]}
        )
        return capabilities

    def _parse_group_by_rawinline(self):
        GROUP_BY_ELEMS = [panflute.RawInline, panflute.LineBreak]
        group_occurences = [
            (self.content_types.get(g.__name__, 0), g) for g in GROUP_BY_ELEMS
        ]
        group_occurences = list(
            sorted(group_occurences, reverse=True, key=lambda t: t[0])
        )
        group_by_cls = group_occurences[0][1]
        group_by_cls = group_by_cls or panflute.RawInline
        _lines = [
            list(y)
            for x, y in itertools.groupby(
                self.contentgetter(), lambda z: isinstance(z, group_by_cls)
            )
            if not x
        ]
        assert _lines
        if len(_lines) == 1:
            lines = [self.tostr(line) for line in _lines[0]]
        else:
            lines = [
                " ".join([self.tostr(l) for l in line if self.tostr(l).strip()])
                for line in _lines
            ]
        capabilities = OrderedDict(
            {
                splitlines[0].strip(): splitlines[1].strip()
                for splitlines in [line.split(":") for line in lines]
            }
        )
        return capabilities

    def _parse_bullet_list(self):
        self.element = t.cast(panflute.BulletList, self.element)
        lines = [self.tostr(line) for line in self.contentgetter()]
        lines = [lstrp for line in lines if (lstrp := line.strip())]
        capabilities = OrderedDict(
            {
                splitlines[0].strip(): splitlines[1].strip()
                for splitlines in [line.split(":") for line in lines]
            }
        )
        return capabilities


class AzureSkuCapabilities:
    REQUIRED_KEYS: t.ClassVar[t.Set[str]] = {
        "premium storage",
        "premium storage caching",
        "live migration",
        "memory preserving updates",
        "accelerated networking",
        "nested virtualization",
    }
    BOOL_VALUE_MAPPING: t.ClassVar[t.Dict[str, bool]] = {
        "not supported": False,
        "supported": True,
        "restricted support": True,
    }
    BOOL_KEYS_MAPPING: t.ClassVar[t.Dict[str, str]] = {
        "premium storage": "cap_premium_storage_capable",
        "premium storage caching": "cap_premium_storage_cache_capable",
        "live migration": "cap_live_migration_capable",
        "memory preserving updates": "cap_memory_preserving_updates_capable",
        "accelerated networking": "cap_accelerated_networking_capable",
        "ephemeral os disk": "cap_ephemeral_disk_capable",
        "ephemeral os disks": "cap_ephemeral_disk_capable",
        "nested virtualization": "cap_nested_virtualization_capable",
        "generation 1 vms": "cap_hyper_v_gen1_capable",
        "generation 2 vms": "cap_hyper_v_gen2_capable",
        "write accelerator": "cap_write_accelerator_capable",
    }

    def __init__(self, capabilities: t.OrderedDict[str, str]) -> None:
        capabilities = OrderedDict(
            {self.clean_key(key): value for key, value in capabilities.items()}
        )
        cap_confidential_compute_capable = capabilities.pop(
            "cap_confidential_compute_capable"
        )
        self.capabilities = capabilities
        self._capabilities = copy(capabilities)
        assert self.REQUIRED_KEYS.issubset(set(capabilities.keys())), set(
            capabilities.keys()
        ).difference(self.REQUIRED_KEYS)
        self.result: t.OrderedDict[str, t.Union[bool, int, str]] = OrderedDict()
        self.get_boolean_values()
        self.get_non_boolean_values()
        assert not self._capabilities, list(self._capabilities.keys())
        self.result["cap_confidential_compute_capable"] = (
            cap_confidential_compute_capable
        )

    def to_dto(self) -> t.OrderedDict[str, t.Union[bool, int, str]]:
        return self.result

    @staticmethod
    def clean_string(content: str) -> str:
        return re.sub(r"<sup>\d</sup>", "", content)

    @classmethod
    def clean_key(cls, key: str) -> str:
        key = key.lower()
        return cls.clean_string(key)

    def get_boolean_values(self) -> None:
        # get the boolean keys first
        for _key, _value in self.capabilities.items():
            _key = self.clean_key(_key)
            if _key not in self.BOOL_KEYS_MAPPING.keys():
                continue
            key = self.BOOL_KEYS_MAPPING[_key]
            _value = _value.lower()
            value = self.BOOL_VALUE_MAPPING.get(_value, False)
            if not value:
                logger.debug(
                    f"No value for key '{key}' (value is '{_value}') found, trying .startswith matching"
                )
                for k, v in self.BOOL_VALUE_MAPPING.items():
                    if _value.startswith(k):
                        value = v
                        logger.debug(
                            f"Found .startswith match for key '{key}' (value was '{_value}')"
                        )
                        break
            self.result[key] = value
            self._capabilities.pop(_key)

    def get_non_boolean_values(self) -> None:
        for _key, value in self.capabilities.items():
            _key = self.clean_key(_key)
            if _key in self.BOOL_KEYS_MAPPING.keys():
                continue
            match _key:
                case "acu":
                    self.result.update(self._get_cap_acus(value))
                    self._capabilities.pop(_key)
                case "acus":
                    self.result.update(self._get_cap_acus(value))
                    self._capabilities.pop(_key)
                case "vm generation support":
                    self.result.update(self._get_cap_vm_generations(value))
                    self._capabilities.pop(_key)
                case "nvme interface":
                    self.result.update(self._get_nvme_interfaces(value))
                    self._capabilities.pop(_key)
                case "scsi interface":
                    self.result.update(self._get_scsi_interfaces(value))
                    self._capabilities.pop(_key)

    def _get_cap_acus(self, content: str) -> t.Dict[str, int]:
        min_acus, max_acus = content.split("-")
        return {"cap_acus_min": int(min_acus), "cap_acus_max": int(max_acus)}

    def _get_cap_vm_generations(self, content: str) -> t.Dict[str, bool]:
        cap_hyper_v_gen1_capable = "1" in content
        cap_hyper_v_gen2_capable = "2" in content
        return {
            "cap_hyper_v_gen1_capable": cap_hyper_v_gen1_capable,
            "cap_hyper_v_gen2_capable": cap_hyper_v_gen2_capable,
        }

    def _get_scsi_interfaces(self, content: str) -> t.Dict[str, str]:
        content = content.lower()
        capable_generations = []
        if "generation" in content and "1" in content:
            capable_generations.append("V1")
        if "generation" in content and "2" in content:
            capable_generations.append("V2")
        return {
            "cap_scsi_interface_capable_vm_generations": ",".join(capable_generations)
        }

    def _get_nvme_interfaces(self, content: str) -> t.Dict[str, str]:
        content = content.lower()
        capable_generations = []
        if "generation" in content and "1" in content:
            capable_generations.append("V1")
        if "generation" in content and "2" in content:
            capable_generations.append("V2")
        return {
            "cap_nvme_interface_capable_vm_generations": ",".join(capable_generations)
        }
