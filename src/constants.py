import re
import typing as t

MS_REPOSITORY_URL = "https://github.com/MicrosoftDocs/azure-compute-docs.git"
MS_REPOSITORY_NAME = t.cast(
    re.Match, re.search(r"^https?\://.+/([a-z-]+)(?:\.git)?$", MS_REPOSITORY_URL)
).group(1)
MS_REPOSITORY_PATH = "articles/virtual-machines/sizes"

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
SUBFAMILIES = {
    "X": "High single-core performance",
    "B": "High memory bandwidth",
    "C": "High-performance computing and ML-workloads",
    "_C": "Confidential compute",
    "D": "Training and interference for deep-learning",
    "P": "FPGA-accelerated",
    "V": "Remote-visualization workloads",
    "G": "Gaming workloads",
    "S": "Premium storage and local SSD cache is available",
}
ADDONS_MAPPING = {
    "s": [
        "Premium storage capable",
        "Premium storage capability with possible Ultra SSD support",
    ],
    "p": ["ARM64-based processor", "Cheapest processor type, cheaper than AMD-based"],
    "a": ["AMD-based processor", "Cheaper processor type than default"],
    "l": ["Low memory", "Lower amount of memory than Memory intensive size"],
    "m": ["Memory intensive", "Most amount of memory for specific size"],
    "t": ["Tiny memory", "Lowest amount of memory for specific size"],
    "i": ["Isolated VM size", "Isolated to a specific hardware type and customer"],
    "d": ["Diskfull", "Local temp disk is present"],
    "r": ["RDMA capable", "'Remote direct memory access' (RDMA) capable"],
    "b": ["Block storage performance", "Higher IOPS for attached managed disks"],
    "e": [
        "Intel AMX & TDX capable",
        "Supports AMX for AI acceleration and TDX for hardware-level confidential compute",
    ],
}
TIER_MAPPING = {
    "basic": "Basic tier VMs are lower-priced than Standard while excluding load balancer and auto-scaling, ideal for dev/test workloads",
    "standard": "Standard tier VMs offer balanced performance, including load balancer and auto-scaling, suitable for general-purpose production workloads",
}
SKU_FIELDS_EXPLANATIONS = {
    "tier": "SKU Tier",
    "name": "Name of the VM instance",
    "family_id": "Single character denoting the family of this SKU",
    "family_description": "Short description of this SKU family",
    "subfamilies": "A list of this SKU families subfamilies and associated descriptions",
    "vcpus": "Number of vCPUs ('size') of this SKU",
    "constrained_cpus": "Number of CPU cores this SKU has been constrained to for per-Core licensing cost savings",
    "addons": "A list of additional SKU features and their descriptions",
    "accelerator": "Denotes the type of hardware accelerator in the specialized/GPU SKUs",
    "version": "Denotes the mainline version of this SKU",
    "iversion": "Denotes a version iteration for an isolated VM-size",
}
