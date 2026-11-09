import pytest

from .harness import Rig


@pytest.fixture
def rig():
    rigs = []

    def make(**kwargs) -> Rig:
        r = Rig(**kwargs)
        rigs.append(r)
        return r

    yield make
    for r in rigs:
        r.close()
