"""MCP server initialization and handler registration."""

import json
from mcp.server.lowlevel import Server
from mcp import types

from .tools import ToolHandlers


from .config import Config


def create_mcp_server() -> Server:
    """Create and initialize the MCP server."""
    return Server(name="VMware-MCP-Server", version="0.0.1")


def register_handlers(mcp_server: Server, tool_handlers: ToolHandlers, config: Config = None):
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
                    "datastore": {"type": "string", "description": "Datastore name (optional, takes precedence over datastore_cluster)"},
                    "datastore_cluster": {"type": "string", "description": "Datastore cluster (StoragePod) name — picks the datastore with most free space (optional)"},
                    "network": {"type": "string", "description": "Network name (optional)"},
                    "folder": {"type": "string", "description": "Target VM folder name (optional)"},
                    "resource_pool": {"type": "string", "description": "Target resource pool name (optional)"},
                    "serial_console": {"type": "boolean", "description": "Add a file-backed serial port for console logging", "default": False}
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
                    "new_name": {"type": "string", "description": "Name for the new VM"},
                    "folder": {"type": "string", "description": "Target VM folder name (optional)"},
                    "resource_pool": {"type": "string", "description": "Target resource pool name (optional)"},
                    "datastore": {"type": "string", "description": "Target datastore name (optional, takes precedence over datastore_cluster)"},
                    "datastore_cluster": {"type": "string", "description": "Datastore cluster (StoragePod) name — picks the datastore with most free space (optional)"}
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
                    "datastore": {"type": "string", "description": "Datastore name (optional, takes precedence over datastore_cluster)"},
                    "datastore_cluster": {"type": "string", "description": "Datastore cluster (StoragePod) name — picks the datastore with most free space (optional)"},
                    "network": {"type": "string", "description": "Network name (optional)"},
                    "thin_provisioned": {"type": "boolean", "description": "Use thin provisioning", "default": True},
                    "annotation": {"type": "string", "description": "VM annotation/description"},
                    "folder": {"type": "string", "description": "Target VM folder name (optional)"},
                    "resource_pool": {"type": "string", "description": "Target resource pool name (optional)"},
                    "serial_console": {"type": "boolean", "description": "Add a file-backed serial port for console logging", "default": False}
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
            description=(
                "Execute a program inside a VM using VMware Tools. "
                "If username/password are omitted, authenticates via SAML "
                "token (requires VMWARE_SAML_ENABLED=true and a guest alias "
                "configured in the VM)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_name": {"type": "string", "description": "Name of the VM"},
                    "program_path": {"type": "string", "description": "Full path to the program in guest OS"},
                    "program_arguments": {"type": "string", "description": "Program arguments (optional)", "default": ""},
                    "username": {"type": "string", "description": "Guest OS username (optional with SAML)"},
                    "password": {"type": "string", "description": "Guest OS password (optional with SAML)"}
                },
                "required": ["vm_name", "program_path"]
            }
        ),
        "upload_file_to_vm": types.Tool(
            name="upload_file_to_vm",
            description=(
                "Upload a file to a VM using VMware Tools. "
                "Provide either local_file_path (a path on the MCP server host) or "
                "file_content_base64 (base64-encoded content — keep files small, "
                "under 1 MB). "
                "If username/password are omitted, authenticates via SAML."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_name": {"type": "string", "description": "Name of the VM"},
                    "local_file_path": {"type": "string", "description": "Local file path on the MCP server to upload (mutually exclusive with file_content_base64)"},
                    "file_content_base64": {"type": "string", "description": "Base64-encoded file content to upload directly. Keep files small (under 1 MB). Mutually exclusive with local_file_path."},
                    "remote_file_path": {"type": "string", "description": "Destination path in guest OS"},
                    "username": {"type": "string", "description": "Guest OS username (optional with SAML)"},
                    "password": {"type": "string", "description": "Guest OS password (optional with SAML)"}
                },
                "required": ["vm_name", "remote_file_path"]
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
        ),
        "capture_vm_screenshot": types.Tool(
            name="capture_vm_screenshot",
            description=(
                "Capture the VM console as a PNG screenshot. Returns base64-encoded "
                "image data. Useful for reading boot output, BIOS screens, or "
                "generated passwords displayed on the console."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_name": {"type": "string", "description": "Name of the VM"}
                },
                "required": ["vm_name"]
            }
        ),
        "add_vm_serial_port": types.Tool(
            name="add_vm_serial_port",
            description=(
                "Add a file-backed virtual serial port to a VM. Logs all guest "
                "console output to a datastore file. The VM should be powered off "
                "when adding the port, or rebooted afterward."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_name": {"type": "string", "description": "Name of the VM"},
                    "output_file": {
                        "type": "string",
                        "description": "Datastore path for the log file. Optional — auto-derived from the VM's datastore path if omitted."
                    }
                },
                "required": ["vm_name"]
            }
        ),
        "read_vm_serial_console": types.Tool(
            name="read_vm_serial_console",
            description=(
                "Read the serial console log for a VM. Returns text output from "
                "the guest OS serial console. Requires a file-backed serial port "
                "(see add_vm_serial_port). Use tail_lines for recent output or "
                "offset_bytes for incremental reads."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_name": {"type": "string", "description": "Name of the VM"},
                    "tail_lines": {
                        "type": "integer",
                        "description": "Lines from end of log to return. 0 = everything from offset onward.",
                        "default": 50
                    },
                    "offset_bytes": {
                        "type": "integer",
                        "description": "Byte offset for incremental reads.",
                        "default": 0
                    }
                },
                "required": ["vm_name"]
            }
        )
    }

    # Experimental tools — only registered when experimental_tools is enabled
    experimental_tools = {
        "download_file_from_vm": types.Tool(
            name="download_file_from_vm",
            description=(
                "[Experimental] Download a file from a VM using VMware Tools. "
                "Returns the file as base64-encoded content along with its size "
                "and SHA-256 hash. Best suited for small files (text configs, "
                "scripts, logs). "
                "If username/password are omitted, authenticates via SAML."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_name": {"type": "string", "description": "Name of the VM"},
                    "remote_file_path": {"type": "string", "description": "Path of the file in the guest OS to download"},
                    "username": {"type": "string", "description": "Guest OS username (optional with SAML)"},
                    "password": {"type": "string", "description": "Guest OS password (optional with SAML)"}
                },
                "required": ["vm_name", "remote_file_path"]
            }
        ),
        "edit_file_on_vm": types.Tool(
            name="edit_file_on_vm",
            description=(
                "[Experimental] Edit a file on a VM using targeted string "
                "replacements. Each edit replaces the first exact occurrence of "
                "old_string with new_string. Edits are applied sequentially — "
                "later edits see the result of earlier ones. "
                "You must supply the SHA-256 of the current file content (from "
                "download_file_from_vm) to guard against stale edits. "
                "If username/password are omitted, authenticates via SAML."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_name": {"type": "string", "description": "Name of the VM"},
                    "file_path": {"type": "string", "description": "Path of the file in the guest OS to edit"},
                    "sha": {"type": "string", "description": "SHA-256 hex digest of the current file content (obtained from download_file_from_vm)"},
                    "edits": {
                        "type": "array",
                        "description": "Ordered list of string-replacement edits to apply",
                        "items": {
                            "type": "object",
                            "properties": {
                                "old_string": {"type": "string", "description": "Exact string to find (first occurrence is replaced)"},
                                "new_string": {"type": "string", "description": "Replacement string"}
                            },
                            "required": ["old_string", "new_string"]
                        }
                    },
                    "username": {"type": "string", "description": "Guest OS username (optional with SAML)"},
                    "password": {"type": "string", "description": "Guest OS password (optional with SAML)"}
                },
                "required": ["vm_name", "file_path", "sha", "edits"]
            }
        ),
    }

    if config and config.experimental_tools:
        tools.update(experimental_tools)

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
        "capture_vm_screenshot": lambda args: tool_handlers.capture_vm_screenshot(**args),
        "add_vm_serial_port": lambda args: tool_handlers.add_vm_serial_port(**args),
        "read_vm_serial_console": lambda args: tool_handlers.read_vm_serial_console(**args),
        "download_file_from_vm": lambda args: tool_handlers.download_file_from_vm(**args),
        "edit_file_on_vm": lambda args: tool_handlers.edit_file_on_vm(**args),
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
        
        # Return screenshot as ImageContent so AI agents can interpret the image directly
        if name == "capture_vm_screenshot" and isinstance(result, dict) and "image_base64" in result:
            try:
                return [types.ImageContent(
                    type="image",
                    data=result["image_base64"],
                    mimeType="image/png"
                )]
            except Exception:
                # Fall back to text if ImageContent is not supported
                return [types.TextContent(type="text", text=result["image_base64"])]

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
