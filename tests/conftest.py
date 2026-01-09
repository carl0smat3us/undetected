import pytest
import undetected as uc

@pytest.fixture(autouse=True)
def before_each_test():
    uc.Patcher.cleanup_unused_files()
    yield
    uc.Patcher.cleanup_unused_files()
