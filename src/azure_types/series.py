import math
import re
import typing as t
from collections import OrderedDict

from src import constants
from src.parsers.families import FamilyMarkdownDocumentParser
from src.parsers.series import SeriesMarkdownDocumentParser


class AzureSkuSeriesType:
    regex = re.compile(
        r"^(?P<fam>[A-Z])(?P<subfam>[A-Z]{0,2})(?P<addons>[a-u,w-z]*)_?(?P<accel>[a-zA-Z\d]+_)?(?P<version>v\d)?(?P<iversion>\d)?$"
    )
    min_max_unit_regex = re.compile(
        r"^(?P<min>[\d.]+)+\s?-?\s?(?P<max>[\d.]+)?+\s?(?P<type>[\w\s]*?)$"
    )
    local_disk_type_mapping = OrderedDict(
        {
            "disk": "local_storage_disks",
            "temp disk": "local_temp_storage_disks",
            "nvme disk": "local_nvme_storage",
        }
    )
    __attrs = (
        "name",
        "family_id",
        "family_description",
        "subfamily_id",
        "subfamily_description",
        "addons",
        "addons_mapping",
        "accelerator",
        "version",
        "vcpus_min",
        "vcpus_max",
        "cpu_processor_models",
        "memory_gb_min",
        "memory_gb_max",
        "local_storage_disks_min",
        "local_storage_disks_max",
        "local_storage_disks_specs",
        "local_temp_storage_disks_min",
        "local_temp_storage_disks_max",
        "local_temp_storage_disks_specs",
        "local_nvme_storage_min",
        "local_nvme_storage_max",
        "local_nvme_storage_specs",
        "remote_storage_disks_min",
        "remote_storage_disks_max",
        "remote_storage_disks_specs",
        "network_nics_min",
        "network_nics_max",
        "networking_specs",
        "cap_acus_min",
        "cap_acus_max",
        "cap_premium_storage_capable",
        "cap_premium_storage_cache_capable",
        "cap_scsi_interface_capable_vm_generations",
        "cap_nvme_interface_capable_vm_generations",
        "cap_live_migration_capable",
        "cap_memory_preserving_updates_capable",
        "cap_hyper_v_gen1_capable",
        "cap_hyper_v_gen2_capable",
        "cap_accelerated_networking_capable",
        "cap_ephemeral_disk_capable",
        "cap_nested_virtualization_capable",
        "cap_write_accelerator_capable",
    )

    def __init__(
        self,
        series_parser: SeriesMarkdownDocumentParser,
        family_parser: FamilyMarkdownDocumentParser,
    ) -> None:
        self.parser = series_parser
        self.family_parser = family_parser

        self.name = series_parser.name
        self._family_attributes = self.regex.search(self.name)
        self.family_id = self._family_attributes.group("fam")
        self.family_description = constants.FAMILIES[self.family_id]
        self.subfamily_id = self._family_attributes.group("subfam") or None
        self.subfamily_description = None
        if self.subfamily_id:
            if self.subfamily_id == "C" and self.parser.is_confidential:
                self.subfamily_description = constants.SUBFAMILIES["_C"]
            self.subfamily_description = constants.SUBFAMILIES[self.subfamily_id]
        self.addons = self._family_attributes.group("addons")
        self.addons_mapping: t.OrderedDict[t.List[str]] = OrderedDict()
        self._get_addons_mapping()
        self.accelerator = self._family_attributes.group("accel")
        if self.accelerator:
            self.accelerator = self.accelerator.rstrip("_")
        self.version = self._family_attributes.group("version") or "v1"
        self.version = self._cast_to_int(self.version[-1])
        self.vcpus_min: t.Optional[int] = None
        self.vcpus_max: t.Optional[int] = None
        self.cpu_processor_models: t.Optional[t.List[str]] = None
        self._get_vcpu_stats()
        self.memory_gb_min: t.Optional[int] = None
        self.memory_gb_max: t.Optional[int] = None
        self._get_memory_stats()
        self.local_storage_disks_min: t.Optional[int] = None
        self.local_storage_disks_max: t.Optional[int] = None
        self.local_storage_disks_specs: t.Optional[t.List[str]] = None
        self.local_temp_storage_disks_min: t.Optional[int] = None
        self.local_temp_storage_disks_max: t.Optional[int] = None
        self.local_temp_storage_disks_specs: t.Optional[t.List[str]] = None
        self.local_nvme_storage_min: t.Optional[int] = None
        self.local_nvme_storage_max: t.Optional[int] = None
        self.local_nvme_storage_specs: t.Optional[t.List[str]] = None
        self._get_local_storage_disks_specs()
        self.remote_storage_disks_min: t.Optional[int] = None
        self.remote_storage_disks_max: t.Optional[int] = None
        self.remote_storage_disks_specs: t.Optional[t.List[str]] = None
        self._get_remote_storage_disks_specs()
        self.network_nics_min: t.Optional[int] = None
        self.network_nics_max: t.Optional[int] = None
        self.networking_specs: t.Optional[t.List[str]] = None
        self._get_networking_specs()
        self.cap_acus_min: t.Optional[int] = None
        self.cap_acus_max: t.Optional[int] = None
        self.cap_premium_storage_capable = False
        self.cap_premium_storage_cache_capable = False
        self.cap_scsi_interface_capable_vm_generations: t.Optional[str] = None
        self.cap_nvme_interface_capable_vm_generations: t.Optional[str] = None
        self.cap_live_migration_capable = False
        self.cap_memory_preserving_updates_capable = False
        self.cap_hyper_v_gen1_capable = False
        self.cap_hyper_v_gen2_capable = False
        self.cap_accelerated_networking_capable = False
        self.cap_ephemeral_disk_capable = False
        self.cap_nested_virtualization_capable = False
        self.cap_write_accelerator_capable = False
        self.cap_confidential_compute_capable = False
        self._get_capabilities()

    def to_dto(self) -> t.Dict[str, t.Union[int, str, bool, None]]:
        return {k: getattr(self, k) for k in self.__attrs}

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

    def _get_addons_mapping(self) -> None:
        if not self.addons:
            return
        for addon in list(self.addons):
            self.addons_mapping[addon] = constants.ADDONS_MAPPING[addon]

    def _get_vcpu_stats(self) -> None:
        cpus = self.parser.host_specs_table["Processor"]
        cpu_quantity = self.min_max_unit_regex.search("".join(cpus["Quantity"]))
        assert cpu_quantity
        cpu_quantity = t.cast(re.Match, cpu_quantity)
        vcpus_min, vcpus_max = [
            self._cast_to_int(cpu_quantity.group(k)) for k in ("min", "max")
        ]
        self.vcpus_min = vcpus_min
        self.vcpus_max = vcpus_max
        self.cpu_processor_models = t.cast(t.List[str], cpus["Specs"])

    def _get_memory_stats(self) -> None:
        memory = self.parser.host_specs_table["Memory"]
        memory_quantity = self.min_max_unit_regex.search("".join(memory["Quantity"]))
        assert memory_quantity
        memory_quantity = t.cast(re.Match, memory_quantity)
        self.memory_gb_min, self.memory_gb_max = [
            self._cast_to_int(memory_quantity.group(k)) for k in ("min", "max")
        ]

    def _get_local_storage_disks_specs(self) -> None:
        local_storage = self.parser.host_specs_table.get("Local Storage", None)
        if not local_storage:
            return
        local_storage_quantity = local_storage["Quantity"]
        if local_storage_quantity[0] == "None":
            return
        local_storage_specs = local_storage["Specs"]
        storage_types = self.local_disk_type_mapping
        for i, storage in enumerate(local_storage_quantity):
            storage_attrs = self.min_max_unit_regex.search(storage)
            _storage_types = [storage_attrs.group("type").lower().startswith(s) for s in storage_types.keys()]  # type: ignore
            _key = list(storage_types.keys())[_storage_types.index(True)]
            key = self.local_disk_type_mapping[_key]
            setattr(self, f"{key}_min", self._cast_to_int(storage_attrs.group("min")))
            setattr(self, f"{key}_max", self._cast_to_int(storage_attrs.group("max")))
            setattr(self, f"{key}_specs", local_storage_specs[i])

    def _get_remote_storage_disks_specs(self) -> None:
        remote_storage = self.parser.host_specs_table.get("Remote Storage", None)
        if not remote_storage:
            return
        remote_storage_quantity = self.min_max_unit_regex.search(
            "".join(remote_storage["Quantity"])
        )
        remote_storage_specs = remote_storage["Specs"]
        self.remote_storage_disks_min, self.remote_storage_disks_max = [
            self._cast_to_int(remote_storage_quantity.group(k)) for k in ("min", "max")
        ]
        self.remote_storage_disks_specs = remote_storage_specs or None

    def _get_networking_specs(self) -> None:
        network = self.parser.host_specs_table.get("Network", None)
        if not network:
            return
        network_quantity = self.min_max_unit_regex.search("".join(network["Quantity"]))
        network_specs = network["Specs"]
        self.network_nics_min, self.network_nics_max = [
            self._cast_to_int(network_quantity.group(k)) for k in ("min", "max")
        ]
        self.networking_specs = network_specs or None

    def _get_capabilities(self) -> None:
        capabilities = self.parser.capabilities
        for key, value in capabilities.items():
            setattr(self, key, value)
