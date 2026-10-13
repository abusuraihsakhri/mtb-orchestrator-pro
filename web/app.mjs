/* Static, local-only preview of the Python agents' demonstration thresholds. */
export const RULES = Object.freeze({ primary: 25, secondary: 12, maxMetric: 1e9 });
const phiPatterns = [
  /\bMRN[:#\s-]*\d{4,10}\b/i,
  /\b\d{3}-\d{2}-\d{4}\b/,
  /\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/,
  /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/,
  /\b(?:DOB|Date of Birth)[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b/i,
  /\b(?:Patient\s+Name|Patient)[:\s]+[A-Z][a-z]+\s+[A-Z][a-z]+\b/i,
];
function label(value, name, max) {
  if (typeof value !== "string" || !value.trim() || value.length > max) {
    throw new Error(name + " must contain 1–" + max + " characters.");
  }
  if (phiPatterns.some(pattern => pattern.test(value))) {
    throw new Error(name + " may contain a direct identifier. Use synthetic data only.");
  }
  return value.trim();
}
function metric(value, name) {
  if (value === "" || value == null || (typeof value !== "string" && typeof value !== "number")) {
    throw new Error(name + " is required.");
  }
  const n = Number(value);
  if (!Number.isFinite(n) || Math.abs(n) > RULES.maxMetric) {
    throw new Error(name + " must be finite and within ±1,000,000,000.");
  }
  return n;
}
export function evaluate(input) {
  const task_id = label(input.task_id, "Task ID", 128);
  const target_identifier = label(input.target_identifier, "Target ID", 128);
  const primary = metric(input.primary_metric, "Primary metric");
  const secondary = metric(input.secondary_metric ?? 0, "Secondary metric");
  const status = label(input.status_descriptor ?? "NOMINAL", "Status descriptor", 64);
  if (typeof input.is_critical_flag !== "boolean") {
    throw new Error("Critical flag must be a boolean.");
  }
  const alerts = [];
  if (primary > RULES.primary) {
    alerts.push({ origin_worker: "InvariantQCWorker", urgency: "ELEVATED_RISK",
      summary: "Primary Metric Threshold Exceeded",
      technical_details: "Primary value " + primary.toFixed(2) + " exceeds the demonstration threshold of 25.",
      actionable_remediation: "Review input and secondary parameters." });
  }
  if (input.is_critical_flag || secondary > RULES.secondary) {
    alerts.push({ origin_worker: "SafetyEscalationWorker",
      urgency: input.is_critical_flag ? "CRITICAL_STAT_PANIC" : "ELEVATED_RISK",
      summary: "Safety Escalation Triggered",
      technical_details: "Critical flag: " + input.is_critical_flag + "; secondary value: " + secondary.toFixed(2) + ".",
      actionable_remediation: "Review the flagged result through an appropriate human process." });
  }
  if (["DISCORDANT", "ANOMALY", "MUTANT", "VIOLATION", "FAIL", "REJECT"].some(term => status.toUpperCase().includes(term))) {
    alerts.push({ origin_worker: "ProtocolConformanceWorker", urgency: "ELEVATED_RISK",
      summary: "Status Descriptor Flagged",
      technical_details: "Status descriptor '" + status + "' matched a demonstration keyword.",
      actionable_remediation: "Verify the descriptor against the applicable local protocol." });
  }
  const critical_alerts_count = alerts.filter(a => a.urgency === "CRITICAL_STAT_PANIC").length;
  const overall_urgency = critical_alerts_count ? "CRITICAL_STAT_PANIC" : alerts.length ? "ELEVATED_RISK" : "ROUTINE";
  return {
    task_id, target_identifier, overall_urgency,
    integrity_status: critical_alerts_count ? "RECALIBRATION_REQUIRED" : alerts.length ? "DISCORDANT_ANOMALY" : "VALIDATED_OPTIMAL",
    total_alerts: alerts.length, critical_alerts_count, alerts,
    audit_hash: null, audit_status: "UNSIGNED_BROWSER_PREVIEW",
    disclaimer: "Demonstration rules only. Not a clinical assessment or a cryptographically signed audit."
  };
}
export function parseCsv(text) {
  if (typeof text !== "string") throw new Error("CSV input must be text.");
  const rows = []; let row = [], value = "", quoted = false, closed = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { value += '"'; i++; }
      else if (c === '"') { quoted = false; closed = true; }
      else value += c;
    } else if (c === '"' && !value && !closed) {
      quoted = true;
    } else if (c === ',' || c === '\n' || c === '\r') {
      row.push(value); value = ""; closed = false;
      if (c === '\r' && text[i + 1] === '\n') i++;
      if (c !== ',') { rows.push(row); row = []; }
    } else if (closed) {
      throw new Error("Invalid characters after a closing CSV quote.");
    } else {
      if (c === '"') throw new Error("Unexpected CSV quote.");
      value += c;
    }
  }
  if (quoted) throw new Error("Unclosed CSV quote.");
  if (value || row.length || closed) { row.push(value); rows.push(row); }
  if (!rows.length) throw new Error("CSV is empty.");
  rows[0][0] = rows[0][0].replace(/^\uFEFF/, "");
  const headers = rows.shift();
  if (new Set(headers).size !== headers.length || headers.some(h => !h)) {
    throw new Error("CSV headers must be unique and non-empty.");
  }
  const data = rows.filter(r => r.some(x => x.trim())).map((r, i) => {
    if (r.length !== headers.length) throw new Error("CSV row " + (i + 2) + " has the wrong number of columns.");
    return Object.fromEntries(headers.map((h, j) => [h, r[j]]));
  });
  return { headers, data };
}
export function csvCell(value) {
  let s = String(value ?? "");
  if (/^[\s\uFEFF]*[=+\-@]/.test(s)) s = "'" + s;
  return '"' + s.replace(/"/g, '""') + '"';
}
export function toCsv(headers, rows) {
  return [headers, ...rows.map(row => headers.map(h => row[h] ?? ""))]
    .map(row => row.map(csvCell).join(",")).join("\r\n") + "\r\n";
}
function download(name, mime, contents) {
  const url = URL.createObjectURL(new Blob([contents], { type: mime }));
  const a = document.createElement("a");
  a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
if (typeof document !== "undefined") {
  const $ = id => document.getElementById(id);
  let processed = 0, rejected = 0, result = null, batchExport = null;
  const show = (value, error = false) => {
    $("output").textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
    $("output").dataset.error = String(error);
  };
  $("audit-form").addEventListener("submit", event => {
    event.preventDefault();
    try {
      result = evaluate({
        task_id: $("task_id").value, target_identifier: $("target_identifier").value,
        primary_metric: $("primary_metric").value, secondary_metric: $("secondary_metric").value,
        status_descriptor: $("status_descriptor").value, is_critical_flag: $("is_critical_flag").checked
      });
      processed++; $("processed").textContent = String(processed);
      $("status").textContent = result.overall_urgency;
      $("json-export").disabled = false;
      show(result);
    } catch (error) {
      result = null; $("json-export").disabled = true;
      rejected++; $("rejected").textContent = String(rejected);
      show("Validation error: " + error.message, true);
    }
  });
  $("json-export").addEventListener("click", () => {
    if (result) download("mtb-local-dossier.json", "application/json", JSON.stringify(result, null, 2));
  });
  $("csv-file").addEventListener("change", async event => {
    batchExport = null; $("csv-export").disabled = true;
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      if (file.size > 2_000_000) throw new Error("CSV limit is 2 MB.");
      const { headers, data } = parseCsv(await file.text());
      if (data.length > 5000) throw new Error("CSV limit is 5,000 rows.");
      if (!["task_id", "target_identifier", "primary_metric"].every(h => headers.includes(h))) {
        throw new Error("CSV requires task_id, target_identifier and primary_metric columns.");
      }
      const rows = []; const failures = [];
      for (let i = 0; i < data.length; i++) {
        const row = data[i];
        try {
          const dossier = evaluate({
            ...row, secondary_metric: row.secondary_metric || 0,
            status_descriptor: row.status_descriptor || "NOMINAL",
            is_critical_flag: ["true", "1", "yes"].includes(String(row.is_critical_flag || "").toLowerCase())
          });
          rows.push({ ...row, overall_urgency: dossier.overall_urgency,
            integrity_status: dossier.integrity_status, total_alerts: dossier.total_alerts });
        } catch (error) { failures.push("Row " + (i + 2) + ": " + error.message); }
      }
      const columns = [...headers, "overall_urgency", "integrity_status", "total_alerts"];
      batchExport = toCsv(columns, rows);
      $("csv-export").disabled = false;
      processed += rows.length; rejected += failures.length;
      $("processed").textContent = String(processed); $("rejected").textContent = String(rejected);
      show({ accepted: rows.length, rejected: failures.length,
        errors: failures.slice(0, 20),
        note: "CSV generated locally; it contains unsigned demonstration results." });
    } catch (error) { show("CSV error: " + error.message, true); }
  });
  $("csv-export").addEventListener("click", () => {
    if (batchExport !== null) download("mtb-local-results.csv", "text/csv;charset=utf-8", batchExport);
  });
}
