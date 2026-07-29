import json
import os
import re
from datetime import datetime
from pathlib import Path

try:
    from openpyxl import Workbook
except ImportError:
    raise RuntimeError("openpyxl is required. Install with: pip install openpyxl")

ROOT = Path(__file__).parent
BACKEND = ROOT / "backend"
OUTPUT_DIR = ROOT / "Vulnerability Test Results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SEVERITY_MAP = {
    "critical": "Critical",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
    "info": "Low"
}


def load_requirements():
    req_path = BACKEND / "requirements.txt"
    if not req_path.exists():
        return []
    lines = req_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    packages = [line.strip() for line in lines if line.strip() and not line.startswith("#")]
    return packages


def detect_backend():
    framework = "Unknown"
    language = "Unknown"
    db_tech = "Unknown"
    orm = "None"
    auth = "Unknown"
    middleware = []
    api_docs = "None"
    file_upload = False
    session_handling = "None"
    third_party = []

    if (BACKEND / "app.py").exists():
        framework = "Flask"
        language = "Python"

    reqs = load_requirements()
    for package in reqs:
        if "sqlalchemy" in package.lower():
            orm = "SQLAlchemy"
        if any(x in package.lower() for x in ["mysql", "postgres", "sqlite", "mongodb"]):
            db_tech = package.split("==")[0]
        if "flask-cors" in package.lower():
            middleware.append("Flask-CORS")
        if "werkzeug" in package.lower():
            middleware.append("Werkzeug")
        if "requests" in package.lower():
            third_party.append("requests")
        if "jwt" in package.lower() or "pyjwt" in package.lower():
            auth = "JWT"
        if "openpyxl" in package.lower():
            third_party.append("openpyxl")
        if "numpy" in package.lower() or "scikit-learn" in package.lower():
            third_party.append("ML/Analytics")

    if (BACKEND / "app.py").exists():
        backend_text = (BACKEND / "app.py").read_text(encoding="utf-8", errors="ignore")
        if "CORS(" in backend_text:
            middleware.append("CORS")
        if "UPLOAD_FOLDER" in backend_text or "upload" in backend_text.lower():
            file_upload = True
        if "session" in backend_text.lower():
            session_handling = "Flask session or custom session handling"

    return {
        "Framework": framework,
        "Language": language,
        "API Architecture": "REST API",
        "Authentication": auth,
        "Authorization": "Role-based / JWT claims",
        "Database": db_tech,
        "ORM": orm,
        "API Documentation": api_docs,
        "Middleware": ", ".join(sorted(set(middleware))) if middleware else "None",
        "File Uploads": "Yes" if file_upload else "No",
        "Session Handling": session_handling,
        "Third-Party Integrations": ", ".join(sorted(set(third_party))) if third_party else "None"
    }


def discover_routes():
    endpoints = []
    route_pattern = re.compile(r"@(?:app\.|[\w_]+\.)route\(['\"]([^'\"]+)['\"],\s*methods=\[([^\]]+)\]\)")
    blueprint_pattern = re.compile(r"(\w+)_bp\s*=\s*Blueprint\(['\"]([\w_]+)['\"],")
    auth_keywords = ["require_auth", "@require_auth", "jwt"]

    for route_file in (BACKEND / "routes").glob("*.py"):
        text = route_file.read_text(encoding="utf-8", errors="ignore")
        blueprint_name = route_file.stem
        for match in route_pattern.finditer(text):
            endpoint = match.group(1)
            methods = [m.strip().strip("'\"") for m in match.group(2).split(",")]
            auth_required = any(k in text[max(0, match.start() - 200): match.end() + 200] for k in auth_keywords)
            expected_roles = "Any authenticated user" if auth_required else "None/Unknown"
            endpoints.append({
                "Endpoint": endpoint,
                "HTTP Method": ", ".join(methods),
                "Authentication Required": "Yes" if auth_required else "No",
                "Expected Roles": expected_roles,
                "Controller/File Path": f"backend/routes/{route_file.name}"
            })

    return endpoints


