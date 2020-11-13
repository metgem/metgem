from pathlib import Path
import pytest


@pytest.fixture(scope="package")
def examples():
    return (Path(__file__).resolve().parent.parent / 'examples').absolute()
