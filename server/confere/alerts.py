"""Observer alerts (OAB, press, both campaigns): POST a JSON notice to each webhook when a divergence opens.

Env: OBSERVER_WEBHOOKS="https://...,https://..." (Slack/Discord/email-gateway style webhooks, chosen by the council).
Only public facts go out: section, status, differences and the public link. Best effort: a failing webhook never blocks
ingestion; the divergence is always on the public list anyway.
"""
import json
import logging
import os
import urllib.request

log = logging.getLogger("confere.alerts")


def notice(doc: dict, public_url: str) -> dict:
    turn, uf, mun, zone, section = doc["key"].split(":")
    diffs = ", ".join(f"{d['key']}: porta {d['door']} × TSE {d['tse']}" for d in doc["differences"][:5]) or "boletins da porta diferentes entre si"
    text = f"Divergência na seção {section}, zona {zone}, {uf.upper()} (município {mun}, {turn}º turno): {diffs}. Fato a ser explicado, não acusação."
    return {"text": text, "section": doc["key"], "status": doc["status"], "differences": doc["differences"],
            "link": f"{public_url}/#/section?s={doc['key']}"}


def notify(doc: dict | None, public_url: str = "", webhooks: str | None = None) -> int:
    """Sends the notice if the section just became divergent; returns how many webhooks accepted it."""
    if not doc or not doc.get("opened"):
        return 0
    body = json.dumps(notice(doc, public_url), ensure_ascii=False).encode()
    sent = 0
    for url in filter(None, (webhooks if webhooks is not None else os.environ.get("OBSERVER_WEBHOOKS", "")).split(",")):
        try:
            urllib.request.urlopen(urllib.request.Request(url.strip(), body, {"content-type": "application/json"}), timeout=10)
            sent += 1
        except OSError:
            log.warning("observer webhook failed: %s", url)
    return sent
