"""Target-isolated persistence and validation for self-healing locator records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import LocatorKey, LocatorRecord


class LocatorMap:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._records: dict[LocatorKey, LocatorRecord] = {}
        if path.exists():
            self._load()

    def get(self, key: LocatorKey, *, viewport: tuple[int, int] | None = None) -> LocatorRecord | None:
        record = self._records.get(key)
        if record is None or (record.viewport is not None and record.viewport != viewport):
            return None
        return record

    def put(self, record: LocatorRecord) -> None:
        self._records[record.key] = record

    def clear_target(self, target_id: str) -> int:
        keys = [key for key in self._records if key.target_id == target_id]
        for key in keys:
            del self._records[key]
        return len(keys)

    def records_for_target(self, target_id: str) -> Iterable[LocatorRecord]:
        return (record for key, record in self._records.items() if key.target_id == target_id)

    @staticmethod
    def matches_intent(record: LocatorRecord, *, role: str | None, name: str | None) -> bool:
        return (
            (record.expected_role is None or record.expected_role == role)
            and (record.expected_name is None or record.expected_name == name)
        )

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        records = [
            {
                "target_id": item.key.target_id,
                "page_identity": item.key.page_identity,
                "element_intent": item.key.element_intent,
                "strategy": item.strategy,
                "value": item.value,
                "expected_role": item.expected_role,
                "expected_name": item.expected_name,
                "viewport": item.viewport,
                "version": item.version,
            }
            for item in self._records.values()
        ]
        self.path.write_text(json.dumps({"version": 1, "records": records}, indent=2) + "\n")

    def _load(self) -> None:
        raw = json.loads(self.path.read_text())
        for item in raw.get("records", []):
            key = LocatorKey(item["target_id"], item["page_identity"], item["element_intent"])
            viewport = tuple(item["viewport"]) if item.get("viewport") else None
            self._records[key] = LocatorRecord(
                key=key,
                strategy=item["strategy"],
                value=item["value"],
                expected_role=item.get("expected_role"),
                expected_name=item.get("expected_name"),
                viewport=viewport,
                version=item.get("version", 1),
            )
