"""Gera um lock das dependências realmente instaladas (fecho transitivo de ``requirements.txt``).

O ``pip freeze`` do interpretador global traria centenas de pacotes sem relação com o projeto;
este script parte das dependências diretas de ``requirements.txt`` e segue os ``Requires-Dist``
instalados (via ``importlib.metadata``), fixando a versão exata de cada pacote alcançado.

Uso:
    python tools/lock_deps.py > requirements-lock.txt
"""
from __future__ import annotations

import platform
import re
import sys
from importlib import metadata
from pathlib import Path

_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def _canonical(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _direct_requirements(path: Path) -> list[str]:
    names = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        match = _NAME.match(line)
        if match:
            names.append(match.group(1))
    return names


def _requires(dist: metadata.Distribution) -> list[str]:
    out = []
    for req in dist.requires or []:
        if "extra ==" in req:  # extras opcionais não fazem parte do fecho mínimo
            continue
        if ";" in req:
            marker = req.split(";", 1)[1]
            if "sys_platform" in marker or "platform_system" in marker or "python_version" in marker:
                try:
                    from packaging.markers import Marker

                    if not Marker(marker.strip()).evaluate():
                        continue
                except Exception:
                    pass
        match = _NAME.match(req)
        if match:
            out.append(match.group(1))
    return out


def lock(requirements: Path) -> dict[str, str]:
    seen: dict[str, str] = {}
    stack = _direct_requirements(requirements)
    while stack:
        name = stack.pop()
        key = _canonical(name)
        if key in seen:
            continue
        try:
            dist = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            seen[key] = "NOT-INSTALLED"
            continue
        seen[key] = dist.version
        stack.extend(_requires(dist))
    return dict(sorted(seen.items()))


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    pins = lock(root / "requirements.txt")
    print(f"# Lock gerado por tools/lock_deps.py — Python {platform.python_version()} ({sys.platform})")
    print("# Fecho transitivo de requirements.txt no ambiente onde os testes passaram.")
    for name, version in pins.items():
        if version == "NOT-INSTALLED":
            print(f"# {name}: não instalado neste ambiente")
        else:
            print(f"{name}=={version}")


if __name__ == "__main__":
    main()
