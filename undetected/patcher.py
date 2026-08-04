# this module is part of undetected

import json
import logging
import os
import pathlib
import random
import re
import secrets
import shutil
import ssl
import string
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from contextlib import contextmanager
from multiprocessing import Lock
from pathlib import Path
from urllib.request import urlopen

import certifi
from packaging.version import Version

from .utils.info import IS_POSIX, get_browser_info

logger = logging.getLogger(__name__)


class Patcher:
    lock = Lock()
    _thread_lock = threading.RLock()
    exe_name = "chromedriver%s"

    platform = sys.platform

    if platform.endswith("win32"):
        d = "~/appdata/roaming/undetected"
    elif "LAMBDA_TASK_ROOT" in os.environ:
        d = "/tmp/undetected"
    elif platform.startswith(("linux", "linux2")):
        d = "~/.local/share/undetected"
    elif platform.endswith("darwin"):
        d = "~/Library/Application Support/undetected"
    else:
        d = "~/.undetected"

    if platform.endswith("win32"):
        # Chrome for Testing ships win64 builds for amd64 Windows.
        platform_name = "win64" if sys.maxsize > 2**32 else "win32"
        exe_name %= ".exe"
    if platform.endswith(("linux", "linux2")):
        platform_name = "linux64"
        exe_name %= ""
    if platform.endswith("darwin"):
        platform_name = "mac-x64"
        exe_name %= ""

    data_path = Path(d).expanduser().resolve()

    ssl_ctx = ssl.create_default_context(cafile=certifi.where())

    def __init__(
        self,
        browser_executable_path=None,
        driver_executable_path=None,
        user_multi_procs=False,
        for_patch=False,
    ):
        """
        Args:
            version_main:
                browser main/major version
            driver_executable_path: None = automatic
                             a full file path to the chromedriver executable
            for_patch: False
                    rather the class is only being used to call the method `patch` or not

        """
        self.for_patch = for_patch

        self._using_custom_driver = False

        self.user_multi_procs = user_multi_procs

        prefix = secrets.token_hex(8)

        browser_info = get_browser_info(browser_executable_path=browser_executable_path)

        self.browser_executable_path = browser_info["browser_path"]

        self.version_main = browser_info["browser_main_version"]

        self.full_version = None

        if self.version_main <= 114:
            raise RuntimeError(
                f"Unsupported browser version: {self.version_main}. "
                "Install a current Google Chrome and retry."
            )

        if not Path(self.data_path).exists():
            os.makedirs(self.data_path, exist_ok=True)

        if not driver_executable_path:
            self.driver_executable_path = (
                Path(self.data_path) / f"{prefix}_{self.exe_name}"
            )

        if not IS_POSIX:
            if driver_executable_path:
                if not driver_executable_path[-4:] == ".exe":
                    driver_executable_path += ".exe"

        self.driver_zip_path = Path(self.data_path) / prefix

        if not driver_executable_path and not self.user_multi_procs:
            self.driver_executable_path = Path(self.driver_executable_path).resolve()

        if driver_executable_path:
            self._using_custom_driver = True
            self.driver_executable_path = driver_executable_path

    def verify(self):
        """
        Verify if the binary is patched.
        """
        if self._using_custom_driver:
            return self.is_binary_patched(self.driver_executable_path)

        p = pathlib.Path(self.data_path)

        with self.lock:
            files = [
                f for f in p.glob("*chromedriver*") if "unpatched" not in f.name.lower()
            ]

            if not files:
                raise Exception(
                    "No patched chromedriver binary was found under %s."
                    % self.data_path
                )

            try:
                most_recent = max(files, key=lambda f: f.stat().st_mtime)
            except ValueError:
                return False

            # deleting old binaries
            for f in files:
                if f != most_recent:
                    try:
                        f.unlink()
                    except (FileNotFoundError, PermissionError):
                        pass

            if self.is_binary_patched(most_recent):
                self.driver_executable_path = str(most_recent)
                return True

    def download_and_patch(self):
        if (
            not self._using_custom_driver
        ):  # the driver_executable_path was not specified, download it
            release = self.fetch_release_number(self.version_main)

            self.version_main = release.major
            self.full_version = release

            unpatched_bin_found = False

            # check if the driver unpatched binary is available
            for file in list(pathlib.Path(self.data_path).glob("*unpatched*")):
                if str(self.full_version) in file.name:
                    unpatched_bin_found = True
                else:
                    try:
                        os.remove(file)
                    except OSError:
                        pass

            if not unpatched_bin_found:
                self.unzip_package(
                    self.fetch_package(self.full_version),
                    f"unpatched_{str(self.full_version)}",
                )

            # make a copy of the unpatched binary
            unpatched_path = (
                Path(str(self.data_path)) / f"unpatched_{str(self.full_version)}"
            )
            shutil.copy(unpatched_path, self.driver_executable_path)
            os.chmod(self.driver_executable_path, 0o755)

        self.patch_exe()

        return self.is_binary_patched()

    def driver_binary_in_use(self, path: str | None = None) -> bool | None:
        """
        naive test to check if a found chromedriver binary is
        currently in use

        Args:
            path: a string or PathLike object to the binary to check.
                  if not specified, we check use this object's driver_executable_path
        """
        if not path:
            path = str(self.driver_executable_path)

        p = pathlib.Path(path)

        if not p.exists():
            raise OSError("file does not exist: %s" % p)
        try:
            with open(p, mode="a+b") as fs:
                exc = []
                try:
                    fs.seek(0, 0)
                except PermissionError as e:
                    exc.append(e)  # since some systems apprently allow seeking
                    # we conduct another test
                try:
                    fs.readline()
                except PermissionError as e:
                    exc.append(e)

                if exc:
                    return True
                return False
            # ok safe to assume this is in use
        except Exception:
            # logger.exception("whoops ", e)
            pass

    @classmethod
    def cleanup_unused_files(cls):
        items = list(pathlib.Path(cls.data_path).glob("*chromedriver*"))

        logger.debug("Cleaning up unused files; found: %s", items)

        for item in items:
            try:
                cls.kill_all_instances(item)
                item.unlink()
                logger.debug("Deleted chromedriver: %s", item)
            except Exception as e:
                logger.debug("Failed to delete chromedriver %s: %s", item, e)

    @classmethod
    def fetch_release_number(cls, version_main):
        """
        Gets the latest full version of the main/major version provided
        :return: version string
        :rtype: Version
        """
        logger.debug("getting release number")

        with urlopen(
            "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json",
            context=cls.ssl_ctx,
        ) as conn:
            response = conn.read().decode()

        return Version(json.loads(response)["milestones"][str(version_main)]["version"])

    def parse_exe_version(self):
        with open(self.driver_executable_path, "rb") as f:
            for line in iter(lambda: f.readline(), b""):
                match = re.search(rb"platform_handle\x00content\x00([0-9.]*)", line)
                if match:
                    return Version(match[1].decode())

    @classmethod
    def fetch_package(cls, full_version):
        """
        Downloads ChromeDriver from source

        :return: path to downloaded file
        """
        zip_name = f"chromedriver_{cls.platform_name}.zip"

        zip_name = zip_name.replace("_", "-", 1)

        download_url = (
            "https://storage.googleapis.com/chrome-for-testing-public/%s/%s/%s"
        )

        download_url %= (str(full_version), cls.platform_name, zip_name)

        logger.debug("downloading from %s" % download_url)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            tmp_path = Path(tmp_file.name)
            with urlopen(download_url, context=cls.ssl_ctx) as response:
                tmp_file.write(response.read())

        return str(tmp_path)

    @classmethod
    def unzip_package(cls, fp, unpatched_path=None):
        """
        Unzips chromedriver and returns the extracted driver path.
        """
        logger.debug("unzipping %s" % fp)

        fp = Path(fp)

        with tempfile.TemporaryDirectory() as extract_dir:
            extract_dir = Path(extract_dir)

            with zipfile.ZipFile(fp, mode="r") as zf:
                zf.extractall(extract_dir)

            extracted_driver = (
                extract_dir / f"chromedriver-{cls.platform_name}" / cls.exe_name
            )

            if unpatched_path is None:
                final_path = Path(cls.data_path) / cls.exe_name
            else:
                final_path = Path(unpatched_path)

                if not final_path.is_absolute():
                    final_path = Path(cls.data_path) / final_path

                if final_path.is_dir():
                    final_path = final_path / cls.exe_name

            final_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.move(str(extracted_driver), str(final_path))

        fp.unlink(missing_ok=True)

        os.chmod(final_path, 0o755)

        return str(final_path)

    @staticmethod
    def kill_all_instances(path):
        if IS_POSIX:
            cmd = f"pidof {path} >/dev/null && kill -9 $(pidof {path}) || true"
            exit_code = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
            )
        else:
            # /IM expects an image name, not a full path.
            image = Path(path).name if path else "chromedriver.exe"
            exit_code = subprocess.run(
                ["taskkill", "/F", "/IM", image, "/T"],
                capture_output=True,
                text=True,
                check=False,
            )

        if getattr(exit_code, "returncode", 1) == 0:
            logger.debug("Killed running instances of %s", path)
        else:
            logger.debug(
                "Failed to kill running instances of %s (exit code: %s)",
                path,
                exit_code,
            )

    @staticmethod
    def gen_random_cdc():
        cdc = random.choices(string.ascii_letters, k=27)
        return "".join(cdc).encode()

    def is_binary_patched(self, driver_executable_path=None):
        driver_executable_path = driver_executable_path or self.driver_executable_path
        for attempt in range(15):
            try:
                with open(driver_executable_path, "rb") as fh:
                    content = fh.read()
                return b"{/*uc*/" in content or b"undetected chromedriver" in content
            except FileNotFoundError:
                return False
            except PermissionError:
                # Windows often denies reading a chromedriver.exe that is running.
                time.sleep(0.1)
                if attempt == 14 and Path(driver_executable_path).is_file():
                    return True
        return False

    def patch_exe(self):
        start = time.perf_counter()
        logger.info("patching driver executable %s" % self.driver_executable_path)
        with open(self.driver_executable_path, "r+b") as fh:
            content = fh.read()
            match_injected_codeblock = re.search(rb"\{window\.cdc.*?;\}", content)
            if match_injected_codeblock:
                target_bytes = match_injected_codeblock[0]
                # Quiet NOP with a short marker for is_binary_patched().
                marker = b"{/*uc*/"
                if len(target_bytes) < len(marker) + 1:
                    new_target_bytes = b" " * len(target_bytes)
                else:
                    new_target_bytes = (
                        marker + (b" " * (len(target_bytes) - len(marker) - 1)) + b"}"
                    )
                content = content.replace(target_bytes, new_target_bytes, 1)
            else:
                logger.warning(
                    "something went wrong patching the driver binary. could not find injection code block"
                )

            test_type = b"test-type=webdriver"
            if test_type in content:
                content = content.replace(test_type, b" " * len(test_type))

            fh.seek(0)
            fh.write(content)
            fh.truncate()
        logger.debug(f"patching took us {time.perf_counter() - start:.2f} seconds")

    @staticmethod
    def patch(browser_executable_path=None, driver_executable_path=None):
        patcher = Patcher(
            browser_executable_path=browser_executable_path,
            driver_executable_path=driver_executable_path,
            for_patch=True,
        )
        patcher.cleanup_unused_files()
        patcher.download_and_patch()

    @classmethod
    @contextmanager
    def _cross_process_lock(cls):
        """
        Exclusive lock shared by threads and processes.
        Uses flock on POSIX and an atomic mkdir lock on Windows
        (msvcrt.locking is unreliable across threads).
        """
        data = pathlib.Path(cls.data_path)
        data.mkdir(parents=True, exist_ok=True)

        if IS_POSIX:
            import fcntl

            lock_path = data / ".patch.lock"
            fh = open(lock_path, "a+b")
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
                yield
            finally:
                try:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
                except OSError:
                    pass
                fh.close()
            return

        # Windows: mkdir is atomic; avoid msvcrt.locking (Errno 13 under threads).
        lock_dir = data / ".patch.lock.d"
        deadline = time.time() + 120
        while True:
            try:
                os.mkdir(lock_dir)
                break
            except FileExistsError:
                if time.time() > deadline:
                    raise TimeoutError(
                        "timed out waiting for chromedriver patch lock"
                    ) from None
                try:
                    if time.time() - lock_dir.stat().st_mtime > 300:
                        os.rmdir(lock_dir)
                        continue
                except OSError:
                    pass
                time.sleep(0.05)
        try:
            yield
        finally:
            try:
                os.rmdir(lock_dir)
            except OSError:
                pass

    @classmethod
    def ensure_patched(cls, browser_executable_path=None, driver_executable_path=None):
        """
        Make sure a shared patched chromedriver exists.
        Safe across threads and processes; only the first caller downloads/patches.
        """
        with cls._thread_lock:
            with cls._cross_process_lock():
                data = pathlib.Path(cls.data_path)
                data.mkdir(parents=True, exist_ok=True)
                files = [
                    f
                    for f in data.glob("*chromedriver*")
                    if "unpatched" not in f.name.lower()
                ]
                probe = cls(
                    browser_executable_path=browser_executable_path,
                    driver_executable_path=driver_executable_path,
                    user_multi_procs=True,
                    for_patch=True,
                )
                if files:
                    most_recent = max(files, key=lambda f: f.stat().st_mtime)
                    if probe.is_binary_patched(most_recent):
                        return
                probe.cleanup_unused_files()
                probe.download_and_patch()

    def __repr__(self):
        return f"{self.__class__.__name__:s}({self.driver_executable_path:s})"

    def __del__(self):
        if (
            not self._using_custom_driver
            and not self.for_patch
            and not self.user_multi_procs
        ):
            max_attempts = 30  # try for ~3 seconds if sleep=0.1
            sleep_time = 0.1

            for _ in range(max_attempts):
                try:
                    os.unlink(self.driver_executable_path)
                    logger.debug(
                        "successfully unlinked %s", self.driver_executable_path
                    )
                    break
                except (PermissionError, OSError):
                    time.sleep(sleep_time)
            else:
                logger.warning(
                    "could not unlink %s after %d attempts",
                    self.driver_executable_path,
                    max_attempts,
                )
