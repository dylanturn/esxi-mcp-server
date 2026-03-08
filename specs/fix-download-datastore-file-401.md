# Fix `_download_datastore_file` HTTP 401 and align with working upload pattern

## Problem

`_download_datastore_file` returns HTTP 401 when downloading files from the
vSphere datastore HTTP file access endpoint. This breaks both
`capture_vm_screenshot` and `read_vm_serial_console`.

The existing `upload_file_to_datastore` method in the same file successfully
authenticates against the same endpoint using the same session cookie. The
download helper must match its HTTP request construction exactly.

## Observed behavior

```
Failed to download [truenas-iscsi-03] claude-nginx/serial.log: HTTP 401
Failed to download [truenas-iscsi-03] claude-nginx/claude-nginx-1.png: HTTP 401
```

Both `capture_vm_screenshot` and `read_vm_serial_console` call
`_download_datastore_file`, and both fail with 401.

## Root cause

`_download_datastore_file` constructs the HTTP request differently from
`upload_file_to_datastore`. The upload method works. The download method does
not. The differences that cause the 401:

1. **Missing `:443` port** — The upload method uses
   `https://{host}:443{resource}`. The download method likely uses
   `https://{host}/folder/{file_path}?...` without the explicit port.

2. **Query params baked into URL string** — The upload method passes `dsName`
   and `dcPath` as a `params` dict to `requests.put()`, which handles URL
   encoding. The download method likely concatenates them into the URL string
   directly, which can produce malformed URLs when datastore names or paths
   contain special characters.

3. **File path not URL-encoded** — Datastore paths can contain spaces and
   other characters that need percent-encoding in URLs. The upload method
   handles this via the `params` dict. The download method needs explicit
   `urllib.parse.quote()` on the file path portion.

## Working reference: `upload_file_to_datastore`

This method in `vmware_manager.py` (line ~580) successfully authenticates:

```python
resource = "/folder" + remote_file_path
params = {
    "dsName": datastore.name,
    "dcPath": self.datacenter_obj.name
}
http_url = f"https://{self.config.vcenter_host}:443{resource}"

client_cookie = self.si._stub.cookie
cookie_name = client_cookie.split("=", 1)[0]
cookie_value = client_cookie.split("=", 1)[1].split(";", 1)[0]
cookie_path = client_cookie.split("=", 1)[1].split(";", 1)[1].split(";", 1)[0].lstrip()
cookie_text = " " + cookie_value + "; $" + cookie_path
cookie = {cookie_name: cookie_text}

resp = requests.put(
    http_url,
    params=params,
    data=file_data,
    headers=headers,
    cookies=cookie,
    verify=False
)
```

Key details: explicit `:443`, query params as dict via `params=`, cookie
extracted from `self.si._stub.cookie`.

## Required fix

Replace `_download_datastore_file` with this implementation that mirrors the
upload method exactly:

```python
def _download_datastore_file(self, datastore_path: str) -> bytes:
    """Download a file from a datastore path like '[dsName] path/to/file'.

    Uses the vSphere HTTP file access endpoint with the existing session
    cookie from the pyvmomi connection. URL construction and cookie handling
    must match upload_file_to_datastore exactly.
    """
    import re
    import requests
    from urllib.parse import quote

    match = re.match(r'\[(.+?)\]\s+(.+)', datastore_path)
    if not match:
        raise Exception(f"Invalid datastore path: {datastore_path}")

    ds_name = match.group(1)
    file_path = match.group(2)

    # URL-encode the file path, preserving forward slashes
    resource = "/folder/" + quote(file_path, safe="/")
    http_url = f"https://{self.config.vcenter_host}:443{resource}"

    # Pass dsName and dcPath as a params dict — NOT baked into the URL
    params = {
        "dsName": ds_name,
        "dcPath": self.datacenter_obj.name
    }

    # Extract session cookie — identical to upload_file_to_datastore
    client_cookie = self.si._stub.cookie
    cookie_name = client_cookie.split("=", 1)[0]
    cookie_value = client_cookie.split("=", 1)[1].split(";", 1)[0]
    cookie_path = (
        client_cookie.split("=", 1)[1]
        .split(";", 1)[1]
        .split(";", 1)[0]
        .lstrip()
    )
    cookie_text = " " + cookie_value + "; $" + cookie_path
    cookies = {cookie_name: cookie_text}

    resp = requests.get(
        http_url,
        params=params,
        cookies=cookies,
        verify=False
    )
    if resp.status_code != 200:
        raise Exception(
            f"Failed to download {datastore_path}: HTTP {resp.status_code}"
        )

    return resp.content
```

## Refactoring opportunity

The cookie-parsing logic is duplicated between `upload_file_to_datastore` and
`_download_datastore_file`. Extract a shared helper:

```python
def _get_session_cookies(self) -> dict:
    """Extract vCenter session cookies from the pyvmomi connection."""
    client_cookie = self.si._stub.cookie
    cookie_name = client_cookie.split("=", 1)[0]
    cookie_value = client_cookie.split("=", 1)[1].split(";", 1)[0]
    cookie_path = (
        client_cookie.split("=", 1)[1]
        .split(";", 1)[1]
        .split(";", 1)[0]
        .lstrip()
    )
    cookie_text = " " + cookie_value + "; $" + cookie_path
    return {cookie_name: cookie_text}
```

Then update both `upload_file_to_datastore` and `_download_datastore_file` to
call `self._get_session_cookies()`.

## Verification

After the fix, these two tool calls should succeed instead of returning 401:

1. `read_vm_serial_console(vm_name="claude-nginx")` — reads the serial log
   from `[truenas-iscsi-03] claude-nginx_1/serial.log`
2. `capture_vm_screenshot(vm_name="claude-nginx")` — captures and downloads
   a console screenshot PNG

## Files to modify

- `esxi_mcp_server/vmware_manager.py` — fix `_download_datastore_file`,
  optionally add `_get_session_cookies` helper, optionally refactor
  `upload_file_to_datastore` to use the shared helper

## Required vCenter privileges

Already granted (no changes needed):
- `Datastore.Browse`
- `Provisioning.AllowFileAccess` (Allow file access)
- `VirtualMachine.Interact.CreateScreenshot` (Create screenshot)
