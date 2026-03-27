from __future__ import annotations

import hashlib
import os
import platform
import subprocess
import threading
import uuid

_PROCESS_TIMEOUT = 5
_CONTAINER_MARKERS = (
    "docker",
    "containerd",
    "kubepods",
    "podman",
    "libpod",
    "lxc",
    "machine.slice",
)
_IGNORED_PREFIXES = (
    "lo",
    "docker",
    "br-",
    "veth",
    "cni",
    "flannel",
    "cali",
    "virbr",
    "podman",
    "vmnet",
    "vboxnet",
    "awdl",
    "llw",
    "utun",
    "dummy",
    "zt",
    "tailscale",
    "wg",
    "tun",
    "tap",
    "isatap",
    "teredo",
    "bond",
    "team",
)
_INVALID_VALUES = frozenset(
    {
        "unknown",
        "none",
        "null",
        "not specified",
        "not available",
        "not settable",
        "not applicable",
        "invalid",
        "n/a",
        "na",
        "default string",
        "system serial number",
        "system product name",
        "system manufacturer",
        "chassis serial number",
        "base board serial number",
        "no asset information",
        "type1productconfigid",
        "o.e.m.",
        "empty",
        "unspecified",
        "default",
        "serial",
        "none specified",
        "123456789",
        "1234567890",
    }
)

_cached: str | None = None
_lock = threading.Lock()


def generate_fingerprint() -> str:
    global _cached
    if _cached is not None:
        return _cached
    with _lock:
        if _cached is not None:
            return _cached
        result = _sha256_hex(_get_platform_id())[:32]
        _cached = result
        return result


def _get_platform_id() -> str:
    system = platform.system().lower()

    if "linux" in system:
        mid = _read_linux_machine_id()
        if mid is not None:
            return mid
    elif "darwin" in system:
        mid = _read_mac_uuid()
        if mid is not None:
            return mid
    elif "windows" in system:
        mid = _read_windows_machine_guid()
        if mid is not None:
            return mid
    elif "bsd" in system:
        mid = _read_bsd_host_uuid()
        if mid is not None:
            return mid

    return _fallback_fingerprint()


def _read_linux_machine_id() -> str | None:
    mid = _read_text_file("/etc/machine-id")
    if mid is not None:
        return mid
    return _read_text_file("/var/lib/dbus/machine-id")


def _read_mac_uuid() -> str | None:
    output = _run_command("ioreg", "-rd1", "-c", "IOPlatformExpertDevice")
    if output is None:
        return None
    for line in output.split("\n"):
        if "IOPlatformUUID" in line:
            eq_idx = line.find("=")
            if eq_idx < 0:
                continue
            start = line.find('"', eq_idx)
            if start < 0:
                continue
            end = line.find('"', start + 1)
            if end > start:
                return _normalize_identifier(line[start + 1 : end])
    return None


def _read_windows_machine_guid() -> str | None:
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
            value, _ = winreg.QueryValueEx(key, "MachineGuid")
            return _normalize_identifier(str(value))
    except Exception:
        pass
    output = _run_command(
        "reg", "query", r"HKLM\SOFTWARE\Microsoft\Cryptography", "/v", "MachineGuid"
    )
    if output is None:
        return None
    for line in output.split("\n"):
        if "MachineGuid" in line:
            parts = line.strip().split()
            if len(parts) >= 3:
                return _normalize_identifier(parts[-1])
    return None


def _read_bsd_host_uuid() -> str | None:
    output = _run_command("sysctl", "-n", "kern.hostuuid")
    if output is None:
        return None
    return _normalize_identifier(output)


def _fallback_fingerprint() -> str:
    parts: list[str] = []

    stable_id = _read_stable_host_id()
    if stable_id is not None:
        parts.append(stable_id)

    dmi = _read_dmi_composite()
    if dmi is not None:
        parts.append(dmi)

    parts.append(platform.system())
    parts.append(platform.machine())

    containerized = _is_containerized()

    hostname = None
    if not containerized:
        hostname = _resolve_hostname()
        if hostname is not None:
            parts.append(hostname)

    macs = _read_mac_addresses(containerized)
    if not macs and containerized:
        macs = _read_mac_addresses(False)
    parts.extend(macs)

    if not macs and hostname is None:
        parts.append(os.environ.get("USER", os.environ.get("USERNAME", "")))
        parts.append(os.path.expanduser("~"))

    joined = "\0".join(parts)
    if not joined.strip():
        return (
            "static-fallback" + "\0" + platform.python_implementation() + "\0" + platform.version()
        )
    return joined


