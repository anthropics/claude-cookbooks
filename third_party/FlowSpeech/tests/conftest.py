import os
import socket
import sys
from pathlib import Path

sys.path.insert(0, os.environ.get("FLOWSPEECH_TEST_ROOT", str(Path(__file__).resolve().parents[1])))

import pytest  # noqa: E402
from test_v1_contract import factory as factory  # noqa: E402


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Offline tests must not connect to the network")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
