"""Shared helpers: HTTPS with certifi's CA bundle (macOS Python ships without one), polite retries."""
import json, ssl, time, urllib.request
from pathlib import Path

import certifi

UA = "sinturon-pipeline/1 (+https://github.com/mendozaivanka/sinturon)"
CTX = ssl.create_default_context(cafile=certifi.where())
HERE = Path(__file__).parent


def get(url: str, *, tries: int = 4, timeout: int = 60) -> bytes:
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, context=CTX, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # network blips, 5xx, rate limits
            if attempt == tries - 1:
                raise RuntimeError(f"GET {url} failed after {tries} tries: {e}") from e
            time.sleep(2 ** attempt * 2)
    raise AssertionError("unreachable")


def get_json(url: str):
    return json.loads(get(url))


def write_json(path: Path, data, *, indent=None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))
    path.write_text(text + "\n")
