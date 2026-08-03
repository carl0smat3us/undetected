import os
import re
import subprocess
import sys
from pathlib import Path

IS_POSIX = sys.platform.startswith(("darwin", "cygwin", "linux", "linux2"))


def find_chrome_executable():
    """
    Finds Google Chrome (stable/beta/canary) first, then Chromium.

    Returns
    -------
    executable_path : str | None
        Full path to the browser executable, or None if not found.
    """

    candidates = []

    PATH = os.environ.get("PATH")

    # -------- POSIX (Linux / macOS) --------
    if IS_POSIX and PATH:
        # Priority order
        binaries = [
            "google-chrome",
            "google-chrome-stable",
            "google-chrome-beta",
            "google-chrome-canary",
            "chrome",
            "chromium",
            "chromium-browser",
        ]

        for path_dir in PATH.split(os.pathsep):
            for binary in binaries:
                candidates.append(Path(path_dir) / binary)

        # macOS .app paths
        if sys.platform == "darwin":
            candidates.extend(
                [
                    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                    "/Applications/Chromium.app/Contents/MacOS/Chromium",
                ]
            )

    # -------- Windows --------
    else:
        install_roots = (
            "PROGRAMFILES",
            "PROGRAMFILES(X86)",
            "LOCALAPPDATA",
            "PROGRAMW6432",
        )

        # Priority order
        subpaths = (
            "Google/Chrome/Application/chrome.exe",
            "Chromium/Application/chrome.exe",
        )

        for root in map(os.environ.get, install_roots):
            if root:
                for subpath in subpaths:
                    candidates.append(Path(str(root)) / subpath)

    # Check existence
    for candidate in candidates:
        if Path(candidate).exists() and Path(candidate).is_file():
            return Path(candidate)

    return None


def get_chrome_version(exe_path):
    if not exe_path:
        return None

    try:
        if sys.platform == "win32":
            # Prefer Win32 APIs — PowerShell is flaky under GUI hosts, and
            # `chrome.exe --version` hangs on Windows (opens a window).
            ver = _win_file_version(str(exe_path))
            if ver:
                return ver
            command = [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                f"(Get-Item -LiteralPath '{exe_path}').VersionInfo.FileVersion",
            ]
        else:
            command = [exe_path, "--version"]

        output = subprocess.check_output(
            command,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=15,
        )

        match = re.search(r"\d+\.\d+\.\d+\.\d+", output)
        return match.group(0) if match else None

    except (subprocess.SubprocessError, OSError):
        return None


def _win_file_version(exe_path: str) -> str | None:
    try:
        import ctypes

        size = ctypes.windll.version.GetFileVersionInfoSizeW(exe_path, None)
        if not size:
            return None
        buf = ctypes.create_string_buffer(size)
        if not ctypes.windll.version.GetFileVersionInfoW(exe_path, 0, size, buf):
            return None
        p = ctypes.c_void_p()
        length = ctypes.c_uint()
        if not ctypes.windll.version.VerQueryValueW(
            buf, "\\", ctypes.byref(p), ctypes.byref(length)
        ):
            return None

        class _VS_FIXEDFILEINFO(ctypes.Structure):
            _fields_ = [
                ("dwSignature", ctypes.c_uint32),
                ("dwStrucVersion", ctypes.c_uint32),
                ("dwFileVersionMS", ctypes.c_uint32),
                ("dwFileVersionLS", ctypes.c_uint32),
                ("dwProductVersionMS", ctypes.c_uint32),
                ("dwProductVersionLS", ctypes.c_uint32),
                ("dwFileFlagsMask", ctypes.c_uint32),
                ("dwFileFlags", ctypes.c_uint32),
                ("dwFileOS", ctypes.c_uint32),
                ("dwFileType", ctypes.c_uint32),
                ("dwFileSubtype", ctypes.c_uint32),
                ("dwFileDateMS", ctypes.c_uint32),
                ("dwFileDateLS", ctypes.c_uint32),
            ]

        info = ctypes.cast(p, ctypes.POINTER(_VS_FIXEDFILEINFO)).contents
        major = info.dwFileVersionMS >> 16
        minor = info.dwFileVersionMS & 0xFFFF
        build = info.dwFileVersionLS >> 16
        patch = info.dwFileVersionLS & 0xFFFF
        if major <= 0:
            return None
        return f"{major}.{minor}.{build}.{patch}"
    except Exception:
        return None


def get_chrome_major_version(exe_path: str):
    version = get_chrome_version(exe_path)

    if not version:
        raise ValueError("Could not determine browser version.")

    return int(version.split(".")[0])


def get_browser_info(browser_executable_path: str | None = None):
    if not browser_executable_path:
        browser_executable_path = str(find_chrome_executable())

    if not browser_executable_path or not Path(browser_executable_path).exists():
        raise FileNotFoundError("Could not determine browser executable.")

    version = get_chrome_version(browser_executable_path)

    if not version:
        raise ValueError("Could not determine browser version.")

    return {
        "browser_path": browser_executable_path,
        "browser_version": version,
        "browser_main_version": get_chrome_major_version(browser_executable_path),
    }
