import json
import re
import typing as t

import bs4
import requests

VM_SIZE_OVERVIEW_URL = "https://learn.microsoft.com/en-us/azure/virtual-machines/sizes"

FAMILIES = {
    "A": "Entry-level economical",
    "B": "Economic burstable",
    "D": "General purpose",
    "F": "Compute optimized",
    "E": "Memory optimized for In-Memory hyperthreaded-applications",
    "M": "Memory optimized",
    "L": "Storage optimized",
    "N": "GPU accelerated",
    "H": "High-performance-compute (HPC)",
    "G": "Memory and storage optimized",
}
CONFIDENTIAL_COMPUTE = "Confidential compute"
SUBFAMILIES = {
    "X": "High single-core performance",
    "B": "High memory bandwidth",
    "C": "High-performance computing and ML-workloads",
    "D": "Training and interference for deep-learning",
    "P": "FPGA-accelerated",
    "V": "Remote-visualization workloads",
    "G": "Gaming workloads",
    "S": "Premium storage and local SSD cache is available",
}
CAP_MAPPING = {
    "acu": None,
    "premium storage": "premium_storage_capable",
    "premium storage caching": "premium_storage_cache_capable",
    "live migration": "live_migration_capable",
    "memory preserving updates": None,
    "vm generation support": "",
    "generation 2 vms": "hyper_v_gen1_capable",
    "generation 1 vms": "hyper_v_gen2_capable",
    "accelerated networking": "accelerated_networking_capable",
    "ephemeral os disks": "ephemeral_disk_capable",
    "nested virtualization": "nested_virtualization_capable",
}


def parse_families_for_row(header, row) -> t.Tuple[dict, list]:
    columns = row.find_all("td")
    family_name = columns[0].find_next("a").get_text()
    if "previous" in (fn := family_name.lower()) or "other" in fn:
        return {}, []
    family_id = re.search(r"^([a-zA-Z]+)\-[Ff]amily", family_name).group(1)
    family_id = re.sub(r"[a-z]", "", family_id)
    subfamily_id = None
    subfamily_description = None
    family_descriptions = re.split(r"\s{2,}", columns[1].get_text())
    family_description = None
    assert len(family_id) <= 2
    if len(family_id) > 1 and "confidential comput" in family_descriptions[0].lower():
        subfamily_id = family_id[-1]
        subfamily_description = CONFIDENTIAL_COMPUTE
        family_id = family_id[0]
    family_description = FAMILIES[family_id[0]]
    if len(family_id) > 1:
        subfamily_id = family_id[-1]
        subfamily_description = SUBFAMILIES[subfamily_id]
        family_id = family_id[0]
    sub_families = columns[2].find_all(
        lambda tag: tag.name == "a" and "previous" not in tag.get_text().lower()
    )
    return {
        "family_id": family_id,
        "family_description": family_description,
        "subfamily_id": subfamily_id,
        "subfamily_description": subfamily_description,
    }, sub_families


def parse_subfamilies(family: dict, subfamily_links: list):
    family_specs = {}
    for subfamily in subfamily_links:
        relative_url, section = subfamily.get("href").split("#")
        res = requests.get(f"{VM_SIZE_OVERVIEW_URL}/{relative_url}")
        soup = bs4.BeautifulSoup(res.text, "html.parser")
        section = soup.find(id=section)
        subfamily_name = section.get_text()
        url = section.find_next("a").get("href")
        if "_" in url:
            url = f"{url.split('_')[-1]}-series"
        details_page_url = f"https://learn.microsoft.com/en-us/azure/virtual-machines/{url.split('/')[-1]}"
        specs = {}
        specs_table = section.find_next("table").find_next("tbody")
        for row in specs_table.find_all("tr"):
            row_columns = row.find_all("td")
            key = row_columns[0].get_text()
            key = re.sub(r"\s+", "_", key.lower())
            value_main = row_columns[1].get_text()
            if value_main.lower() == "none":
                value_main = None
            value_extra = [l.strip() for l in row_columns[2].find_all(string=True)]
            specs[key] = {
                "value": value_main or None,
                "extra": [v for v in value_extra if v] or None,
            }
        # res = requests.get(details_page_url)
        # if res.status_code == 404:
        #     details_page_url = f"https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/{relative_url.split('/')[0]}/{url.split('/')[-1]}"
        #     res = requests.get(details_page_url)
        # soup = bs4.BeautifulSoup(res.text, "html.parser")
        # section = soup.find(id="feature-support")
        # if not section:
        #     section = soup.find(
        #         lambda tag: tag.name == "a" and tag.get("href") == "acu"
        #     )
        #     if not section:
        #         section = soup.find(
        #             lambda tag: tag.name == "a" and tag.get("href") == "premium-storage-performance"
        #         )
        #     section = section.find_parent()
        # else:
        #     section = section.find_next("p")
        # _capabilities = section.get_text().splitlines()
        # capabilities = {}
        # for cap in _capabilities:
        #     cap = [c.strip() for c in cap.split(":")]
        #     key = re.sub(r"\d", "", cap[0].lower())
        #     key = CAP_MAPPING[key]
        #     if key is None:
        #         continue
        #     elif not key:
        #         continue
        #     else:
        #         capabilities[key] = cap[1].lower() == "supported"
        # specs["capabilities"] = capabilities
        family_specs.setdefault(subfamily_name, {})
        if specs.get("accelerator"):
            specs.pop("accelerator")
        if specs.get("accelerators"):
            specs.pop("accelerators")
        family_specs[subfamily_name]["specs"] = specs
    return family_specs


