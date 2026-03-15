from __future__ import annotations

from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Iterable

import yaml


@dataclass(frozen=True)
class MarkerSet:
    id: str
    logic: str
    genes: tuple[str, ...]
    tier: str = "core"
    min_hits: int = 1
    weight: float = 1.0
    notes: str = ""


@dataclass(frozen=True)
class PhenotypeDefinition:
    id: str
    name: str
    element: str
    summary: str
    threshold_hint: float = 0.5
    core_min_hits: int = 1
    evidence_urls: tuple[str, ...] = ()
    markers: tuple[MarkerSet, ...] = ()


@dataclass(frozen=True)
class PhenotypeLibrary:
    phenotypes: tuple[PhenotypeDefinition, ...] = field(default_factory=tuple)

    def ids(self) -> list[str]:
        return [phenotype.id for phenotype in self.phenotypes]

    def __iter__(self) -> Iterable[PhenotypeDefinition]:
        return iter(self.phenotypes)


def bundled_phenotype_config_path() -> Path:
    return Path(resources.files("tracepheno.data").joinpath("trace_element_phenotypes.yaml"))


def load_phenotype_library(config_path: str | Path | None = None) -> PhenotypeLibrary:
    path = Path(config_path) if config_path else bundled_phenotype_config_path()
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    phenotypes: list[PhenotypeDefinition] = []
    for phenotype in raw.get("phenotypes", []):
        markers = tuple(
            MarkerSet(
                id=item["id"],
                logic=item["logic"],
                genes=tuple(str(gene) for gene in item["genes"]),
                tier=str(item.get("tier", "core")),
                min_hits=int(item.get("min_hits", 1)),
                weight=float(item.get("weight", 1.0)),
                notes=str(item.get("notes", "")),
            )
            for item in phenotype.get("markers", [])
        )
        phenotypes.append(
            PhenotypeDefinition(
                id=str(phenotype["id"]),
                name=str(phenotype["name"]),
                element=str(phenotype.get("element", "")),
                summary=str(phenotype.get("summary", "")),
                threshold_hint=float(phenotype.get("threshold_hint", 0.5)),
                core_min_hits=int(phenotype.get("core_min_hits", 1)),
                evidence_urls=tuple(str(url) for url in phenotype.get("evidence_urls", [])),
                markers=markers,
            )
        )

    return PhenotypeLibrary(phenotypes=tuple(phenotypes))
