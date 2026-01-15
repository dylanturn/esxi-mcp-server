"""MCP server initialization and handler registration."""

import json
from mcp.server.lowlevel import Server
from mcp import types

from .tools import ToolHandlers


def create_mcp_server() -> Server:
    """Create and initialize the MCP server."""
    return Server(name="VMware-MCP-Server", version="0.0.1")


def register_handlers(mcp_server: Server, tool_handlers: ToolHandlers):
    """
    Register all MCP tool and resource handlers.
    
    Args:
        mcp_server: The MCP Server instance
        tool_handlers: The ToolHandlers instance containing handler methods
    """
    # Define tools with proper MCP Tool schema (name, description, inputSchema only)
    tools = {
        "create_vm": types.Tool(
            name="create_vm",
            description="Create a new virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "VM name"},
                    "cpu": {"type": "integer", "description": "Number of CPUs"},
                    "memory": {"type": "integer", "description": "Memory in MB"},
                    "datastore": {"type": "string", "description": "Datastore name (optional)"},
                    "network": {"type": "string", "description": "Network name (optional)"}
                },
                "required": ["name", "cpu", "memory"]
            }
        ),
        "clone_vm": types.Tool(
            name="clone_vm",
            description="Clone a virtual machine from a template or existing VM",
            inputSchema={
                "type": "object",
                "properties": {
                    "template_name": {"type": "string", "description": "Name of the template or VM to clone"},
                    "new_name": {"type": "string", "description": "Name for the new VM"}
                },
                "required": ["template_name", "new_name"]
            }
        ),
        "delete_vm": types.Tool(
            name="delete_vm",
            description="Delete a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {"name": {"type": "string", "description": "VM name"}},
                "required": ["name"]
            }
        ),
        "power_on_vm": types.Tool(
            name="power_on_vm",
            description="Power on a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {"name": {"type": "string", "description": "VM name"}},
                "required": ["name"]
            }
        ),
        "power_off_vm": types.Tool(
            name="power_off_vm",
            description="Power off a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {"name": {"type": "string", "description": "VM name"}},
                "required": ["name"]
            }
        ),
        "list_vms": types.Tool(
            name="list_vms",
            description="List all virtual machines",
            inputSchema={"type": "object", "properties": {}}
        ),
        "get_vm_details": types.Tool(
            name="get_vm_details",
            description="Get detailed information about a specific virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_name": {"type": "string", "description": "Name of the virtual machine"}
                },
                "required": ["vm_name"]
            }
        ),
        "get_vm_performance": types.Tool(
            name="get_vm_performance",
            description="Get performance data for a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_name": {"type": "string", "description": "Name of the virtual machine"}
                },
                "required": ["vm_name"]
            }
        ),
        "get_vm_summary_stats": types.Tool(
            name="get_vm_summary_stats",
            description="Get summary statistics for a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_name": {"type": "string", "description": "Name of the virtual machine"}
                },
                "required": ["vm_name"]
            }
        ),
        "create_vm_custom": types.Tool(
            name="create_vm_custom",
            description="Create a custom virtual machine with advanced configuration options",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "VM name"},
                    "cpu": {"type": "integer", "description": "Number of CPUs"},
                    "memory": {"type": "integer", "description": "Memory in MB"},
                    "disk_size_gb": {"type": "integer", "description": "Disk size in GB", "default": 10},
                    "guest_id": {"type": "string", "description": "Guest OS identifier", "default": "otherGuest"},
                    "datastore": {"type": "string", "description": "Datastore name (optional)"},
                    "network": {"type": "string", "description": "Network name (optional)"},
                    "thin_provisioned": {"type": "boolean", "description": "Use thin provisioning", "default": True},
                    "annotation": {"type": "string", "description": "VM annotation/description"}
                },
                "required": ["name", "cpu", "memory"]
            }
        ),
        "list_templates": types.Tool(
            name="list_templates",
            description="List all virtual machine templates",
            inputSchema={"type": "object", "properties": {}}
        ),
        "list_datastores": types.Tool(
            name="list_datastores",
            description="List all datastores with their details",
            inputSchema={"type": "object", "properties": {}}
        ),
        "list_datastore_clusters": types.Tool(
            name="list_datastore_clusters",
            description="List all datastore clusters (StoragePods) with their datastores",
            inputSchema={"type": "object", "properties": {}}
        ),
        "list_networks": types.Tool(
            name="list_networks",
            description="List all networks",
            inputSchema={"type": "object", "properties": {}}
        ),
        "list_hosts": types.Tool(
            name="list_hosts",
            description="List all ESXi hosts",
            inputSchema={"type": "object", "properties": {}}
        ),
        "get_host_details": types.Tool(
            name="get_host_details",
            description="Get detailed information about a specific host",
            inputSchema={
                "type": "object",
                "properties": {
                    "host_name": {"type": "string", "description": "Name of the host"}
                },
                "required": ["host_name"]
            }
        ),
        "get_host_performance_metrics": types.Tool(
            name="get_host_performance_metrics",
            description="Get performance metrics for a specific host",
            inputSchema={
                "type": "object",
                "properties": {
                    "host_name": {"type": "string", "description": "Name of the host"}
                },
                "required": ["host_name"]
            }
        ),
        "get_host_hardware_health": types.Tool(
            name="get_host_hardware_health",
            description="Get hardware health information for a specific host",
            inputSchema={
                "type": "object",
                "properties": {
                    "host_name": {"type": "string", "description": "Name of the host"}
                },
                "required": ["host_name"]
            }
        ),
        "get_host_performance": types.Tool(
            name="get_host_performance",
            description="Get detailed performance data for a specific host",
            inputSchema={
                "type": "object",
                "properties": {
                    "host_name": {"type": "string", "description": "Name of the host"}
                },
                "required": ["host_name"]
            }
        ),
        "list_performance_counters": types.Tool(
            name="list_performance_counters",
            description="List all available performance counters",
            inputSchema={"type": "object", "properties": {}}
        ),
        "create_snapshot": types.Tool(
            name="create_snapshot",
            description="Create a snapshot of a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_name": {"type": "string", "description": "Name of the VM"},
                    "snapshot_name": {"type": "string", "description": "Name for the snapshot"},
                    "description": {"type": "string", "description": "Snapshot description", "default": ""},
                    "memory": {"type": "boolean", "description": "Include VM memory in snapshot", "default": False},
                    "quiesce": {"type": "boolean", "description": "Quiesce guest file system", "default": False}
                },
                "required": ["vm_name", "snapshot_name"]
            }
        ),
        "remove_snapshot": types.Tool(
            name="remove_snapshot",
            description="Remove a snapshot from a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_name": {"type": "string", "description": "Name of the VM"},
                    "snapshot_name": {"type": "string", "description": "Name of the snapshot to remove"},
                    "remove_children": {"type": "boolean", "description": "Remove child snapshots", "default": True}
                },
                "required": ["vm_name", "snapshot_name"]
            }
        ),
        "revert_snapshot": types.Tool(
            name="revert_snapshot",
            description="Revert a virtual machine to a specific snapshot",
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_name": {"type": "string", "description": "Name of the VM"},
                    "snapshot_name": {"type": "string", "description": "Name of the snapshot to revert to"}
                },
                "required": ["vm_name", "snapshot_name"]
            }
        ),
        "list_snapshots": types.Tool(
            name="list_snapshots",
            description="List all snapshots for a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_name": {"type": "string", "description": "Name of the VM"}
                },
                "required": ["vm_name"]
            }
        ),
        "remove_all_snapshots": types.Tool(
            name="remove_all_snapshots",
            description="Remove all snapshots from a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_name": {"type": "string", "description": "Name of the VM"}
                },
                "required": ["vm_name"]
            }
        ),
        "execute_program_in_vm": types.Tool(
            name="execute_program_in_vm",
            description="Execute a program inside a VM using VMware Tools",
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_name": {"type": "string", "description": "Name of the VM"},
                    "username": {"type": "string", "description": "Guest OS username"},
                    "password": {"type": "string", "description": "Guest OS password"},
                    "program_path": {"type": "string", "description": "Full path to the program in guest OS"},
                    "program_arguments": {"type": "string", "description": "Program arguments (optional)", "default": ""}
                },
                "required": ["vm_name", "username", "password", "program_path"]
            }
        ),
        "upload_file_to_vm": types.Tool(
            name="upload_file_to_vm",
            description="Upload a file to a VM using VMware Tools",
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_name": {"type": "string", "description": "Name of the VM"},
                    "username": {"type": "string", "description": "Guest OS username"},
                    "password": {"type": "string", "description": "Guest OS password"},
                    "local_file_path": {"type": "string", "description": "Local file path to upload"},
                    "remote_file_path": {"type": "string", "description": "Destination path in guest OS"}
                },
                "required": ["vm_name", "username", "password", "local_file_path", "remote_file_path"]
            }
        ),
        "upload_file_to_datastore": types.Tool(
            name="upload_file_to_datastore",
            description="Upload a file directly to a datastore",
            inputSchema={
                "type": "object",
                "properties": {
                    "datastore_name": {"type": "string", "description": "Name of the datastore"},
                    "local_file_path": {"type": "string", "description": "Local file path to upload"},
                    "remote_file_path": {"type": "string", "description": "Destination path on datastore"}
                },
                "required": ["datastore_name", "local_file_path", "remote_file_path"]
            }
        ),
        "deploy_ovf": types.Tool(
            name="deploy_ovf",
            description="Deploy a VM from OVF and VMDK files",
            inputSchema={
                "type": "object",
                "properties": {
                    "ovf_path": {"type": "string", "description": "Path to OVF file"},
                    "vmdk_path": {"type": "string", "description": "Path to VMDK file"},
                    "vm_name": {"type": "string", "description": "Name for the new VM (optional)"},
                    "datastore_name": {"type": "string", "description": "Target datastore (optional)"},
                    "resource_pool_name": {"type": "string", "description": "Target resource pool (optional)"}
                },
                "required": ["ovf_path", "vmdk_path"]
            }
        ),
        "deploy_ova": types.Tool(
            name="deploy_ova",
            description="Deploy a VM from an OVA file",
            inputSchema={
                "type": "object",
                "properties": {
                    "ova_path": {"type": "string", "description": "Path to OVA file"},
                    "vm_name": {"type": "string", "description": "Name for the new VM (optional)"},
                    "datastore_name": {"type": "string", "description": "Target datastore (optional)"},
                    "resource_pool_name": {"type": "string", "description": "Target resource pool (optional)"}
                },
                "required": ["ova_path"]
            }
        ),
        "wait_for_updates": types.Tool(
            name="wait_for_updates",
            description="Wait for property updates on vSphere objects",
            inputSchema={
                "type": "object",
                "properties": {
                    "object_type": {"type": "string", "description": "Object type (e.g., 'VirtualMachine', 'Host')"},
                    "properties": {"type": "array", "items": {"type": "string"}, "description": "Properties to monitor"},
                    "max_wait_seconds": {"type": "integer", "description": "Max wait time per iteration", "default": 30},
                    "max_iterations": {"type": "integer", "description": "Max number of iterations", "default": 1}
                },
                "required": ["object_type", "properties"]
            }
        )
    }
    
    # Map tool names to their handler functions
    tool_handler_map = {
        "create_vm": lambda args: tool_handlers.create_vm(**args),
        "clone_vm": lambda args: tool_handlers.clone_vm(**args),
        "delete_vm": lambda args: tool_handlers.delete_vm(**args),
        "power_on_vm": lambda args: tool_handlers.power_on_vm(**args),
        "power_off_vm": lambda args: tool_handlers.power_off_vm(**args),
        "list_vms": lambda args: tool_handlers.list_vms(),
        "get_vm_details": lambda args: tool_handlers.get_vm_details(**args),
        "get_vm_performance": lambda args: tool_handlers.get_vm_performance(**args),
        "get_vm_summary_stats": lambda args: tool_handlers.get_vm_summary_stats(**args),
        "create_vm_custom": lambda args: tool_handlers.create_vm_custom(**args),
        "list_templates": lambda args: tool_handlers.list_templates(),
        "list_datastores": lambda args: tool_handlers.list_datastores(),
        "list_datastore_clusters": lambda args: tool_handlers.list_datastore_clusters(),
        "list_networks": lambda args: tool_handlers.list_networks(),
        "list_hosts": lambda args: tool_handlers.list_hosts(),
        "get_host_details": lambda args: tool_handlers.get_host_details(**args),
        "get_host_performance_metrics": lambda args: tool_handlers.get_host_performance_metrics(**args),
        "get_host_hardware_health": lambda args: tool_handlers.get_host_hardware_health(**args),
        "get_host_performance": lambda args: tool_handlers.get_host_performance(**args),
        "list_performance_counters": lambda args: tool_handlers.list_performance_counters(),
        "create_snapshot": lambda args: tool_handlers.create_snapshot(**args),
        "remove_snapshot": lambda args: tool_handlers.remove_snapshot(**args),
        "revert_snapshot": lambda args: tool_handlers.revert_snapshot(**args),
        "list_snapshots": lambda args: tool_handlers.list_snapshots(**args),
        "remove_all_snapshots": lambda args: tool_handlers.remove_all_snapshots(**args),
        "execute_program_in_vm": lambda args: tool_handlers.execute_program_in_vm(**args),
        "upload_file_to_vm": lambda args: tool_handlers.upload_file_to_vm(**args),
        "upload_file_to_datastore": lambda args: tool_handlers.upload_file_to_datastore(**args),
        "deploy_ovf": lambda args: tool_handlers.deploy_ovf(**args),
        "deploy_ova": lambda args: tool_handlers.deploy_ova(**args),
        "wait_for_updates": lambda args: tool_handlers.wait_for_updates(**args),
    }
    
    resources = {
        "vmStats": types.Resource(
            name="vmStats",
            uri="vmstats://{vm_name}",
            description="Get CPU, memory, storage, network usage of a VM",
            mimeType="application/json"
        )
    }
    
    # Register tool handlers using decorators
    @mcp_server.list_tools()
    async def list_tools_handler():
        """List all available tools."""
        return list(tools.values())
    
    @mcp_server.call_tool()
    async def call_tool_handler(name: str, arguments: dict):
        """Handle tool calls."""
        if name not in tool_handler_map:
            raise ValueError(f"Unknown tool: {name}")
        
        # Call the handler function
        handler = tool_handler_map[name]
        result = handler(arguments)
        
        # Return result as text content
        if isinstance(result, (dict, list)):
            text = json.dumps(result, indent=2)
        else:
            text = str(result)
        
        return [types.TextContent(type="text", text=text)]
    
    # Register resource handlers
    @mcp_server.list_resources()
    async def list_resources_handler():
        """List all available resources."""
        return list(resources.values())
    
    @mcp_server.read_resource()
    async def read_resource_handler(uri: str):
        """Handle resource reads."""
        # Parse URI to extract resource name and parameters
        for resource_name, resource in resources.items():
            if uri.startswith(resource.uri.split("{")[0]):
                # Extract parameters from URI
                # For vmstats://{vm_name}, extract vm_name
                if resource_name == "vmStats":
                    vm_name = uri.replace("vmstats://", "")
                    result = tool_handlers.vm_performance_resource(vm_name)
                    # Return resource content
                    return [types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )]
        
        raise ValueError(f"Unknown resource: {uri}")
