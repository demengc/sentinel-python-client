import time

import pytest

from sentinel._exceptions import ReplayDetectedError
from sentinel._replay import ReplayProtector


def test_accepts_fresh_nonce():
    rp = ReplayProtector(window_seconds=30.0, max_size=100)
    now_ms = int(time.time() * 1000)
    rp.check("nonce-1", now_ms)


def test_rejects_duplicate_nonce():
    rp = ReplayProtector(window_seconds=30.0, max_size=100)
    now_ms = int(time.time() * 1000)
    rp.check("nonce-1", now_ms)
    with pytest.raises(ReplayDetectedError, match="Duplicate nonce"):
        rp.check("nonce-1", now_ms)


def test_rejects_stale_timestamp():
    rp = ReplayProtector(window_seconds=5.0, max_size=100)
    old_ms = int(time.time() * 1000) - 60_000
    with pytest.raises(ReplayDetectedError, match="outside the acceptable window"):
        rp.check("nonce-old", old_ms)


def test_rejects_future_timestamp():
    rp = ReplayProtector(window_seconds=5.0, max_size=100)
    future_ms = int(time.time() * 1000) + 60_000
    with pytest.raises(ReplayDetectedError, match="outside the acceptable window"):
        rp.check("nonce-future", future_ms)


def test_evicts_oldest_nonce():
    rp = ReplayProtector(window_seconds=30.0, max_size=3)
    now_ms = int(time.time() * 1000)
    rp.check("a", now_ms)
    rp.check("b", now_ms)
    rp.check("c", now_ms)
    rp.check("d", now_ms)
    rp.check("a", now_ms)
