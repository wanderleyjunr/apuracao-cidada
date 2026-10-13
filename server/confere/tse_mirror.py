"""Mirror of the TSE per-section urna files (resultados.tse.jus.br). MUST run from a Brazilian IP.

Flow per UF: read config cs.json (every section + its last-update timestamp) → for sections whose timestamp
changed since last run, read the section aux.json → download bu.dat (and vota.vsc) once, keyed by the aux hash.
Polite by design: bounded concurrency, retries with backoff, each file fetched once (content never changes per hash).
"""
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

import httpx

BASE = "https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna"
ELECTION = {1: 3220, 2: 3221}  # pleito code per round
UFS = "ac al am ap ba ce df es go ma mg ms mt pa pb pe pi pr rj rn ro rr rs sc se sp to zz".split()


@dataclass(frozen=True)
class Section:
    uf: str
    municipality: int
    zone: int
    section: int
    updated: str  # "dd/mm/yyyy hh:mm:ss" from cs.json

    def key(self, turn: int) -> str:  # same format as shared/ballot.ts sectionKey
        return f"{turn}:{self.uf}:{self.municipality}:{self.zone}:{self.section}"


def config_url(pleito: int, uf: str) -> str:
    return f"{BASE}/{pleito}/config/{uf}/{uf}-p{pleito:06d}-cs.json"


def section_dir(pleito: int, s: Section) -> str:
    return f"{BASE}/{pleito}/dados/{s.uf}/{s.municipality:05d}/{s.zone:04d}/{s.section:04d}"


def aux_url(pleito: int, s: Section) -> str:
    return f"{section_dir(pleito, s)}/p{pleito:06d}-{s.uf}-m{s.municipality:05d}-z{s.zone:04d}-s{s.section:04d}-aux.json"


def file_url(pleito: int, s: Section, file_hash: str, name: str) -> str:
    return f"{section_dir(pleito, s)}/{file_hash}/{name}"


def parse_config(cfg: dict) -> list[Section]:
    out = []
    for state in cfg["abr"]:
        for mu in state["mu"]:
            for zone in mu["zon"]:
                for sec in zone["sec"]:
                    out.append(Section(state["cd"], int(mu["cd"]), int(zone["cd"]), int(sec["ns"]), f"{sec['da']} {sec['ha']}"))
    return out


def municipality_names(cfg: dict) -> dict[int, str]:
    """TSE municipality code → name (feeds the app's name→code lookup)."""
    return {int(mu["cd"]): mu["nm"] for state in cfg["abr"] for mu in state["mu"]}


def latest_files(aux: dict) -> tuple[str, str, dict[str, str]] | None:
    """(hash, received 'dd/mm/yyyy hh:mm:ss', {type: filename}) of the most recent upload, or None if absent."""
    if not aux.get("hashes"):
        return None
    h = aux["hashes"][-1]
    return h["hash"], f"{h['dr']} {h['hr']}", {a["tp"]: a["nm"] for a in h["arq"]}


class Mirror:
    """Downloads into `root/<pleito>/<uf>/<mun>/<zone>/<section>/<hash>/<file>`; a state file remembers timestamps."""

    def __init__(self, root: Path, concurrency: int = 8):
        self.root = root
        self.sem = asyncio.Semaphore(concurrency)
        self.state_path = root / "state.json"
        self.state: dict[str, str] = json.loads(self.state_path.read_text()) if self.state_path.exists() else {}

    async def _get(self, client: httpx.AsyncClient, url: str) -> httpx.Response:
        async with self.sem:
            for attempt in range(4):
                try:
                    r = await client.get(url, timeout=30)
                    if r.status_code == 404:
                        return r
                    r.raise_for_status()
                    return r
                except httpx.HTTPError:
                    if attempt == 3:
                        raise
                    await asyncio.sleep(2 ** attempt)

    async def sync_section(self, client: httpx.AsyncClient, pleito: int, s: Section) -> Path | None:
        """Fetches a section if new/changed; returns the bu.dat path or None."""
        r = await self._get(client, aux_url(pleito, s))
        if r.status_code == 404:
            return None
        latest = latest_files(r.json())
        if not latest:
            return None
        file_hash, _received, files = latest
        target = self.root / str(pleito) / s.uf / str(s.municipality) / str(s.zone) / str(s.section) / file_hash
        (target / "aux.json").parent.mkdir(parents=True, exist_ok=True)
        (target / "aux.json").write_bytes(r.content)
        for kind in ("bu", "vota"):
            name = files.get(kind)
            if name and not (target / name).exists():
                (target / name).write_bytes((await self._get(client, file_url(pleito, s, file_hash, name))).content)
        return target / files["bu"] if "bu" in files else None

    async def sync_uf(self, pleito: int, uf: str, on_ballot=None) -> int:
        """One pass over a UF. `on_ballot(section, bu_path)` is called for each new/changed section."""
        async with httpx.AsyncClient(headers={"user-agent": "apuracao-cidada-mirror (open source citizen audit)"}) as client:
            cfg = (await self._get(client, config_url(pleito, uf))).json()
            changed = [s for s in parse_config(cfg) if self.state.get(f"{pleito}:{s.key(0)}") != s.updated]

            async def one(s: Section):
                path = await self.sync_section(client, pleito, s)
                if path:
                    self.state[f"{pleito}:{s.key(0)}"] = s.updated
                    if on_ballot:
                        on_ballot(s, path)

            await asyncio.gather(*(one(s) for s in changed))
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self.state))
        return len(changed)