def find_security_findings():
    findings = []
    backend_files = list((BACKEND / "routes").glob("*.py")) + [BACKEND / "app.py", BACKEND / "utils" / "jwt_handler.py"]

    cors_text = (BACKEND / "app.py").read_text(encoding="utf-8", errors="ignore") if (BACKEND / "app.py").exists() else ""
    # Detect wildcard CORS origins (e.g., origins: '*')
    try:
        if re.search(r"origins\s*[:=]\s*['\"]\*['\"]", cors_text, re.IGNORECASE):
            findings.append({
                "Severity": "High",
                "Type": "Configuration",
                "File Path": "backend/app.py",
                "Endpoint": "All /api/*",
                "Description": "Wildcard CORS is enabled, allowing any origin to access API endpoints.",
                "Impact": "Cross-origin requests can be initiated from untrusted websites, increasing attack surface.",
                "Recommendation": "Restrict CORS origins to trusted frontend domains only."
            })
    except re.error:
        # If regex fails for any reason, skip the CORS wildcard detection gracefully
        pass

    if (BACKEND / "utils" / "jwt_handler.py").exists():
        jwt_text = (BACKEND / "utils" / "jwt_handler.py").read_text(encoding="utf-8", errors="ignore")
        if "JWT_SECRET_KEY" not in os.environ:
            findings.append({
                "Severity": "High",
                "Type": "Cryptography",
                "File Path": "backend/utils/jwt_handler.py",
                "Endpoint": "Authentication endpoints",
                "Description": "JWT secret key is required but may not be configured in environment variables.",
                "Impact": "Weak or missing secret allows attackers to forge valid tokens.",
                "Recommendation": "Set a strong JWT_SECRET_KEY in environment and never commit it to source control."
            })

    for file_path in backend_files:
        if not file_path.exists():
            continue
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        if "pickle.load" in text or "pickle.loads" in text:
            findings.append({
                "Severity": "Critical",
                "Type": "Unsafe Deserialization",
                "File Path": str(file_path.relative_to(ROOT)),
                "Endpoint": "Model/load operations",
                "Description": "Usage of pickle deserialization is insecure and can execute arbitrary code.",
                "Impact": "Remote code execution if attacker controls or tampers with serialized input.",
                "Recommendation": "Replace pickle with a safe serialization library such as joblib, json, or protobuf."
            })
        if "request.get_json" in text and "validate" not in text.lower():
            findings.append({
                "Severity": "Medium",
                "Type": "Input Validation",
                "File Path": str(file_path.relative_to(ROOT)),
                "Endpoint": "API endpoints accepting JSON",
                "Description": "JSON input is consumed without explicit schema validation.",
                "Impact": "Malformed or malicious JSON may reach business logic and cause unexpected behavior.",
                "Recommendation": "Add request validation using marshmallow, pydantic, or manual schema checks."
            })

    app_text = cors_text
    if "UPLOAD_FOLDER" in app_text and "max_content_length" not in app_text:
        findings.append({
            "Severity": "Medium",
            "Type": "File Upload",
            "File Path": "backend/app.py",
            "Endpoint": "Upload endpoints",
            "Description": "Upload directory exists but upload size limits or content validation are not enforced.",
            "Impact": "Large or malicious uploads may exhaust storage or execute unsafe file handling.",
            "Recommendation": "Enforce max upload sizes and validate allowed file types before saving."
        })

    if "@app.route('/api/equipment', methods=['POST'])" in app_text or "@app.route('/api/products/order'" in app_text:
        findings.append({
            "Severity": "High",
            "Type": "Authorization",
            "File Path": "backend/app.py",
            "Endpoint": "/api/equipment, /api/products/order",
            "Description": "State-changing endpoints appear to lack authentication enforcement.",
            "Impact": "Unauthenticated users may create bookings or orders.",
            "Recommendation": "Protect POST endpoints with authentication and authorization checks."
        })

    return findings


def build_excel_reports(finding_rows, endpoint_rows, dependency_rows, summary_counts):
    findings_wb = Workbook()
    ws = findings_wb.active
    ws.title = "Security Findings"
    ws.append(["Severity", "Type", "File Path", "Endpoint", "Description", "Impact", "Recommendation"] )
    for row in finding_rows:
        ws.append([row["Severity"], row["Type"], row["File Path"], row["Endpoint"], row["Description"], row["Impact"], row["Recommendation"]])
    findings_wb.save(OUTPUT_DIR / "findings.xlsx")

    endpoint_wb = Workbook()
    ws = endpoint_wb.active
    ws.title = "Endpoint Inventory"
    ws.append(["Endpoint", "HTTP Method", "Authentication Required", "Expected Roles", "Controller/File Path"])
    for row in endpoint_rows:
        ws.append([row["Endpoint"], row["HTTP Method"], row["Authentication Required"], row["Expected Roles"], row["Controller/File Path"]])
    endpoint_wb.save(OUTPUT_DIR / "endpoint-inventory.xlsx")

    summary_wb = Workbook()
    ws = summary_wb.active
    ws.title = "Risk Summary"
    ws.append(["Severity", "Count"])
    for severity, count in summary_counts.items():
        ws.append([severity, count])
    summary_wb.save(OUTPUT_DIR / "risk-summary.xlsx")

    dependencies_wb = Workbook()
    ws = dependencies_wb.active
    ws.title = "Dependency Vulnerabilities"
    ws.append(["Requirement", "Notes"])
    for name in dependency_rows:
        ws.append([name, "Review package for CVEs and version pinning."])
    dependencies_wb.save(OUTPUT_DIR / "dependency-vulnerabilities.xlsx")


