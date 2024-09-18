import os
import re
import typing as t

from dotenv import load_dotenv

load_dotenv()
MONGODB_HOSTNAME = os.environ.get("MONGODB_HOSTNAME", None) or "localhost"
MONGODB_DATABASE_NAME = (
    os.environ.get("MONGODB_DATABASE_NAME", None) or "ms_instance_family_scraper"
)
MONGODB_USERNAME = os.environ.get("MONGODB_USERNAME", None) or "root"
MONGODB_PASSWORD = os.environ.get("MONGODB_PASSWORD", None) or "root"

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
    "vcpus": "Number of vCPUs (size) of this SKU",
    "constrained_vcpus": "Number of CPU cores this SKU has been constrained to for per-Core licensing cost savings",
    "addons": "A list of additional SKU features and their descriptions",
    "accelerator": "Denotes the type of hardware accelerator in the specialized/GPU SKUs",
    "version": "Denotes the mainline version of this SKU",
    "iversion": "Denotes a version iteration for an isolated VM-size",
}
SKU_ACCELERATOR_EXPLANATIONS = {
    "cc": [
        "Confidential child capable VMs",
        "Enables creation of AMD SEV-SNP protected child VMs",
    ],
    "V620": [
        "AMD Radeon PRO V620 GPU enabled VMs",
        "AMD Radeon PRO V620 GPU enabled VMs with 32GiB of frame buffer",
    ],
    "V710": [
        "AMD Radeon PRO V710 GPU enabled VMs",
        "AMD Radeon PRO V710 GPU enabled VMs with between 4GiB and 32GiB of frame buffer",
    ],
    "MI300X": [
        "AMD Instinct MI300 GPUs enabled VMs",
        "VMs using AMD Instinct MI300 GPUs connected and scaled via Infinity-Link for High-End Deep-Learning",
    ],
    "T4": [
        "Nvidia Tesla 4 GPU enabled VMs",
        "VMs using Nvidia Tesla 4 GPUs supporting CUDA, vGPUs and Nvidia GRID",
    ],
    "A10": [
        "Nvidia A10 GPU enabled VMs",
        "VMs using Nvidia A10 GPUs with 24GiB of frame buffer and Nvidia GRID support",
    ],
    "A100": [
        "Nvidia A100 GPU enabled VMs",
        "VMs using Nvidia A100 GPUs with 80Gib of vRAM per accelerator",
    ],
    "H100": [
        "Nvidia H100 NVL GPU enabled VMs",
        "VMs using Nvidia H100 NVL GPUs with 94Gib of vRAM per accelerator",
    ],
    "1": [
        "VM uses 1 NUMA Domain",
        "Refers to the number of 'Non-uniform Memory Access' (NUMA) domains this VM has access to",
    ],
    "2": [
        "VM uses 2 NUMA Domains",
        "Refers to the number of 'Non-uniform Memory Access' (NUMA) domains this VM has access to",
    ],
    "3": [
        "VM uses 3 NUMA Domains",
        "Refers to the number of 'Non-uniform Memory Access' (NUMA) domains this VM has access to",
    ],
    "4": [
        "VM uses 4 NUMA Domains",
        "Refers to the number of 'Non-uniform Memory Access' (NUMA) domains this VM has access to",
    ],
    "8": [
        "VM uses 8 NUMA Domains",
        "Refers to the number of 'Non-uniform Memory Access' (NUMA) domains this VM has access to",
    ],
}
