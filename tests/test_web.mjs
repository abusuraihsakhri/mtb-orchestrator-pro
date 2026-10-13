import test from "node:test";
import assert from "node:assert/strict";
import { evaluate, parseCsv, csvCell, toCsv } from "../web/app.mjs";

const base = { task_id: "TASK-01", target_identifier: "SPECIMEN-01",
  primary_metric: 12, secondary_metric: 4, status_descriptor: "NOMINAL", is_critical_flag: false };

test("routine yields zero alerts", () => {
  const r = evaluate(base);
  assert.equal(r.total_alerts, 0);
  assert.equal(r.overall_urgency, "ROUTINE");
  assert.equal(r.integrity_status, "VALIDATED_OPTIMAL");
  assert.equal(r.audit_hash, null);
});
test("strict boundaries and escalation match worker logic", () => {
  assert.equal(evaluate({ ...base, primary_metric: 25, secondary_metric: 12 }).total_alerts, 0);
  const r = evaluate({ ...base, primary_metric: 25.1, secondary_metric: 12.1, status_descriptor: "DISCORDANT", is_critical_flag: true });
  assert.equal(r.total_alerts, 3);
  assert.equal(r.critical_alerts_count, 1);
  assert.equal(r.overall_urgency, "CRITICAL_STAT_PANIC");
});
test("secondary breach alone is elevated, not critical", () => {
  const r = evaluate({ ...base, secondary_metric: 12.1 });
  assert.equal(r.overall_urgency, "ELEVATED_RISK");
  assert.equal(r.critical_alerts_count, 0);
});
test("malformed numeric and identifier input is rejected", () => {
  for (const value of ["", "Infinity", "NaN", 1e12]) {
    assert.throws(() => evaluate({ ...base, primary_metric: value }));
  }
  assert.throws(() => evaluate({ ...base, task_id: "MRN-994827" }), /direct identifier/);
  assert.throws(() => evaluate({ ...base, target_identifier: "test@example.com" }), /direct identifier/);
  assert.throws(() => evaluate({ ...base, is_critical_flag: "false" }), /boolean/);
});
test("CSV parser handles CRLF, BOM and quoted fields", () => {
  const result = parseCsv('\uFEFFtask_id,target_identifier,primary_metric,status_descriptor\r\n"CASE,1",SPEC-1,10,"NOMINAL"\r\n');
  assert.equal(result.data[0].task_id, "CASE,1");
  assert.equal(result.data.length, 1);
  assert.deepEqual(result.headers, ["task_id", "target_identifier", "primary_metric", "status_descriptor"]);
});
test("CSV parser rejects invalid row sizes and unterminated quotes", () => {
  assert.throws(() => parseCsv("a,b\n1\n"), /number of columns/);
  assert.throws(() => parseCsv('a,b\n"x,2'), /Unclosed/);
  assert.throws(() => parseCsv("a,a\n1,2"), /unique/);
});
test("CSV output quotes cells and protects formula injection", () => {
  assert.equal(csvCell('=HYPERLINK("https://example.com")'), "\"'=HYPERLINK(\"\"https://example.com\"\")\"");
  assert.match(toCsv(["task_id", "status"], [{ task_id: "A,1", status: "GOOD" }]), /"A,1","GOOD"/);
});
