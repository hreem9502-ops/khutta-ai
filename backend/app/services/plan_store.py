"""Where study plans are persisted. The repository depends only on :class:`PlanStore`."""

import json
from pathlib import Path
from typing import Protocol

import httpx

from app.models.course import StudyPlan


class PlanStoreError(Exception):
    """The plan store could not be read or written."""


class PlanStore(Protocol):
    """Durable storage for study plans."""

    def load_all(self) -> list[StudyPlan]: ...

    def save(self, plan: StudyPlan) -> None: ...


class DirectoryPlanStore:
    """Stores each plan as ``<code>.json`` in a local directory. Used for local development."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def load_all(self) -> list[StudyPlan]:
        paths = sorted(self._directory.glob("*.json"))
        if not paths:
            raise FileNotFoundError(f"No study plans found in {self._directory}")
        return [StudyPlan.model_validate_json(path.read_text(encoding="utf-8")) for path in paths]

    def save(self, plan: StudyPlan) -> None:
        """Write atomically so a crash never leaves a half-written plan."""
        path = self._directory / f"{plan.code}.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(plan.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(path)


class RedisPlanStore:
    """Stores all plans as one JSON document in Redis, through the Upstash REST API.

    Serverless hosts such as Vercel have no persistent disk, so published plans live here.
    Until the first publish the key is empty and the plans bundled with the code (``seed``)
    are served.
    """

    def __init__(
        self,
        url: str,
        token: str,
        seed: PlanStore,
        key: str = "khutta:plans",
        timeout_seconds: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(
            base_url=url.rstrip("/"),
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout_seconds,
            transport=transport,
        )
        self._seed = seed
        self._key = key

    def load_all(self) -> list[StudyPlan]:
        stored = self._command(["GET", self._key])
        if stored is None:
            return self._seed.load_all()
        return [StudyPlan.model_validate(item) for item in json.loads(stored)]

    def save(self, plan: StudyPlan) -> None:
        """Replace ``plan`` (by department code) in the stored set, keeping the others."""
        plans = {existing.code: existing for existing in self.load_all()}
        plans[plan.code] = plan
        document = json.dumps([item.model_dump(mode="json") for item in plans.values()], ensure_ascii=False)
        self._command(["SET", self._key, document])

    def _command(self, command: list[str]) -> str | None:
        try:
            response = self._client.post("", json=command)
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise PlanStoreError(f"Redis request failed: {error}") from error
        if "error" in body:
            raise PlanStoreError(f"Redis command failed: {body['error']}")
        return body.get("result")