def _resolve_hostname() -> str | None:
    for var in ("HOSTNAME", "COMPUTERNAME"):
        val = os.environ.get(var)
        if val and val.strip():
            return val
    val = _read_text_file("/etc/hostname")
    if val is not None:
        return val
    return None


def _read_stable_host_id() -> str | None:
    paths = [
        "/sys/class/dmi/id/product_serial",
        "/sys/devices/virtual/dmi/id/product_serial",
        "/sys/class/dmi/id/board_serial",
        "/sys/devices/virtual/dmi/id/board_serial",
        "/sys/class/dmi/id/product_uuid",
        "/sys/devices/virtual/dmi/id/product_uuid",
    ]
    for path in paths:
        val = _read_text_file(path)
        if val is not None:
            return val

    val = _read_binary_text_file("/proc/device-tree/serial-number")
    if val is not None:
        return val
    return None


def _read_dmi_composite() -> str | None:
    parts: list[str] = []
    for path in [
        "/sys/class/dmi/id/board_vendor",
        "/sys/class/dmi/id/board_name",
        "/sys/class/dmi/id/product_name",
        "/sys/class/dmi/id/sys_vendor",
    ]:
        val = _read_text_file(path)
        if val is not None:
            parts.append(val)
    return "\0".join(parts) if parts else None


def _read_mac_addresses(skip_locally_administered: bool) -> list[str]:
    try:
        node = uuid.getnode()
        if node and not (node >> 40) & 0x01:
            mac_hex = f"{node:012x}"
            mac_bytes = bytes.fromhex(mac_hex)
            if not _is_all_zeros(mac_bytes) and not _is_all_ones(mac_bytes):
                if not (skip_locally_administered and (mac_bytes[0] & 0x02)):
                    return [mac_hex]
    except Exception:
        pass
    return []


def _is_containerized() -> bool:
    if os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv"):
        return True
    for var in ("KUBERNETES_SERVICE_HOST", "container", "DOTNET_RUNNING_IN_CONTAINER"):
        if os.environ.get(var) is not None:
            return True
    cgroup = _read_raw_text_file("/proc/1/cgroup")
    if cgroup is not None:
        lower = cgroup.lower()
        for marker in _CONTAINER_MARKERS:
            if marker in lower:
                return True
    self_cgroup = _read_raw_text_file("/proc/self/cgroup")
    if self_cgroup is not None:
        for line in self_cgroup.split("\n"):
            if line.startswith("0::"):
                path = line[3:].strip().lower()
                for marker in _CONTAINER_MARKERS:
                    if marker in path:
                        return True
    mountinfo = _read_raw_text_file("/proc/1/mountinfo")
    if mountinfo is not None:
        for line in mountinfo.split("\n"):
            if " / / " in line and "overlay" in line:
                return True
    return False


def _normalize_identifier(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    value = raw_value.strip()
    if not value:
        return None
    lower = value.lower()

    if lower in _INVALID_VALUES:
        return None
    if lower.startswith("to be filled"):
        return None
    if lower.startswith("0123456789"):
        return None
    compact = lower.replace("-", "").replace(":", "").replace(" ", "")
    if compact == "03000200040005000006000700080009":
        return None
    if len(compact) <= 3:
        return None
    if all(c == "0" for c in compact):
        return None
    if all(c == "f" for c in compact):
        return None
    if all(c == "1" for c in compact):
        return None
    if all(c == "x" for c in compact):
        return None

    return lower


def _run_command(*args: str) -> str | None:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=_PROCESS_TIMEOUT,
        )
        if result.returncode != 0:
            return None
        return result.stdout
    except Exception:
        return None


def _read_text_file(path: str) -> str | None:
    try:
        with open(path) as f:
            return _normalize_identifier(f.read())
    except Exception:
        return None


def _read_binary_text_file(path: str) -> str | None:
    try:
        with open(path, "rb") as f:
            data = f.read()
        length = data.find(b"\x00")
        if length < 0:
            length = len(data)
        return _normalize_identifier(data[:length].decode("utf-8", errors="replace"))
    except Exception:
        return None


def _read_raw_text_file(path: str) -> str | None:
    try:
        with open(path) as f:
            return f.read()
    except Exception:
        return None


def _is_all_zeros(data: bytes) -> bool:
    return all(b == 0 for b in data)


def _is_all_ones(data: bytes) -> bool:
    return all(b == 0xFF for b in data)


def _sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
