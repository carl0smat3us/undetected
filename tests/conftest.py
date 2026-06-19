import logging

import pytest

import undetected as uc


def pytest_configure():
    for name in ["urllib3", "selenium"]:
        logger = logging.getLogger(name)
        logger.disabled = True
        logger.propagate = False
        logger.handlers.clear()


@pytest.fixture(autouse=True)
def before_each_test():
    uc.Patcher.cleanup_unused_files()
    yield
    uc.Patcher.cleanup_unused_files()