if __name__ == "__main__":
    res = requests.get(f"{VM_SIZE_OVERVIEW_URL}/overview")
    soup = bs4.BeautifulSoup(res.text, "html.parser")
    main_element = soup.find(id="main")
    h3_elements = main_element.find_all("h3", id=True)
    families = []
    for section in h3_elements[1:]:
        table_elem = (
            section.find_next("div", class_="tabGroup")
            .find_next("section")
            .find_next("tbody")
        )
        for row in table_elem.find_all("tr"):
            family, subfamily_links = parse_families_for_row(section, row)
            if not all((family, subfamily_links)):
                continue
            _family_specs = parse_subfamilies(family, subfamily_links)
            family_specs = {}
            for key in _family_specs.keys():
                v = _family_specs[key]
                key = key.split("-")[0]
                if "and" in key:
                    key = key.split("and")
                    key = [k.strip() for k in key]
                    for k in key:
                        k = k.replace(" ", "_")
                        family_specs[k] = v
                        family_specs[k]["family"] = {
                            "id": family["family_id"],
                            "description": family["family_description"],
                            "subfamily_id": family["subfamily_id"],
                            "subfamily_description": family["subfamily_description"],
                        }
                        version = k.split("v")
                        if not len(version):
                            version = 1
                        else:
                            version = version[-1]
                        family_specs[k]["family"]["version"] = int(version)
                        addons = re.search(
                            r"[A-Z]{1,2}([a-z]*?)([_A-Z][a-zA-Z\d]+_?)?v?\d?$", k
                        )
                        family_specs[k]["family"]["addons"] = addons.group(1) or None
                        family_specs[k]["family"]["accelerator"] = None
                        if accelerator := addons.group(2):
                            if "v" in accelerator:
                                accelerator = accelerator.split("v")[0]
                            family_specs[k]["family"][
                                "accelerator"
                            ] = accelerator.strip().strip("_")
                else:
                    key = key.replace(" ", "_")
                    family_specs[key] = v
                    family_specs[key]["family"] = {
                        "id": family["family_id"],
                        "description": family["family_description"],
                        "subfamily_id": family["subfamily_id"],
                        "subfamily_description": family["subfamily_description"],
                    }
                    version = key.split("v")
                    if not isinstance(version, list) or len(version) >= 1:
                        version = 1
                    else:
                        version = version[-1]
                    family_specs[key]["family"]["version"] = int(version)
                    addons = re.search(
                        r"[A-Z]{1,2}([a-z]*?)([_A-Z][a-zA-Z\d]+_?)?v?\d?$", key
                    )
                    family_specs[key]["family"]["addons"] = addons.group(1) or None
                    family_specs[key]["family"]["accelerator"] = None
                    if accelerator := addons.group(2):
                        if "v" in accelerator:
                            accelerator = accelerator.split("v")[0]
                        family_specs[key]["family"][
                            "accelerator"
                        ] = accelerator.strip().strip("_")
            for family_id, family_data in family_specs.items():
                vcpus = re.search(
                    r"^(\d{1,2})-?(\d{1,5})?\w+$",
                    re.sub(
                        r"\s+", "", family_data["specs"]["processor"]["value"] or ""
                    ),
                )
                vcpus_min = int(vcpus.group(1)) if (vcpus and vcpus.group(1)) else None
                vcpus_max = int(vcpus.group(2)) if (vcpus and vcpus.group(2)) else None
                memory = re.search(
                    r"^(\d{1,2})-?(\d{1,5})?\w+$",
                    re.sub(r"\s+", "", family_data["specs"]["memory"]["value"] or ""),
                )
                memory_gb_min = (
                    int(memory.group(1)) if (memory and memory.group(1)) else None
                )
                memory_gb_max = (
                    int(memory.group(2)) if (memory and memory.group(2)) else None
                )
                if family_data["specs"].get("local_storage"):
                    _local_storage = (
                        family_data["specs"]["local_storage"]["value"] or ""
                    )
                else:
                    _local_storage = ""
                local_storage = re.search(
                    r"^(\d{1,2})-?(\d{1,5})?\w+$", re.sub(r"\s+", "", _local_storage)
                )
                local_storage_disks_min = (
                    int(local_storage.group(1))
                    if (local_storage and local_storage.group(1))
                    else None
                )
                local_storage_disks_max = (
                    int(local_storage.group(2))
                    if (local_storage and local_storage.group(2))
                    else None
                )
                local_storage_disks_specs = (
                    family_data["specs"]["local_storage"]["extra"]
                    if family_data["specs"].get("local_storage")
                    else None
                )
                if family_data["specs"].get("remote_storage"):
                    _remote_storage = (
                        family_data["specs"]["remote_storage"]["value"] or ""
                    )
                else:
                    _remote_storage = family_data["specs"]["data_disks"]["value"] or ""
                    _remote_storage_disks_specs = (
                        family_data["specs"]["data_disks"]["extra"] or None
                    )
                remote_storage = re.search(
                    r"^(\d{1,2})-?(\d{1,5})?\w+$", re.sub(r"\s+", "", _remote_storage)
                )
                remote_storage_disks_min = (
                    int(remote_storage.group(1))
                    if (remote_storage and remote_storage.group(1))
                    else None
                )
                remote_storage_disks_max = (
                    int(remote_storage.group(2))
                    if (remote_storage and remote_storage.group(2))
                    else None
                )
                remote_storage_disks_specs = (
                    family_data["specs"]["remote_storage"]["extra"]
                    if family_data["specs"].get("remote_storage")
                    else _remote_storage_disks_specs
                )
                network = re.search(
                    r"^(\d{1,2})-?(\d{1,5})?\w+$",
                    re.sub(r"\s+", "", family_data["specs"]["network"]["value"] or ""),
                )
                network_nics_min = (
                    int(network.group(1)) if (network and network.group(1)) else None
                )
                network_nics_max = (
                    int(network.group(2)) if (network and network.group(2)) else None
                )
                obj = {
                    "name": family_id,
                    "family_id": family_data["family"]["id"],
                    "family_description": family_data["family"]["description"],
                    "subfamily_id": family_data["family"]["subfamily_id"],
                    "subfamily_description": family_data["family"][
                        "subfamily_description"
                    ],
                    "addons": family_data["family"]["addons"],
                    "accelerator": family_data["family"]["accelerator"],
                    "version": family_data["family"]["version"],
                    "vcpus_min": vcpus_min,
                    "vcpus_max": vcpus_max,
                    "cpu_processor_models": family_data["specs"]["processor"]["extra"],
                    "memory_gb_min": memory_gb_min,
                    "memory_gb_max": memory_gb_max,
                    "local_storage_disks_min": local_storage_disks_min,
                    "local_storage_disks_max": local_storage_disks_max,
                    "local_storage_disks_specs": local_storage_disks_specs,
                    "remote_storage_disks_min": remote_storage_disks_min,
                    "remote_storage_disks_max": remote_storage_disks_max,
                    "remote_storage_disks_specs": remote_storage_disks_specs,
                    "network_nics_min": network_nics_min,
                    "network_nics_max": network_nics_max,
                    "networking_specs": family_data["specs"]["network"]["extra"],
                }
                families.append(obj)
    with open("azure_vm_sizes.json", "w") as fout:
        json.dump(families, fout, indent=2)
