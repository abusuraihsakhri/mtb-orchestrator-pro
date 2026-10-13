import csv

import pytest

from agents.base import AuditTrail, SecurityException
from agents.llm_factory import LLMFactory
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from cli import main


def test_batch_cli_uses_documented_csv_schema(tmp_path):
    source = tmp_path / "in.csv"
    target = tmp_path / "out.csv"
    source.write_text(
        "task_id,target_identifier,primary_metric,secondary_metric,is_critical_flag,status_descriptor\n"
        "T1,SPEC-01,26,13,true,DISCORDANT\n"
        "T2,SPEC-02,5,1,false,NOMINAL\n",
        encoding="utf-8",
    )
    assert main(["batch", "-i", str(source), "-o", str(target)]) == 0
    with target.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 2
    assert rows[0]["overall_urgency"] == "CRITICAL_STAT_PANIC"
    assert rows[0]["total_alerts"] == "3"
    assert rows[1]["overall_urgency"] == "ROUTINE"


def test_batch_rejects_missing_required_header(tmp_path):
    source = tmp_path / "in.csv"
    source.write_text("task_id,target_identifier\nT1,SPEC-01\n", encoding="utf-8")
    assert main(["batch", "-i", str(source), "-o", str(tmp_path / "out.csv")]) == 1


def test_attributes_guarded_and_logs_are_copied():
    task = SystemTaskPayload(
        task_id="TASK-X", target_identifier="SPEC-X", primary_metric=10,
        attributes={"comment": "Contact test@example.com"}
    )
    with pytest.raises(SecurityException):
        SystemSupervisor().process_task(task)
    trail = AuditTrail(secret_key="test-key")
    trail.log("test", "worker", "event", {"value": "clean"})
    returned = trail.get_trail()
    returned[0]["current_hash"] = "fake"
    assert trail.verify_integrity() is True


def test_only_mock_adapter_is_implemented():
    assert "not clinical analysis" in LLMFactory.create("mock").invoke("status")
    with pytest.raises(ValueError):
        LLMFactory.create("openai")


def test_cli_csv_export_escapes_formula_cells_but_keeps_negatives(tmp_path):
    source = tmp_path / "formula.csv"
    result = tmp_path / "result.csv"
    source.write_text(
        "task_id,target_identifier,primary_metric,secondary_metric,status_descriptor\n"
        "=1+1,SPEC-01,-2.5,0,NOMINAL\n", encoding="utf-8"
    )
    assert main(["batch", "-i", str(source), "-o", str(result)]) == 0
    with result.open(newline="", encoding="utf-8") as stream:
        row = next(csv.DictReader(stream))
    assert row["task_id"] == "'=1+1"
    assert row["primary_metric"] == "-2.5"


def test_invalid_csv_critical_flag_is_rejected(tmp_path, capsys):
    source = tmp_path / "invalid-flag.csv"
    target = tmp_path / "out.csv"
    source.write_text(
        "task_id,target_identifier,primary_metric,is_critical_flag\n"
        "T1,SPEC-01,10,maybe\n", encoding="utf-8"
    )
    assert main(["batch", "-i", str(source), "-o", str(target)]) == 0
    assert "1 skipped" in capsys.readouterr().out
    with target.open(newline="", encoding="utf-8") as stream:
        assert list(csv.DictReader(stream)) == []


def test_batch_skips_direct_identifier_row(tmp_path, capsys):
    source = tmp_path / "with-identifier.csv"
    target = tmp_path / "out.csv"
    source.write_text(
        "task_id,target_identifier,primary_metric\n"
        "T1,MRN-994827,10\n"
        "T2,SPEC-02,10\n", encoding="utf-8"
    )
    assert main(["batch", "-i", str(source), "-o", str(target)]) == 0
    assert "1 skipped" in capsys.readouterr().out
    with target.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    assert rows[0]["task_id"] == "T2"
