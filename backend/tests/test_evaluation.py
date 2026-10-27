import pytest

from evaluation.cases import load_cases
from evaluation.harness import Harness

pytestmark = pytest.mark.anyio

CASES = load_cases()


@pytest.fixture(scope="module")
def harness(monkeypatch_module) -> Harness:
    return Harness.create(use_ai=False)


@pytest.fixture(scope="module")
def monkeypatch_module():
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("GEMINI_API_KEY", "")
        patch.setenv("GEMINI_API_KEY_BACKUP", "")
        yield patch


@pytest.mark.parametrize("case", CASES, ids=[case.name for case in CASES])
async def test_case_has_no_hard_rule_violations(harness, case):
    result = await harness.evaluate(case)

    assert result.violations == []


@pytest.mark.parametrize(
    "case",
    [case for case in CASES if "rules-reader-limit" not in case.tags],
    ids=lambda case: case.name,
)
async def test_rule_reader_reads_supported_layouts_exactly(harness, case):
    result = await harness.evaluate(case)

    assert (result.reading.precision, result.reading.recall) == (1.0, 1.0)
    assert result.reading.gpa_correct is not False
