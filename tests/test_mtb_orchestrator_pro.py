"""
Automated Pytest Test Suite for Mtb Orchestrator Pro.
Domain: Antimicrobial Stewardship & Microbiology
Standard: CLSI M100 / EUCAST / CDC NHSN Guidelines
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import PHIGuard, AuditLogger, SecurityException, AuditTrail
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_phi_guard_redaction():
    redacted = PHIGuard.redact_phi("Contact patient at 555-123-4567 or test@example.com")
    assert "555-123-4567" not in redacted
    assert "test@example.com" not in redacted
    assert "[REDACTED_IDENTIFIER]" in redacted


def test_phi_guard_ssn_pattern():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient SSN 123-45-6789 verified")


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0


def test_payload_validation_rejects_nan():
    import math
    with pytest.raises((ValueError, Exception)):
        SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=math.nan)


def test_payload_validation_rejects_inf():
    with pytest.raises((ValueError, Exception)):
        SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=float("inf"))


def test_payload_validation_rejects_extreme_values():
    with pytest.raises((ValueError, Exception)):
        SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=1e15)


def test_audit_trail_integrity_verification():
    trail = AuditTrail(secret_key="test-key-for-integrity-check")
    trail.log("test_actor", "worker", "TEST_EVENT", {"data": "value1"})
    trail.log("test_actor", "worker", "TEST_EVENT", {"data": "value2"})
    assert trail.verify_integrity() is True
    assert len(trail.get_trail()) == 2


def test_audit_trail_tamper_detection():
    trail = AuditTrail(secret_key="test-key-for-tamper-detection")
    trail.log("test_actor", "worker", "TEST_EVENT", {"data": "original"})
    # Tamper with the log entry
    trail.logs[0]["payload_hash"] = "tampered_hash"
    assert trail.verify_integrity() is False


def test_batch_missing_file_returns_error():
    result = main(["batch", "-i", "/nonexistent/path/file.csv"])
    assert result == 1


def test_batch_output_to_invalid_directory():
    import os
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("task_id,target_identifier,primary_metric\nT1,KEY-01,10.0\n")
        tmp_path = f.name
    try:
        result = main(["batch", "-i", tmp_path, "-o", "/nonexistent_dir_12345/output.csv"])
        assert result == 1
    finally:
        os.unlink(tmp_path)
