import json

import httpx
import pytest

from app.services.plan_repository import PlanRepository
from app.services.plan_store import DirectoryPlanStore, PlanStoreError, RedisPlanStore


class FakeUpstash:
    """Minimal in-memory stand-in for the Upstash REST API (GET and SET only)."""

    def __init__(self) -> None:
        self.data: dict[str, str] = {}
        self.commands: list[list[str]] = []
        self.tokens: set[str] = set()

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.tokens.add(request.headers["Authorization"])
        command = json.loads(request.content)
        self.commands.append(command)
        if command[0] == "GET":
            return httpx.Response(200, json={"result": self.data.get(command[1])})
        if command[0] == "SET":
            self.data[command[1]] = command[2]
            return httpx.Response(200, json={"result": "OK"})
        return httpx.Response(200, json={"error": "unknown command"})


@pytest.fixture
def upstash() -> FakeUpstash:
    return FakeUpstash()


@pytest.fixture
def store(upstash, data_dir) -> RedisPlanStore:
    return RedisPlanStore(
        "https://example.upstash.io/",
        "secret",
        seed=DirectoryPlanStore(data_dir),
        transport=httpx.MockTransport(upstash.handle),
    )


def renamed(plan, code: str):
    return plan.model_copy(update={"code": code})


def test_empty_redis_serves_the_bundled_plans(store, upstash):
    codes = {plan.code for plan in store.load_all()}

    assert codes == {"cs", "net"}
    assert upstash.tokens == {"Bearer secret"}


def test_saving_keeps_existing_plans_and_adds_the_new_one(store, cs_plan):
    store.save(renamed(cs_plan, "se"))

    assert {plan.code for plan in store.load_all()} == {"cs", "net", "se"}


def test_saved_plans_survive_a_new_store_instance(store, upstash, cs_plan, data_dir):
    store.save(renamed(cs_plan, "se"))
    fresh = RedisPlanStore(
        "https://example.upstash.io", "secret",
        seed=DirectoryPlanStore(data_dir), transport=httpx.MockTransport(upstash.handle),
    )

    assert "se" in {plan.code for plan in fresh.load_all()}


def test_redis_errors_are_raised(data_dir):
    failing = RedisPlanStore(
        "https://example.upstash.io", "secret",
        seed=DirectoryPlanStore(data_dir),
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"error": "WRONGPASS"})),
    )

    with pytest.raises(PlanStoreError):
        failing.load_all()


def test_repository_picks_up_plans_published_by_another_instance(store, cs_plan):
    now = [0.0]
    reader = PlanRepository(store.load_all(), store, refresh_seconds=60, clock=lambda: now[0])

    PlanRepository.from_store(store).save(renamed(cs_plan, "se"))  # another server instance

    assert "se" not in {d.code for d in reader.list_departments()}  # still within the cache window
    now[0] = 61
    assert "se" in {d.code for d in reader.list_departments()}


def test_repository_without_refresh_never_rereads(store, upstash):
    repository = PlanRepository.from_store(store)
    count = len(upstash.commands)

    repository.list_departments()
    repository.get("cs")

    assert len(upstash.commands) == count
