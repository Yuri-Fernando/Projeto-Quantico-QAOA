"""Manifesto por execução e utilitários de serialização (auditoria §7, "registro por execução").

O manifesto amarra cada resultado a: commit (``git_sha`` + ``git_dirty``), versões das bibliotecas,
config resolvida e seu hash, dispositivos detectados e linha de comando. Sem isso, um número
publicado não é reproduzível.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import platform
import subprocess
import sys
import uuid
from collections.abc import Iterable, Iterator
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from hpc.devices import detect_devices
from quantum.backends.base import library_versions

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_MANIFEST_KEYS = (
    "run_id", "experiment", "kind", "track", "timestamp_utc", "git_sha", "git_dirty", "python_version",
    "platform", "library_versions", "devices", "config", "config_hash", "command",
)
REQUIRED_RECORD_KEYS = ("record_id", "experiment", "kind", "track")


def _git(*args: str) -> str | None:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True,
                              timeout=15).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def to_jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def config_hash(config: dict) -> str:
    return hashlib.sha256(json.dumps(to_jsonable(config), sort_keys=True).encode()).hexdigest()


def build_manifest(experiment: str, kind: str, track: str, config: dict, argv: Iterable[str]) -> dict:
    now = datetime.now(timezone.utc)
    dirty = _git("status", "--porcelain", "--untracked-files=no")
    return {
        "run_id": f"{now:%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:6]}",
        "experiment": experiment,
        "kind": kind,
        "track": track,
        "timestamp_utc": now.isoformat(),
        "git_sha": _git("rev-parse", "HEAD"),
        "git_dirty": bool(dirty) if dirty is not None else None,
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "library_versions": library_versions(),
        "devices": detect_devices(),
        "dependency_lock": "requirements-lock.txt",
        "config": to_jsonable(config),
        "config_hash": config_hash(config),
        "command": " ".join(argv),
    }


class RunWriter:
    """Escreve ``manifest.json``, ``records.jsonl`` e ``raw_counts.jsonl.gz`` num diretório novo por execução."""

    def __init__(self, out_root: Path, manifest: dict):
        self.dir = Path(out_root) / manifest["experiment"] / manifest["run_id"]
        self.dir.mkdir(parents=True, exist_ok=False)  # nunca sobrescreve uma execução anterior
        self.manifest = manifest
        self._records = open(self.dir / "records.jsonl", "w", encoding="utf-8")
        self._counts = gzip.open(self.dir / "raw_counts.jsonl.gz", "wt", encoding="utf-8")
        self.n_records = 0

    def write(self, record: dict, counts: dict | None = None) -> None:
        record = {"record_id": f"r{self.n_records:05d}", "experiment": self.manifest["experiment"],
                  "kind": self.manifest["kind"], "track": self.manifest["track"], **record}
        if counts is not None:
            self._counts.write(json.dumps({"record_id": record["record_id"], "counts": counts}) + "\n")
            record["raw_counts_ref"] = f"raw_counts.jsonl.gz#{record['record_id']}"
        self._records.write(json.dumps(to_jsonable(record), ensure_ascii=False) + "\n")
        self._records.flush()
        self.n_records += 1

    def close(self, extra: dict | None = None) -> Path:
        self._records.close()
        self._counts.close()
        manifest = {**self.manifest, "n_records": self.n_records, **(extra or {})}
        (self.dir / "manifest.json").write_text(json.dumps(to_jsonable(manifest), indent=2, ensure_ascii=False),
                                                encoding="utf-8")
        return self.dir


def read_records(run_dir: Path) -> Iterator[dict]:
    with open(Path(run_dir) / "records.jsonl", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def read_manifest(run_dir: Path) -> dict:
    return json.loads((Path(run_dir) / "manifest.json").read_text(encoding="utf-8"))
