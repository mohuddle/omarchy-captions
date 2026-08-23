from __future__ import annotations

import tarfile
import urllib.request
from pathlib import Path

from .paths import models_dir

# Small English streaming Zipformer. Fast enough to caption a lecture
# while a browser is decoding video on a laptop CPU.
DEFAULT_MODEL = {
    "id": "zipformer-en-20m",
    "url": (
        "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/"
        "sherpa-onnx-streaming-zipformer-en-20M-2023-02-17.tar.bz2"
    ),
    "dirname": "sherpa-onnx-streaming-zipformer-en-20M-2023-02-17",
}


def model_root() -> Path:
    return models_dir() / DEFAULT_MODEL["dirname"]


def _pick(files: list[Path], *needles: str) -> Path:
    for needle in needles:
        for path in files:
            name = path.name.lower()
            if needle in name:
                return path
    raise FileNotFoundError(f"missing {needles} in {files}")


def transducer_paths(root: Path | None = None) -> dict[str, str]:
    root = root or model_root()
    onnx = [p for p in root.glob("*.onnx") if p.is_file()]
    tokens = root / "tokens.txt"
    if not tokens.is_file():
        raise FileNotFoundError(f"no tokens.txt in {root}")
    return {
        "encoder": str(_pick(onnx, "encoder")),
        "decoder": str(_pick(onnx, "decoder")),
        "joiner": str(_pick(onnx, "joiner")),
        "tokens": str(tokens),
    }


def model_ready() -> bool:
    try:
        transducer_paths()
        return True
    except FileNotFoundError:
        return False


def download_default(progress=print) -> Path:
    root = model_root()
    if model_ready():
        progress(f"model already present: {root}")
        return root

    archive = models_dir() / Path(DEFAULT_MODEL["url"]).name
    progress(f"downloading {DEFAULT_MODEL['url']}")
    urllib.request.urlretrieve(DEFAULT_MODEL["url"], archive)
    progress(f"extracting {archive.name}")
    with tarfile.open(archive, "r:bz2") as tar:
        tar.extractall(models_dir())
    if not model_ready():
        raise RuntimeError(f"extracted archive but could not find transducer files in {root}")
    progress(f"model ready: {root}")
    return root
