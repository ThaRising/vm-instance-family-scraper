---
title: Lsv2 size series
description: Information on and specifications of the Lsv2-series sizes
author: mattmcinnes
ms.service: azure-virtual-machines
ms.subservice: sizes
ms.topic: conceptual
ms.date: 07/31/2024
ms.author: mattmcinnes
ms.reviewer: mattmcinnes
---

# Lsv2 sizes series

[!INCLUDE [lsv2-summary](./includes/lsv2-series-summary.md)]

## Host specifications
[!INCLUDE [lsv2-series-specs](./includes/lsv2-series-specs.md)]

## Feature support
[Premium Storage](../../premium-storage-performance.md): Supported <br>[Premium Storage caching](../../premium-storage-performance.md): Not Supported <br>[Live Migration](../../maintenance-and-updates.md): Not Supported <br>[Memory Preserving Updates](../../maintenance-and-updates.md): Not Supported <br>[Generation 2 VMs](../../generation-2.md): Supported <br>[Generation 1 VMs](../../generation-2.md): Supported <br>[Accelerated Networking](/azure/virtual-network/create-vm-accelerated-networking-cli): Supported <br>[Ephemeral OS Disk](../../ephemeral-os-disks.md): Supported <br>[Nested Virtualization](/virtualization/hyper-v-on-windows/user-guide/nested-virtualization): Not Supported <br>

## Sizes in series

### [Basics](#tab/sizebasic)

vCPUs (Qty.) and Memory for each size

| Size Name | vCPUs (Qty.) | Memory (GB) |
| --- | --- | --- |
| Standard_L8s_v2 | 8 | 64 |
| Standard_L16s_v2 | 16 | 128 |
| Standard_L32s_v2 | 32 | 256 |
| Standard_L48s_v2 | 48 | 384 |
| Standard_L64s_v2 | 64 | 512 |
| Standard_L80s_v26 | 80 | 640 |

#### VM Basics resources
- [Check vCPU quotas](../../../virtual-machines/quotas.md)

### [Local storage](#tab/sizestoragelocal)

Local (temp) storage info for each size

| Size Name | Max Temp Storage Disks (Qty.) | Temp Disk Size (GiB) | Temp Disk Random Read (RR)<sup>1</sup> IOPS | Temp Disk Random Read (RR)<sup>1</sup> Speed (MBps) | Temp Disk Random Write (RW)<sup>1</sup> IOPS | Temp Disk Random Write (RW)<sup>1</sup> Speed (MBps) | Max NVMe Disks (Qty.) | NVMe Disk Size (TiB) | NVMe Disk IOPS | NVMe Disk Speed (MBps) | 
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Standard_L8s_v2  | 1 | 80  |  |  |  |  | 1  | 1.92 | 400000 | 2000 |
| Standard_L16s_v2 | 1 | 160 |  |  |  |  | 2  | 1.92 | 800000 | 4000 |
| Standard_L32s_v2 | 1 | 320 |  |  |  |  | 4  | 1.92 | 1.5M   | 8000 |
| Standard_L48s_v2 | 1 | 480 |  |  |  |  | 6  | 1.92 | 2.2M   | 14000 |
| Standard_L64s_v2 | 1 | 640 |  |  |  |  | 8  | 1.92 | 2.9M   | 16000 |
| Standard_L80s_v2 | 1 | 800 |  |  |  |  | 10 | 1.92 | 3.8M   | 20000 |

#### Storage resources
- [Introduction to Azure managed disks](../../../virtual-machines/managed-disks-overview.md)
- [Azure managed disk types](../../../virtual-machines/disks-types.md)
- [Share an Azure managed disk](../../../virtual-machines/disks-shared.md)

#### Table definitions
- <sup>1</sup>Temp disk speed often differs between RR (Random Read) and RW (Random Write) operations. RR operations are typically faster than RW operations. The RW speed is usually slower than the RR speed on series where only the RR speed value is listed.
- Storage capacity is shown in units of GiB or 1024^3 bytes. When you compare disks measured in GB (1000^3 bytes) to disks measured in GiB (1024^3) remember that capacity numbers given in GiB may appear smaller. For example, 1023 GiB = 1098.4 GB.
- Disk throughput is measured in input/output operations per second (IOPS) and MBps where MBps = 10^6 bytes/sec.
- To learn how to get the best storage performance for your VMs, see [Virtual machine and disk performance](../../../virtual-machines/disks-performance.md).

### [Remote storage](#tab/sizestorageremote)

Remote (uncached) storage info for each size

