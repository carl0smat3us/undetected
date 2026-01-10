import os
import pathlib
import re
import subprocess
import sys

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
                candidates.append(os.path.join(path_dir, binary))

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

        # Priority order (Chrome FIRST)
        subpaths = (
            "Google/Chrome/Application/chrome.exe",
            "Chromium/Application/chrome.exe",
        )

        for root in map(os.environ.get, install_roots):
            if root:
                for subpath in subpaths:
                    candidates.append(os.path.join(root, subpath))

    # -------- Check existence --------
    for candidate in candidates:
        if os.path.exists(candidate) and os.access(candidate, os.X_OK):
            return os.path.normpath(candidate)

    return None


def get_chrome_version(exe_path):
    if not exe_path:
        return None

    try:
        if sys.platform != "win32":
            command = [exe_path, "--version"]
        else:
            command = [
                "powershell",
                "-Command",
                f"& {{(Get-Item '{exe_path}').VersionInfo.FileVersion}}",
            ]

        output = subprocess.check_output(
            command,
            stderr=subprocess.DEVNULL,
            text=True,
        )

        match = re.search(r"\d+\.\d+\.\d+\.\d+", output)
        return match.group(0) if match else None

    except (subprocess.SubprocessError, OSError):
        return None


def get_chrome_major_version(exe_path: str):
    version = get_chrome_version(exe_path)

    if not version:
        raise ValueError("Could not determine browser version.")

    return int(version.split(".")[0])


def get_browser_info(browser_executable_path: str | None = None):
    if not browser_executable_path:
        browser_executable_path = find_chrome_executable()

    if (
        not browser_executable_path
        or not pathlib.Path(browser_executable_path).exists()
    ):
        raise FileNotFoundError("Could not determine browser executable.")

    version = get_chrome_version(browser_executable_path)

    if not version:
        raise ValueError("Could not determine browser version.")

    return {
        "browser_path": browser_executable_path,
        "browser_major_version": get_chrome_major_version(browser_executable_path),
    }
