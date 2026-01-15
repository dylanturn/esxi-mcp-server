"""MCP tool handler functions."""

import logging
from typing import Optional

from .vmware_manager import VMwareManager
from .config import Config


class ToolHandlers:
    """Container for MCP tool handler functions."""
    
    def __init__(self, manager: VMwareManager, config: Config):
        self.manager = manager
        self.config = config
    
    def _check_auth(self):
        """Internal helper: Check API access permissions."""
        if self.config.api_key:
            # If an API key is configured, require that manager.authenticated is True
            if not self.manager.authenticated:
                raise Exception("Unauthorized: API key required.")
    
    def create_vm(self, name: str, cpu: int, memory: int, datastore: Optional[str] = None, network: Optional[str] = None) -> str:
        """Create a new virtual machine."""
        self._check_auth()
        return self.manager.create_vm(name, cpu, memory, datastore, network)
    
    def clone_vm(self, template_name: str, new_name: str) -> str:
        """Clone a virtual machine from a template."""
        self._check_auth()
        return self.manager.clone_vm(template_name, new_name)
    
    def delete_vm(self, name: str) -> str:
        """Delete the specified virtual machine."""
        self._check_auth()
        return self.manager.delete_vm(name)
    
    def power_on_vm(self, name: str) -> str:
        """Power on the specified virtual machine."""
        self._check_auth()
        return self.manager.power_on_vm(name)
    
    def power_off_vm(self, name: str) -> str:
        """Power off the specified virtual machine."""
        self._check_auth()
        return self.manager.power_off_vm(name)
    
    def list_vms(self) -> list:
        """Return a list of all virtual machine names."""
        self._check_auth()
        return self.manager.list_vms()
    
    def get_vm_details(self, vm_name: str) -> dict:
        """Get detailed information about a virtual machine."""
        self._check_auth()
        return self.manager.get_vm_details(vm_name)
    
    def get_vm_performance(self, vm_name: str) -> dict:
        """Get performance data for a virtual machine."""
        self._check_auth()
        return self.manager.get_vm_performance(vm_name)
    
    def get_vm_summary_stats(self, vm_name: str) -> dict:
        """Get summary statistics for a virtual machine."""
        self._check_auth()
        return self.manager.get_vm_summary_stats(vm_name)
    
    def create_vm_custom(self, name: str, cpu: int, memory: int, disk_size_gb: int = 10,
                        guest_id: str = "otherGuest", datastore: Optional[str] = None,
                        network: Optional[str] = None, thin_provisioned: bool = True,
                        annotation: Optional[str] = None) -> str:
        """Create a custom virtual machine with advanced options."""
        self._check_auth()
        return self.manager.create_vm_custom(name, cpu, memory, disk_size_gb, guest_id,
                                            datastore, network, thin_provisioned, annotation)
    
    def list_templates(self) -> list:
        """List all virtual machine templates."""
        self._check_auth()
        return self.manager.list_templates()
    
    def list_datastores(self) -> list:
        """List all datastores."""
        self._check_auth()
        return self.manager.list_datastores()
    
    def list_datastore_clusters(self) -> list:
        """List all datastore clusters (StoragePods)."""
        self._check_auth()
        return self.manager.list_datastore_clusters()
    
    def list_networks(self) -> list:
        """List all networks."""
        self._check_auth()
        return self.manager.list_networks()
    
    def list_hosts(self) -> list:
        """List all ESXi hosts."""
        self._check_auth()
        return self.manager.list_hosts()
    
    def get_host_details(self, host_name: str) -> dict:
        """Get detailed information about a host."""
        self._check_auth()
        return self.manager.get_host_details(host_name)
    
    def get_host_performance_metrics(self, host_name: str) -> dict:
        """Get performance metrics for a host."""
        self._check_auth()
        return self.manager.get_host_performance_metrics(host_name)
    
    def get_host_hardware_health(self, host_name: str) -> dict:
        """Get hardware health information for a host."""
        self._check_auth()
        return self.manager.get_host_hardware_health(host_name)
    
    def get_host_performance(self, host_name: str) -> dict:
        """Get detailed performance data for a host."""
        self._check_auth()
        return self.manager.get_host_performance(host_name)
    
    def list_performance_counters(self) -> list:
        """List all available performance counters."""
        self._check_auth()
        return self.manager.list_performance_counters()
    
    def create_snapshot(self, vm_name: str, snapshot_name: str, description: str = "",
                       memory: bool = False, quiesce: bool = False) -> str:
        """Create a snapshot of a virtual machine."""
        self._check_auth()
        return self.manager.create_snapshot(vm_name, snapshot_name, description, memory, quiesce)
    
    def remove_snapshot(self, vm_name: str, snapshot_name: str, remove_children: bool = True) -> str:
        """Remove a snapshot from a virtual machine."""
        self._check_auth()
        return self.manager.remove_snapshot(vm_name, snapshot_name, remove_children)
    
    def revert_snapshot(self, vm_name: str, snapshot_name: str) -> str:
        """Revert a virtual machine to a specific snapshot."""
        self._check_auth()
        return self.manager.revert_snapshot(vm_name, snapshot_name)
    
    def list_snapshots(self, vm_name: str) -> list:
        """List all snapshots for a virtual machine."""
        self._check_auth()
        return self.manager.list_snapshots(vm_name)
    
    def remove_all_snapshots(self, vm_name: str) -> str:
        """Remove all snapshots from a virtual machine."""
        self._check_auth()
        return self.manager.remove_all_snapshots(vm_name)
    
    def execute_program_in_vm(self, vm_name: str, username: str, password: str,
                             program_path: str, program_arguments: str = "") -> dict:
        """Execute a program inside a VM."""
        self._check_auth()
        return self.manager.execute_program_in_vm(vm_name, username, password,
                                                 program_path, program_arguments)
    
    def upload_file_to_vm(self, vm_name: str, username: str, password: str,
                         local_file_path: str, remote_file_path: str) -> str:
        """Upload a file to a VM."""
        self._check_auth()
        return self.manager.upload_file_to_vm(vm_name, username, password,
                                             local_file_path, remote_file_path)
    
    def upload_file_to_datastore(self, datastore_name: str, local_file_path: str,
                                 remote_file_path: str) -> str:
        """Upload a file to a datastore."""
        self._check_auth()
        return self.manager.upload_file_to_datastore(datastore_name, local_file_path,
                                                     remote_file_path)
    
    def deploy_ovf(self, ovf_path: str, vmdk_path: str, vm_name: str = None,
                   datastore_name: str = None, resource_pool_name: str = None) -> str:
        """Deploy a VM from OVF and VMDK files."""
        self._check_auth()
        return self.manager.deploy_ovf(ovf_path, vmdk_path, vm_name,
                                      datastore_name, resource_pool_name)
    
    def deploy_ova(self, ova_path: str, vm_name: str = None,
                   datastore_name: str = None, resource_pool_name: str = None) -> str:
        """Deploy a VM from an OVA file."""
        self._check_auth()
        return self.manager.deploy_ova(ova_path, vm_name, datastore_name, resource_pool_name)
    
    def wait_for_updates(self, object_type: str, properties: list,
                        max_wait_seconds: int = 30, max_iterations: int = 1) -> dict:
        """Wait for property updates on vSphere objects."""
        self._check_auth()
        return self.manager.wait_for_updates(object_type, properties,
                                            max_wait_seconds, max_iterations)
    
    def vm_performance_resource(self, vm_name: str) -> dict:
        """Retrieve CPU, memory, storage, and network usage for the specified virtual machine."""
        self._check_auth()
        return self.manager.get_vm_performance(vm_name)
