"""VMware vSphere management using pyVmomi."""

import ssl
import logging
from typing import Optional, Dict, Any

from pyVim import connect
from pyVmomi import vim, vmodl

from .config import Config


class VMwareManager:
    """VMware management class, encapsulating pyVmomi operations for vSphere."""
    
    def __init__(self, config: Config):
        self.config = config
        self.si = None               # Service instance (ServiceInstance)
        self.content = None          # vSphere content root
        self.datacenter_obj = None
        self.resource_pool = None
        self.datastore_obj = None
        self.network_obj = None
        self.authenticated = False   # Authentication flag for API key verification
        self._connect_vcenter()

    def _connect_vcenter(self):
        """Connect to vCenter/ESXi and retrieve main resource object references."""
        try:
            if self.config.insecure:
                # Connection method without SSL certificate verification
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.check_hostname = False  # Disable hostname checking
                context.verify_mode = ssl.CERT_NONE
                self.si = connect.SmartConnect(
                    host=self.config.vcenter_host,
                    user=self.config.vcenter_user,
                    pwd=self.config.vcenter_password,
                    sslContext=context)
            else:
                # Standard SSL verification connection
                self.si = connect.SmartConnect(
                    host=self.config.vcenter_host,
                    user=self.config.vcenter_user,
                    pwd=self.config.vcenter_password)
        except Exception as e:
            logging.error(f"Failed to connect to vCenter/ESXi: {e}")
            raise
        # Retrieve content root object
        self.content = self.si.RetrieveContent()
        logging.info("Successfully connected to VMware vCenter/ESXi API")

        # Retrieve target datacenter object
        if self.config.datacenter:
            # Find specified datacenter by name
            self.datacenter_obj = next((dc for dc in self.content.rootFolder.childEntity
                                        if isinstance(dc, vim.Datacenter) and dc.name == self.config.datacenter), None)
            if not self.datacenter_obj:
                logging.error(f"Datacenter named {self.config.datacenter} not found")
                raise Exception(f"Datacenter {self.config.datacenter} not found")
        else:
            # Default to the first available datacenter
            self.datacenter_obj = next((dc for dc in self.content.rootFolder.childEntity
                                        if isinstance(dc, vim.Datacenter)), None)
        if not self.datacenter_obj:
            raise Exception("No datacenter object found")

        # Retrieve resource pool (if a cluster is configured, use the cluster's resource pool; otherwise, use the host resource pool)
        compute_resource = None
        if self.config.cluster:
            # Find specified cluster
            for folder in self.datacenter_obj.hostFolder.childEntity:
                if isinstance(folder, vim.ClusterComputeResource) and folder.name == self.config.cluster:
                    compute_resource = folder
                    break
            if not compute_resource:
                logging.error(f"Cluster named {self.config.cluster} not found")
                raise Exception(f"Cluster {self.config.cluster} not found")
        else:
            # Default to the first ComputeResource (cluster or standalone host)
            compute_resource = next((cr for cr in self.datacenter_obj.hostFolder.childEntity
                                      if isinstance(cr, vim.ComputeResource)), None)
        if not compute_resource:
            raise Exception("No compute resource (cluster or host) found")
        self.resource_pool = compute_resource.resourcePool
        logging.info(f"Using resource pool: {self.resource_pool.name}")

        # Retrieve datastore object
        if self.config.datastore:
            # Find specified datastore in the datacenter
            self.datastore_obj = next((ds for ds in self.datacenter_obj.datastoreFolder.childEntity
                                       if isinstance(ds, vim.Datastore) and ds.name == self.config.datastore), None)
            if not self.datastore_obj:
                logging.error(f"Datastore named {self.config.datastore} not found")
                raise Exception(f"Datastore {self.config.datastore} not found")
        else:
            # Default to the datastore with the largest available capacity
            datastores = [ds for ds in self.datacenter_obj.datastoreFolder.childEntity if isinstance(ds, vim.Datastore)]
            if not datastores:
                raise Exception("No available datastore found in the datacenter")
            # Select the one with the maximum free space
            self.datastore_obj = max(datastores, key=lambda ds: ds.summary.freeSpace)
        logging.info(f"Using datastore: {self.datastore_obj.name}")

        # Retrieve network object (network or distributed virtual portgroup)
        if self.config.network:
            # Find specified network in the datacenter network list
            networks = self.datacenter_obj.networkFolder.childEntity
            self.network_obj = next((net for net in networks if net.name == self.config.network), None)
            if not self.network_obj:
                logging.error(f"Network {self.config.network} not found")
                raise Exception(f"Network {self.config.network} not found")
            logging.info(f"Using network: {self.network_obj.name}")
        else:
            self.network_obj = None  # If no network is specified, VM creation can choose to not connect to a network

    def list_vms(self) -> list:
        """List all virtual machine names."""
        vm_list = []
        # Create a view to iterate over all virtual machines
        container = self.content.viewManager.CreateContainerView(self.content.rootFolder, [vim.VirtualMachine], True)
        for vm in container.view:
            vm_list.append(vm.name)
        container.Destroy()
        return vm_list

    def find_vm(self, name: str) -> Optional[vim.VirtualMachine]:
        """Find virtual machine object by name."""
        container = self.content.viewManager.CreateContainerView(self.content.rootFolder, [vim.VirtualMachine], True)
        vm_obj = None
        for vm in container.view:
            if vm.name == name:
                vm_obj = vm
                break
        container.Destroy()
        return vm_obj

    def get_vm_performance(self, vm_name: str) -> Dict[str, Any]:
        """Retrieve performance data (CPU, memory, storage, and network) for the specified virtual machine."""
        vm = self.find_vm(vm_name)
        if not vm:
            raise Exception(f"VM {vm_name} not found")
        # CPU and memory usage (obtained from quickStats)
        stats = {}
        qs = vm.summary.quickStats
        stats["cpu_usage"] = qs.overallCpuUsage  # MHz
        stats["memory_usage"] = qs.guestMemoryUsage  # MB
        # Storage usage (committed storage, in GB)
        committed = vm.summary.storage.committed if vm.summary.storage else 0
        stats["storage_usage"] = round(committed / (1024**3), 2)  # Convert to GB
        # Network usage (obtained from host or VM NIC statistics, latest sample)
        # Here we simply obtain the latest performance counter for VM network I/O
        net_bytes_transmitted = 0
        net_bytes_received = 0
        try:
            pm = self.content.perfManager
            # Define performance counter IDs to query: network transmitted and received bytes
            counter_ids = []
            for c in pm.perfCounter:
                counter_full_name = f"{c.groupInfo.key}.{c.nameInfo.key}.{c.rollupType}"
                if counter_full_name in ("net.transmitted.average", "net.received.average"):
                    counter_ids.append(c.key)
            if counter_ids:
                query = vim.PerformanceManager.QuerySpec(maxSample=1, entity=vm, metricId=[vim.PerformanceManager.MetricId(counterId=cid, instance="*") for cid in counter_ids])
                stats_res = pm.QueryStats(querySpec=[query])
                for series in stats_res[0].value:
                    # Sum data from each network interface
                    if series.id.counterId == counter_ids[0]:
                        net_bytes_transmitted = sum(series.value)
                    elif series.id.counterId == counter_ids[1]:
                        net_bytes_received = sum(series.value)
            stats["network_transmit_KBps"] = net_bytes_transmitted
            stats["network_receive_KBps"] = net_bytes_received
        except Exception as e:
            # If obtaining performance counters fails, log the error but do not terminate
            logging.warning(f"Failed to retrieve network performance data: {e}")
            stats["network_transmit_KBps"] = None
            stats["network_receive_KBps"] = None
        return stats

    def get_vm_details(self, vm_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific virtual machine."""
        vm = self.find_vm(vm_name)
        if not vm:
            raise Exception(f"VM {vm_name} not found")
        
        details = {
            "name": vm.name,
            "power_state": str(vm.runtime.powerState),
            "guest_os": vm.config.guestFullName if vm.config else "Unknown",
            "cpu_count": vm.config.hardware.numCPU if vm.config else 0,
            "memory_mb": vm.config.hardware.memoryMB if vm.config else 0,
            "uuid": vm.config.uuid if vm.config else None,
            "instance_uuid": vm.config.instanceUuid if vm.config else None,
            "ip_address": vm.guest.ipAddress if vm.guest else None,
            "tools_status": str(vm.guest.toolsStatus) if vm.guest else "Unknown",
            "tools_version": vm.guest.toolsVersion if vm.guest else None,
            "hostname": vm.guest.hostName if vm.guest else None,
            "template": vm.config.template if vm.config else False,
            "annotation": vm.config.annotation if vm.config else "",
        }
        
        # Get disk information
        if vm.config and vm.config.hardware:
            disks = []
            for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualDisk):
                    disk_info = {
                        "label": device.deviceInfo.label,
                        "capacity_gb": round(device.capacityInKB / (1024**2), 2),
                        "disk_mode": device.backing.diskMode if hasattr(device.backing, 'diskMode') else None,
                    }
                    disks.append(disk_info)
            details["disks"] = disks
        
        # Get network adapter information
        if vm.config and vm.config.hardware:
            networks = []
            for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard):
                    net_info = {
                        "label": device.deviceInfo.label,
                        "mac_address": device.macAddress,
                        "connected": device.connectable.connected if device.connectable else False,
                    }
                    if hasattr(device.backing, 'deviceName'):
                        net_info["network"] = device.backing.deviceName
                    networks.append(net_info)
            details["networks"] = networks
        
        return details

    def list_templates(self) -> list:
        """List all virtual machine templates."""
        templates = []
        container = self.content.viewManager.CreateContainerView(self.content.rootFolder, [vim.VirtualMachine], True)
        for vm in container.view:
            if vm.config and vm.config.template:
                templates.append(vm.name)
        container.Destroy()
        return templates

    def list_datastores(self) -> list:
        """List all datastores with their details."""
        datastores = []
        container = self.content.viewManager.CreateContainerView(self.content.rootFolder, [vim.Datastore], True)
        for ds in container.view:
            ds_info = {
                "name": ds.name,
                "type": ds.summary.type,
                "capacity_gb": round(ds.summary.capacity / (1024**3), 2),
                "free_space_gb": round(ds.summary.freeSpace / (1024**3), 2),
                "accessible": ds.summary.accessible,
                "maintenance_mode": ds.summary.maintenanceMode if hasattr(ds.summary, 'maintenanceMode') else "normal",
            }
            datastores.append(ds_info)
        container.Destroy()
        return datastores

    def list_networks(self) -> list:
        """List all networks."""
        networks = []
        container = self.content.viewManager.CreateContainerView(self.content.rootFolder, [vim.Network], True)
        for net in container.view:
            net_info = {
                "name": net.name,
                "accessible": net.summary.accessible if hasattr(net.summary, 'accessible') else True,
            }
            # Check if it's a distributed virtual portgroup
            if isinstance(net, vim.dvs.DistributedVirtualPortgroup):
                net_info["type"] = "DistributedVirtualPortgroup"
                net_info["vlan"] = net.config.defaultPortConfig.vlan.vlanId if hasattr(net.config.defaultPortConfig, 'vlan') else None
            else:
                net_info["type"] = "Network"
            networks.append(net_info)
        container.Destroy()
        return networks

    def list_hosts(self) -> list:
        """List all ESXi hosts."""
        hosts = []
        container = self.content.viewManager.CreateContainerView(self.content.rootFolder, [vim.HostSystem], True)
        for host in container.view:
            hosts.append(host.name)
        container.Destroy()
        return hosts

    def find_host(self, name: str) -> Optional[vim.HostSystem]:
        """Find host object by name."""
        container = self.content.viewManager.CreateContainerView(self.content.rootFolder, [vim.HostSystem], True)
        host_obj = None
        for host in container.view:
            if host.name == name:
                host_obj = host
                break
        container.Destroy()
        return host_obj

    def get_host_details(self, host_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific host."""
        host = self.find_host(host_name)
        if not host:
            raise Exception(f"Host {host_name} not found")
        
        details = {
            "name": host.name,
            "connection_state": str(host.runtime.connectionState),
            "power_state": str(host.runtime.powerState),
            "standby_mode": str(host.runtime.standbyMode) if host.runtime.standbyMode else None,
            "in_maintenance_mode": host.runtime.inMaintenanceMode,
            "vendor": host.hardware.systemInfo.vendor if host.hardware else None,
            "model": host.hardware.systemInfo.model if host.hardware else None,
            "uuid": host.hardware.systemInfo.uuid if host.hardware else None,
            "cpu_model": host.hardware.cpuInfo.model if host.hardware and host.hardware.cpuInfo else None,
            "cpu_cores": host.hardware.cpuInfo.numCpuCores if host.hardware and host.hardware.cpuInfo else 0,
            "cpu_threads": host.hardware.cpuInfo.numCpuThreads if host.hardware and host.hardware.cpuInfo else 0,
            "cpu_mhz": host.hardware.cpuInfo.hz // 1000000 if host.hardware and host.hardware.cpuInfo else 0,
            "memory_gb": round(host.hardware.memorySize / (1024**3), 2) if host.hardware else 0,
            "hypervisor_version": host.config.product.version if host.config and host.config.product else None,
            "hypervisor_build": host.config.product.build if host.config and host.config.product else None,
        }
        
        return details

    def get_host_performance_metrics(self, host_name: str) -> Dict[str, Any]:
        """Get performance metrics for a specific host."""
        host = self.find_host(host_name)
        if not host:
            raise Exception(f"Host {host_name} not found")
        
        metrics = {
            "cpu_usage_mhz": host.summary.quickStats.overallCpuUsage if host.summary.quickStats else 0,
            "memory_usage_mb": host.summary.quickStats.overallMemoryUsage if host.summary.quickStats else 0,
            "uptime_seconds": host.summary.quickStats.uptime if host.summary.quickStats else 0,
        }
        
        return metrics

    def get_host_hardware_health(self, host_name: str) -> Dict[str, Any]:
        """Get hardware health information for a specific host."""
        host = self.find_host(host_name)
        if not host:
            raise Exception(f"Host {host_name} not found")
        
        health = {
            "overall_status": str(host.overallStatus),
            "hardware_status": [],
        }
        
        # Get hardware sensor information if available
        if hasattr(host.runtime, 'healthSystemRuntime') and host.runtime.healthSystemRuntime:
            health_info = host.runtime.healthSystemRuntime
            if hasattr(health_info, 'systemHealthInfo') and health_info.systemHealthInfo:
                sensor_info = health_info.systemHealthInfo.numericSensorInfo
                if sensor_info:
                    for sensor in sensor_info:
                        sensor_data = {
                            "name": sensor.name,
                            "health_state": str(sensor.healthState),
                            "current_reading": sensor.currentReading,
                            "unit": sensor.unitModifier,
                            "sensor_type": sensor.sensorType,
                        }
                        health["hardware_status"].append(sensor_data)
        
        return health

    def get_host_performance(self, host_name: str) -> Dict[str, Any]:
        """Get detailed performance data for a specific host."""
        host = self.find_host(host_name)
        if not host:
            raise Exception(f"Host {host_name} not found")
        
        stats = {}
        qs = host.summary.quickStats
        
        # Basic performance stats
        stats["cpu_usage_mhz"] = qs.overallCpuUsage if qs else 0
        stats["memory_usage_mb"] = qs.overallMemoryUsage if qs else 0
        stats["uptime_seconds"] = qs.uptime if qs else 0
        
        # Calculate utilization percentages
        if host.hardware:
            total_cpu_mhz = host.hardware.cpuInfo.numCpuCores * (host.hardware.cpuInfo.hz // 1000000) if host.hardware.cpuInfo else 0
            total_memory_mb = host.hardware.memorySize // (1024**2) if host.hardware.memorySize else 0
            
            stats["cpu_total_mhz"] = total_cpu_mhz
            stats["cpu_usage_percent"] = round((stats["cpu_usage_mhz"] / total_cpu_mhz * 100), 2) if total_cpu_mhz > 0 else 0
            stats["memory_total_mb"] = total_memory_mb
            stats["memory_usage_percent"] = round((stats["memory_usage_mb"] / total_memory_mb * 100), 2) if total_memory_mb > 0 else 0
        
        return stats

    def list_performance_counters(self) -> list:
        """List available performance counters."""
        counters = []
        pm = self.content.perfManager
        
        for counter in pm.perfCounter:
            counter_info = {
                "key": counter.key,
                "group": counter.groupInfo.key,
                "name": counter.nameInfo.key,
                "rollup_type": str(counter.rollupType),
                "stats_type": str(counter.statsType),
                "unit": counter.unitInfo.key,
                "description": counter.nameInfo.summary if counter.nameInfo else "",
            }
            counters.append(counter_info)
        
        return counters

    def get_vm_summary_stats(self, vm_name: str) -> Dict[str, Any]:
        """Get summary statistics for a virtual machine."""
        vm = self.find_vm(vm_name)
        if not vm:
            raise Exception(f"VM {vm_name} not found")
        
        stats = {
            "name": vm.name,
            "power_state": str(vm.runtime.powerState),
            "overall_cpu_usage_mhz": vm.summary.quickStats.overallCpuUsage if vm.summary.quickStats else 0,
            "overall_cpu_demand_mhz": vm.summary.quickStats.overallCpuDemand if vm.summary.quickStats else 0,
            "guest_memory_usage_mb": vm.summary.quickStats.guestMemoryUsage if vm.summary.quickStats else 0,
            "host_memory_usage_mb": vm.summary.quickStats.hostMemoryUsage if vm.summary.quickStats else 0,
            "uptime_seconds": vm.summary.quickStats.uptimeSeconds if vm.summary.quickStats else 0,
            "committed_storage_gb": round(vm.summary.storage.committed / (1024**3), 2) if vm.summary.storage else 0,
            "uncommitted_storage_gb": round(vm.summary.storage.uncommitted / (1024**3), 2) if vm.summary.storage else 0,
        }
        
        return stats

    def create_vm(self, name: str, cpus: int, memory_mb: int, datastore: Optional[str] = None, network: Optional[str] = None) -> str:
        """Create a new virtual machine (from scratch, with an empty disk and optional network)."""
        # If a specific datastore or network is provided, update the corresponding object accordingly
        datastore_obj = self.datastore_obj
        network_obj = self.network_obj
        if datastore:
            datastore_obj = next((ds for ds in self.datacenter_obj.datastoreFolder.childEntity
                                   if isinstance(ds, vim.Datastore) and ds.name == datastore), None)
            if not datastore_obj:
                raise Exception(f"Specified datastore {datastore} not found")
        if network:
            networks = self.datacenter_obj.networkFolder.childEntity
            network_obj = next((net for net in networks if net.name == network), None)
            if not network_obj:
                raise Exception(f"Specified network {network} not found")

        # Build VM configuration specification
        vm_spec = vim.vm.ConfigSpec(name=name, memoryMB=memory_mb, numCPUs=cpus, guestId="otherGuest")  # guestId can be adjusted as needed
        device_specs = []

        # Add SCSI controller
        controller_spec = vim.vm.device.VirtualDeviceSpec()
        controller_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        controller_spec.device = vim.vm.device.ParaVirtualSCSIController()  # Using ParaVirtual SCSI controller
        controller_spec.device.deviceInfo = vim.Description(label="SCSI Controller", summary="ParaVirtual SCSI Controller")
        controller_spec.device.busNumber = 0
        controller_spec.device.sharedBus = vim.vm.device.VirtualSCSIController.Sharing.noSharing
        # Set a temporary negative key for the controller for later reference
        controller_spec.device.key = -101
        device_specs.append(controller_spec)

        # Add virtual disk
        disk_spec = vim.vm.device.VirtualDeviceSpec()
        disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        disk_spec.fileOperation = vim.vm.device.VirtualDeviceSpec.FileOperation.create
        disk_spec.device = vim.vm.device.VirtualDisk()
        disk_spec.device.capacityInKB = 1024 * 1024 * 10  # Create a 10GB disk
        disk_spec.device.deviceInfo = vim.Description(label="Hard Disk 1", summary="10 GB disk")
        disk_spec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
        disk_spec.device.backing.diskMode = "persistent"
        disk_spec.device.backing.thinProvisioned = True  # Thin provisioning
        disk_spec.device.backing.datastore = datastore_obj
        # Attach the disk to the previously created controller
        disk_spec.device.controllerKey = controller_spec.device.key
        disk_spec.device.unitNumber = 0
        device_specs.append(disk_spec)

        # If a network is provided, add a virtual network adapter
        if network_obj:
            nic_spec = vim.vm.device.VirtualDeviceSpec()
            nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            nic_spec.device = vim.vm.device.VirtualVmxnet3()  # Using VMXNET3 network adapter
            nic_spec.device.deviceInfo = vim.Description(label="Network Adapter 1", summary=network_obj.name)
            if isinstance(network_obj, vim.Network):
                nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo(network=network_obj, deviceName=network_obj.name)
            elif isinstance(network_obj, vim.dvs.DistributedVirtualPortgroup):
                # Distributed virtual switch portgroup
                dvs_uuid = network_obj.config.distributedVirtualSwitch.uuid
                port_key = network_obj.key
                nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo(
                    port=vim.dvs.PortConnection(portgroupKey=port_key, switchUuid=dvs_uuid)
                )
            nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo(startConnected=True, allowGuestControl=True)
            device_specs.append(nic_spec)

        vm_spec.deviceChange = device_specs

        # Get the folder in which to place the VM (default is the datacenter's vmFolder)
        vm_folder = self.datacenter_obj.vmFolder
        # Create the VM in the specified resource pool
        try:
            task = vm_folder.CreateVM_Task(config=vm_spec, pool=self.resource_pool)
            # Wait for the task to complete
            while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                continue
            if task.info.state == vim.TaskInfo.State.error:
                raise task.info.error
        except Exception as e:
            logging.error(f"Failed to create virtual machine: {e}")
            raise
        logging.info(f"Virtual machine created: {name}")
        return f"VM '{name}' created."

    def clone_vm(self, template_name: str, new_name: str) -> str:
        """Clone a new virtual machine from an existing template or VM."""
        template_vm = self.find_vm(template_name)
        if not template_vm:
            raise Exception(f"Template virtual machine {template_name} not found")
        vm_folder = template_vm.parent  # Place the new VM in the same folder as the template
        if not isinstance(vm_folder, vim.Folder):
            vm_folder = self.datacenter_obj.vmFolder
        # Use the resource pool of the host/cluster where the template is located
        resource_pool = template_vm.resourcePool or self.resource_pool
        relocate_spec = vim.vm.RelocateSpec(pool=resource_pool, datastore=self.datastore_obj)
        clone_spec = vim.vm.CloneSpec(powerOn=False, template=False, location=relocate_spec)
        try:
            task = template_vm.Clone(folder=vm_folder, name=new_name, spec=clone_spec)
            while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                continue
            if task.info.state == vim.TaskInfo.State.error:
                raise task.info.error
        except Exception as e:
            logging.error(f"Failed to clone virtual machine: {e}")
            raise
        logging.info(f"Cloned virtual machine {template_name} to new VM: {new_name}")
        return f"VM '{new_name}' cloned from '{template_name}'."

    def create_vm_custom(self, name: str, cpus: int, memory_mb: int, disk_size_gb: int = 10,
                        guest_id: str = "otherGuest", datastore: Optional[str] = None,
                        network: Optional[str] = None, thin_provisioned: bool = True,
                        annotation: Optional[str] = None) -> str:
        """Create a custom virtual machine with more configuration options."""
        # If a specific datastore or network is provided, update the corresponding object accordingly
        datastore_obj = self.datastore_obj
        network_obj = self.network_obj
        if datastore:
            datastore_obj = next((ds for ds in self.datacenter_obj.datastoreFolder.childEntity
                                   if isinstance(ds, vim.Datastore) and ds.name == datastore), None)
            if not datastore_obj:
                raise Exception(f"Specified datastore {datastore} not found")
        if network:
            networks = self.datacenter_obj.networkFolder.childEntity
            network_obj = next((net for net in networks if net.name == network), None)
            if not network_obj:
                raise Exception(f"Specified network {network} not found")

        # Build VM configuration specification
        vm_spec = vim.vm.ConfigSpec(name=name, memoryMB=memory_mb, numCPUs=cpus, guestId=guest_id)
        if annotation:
            vm_spec.annotation = annotation
        
        device_specs = []

        # Add SCSI controller
        controller_spec = vim.vm.device.VirtualDeviceSpec()
        controller_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        controller_spec.device = vim.vm.device.ParaVirtualSCSIController()
        controller_spec.device.deviceInfo = vim.Description(label="SCSI Controller", summary="ParaVirtual SCSI Controller")
        controller_spec.device.busNumber = 0
        controller_spec.device.sharedBus = vim.vm.device.VirtualSCSIController.Sharing.noSharing
        controller_spec.device.key = -101
        device_specs.append(controller_spec)

        # Add virtual disk
        disk_spec = vim.vm.device.VirtualDeviceSpec()
        disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        disk_spec.fileOperation = vim.vm.device.VirtualDeviceSpec.FileOperation.create
        disk_spec.device = vim.vm.device.VirtualDisk()
        disk_spec.device.capacityInKB = 1024 * 1024 * disk_size_gb
        disk_spec.device.deviceInfo = vim.Description(label="Hard Disk 1", summary=f"{disk_size_gb} GB disk")
        disk_spec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
        disk_spec.device.backing.diskMode = "persistent"
        disk_spec.device.backing.thinProvisioned = thin_provisioned
        disk_spec.device.backing.datastore = datastore_obj
        disk_spec.device.controllerKey = controller_spec.device.key
        disk_spec.device.unitNumber = 0
        device_specs.append(disk_spec)

        # If a network is provided, add a virtual network adapter
        if network_obj:
            nic_spec = vim.vm.device.VirtualDeviceSpec()
            nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            nic_spec.device = vim.vm.device.VirtualVmxnet3()
            nic_spec.device.deviceInfo = vim.Description(label="Network Adapter 1", summary=network_obj.name)
            if isinstance(network_obj, vim.Network):
                nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo(network=network_obj, deviceName=network_obj.name)
            elif isinstance(network_obj, vim.dvs.DistributedVirtualPortgroup):
                dvs_uuid = network_obj.config.distributedVirtualSwitch.uuid
                port_key = network_obj.key
                nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo(
                    port=vim.dvs.PortConnection(portgroupKey=port_key, switchUuid=dvs_uuid)
                )
            nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo(startConnected=True, allowGuestControl=True)
            device_specs.append(nic_spec)

        vm_spec.deviceChange = device_specs

        # Get the folder in which to place the VM
        vm_folder = self.datacenter_obj.vmFolder
        try:
            task = vm_folder.CreateVM_Task(config=vm_spec, pool=self.resource_pool)
            while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                continue
            if task.info.state == vim.TaskInfo.State.error:
                raise task.info.error
        except Exception as e:
            logging.error(f"Failed to create custom virtual machine: {e}")
            raise
        logging.info(f"Custom virtual machine created: {name}")
        return f"Custom VM '{name}' created with {cpus} CPUs, {memory_mb}MB RAM, and {disk_size_gb}GB disk."

    def delete_vm(self, name: str) -> str:
        """Delete the specified virtual machine."""
        vm = self.find_vm(name)
        if not vm:
            raise Exception(f"Virtual machine {name} not found")
        try:
            task = vm.Destroy_Task()
            while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                continue
            if task.info.state == vim.TaskInfo.State.error:
                raise task.info.error
        except Exception as e:
            logging.error(f"Failed to delete virtual machine: {e}")
            raise
        logging.info(f"Virtual machine deleted: {name}")
        return f"VM '{name}' deleted."

    def power_on_vm(self, name: str) -> str:
        """Power on the specified virtual machine."""
        vm = self.find_vm(name)
        if not vm:
            raise Exception(f"Virtual machine {name} not found")
        if vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOn:
            return f"VM '{name}' is already powered on."
        task = vm.PowerOnVM_Task()
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            continue
        if task.info.state == vim.TaskInfo.State.error:
            raise task.info.error
        logging.info(f"Virtual machine powered on: {name}")
        return f"VM '{name}' powered on."

    def power_off_vm(self, name: str) -> str:
        """Power off the specified virtual machine."""
        vm = self.find_vm(name)
        if not vm:
            raise Exception(f"Virtual machine {name} not found")
        if vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOff:
            return f"VM '{name}' is already powered off."
        task = vm.PowerOffVM_Task()
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            continue
        if task.info.state == vim.TaskInfo.State.error:
            raise task.info.error
        logging.info(f"Virtual machine powered off: {name}")
        return f"VM '{name}' powered off."

    def list_datastore_clusters(self) -> list:
        """List all datastore clusters (StoragePods)."""
        clusters = []
        container = self.content.viewManager.CreateContainerView(
            self.content.rootFolder, [vim.StoragePod], True)
        for pod in container.view:
            cluster_info = {
                "name": pod.name,
                "capacity_gb": round(pod.summary.capacity / (1024**3), 2) if pod.summary else 0,
                "free_space_gb": round(pod.summary.freeSpace / (1024**3), 2) if pod.summary else 0,
                "datastores": [ds.name for ds in pod.childEntity if isinstance(ds, vim.Datastore)]
            }
            clusters.append(cluster_info)
        container.Destroy()
        return clusters

    def wait_for_task(self, task: vim.Task, timeout: int = 300) -> Dict[str, Any]:
        """Wait for a vCenter task to complete or timeout."""
        import time
        start_time = time.time()
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            if time.time() - start_time > timeout:
                return {
                    "status": "timeout",
                    "message": f"Task timed out after {timeout} seconds",
                    "task_state": str(task.info.state)
                }
            time.sleep(1)
        
        if task.info.state == vim.TaskInfo.State.success:
            return {
                "status": "success",
                "message": "Task completed successfully",
                "result": str(task.info.result) if task.info.result else None
            }
        else:
            return {
                "status": "error",
                "message": str(task.info.error) if task.info.error else "Unknown error",
                "error": str(task.info.error) if task.info.error else None
            }

    def create_snapshot(self, vm_name: str, snapshot_name: str, description: str = "", 
                       memory: bool = False, quiesce: bool = False) -> str:
        """Create a snapshot of a virtual machine."""
        vm = self.find_vm(vm_name)
        if not vm:
            raise Exception(f"VM {vm_name} not found")
        
        task = vm.CreateSnapshot(snapshot_name, description, memory, quiesce)
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            continue
        if task.info.state == vim.TaskInfo.State.error:
            raise task.info.error
        
        logging.info(f"Snapshot '{snapshot_name}' created for VM '{vm_name}'")
        return f"Snapshot '{snapshot_name}' created successfully for VM '{vm_name}'"

    def remove_snapshot(self, vm_name: str, snapshot_name: str, remove_children: bool = True) -> str:
        """Remove a snapshot from a virtual machine."""
        vm = self.find_vm(vm_name)
        if not vm:
            raise Exception(f"VM {vm_name} not found")
        
        if not vm.snapshot:
            raise Exception(f"VM {vm_name} has no snapshots")
        
        snapshot = self._find_snapshot_by_name(vm.snapshot.rootSnapshotList, snapshot_name)
        if not snapshot:
            raise Exception(f"Snapshot '{snapshot_name}' not found on VM '{vm_name}'")
        
        task = snapshot.snapshot.RemoveSnapshot_Task(remove_children)
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            continue
        if task.info.state == vim.TaskInfo.State.error:
            raise task.info.error
        
        logging.info(f"Snapshot '{snapshot_name}' removed from VM '{vm_name}'")
        return f"Snapshot '{snapshot_name}' removed successfully from VM '{vm_name}'"

    def revert_snapshot(self, vm_name: str, snapshot_name: str) -> str:
        """Revert a virtual machine to a specific snapshot."""
        vm = self.find_vm(vm_name)
        if not vm:
            raise Exception(f"VM {vm_name} not found")
        
        if not vm.snapshot:
            raise Exception(f"VM {vm_name} has no snapshots")
        
        snapshot = self._find_snapshot_by_name(vm.snapshot.rootSnapshotList, snapshot_name)
        if not snapshot:
            raise Exception(f"Snapshot '{snapshot_name}' not found on VM '{vm_name}'")
        
        task = snapshot.snapshot.RevertToSnapshot_Task()
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            continue
        if task.info.state == vim.TaskInfo.State.error:
            raise task.info.error
        
        logging.info(f"VM '{vm_name}' reverted to snapshot '{snapshot_name}'")
        return f"VM '{vm_name}' reverted successfully to snapshot '{snapshot_name}'"

    def list_snapshots(self, vm_name: str) -> list:
        """List all snapshots for a virtual machine."""
        vm = self.find_vm(vm_name)
        if not vm:
            raise Exception(f"VM {vm_name} not found")
        
        if not vm.snapshot:
            return []
        
        snapshots = []
        self._collect_snapshots(vm.snapshot.rootSnapshotList, snapshots)
        return snapshots

    def remove_all_snapshots(self, vm_name: str) -> str:
        """Remove all snapshots from a virtual machine."""
        vm = self.find_vm(vm_name)
        if not vm:
            raise Exception(f"VM {vm_name} not found")
        
        if not vm.snapshot:
            return f"VM '{vm_name}' has no snapshots to remove"
        
        task = vm.RemoveAllSnapshots()
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            continue
        if task.info.state == vim.TaskInfo.State.error:
            raise task.info.error
        
        logging.info(f"All snapshots removed from VM '{vm_name}'")
        return f"All snapshots removed successfully from VM '{vm_name}'"

    def _find_snapshot_by_name(self, snapshots, name: str):
        """Recursively find a snapshot by name."""
        for snapshot in snapshots:
            if snapshot.name == name:
                return snapshot
            if snapshot.childSnapshotList:
                result = self._find_snapshot_by_name(snapshot.childSnapshotList, name)
                if result:
                    return result
        return None

    def _collect_snapshots(self, snapshots, result: list, level: int = 0):
        """Recursively collect snapshot information."""
        for snapshot in snapshots:
            snap_info = {
                "name": snapshot.name,
                "description": snapshot.description,
                "create_time": str(snapshot.createTime),
                "state": str(snapshot.state),
                "level": level
            }
            result.append(snap_info)
            if snapshot.childSnapshotList:
                self._collect_snapshots(snapshot.childSnapshotList, result, level + 1)

    def execute_program_in_vm(self, vm_name: str, username: str, password: str, 
                             program_path: str, program_arguments: str = "") -> Dict[str, Any]:
        """Execute a program inside a VM using VMware Tools."""
        import time
        import re
        
        vm = self.find_vm(vm_name)
        if not vm:
            raise Exception(f"VM {vm_name} not found")
        
        # Check VMware Tools status
        tools_status = vm.guest.toolsStatus
        if tools_status in ('toolsNotInstalled', 'toolsNotRunning'):
            raise Exception(
                "VMware Tools is either not running or not installed. "
                "Ensure VMware Tools is running before executing programs.")
        
        # Create credentials
        creds = vim.vm.guest.NamePasswordAuthentication(
            username=username, password=password)
        
        # Get process manager
        process_manager = self.content.guestOperationsManager.processManager
        
        # Create program spec
        if program_arguments:
            program_spec = vim.vm.guest.ProcessManager.ProgramSpec(
                programPath=program_path,
                arguments=program_arguments)
        else:
            program_spec = vim.vm.guest.ProcessManager.ProgramSpec(
                programPath=program_path)
        
        # Start the program
        pid = process_manager.StartProgramInGuest(vm, creds, program_spec)
        
        if pid > 0:
            logging.info(f"Program started in VM '{vm_name}', PID: {pid}")
            
            # Wait for program to complete (with timeout)
            max_wait = 30  # seconds
            wait_count = 0
            while wait_count < max_wait:
                processes = process_manager.ListProcessesInGuest(vm, creds, [pid])
                if processes:
                    exit_code = processes[0].exitCode
                    # Check if process has completed
                    if exit_code is not None:
                        return {
                            "pid": pid,
                            "exit_code": exit_code,
                            "status": "completed",
                            "success": exit_code == 0
                        }
                time.sleep(1)
                wait_count += 1
            
            return {
                "pid": pid,
                "status": "running",
                "message": "Program is still running after timeout"
            }
        else:
            raise Exception("Failed to start program in VM")

    def upload_file_to_vm(self, vm_name: str, username: str, password: str,
                         local_file_path: str, remote_file_path: str) -> str:
        """Upload a file to a VM using VMware Tools."""
        import re
        import requests
        
        vm = self.find_vm(vm_name)
        if not vm:
            raise Exception(f"VM {vm_name} not found")
        
        # Check VMware Tools status
        tools_status = vm.guest.toolsStatus
        if tools_status in ('toolsNotInstalled', 'toolsNotRunning'):
            raise Exception(
                "VMware Tools is either not running or not installed.")
        
        # Create credentials
        creds = vim.vm.guest.NamePasswordAuthentication(
            username=username, password=password)
        
        # Read the local file
        with open(local_file_path, 'rb') as f:
            file_data = f.read()
        
        # Get file manager
        file_manager = self.content.guestOperationsManager.fileManager
        
        # Create file attributes
        file_attribute = vim.vm.guest.FileManager.FileAttributes()
        
        # Initiate file transfer
        url = file_manager.InitiateFileTransferToGuest(
            vm, creds, remote_file_path, file_attribute, len(file_data), True)
        
        # Fix the URL (replace wildcard with actual host)
        url = re.sub(r"^https://\*:", f"https://{self.config.vcenter_host}:", url)
        
        # Upload the file
        resp = requests.put(url, data=file_data, verify=False)
        
        if resp.status_code == 200:
            logging.info(f"File uploaded to VM '{vm_name}': {remote_file_path}")
            return f"Successfully uploaded file to {remote_file_path} in VM '{vm_name}'"
        else:
            raise Exception(f"Failed to upload file. HTTP status: {resp.status_code}")

    def upload_file_to_datastore(self, datastore_name: str, local_file_path: str,
                                 remote_file_path: str) -> str:
        """Upload a file to a datastore."""
        import requests
        
        # Find the datastore
        datastore = None
        container = self.content.viewManager.CreateContainerView(
            self.content.rootFolder, [vim.Datastore], True)
        for ds in container.view:
            if ds.name == datastore_name:
                datastore = ds
                break
        container.Destroy()
        
        if not datastore:
            raise Exception(f"Datastore '{datastore_name}' not found")
        
        # Build the URL
        if not remote_file_path.startswith("/"):
            remote_file_path = "/" + remote_file_path
        
        resource = "/folder" + remote_file_path
        params = {
            "dsName": datastore.name,
            "dcPath": self.datacenter_obj.name
        }
        http_url = f"https://{self.config.vcenter_host}:443{resource}"
        
        # Get the session cookie
        client_cookie = self.si._stub.cookie
        cookie_name = client_cookie.split("=", 1)[0]
        cookie_value = client_cookie.split("=", 1)[1].split(";", 1)[0]
        cookie_path = client_cookie.split("=", 1)[1].split(";", 1)[1].split(";", 1)[0].lstrip()
        cookie_text = " " + cookie_value + "; $" + cookie_path
        cookie = {cookie_name: cookie_text}
        
        # Set headers
        headers = {'Content-Type': 'application/octet-stream'}
        
        # Upload the file
        with open(local_file_path, "rb") as file_data:
            resp = requests.put(
                http_url,
                params=params,
                data=file_data,
                headers=headers,
                cookies=cookie,
                verify=False
            )
        
        if resp.status_code in (200, 201):
            logging.info(f"File uploaded to datastore '{datastore_name}': {remote_file_path}")
            return f"Successfully uploaded file to {remote_file_path} on datastore '{datastore_name}'"
        else:
            raise Exception(f"Failed to upload file. HTTP status: {resp.status_code}")