| Size Name | Max Remote Storage Disks (Qty.) | Uncached Disk IOPS | Uncached Disk Speed (MBps) | Uncached Disk Burst<sup>1</sup> IOPS | Uncached Disk Burst<sup>1</sup> Speed (MBps) | Uncached Special<sup>2</sup> Disk IOPS | Uncached Special<sup>2</sup> Disk Speed (MBps) | Uncached Burst<sup>1</sup> Special<sup>2</sup> Disk IOPS | Uncached Burst<sup>1</sup> Special<sup>2</sup> Disk Speed (MBps) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Standard_L8s_v2 | 16 | 8000 | 160 | 8000 | 1280 | 400000 | 2000 |  |  |
| Standard_L16s_v2 | 32 | 16000 | 320 | 16000 | 1280 | 800000 | 4000 |  |  |
| Standard_L32s_v2 | 32 | 32000 | 640 | 32000 | 1280 | 1.5M | 8000 |  |  |
| Standard_L48s_v2 | 32 | 48000 | 960 | 48000 | 2000 | 2.2M | 14000 |  |  |
| Standard_L64s_v2 | 32 | 64000 | 1280 | 64000 | 2000 | 2.9M | 16000 |  |  |
| Standard_L80s_v26 | 32 | 80000 | 1400 | 80000 | 2000 | 3.8M | 20000 |  |  |

#### Storage resources
- [Introduction to Azure managed disks](../../../virtual-machines/managed-disks-overview.md)
- [Azure managed disk types](../../../virtual-machines/disks-types.md)
- [Share an Azure managed disk](../../../virtual-machines/disks-shared.md)

#### Table definitions
- <sup>1</sup>Some sizes support [bursting](../../disk-bursting.md) to temporarily increase disk performance. Burst speeds can be maintained for up to 30 minutes at a time.
- <sup>2</sup>Special Storage refers to either [Ultra Disk](../../../virtual-machines/disks-enable-ultra-ssd.md) or [Premium SSD v2](../../../virtual-machines/disks-deploy-premium-v2.md) storage.
- Storage capacity is shown in units of GiB or 1024^3 bytes. When you compare disks measured in GB (1000^3 bytes) to disks measured in GiB (1024^3) remember that capacity numbers given in GiB may appear smaller. For example, 1023 GiB = 1098.4 GB.
- Disk throughput is measured in input/output operations per second (IOPS) and MBps where MBps = 10^6 bytes/sec.
- Data disks can operate in cached or uncached modes. For cached data disk operation, the host cache mode is set to ReadOnly or ReadWrite. For uncached data disk operation, the host cache mode is set to None.
- To learn how to get the best storage performance for your VMs, see [Virtual machine and disk performance](../../../virtual-machines/disks-performance.md).


### [Network](#tab/sizenetwork)

Network interface info for each size

| Size Name | Max NICs (Qty.) | Max Bandwidth (Mbps) |
| --- | --- | --- |
| Standard_L8s_v2 | 2 | 3200 |
| Standard_L16s_v2 | 4 | 6400 |
| Standard_L32s_v2 | 8 | 12800 |
| Standard_L48s_v2 | 8 | 16000+ |
| Standard_L64s_v2 | 8 | 16000+ |
| Standard_L80s_v26 | 8 | 16000+ |

#### Networking resources
- [Virtual networks and virtual machines in Azure](/azure/virtual-network/network-overview)
- [Virtual machine network bandwidth](/azure/virtual-network/virtual-machine-network-throughput)

#### Table definitions
- Expected network bandwidth is the maximum aggregated bandwidth allocated per VM type across all NICs, for all destinations. For more information, see [Virtual machine network bandwidth](/azure/virtual-network/virtual-machine-network-throughput)
- Upper limits aren't guaranteed. Limits offer guidance for selecting the right VM type for the intended application. Actual network performance will depend on several factors including network congestion, application loads, and network settings. For information on optimizing network throughput, see [Optimize network throughput for Azure virtual machines](/azure/virtual-network/virtual-network-optimize-network-bandwidth). 
-  To achieve the expected network performance on Linux or Windows, you may need to select a specific version or optimize your VM. For more information, see [Bandwidth/Throughput testing (NTTTCP)](/azure/virtual-network/virtual-network-bandwidth-testing).

### [Accelerators](#tab/sizeaccelerators)

Accelerator (GPUs, FPGAs, etc.) info for each size

> [!NOTE]
> No accelerators are present in this series.

---

[!INCLUDE [sizes-footer](../includes/sizes-footer.md)]
