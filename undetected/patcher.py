# this module is part of undetected

import io
import json
import logging
import os
import pathlib
import random
import re
import secrets
import shutil
import string
import sys
import time
import zipfile
from multiprocessing import Lock
from urllib.request import urlopen, urlretrieve

from packaging.version import Version

from .utils.info import IS_POSIX, get_browser_info

logger = logging.getLogger(__name__)


class Patcher:
    lock = Lock()
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

    data_path = os.path.abspath(os.path.expanduser(d))

    def __init__(
        self,
        version_main,
        driver_executable_path=None,
        force=False,
        user_multi_procs=False,
        for_patch=False,
    ):
        """
        Args:
            version_main:
                specify main chrome version (rounded, ex: 82)
            driver_executable_path: None = automatic
                             a full file path to the chromedriver executable
            force: False
                    terminate processes which are holding lock
            for_patch: False
                    rather the class is only being used to call the method `patch` or not

        """
        self.force = force
        self.for_patch = for_patch
        self._using_custom_exe = False

        prefix = secrets.token_hex(8)

        self.user_multi_procs = user_multi_procs

        self.is_old_chromedriver = version_main <= 114
        # Needs to be called before self.exe_name is accessed
        self._set_platform_name()

        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path, exist_ok=True)

        if not driver_executable_path:
            self.driver_executable_path = os.path.join(
                self.data_path, "_".join([prefix, self.exe_name])
            )

        if not IS_POSIX:
            if driver_executable_path:
                if not driver_executable_path[-4:] == ".exe":
                    driver_executable_path += ".exe"

        self.zip_path = os.path.join(self.data_path, prefix)

        if not driver_executable_path and not self.user_multi_procs:
            self.driver_executable_path = os.path.abspath(
                os.path.join(".", self.driver_executable_path)
            )

        if driver_executable_path:
            self._using_custom_exe = True
            self.driver_executable_path = driver_executable_path

        # Set the correct repository to download the Chromedriver from
        if self.is_old_chromedriver:
            self.url_repo = "https://chromedriver.storage.googleapis.com"
        else:
            self.url_repo = "https://googlechromelabs.github.io/chrome-for-testing"

        self.version_main = version_main
        self.version_full = None

    def _set_platform_name(self):
        """
        Set the platform and exe name based on the platform undetected is running on
        in order to download the correct chromedriver.
        """
        if self.platform.endswith("win32"):
            self.platform_name = "win32"
            self.exe_name %= ".exe"
        if self.platform.endswith(("linux", "linux2")):
            self.platform_name = "linux64"
            self.exe_name %= ""
        if self.platform.endswith("darwin"):
            if self.is_old_chromedriver:
                self.platform_name = "mac64"
            else:
                self.platform_name = "mac-x64"
            self.exe_name %= ""

    def verify(self):
        """
        Verify if the binary is patched.
        """
        p = pathlib.Path(self.data_path)

        with self.lock:
            files = list(p.glob("*chromedriver*"))

            if not files:
                raise Exception(
                    """
                    No undetected chromedriver binary were found.

                    Call `Patcher.patch()` outside of multiprocessing/threading implementation.
                    """
                )

            try:
                most_recent = max(files, key=lambda f: f.stat().st_mtime)
            except ValueError:
                return False

            for f in files:
                if f != most_recent:
                    try:
                        f.unlink()
                    except FileNotFoundError:
                        pass

            if self.is_binary_patched(most_recent):
                self.driver_executable_path = str(most_recent)
                return True

    def download_and_patch(self):
        release = self.fetch_release_number()

        self.version_main = release.major
        self.version_full = release

        self.unzip_package(self.fetch_package())
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
            path = self.driver_executable_path

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
        except Exception as e:
            # logger.exception("whoops ", e)
            pass

    @classmethod
    def cleanup_unused_files(cls):
        p = pathlib.Path(cls.data_path)
        items = list(p.glob("*chromedriver*"))

        logger.debug("Cleaning up unused files; found: %s", items)

        for item in items:
            try:
                cls.kill_all_instances(item)
                item.unlink()
                logger.debug("Deleted chromedriver: %s", item)
            except Exception as e:
                logger.debug("Failed to delete chromedriver %s: %s", item, e)

    def fetch_release_number(self):
        """
        Gets the latest major version available, or the latest major version of self.target_version if set explicitly.
        :return: version string
        :rtype: Version
        """
        # Endpoint for old versions of Chromedriver (114 and below)
        if self.is_old_chromedriver:
            path = f"/latest_release_{self.version_main}"
            path = path.upper()
            logger.debug("getting release number from %s" % path)
            return Version(urlopen(self.url_repo + path).read().decode())

        # Endpoint for new versions of Chromedriver (115+)
        if not self.version_main:
            # Fetch the latest version
            path = "/last-known-good-versions-with-downloads.json"
            logger.debug("getting release number from %s" % path)
            with urlopen(self.url_repo + path) as conn:
                response = conn.read().decode()

            last_versions = json.loads(response)
            return Version(last_versions["channels"]["Stable"]["version"])

        # Fetch the latest minor version of the major version provided
        path = "/latest-versions-per-milestone-with-downloads.json"
        logger.debug("getting release number from %s" % path)
        with urlopen(self.url_repo + path) as conn:
            response = conn.read().decode()

        major_versions = json.loads(response)
        return Version(major_versions["milestones"][str(self.version_main)]["version"])

    def parse_exe_version(self):
        with io.open(self.driver_executable_path, "rb") as f:
            for line in iter(lambda: f.readline(), b""):
                match = re.search(rb"platform_handle\x00content\x00([0-9.]*)", line)
                if match:
                    return Version(match[1].decode())

    def fetch_package(self):
        """
        Downloads ChromeDriver from source

        :return: path to downloaded file
        """
        zip_name = f"chromedriver_{self.platform_name}.zip"
        if self.is_old_chromedriver:
            download_url = "%s/%s/%s" % (
                self.url_repo,
                str(self.version_full),
                zip_name,
            )
        else:
            zip_name = zip_name.replace("_", "-", 1)
            download_url = (
                "https://storage.googleapis.com/chrome-for-testing-public/%s/%s/%s"
            )
            download_url %= (str(self.version_full), self.platform_name, zip_name)

        logger.debug("downloading from %s" % download_url)
        return urlretrieve(download_url)[0]

    def unzip_package(self, fp):
        """
        Unzips chromedriver

        :return: path to unpacked executable
        """
        exe_path = self.exe_name
        if not self.is_old_chromedriver:
            # The new chromedriver unzips into its own folder
            zip_name = f"chromedriver-{self.platform_name}"
            exe_path = os.path.join(zip_name, self.exe_name)

        logger.debug("unzipping %s" % fp)

        try:
            os.unlink(self.zip_path)
        except (FileNotFoundError, OSError):
            pass

        os.makedirs(self.zip_path, mode=0o755, exist_ok=True)
        with zipfile.ZipFile(fp, mode="r") as zf:
            zf.extractall(self.zip_path)
        os.rename(os.path.join(self.zip_path, exe_path), self.driver_executable_path)
        os.remove(fp)
        shutil.rmtree(self.zip_path)
        os.chmod(self.driver_executable_path, 0o755)
        return self.driver_executable_path

    @staticmethod
    def kill_all_instances(path):
        if IS_POSIX:
            cmd = f"pidof {path} >/dev/null && kill -9 $(pidof {path}) || true"
        else:
            cmd = f"taskkill /f /im {path} >nul 2>&1"

        exit_code = os.system(cmd)

        if exit_code == 0:
            logger.debug("Killed running instances of %s", path)
        else:
            logger.error(
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
        try:
            with io.open(driver_executable_path, "rb") as fh:
                return fh.read().find(b"undetected chromedriver") != -1
        except FileNotFoundError:
            return False

    def patch_exe(self):
        start = time.perf_counter()
        logger.info("patching driver executable %s" % self.driver_executable_path)
        with io.open(self.driver_executable_path, "r+b") as fh:
            content = fh.read()
            # match_injected_codeblock = re.search(rb"{window.*;}", content)
            match_injected_codeblock = re.search(rb"\{window\.cdc.*?;\}", content)
            if match_injected_codeblock:
                target_bytes = match_injected_codeblock[0]
                new_target_bytes = (
                    b'{console.log("undetected chromedriver 1337!")}'.ljust(
                        len(target_bytes), b" "
                    )
                )
                new_content = content.replace(target_bytes, new_target_bytes)
                if new_content == content:
                    logger.warning(
                        "something went wrong patching the driver binary. could not find injection code block"
                    )
                else:
                    logger.debug(
                        "found block:\n%s\nreplacing with:\n%s"
                        % (target_bytes, new_target_bytes)
                    )
                fh.seek(0)
                fh.write(new_content)
        logger.debug(
            "patching took us {:.2f} seconds".format(time.perf_counter() - start)
        )

    @staticmethod
    def patch(browser_executable_path=None, driver_executable_path=None):
        patcher = Patcher(
            version_main=get_browser_info(browser_executable_path)[
                "browser_major_version"
            ],
            driver_executable_path=driver_executable_path,
            for_patch=True,
        )
        patcher.cleanup_unused_files()
        patcher.download_and_patch()

    def __repr__(self):
        return "{0:s}({1:s})".format(
            self.__class__.__name__,
            self.driver_executable_path,
        )

    def __del__(self):
        if (
            not self._using_custom_exe
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
