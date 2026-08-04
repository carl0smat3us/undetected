# this module is part of undetected

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from selenium.webdriver.chromium.options import ChromiumOptions as _ChromiumOptions


class ChromeOptions(_ChromiumOptions):
    _session = None
    _user_data_dir = None
    _languages: list[str] | None = None

    @property
    def user_data_dir(self):
        return self._user_data_dir

    @user_data_dir.setter
    def user_data_dir(self, path: str):
        """
        Sets the browser profile folder to use, or creates a new profile
        at given <path>.

        Parameters
        ----------
        path: str
            the path to a chrome profile folder
            if it does not exist, a new profile will be created at given location
        """
        self._user_data_dir = Path(path).resolve()

    @property
    def languages(self) -> list[str] | None:
        """Browser / navigator languages, e.g. ``["fr-FR", "fr"]``."""
        return self._languages

    @languages.setter
    def languages(self, value: list[str] | tuple[str, ...] | str | None):
        if value is None:
            self._languages = None
            return

        if isinstance(value, str):
            parts = [
                chunk.strip().split(";", 1)[0].strip()
                for chunk in value.split(",")
                if chunk.strip()
            ]
        else:
            parts = [
                str(item).strip().split(";", 1)[0].strip()
                for item in value
                if str(item).strip()
            ]

        self._languages = parts or None
        self._sync_lang_argument()

    def _sync_lang_argument(self) -> None:
        """Keep ``--lang`` in sync with ``options.languages``."""
        self.arguments[:] = [
            arg for arg in self.arguments if not re.match(r"(?:--)?lang(?:[ =]|$)", arg)
        ]
        if self._languages:
            self.add_argument("--lang=%s" % ",".join(self._languages))

    @staticmethod
    def _undot_key(key, value):
        """turn a (dotted key, value) into a proper nested dict"""
        if "." in key:
            key, rest = key.split(".", 1)
            value = ChromeOptions._undot_key(rest, value)
        return {key: value}

    @staticmethod
    def _merge_nested(a, b):
        """
        merges b into a
        leaf values in a are overwritten with values from b
        """
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    ChromeOptions._merge_nested(a[key], b[key])
                    continue
            a[key] = b[key]
        return a

    def handle_prefs(self, user_data_dir):
        prefs = self.experimental_options.get("prefs")
        if prefs:
            user_data_dir = user_data_dir or self._user_data_dir
            default_path = Path(str(user_data_dir)) / "Default"
            os.makedirs(default_path, exist_ok=True)

            # undot prefs dict keys
            undot_prefs = {}
            for key, value in prefs.items():
                undot_prefs = self._merge_nested(
                    undot_prefs, self._undot_key(key, value)
                )

            prefs_file = Path(str(default_path)) / "Preferences"
            if Path(prefs_file).exists():
                with open(prefs_file, encoding="latin1") as f:
                    undot_prefs = self._merge_nested(json.load(f), undot_prefs)

            with open(prefs_file, encoding="latin1", mode="w") as f:
                json.dump(undot_prefs, f)

            # remove the experimental_options to avoid an error
            del self._experimental_options["prefs"]

    @classmethod
    def from_options(cls, options):
        o = cls()
        o.__dict__.update(options.__dict__)
        return o
