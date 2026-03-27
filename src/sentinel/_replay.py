from __future__ import annotations

import threading
import time
from collections import OrderedDict

from sentinel._exceptions import ReplayDetectedError


class ReplayProtector:
    def __init__(self, window_seconds: float, max_size: int) -> None:
        self._window_ms = window_seconds * 1000
        self._max_size = max_size
        self._nonce_cache: OrderedDict[str, bool] = OrderedDict()
        self._lock = threading.Lock()

    def check(self, nonce: str, response_timestamp_ms: int) -> None:
        now = time.time() * 1000
        drift = abs(now - response_timestamp_ms)

        if drift > self._window_ms:
            raise ReplayDetectedError(
                f"Response timestamp is outside the acceptable window: "
                f"drift={int(drift)}ms, window={int(self._window_ms)}ms"
            )

        with self._lock:
            if nonce in self._nonce_cache:
                raise ReplayDetectedError(f"Duplicate nonce detected: {nonce}")
            self._nonce_cache[nonce] = True
            while len(self._nonce_cache) > self._max_size:
                self._nonce_cache.popitem(last=False)