def write_markdown(reports, findings, endpoint_rows, dependency_rows, summary_counts):
    summary_lines = [
        "# Executive Summary",
        "",
        f"Total Findings: {len(findings)}",
        f"Critical: {summary_counts.get('Critical', 0)}",
        f"High: {summary_counts.get('High', 0)}",
        f"Medium: {summary_counts.get('Medium', 0)}",
        f"Low: {summary_counts.get('Low', 0)}",
        "",
        "## Most Critical Risks",
    ]

    critical_findings = [item for item in findings if item["Severity"] == "Critical"]
    if critical_findings:
        for idx, item in enumerate(critical_findings[:3], start=1):
            summary_lines.append(f"{idx}. {item['Type']}: {item['Description']}")
    else:
        summary_lines.append("No critical issues detected in static analysis.")

    summary_lines.extend([
        "",
        "## Overall Security Score",
        "",
        f"{max(0, 80 - len(findings) * 2)}/100",
        "",
        "The score is based on automated source analysis and should be validated with runtime testing."
    ])

    (OUTPUT_DIR / "executive-summary.md").write_text("\n".join(summary_lines), encoding="utf-8")

    dep_lines = [
        "# Dependency Report",
        "",
        "The following packages were found in backend requirements and should be audited for vulnerabilities:",
        "",
    ]
    dep_lines.extend([f"- {pkg}" for pkg in dependency_rows])
    dep_lines.append("")
    dep_lines.append("Run `python -m pip-audit --output dependency-audit.json` and review the JSON for critical vulnerabilities.")
    (OUTPUT_DIR / "dependency-report.md").write_text("\n".join(dep_lines), encoding="utf-8")

    review_lines = [
        "# Security Review",
        "",
        "## Backend Inventory",
    ]
    for key, value in reports.items():
        review_lines.append(f"- **{key}**: {value}")
    review_lines.extend([
        "",
        "## Findings",
    ])
    for item in findings:
        review_lines.extend([
            f"### {item['Severity']} - {item['Type']}",
            f"- File: {item['File Path']}",
            f"- Endpoint: {item['Endpoint']}",
            f"- Description: {item['Description']}",
            f"- Impact: {item['Impact']}",
            f"- Recommendation: {item['Recommendation']}",
            ""
        ])
    review_lines.append("## Endpoint Inventory Summary")
    review_lines.append(f"Total discovered endpoints: {len(endpoint_rows)}")
    review_lines.append("")
    review_lines.append("## Notes")
    review_lines.append("- This report is generated from static code scanning and should be combined with dynamic testing.")
    review_lines.append("- Any findings marked as Critical or High should be remediated before production deployment.")
    (OUTPUT_DIR / "security-review.md").write_text("\n".join(review_lines), encoding="utf-8")


def main():
    print("Running backend discovery and security review generator...")
    reports = detect_backend()
    endpoint_rows = discover_routes()
    findings = find_security_findings()
    summary_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for item in findings:
        summary_counts[item["Severity"]] = summary_counts.get(item["Severity"], 0) + 1

    dep_rows = load_requirements()
    build_excel_reports(findings, endpoint_rows, dep_rows, summary_counts)
    write_markdown(reports, findings, endpoint_rows, dep_rows, summary_counts)
    print(f"Reports generated under {OUTPUT_DIR}")

    security_inventory = OUTPUT_DIR / "endpoint-inventory.xlsx"
    findings_file = OUTPUT_DIR / "findings.xlsx"
    assert security_inventory.exists(), "Endpoint inventory workbook not generated"
    assert findings_file.exists(), "Findings workbook not generated"

    print("Security review generation complete.")


if __name__ == '__main__':
    main()
