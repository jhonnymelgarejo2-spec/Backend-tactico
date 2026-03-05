# scanner.py
from __future__ import annotations
import asyncio
from typing import Dict, Any, List
from providers import DataProvider, MockProvider, to_dict as p_to_dict
from signals import generate_signal, to_dict as s_to_dict

class Scanner:
    def __init__(self, provider: DataProvider, max_matches: int = 60):
        self.provider = provider
        self.max_matches = max_matches
        self.last_snapshot: Dict[str, Any] = {
            "matches": [],
            "signals": [],
            "updated_at": None,
        }

    async def run_once(self) -> Dict[str, Any]:
        matches = await self.provider.get_live_matches()

        # “Primera división” (por ahora mock ya viene True; con API real filtramos aquí)
        first_div = [m for m in matches if m.is_first_division][: self.max_matches]

        signals = []
        for m in first_div:
            stats = await self.provider.get_live_stats(m.id)
            odds = await self.provider.get_odds(m.id)
            sig = generate_signal(m, stats, odds)
            signals.append(s_to_dict(sig))

        snapshot = {
            "matches": [p_to_dict(m) for m in first_div],
            "signals": signals,
        }
        self.last_snapshot = snapshot
        return snapshot

    async def loop(self, interval_sec: int = 60):
        while True:
            try:
                await self.run_once()
            except Exception as e:
                self.last_snapshot = {"error": str(e), "matches": [], "signals": []}
            await asyncio.sleep(interval_sec)
