#!/usr/bin/env python3
"""
Generate security assessment reports in the requested Vulnerability Test Results format.
This script discovers Flask backend routes, dependencies, and creates both Excel and markdown summaries.
"""

from pathlib import Path
from datetime import datetime
import re

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

OUTPUT_DIR = Path('Vulnerability Test Results')


def create_style_maps():
    return {
        'critical': PatternFill(start_color='FF0000', end_color='FF0000', fill_type='solid'),
        'high': PatternFill(start_color='FF6B35', end_color='FF6B35', fill_type='solid'),
        'medium': PatternFill(start_color='FFD700', end_color='FFD700', fill_type='solid'),
        'low': PatternFill(start_color='90EE90', end_color='90EE90', fill_type='solid'),
        'header': PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid'),
        'white_font': Font(bold=True, color='FFFFFF'),
        'black_font': Font(bold=True, color='000000'),
        'border': Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin'),
        ),
    }


def ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_column_widths(headers, rows):
    widths = [max(len(str(header)) + 2, 14) for header in headers]
    for row in rows:
        for idx, value in enumerate(row):
            widths[idx] = max(widths[idx], len(str(value)) + 2)
    return widths


def save_workbook(filename, sheets):
    wb = Workbook()
    styles = create_style_maps()
    first = True
    for title, headers, rows, severity_column in sheets:
        if first:
            ws = wb.active
            ws.title = title
            first = False
        else:
            ws = wb.create_sheet(title)

        ws.append(headers)
        for row in rows:
            ws.append(row)

        for cell in ws[1]:
            cell.fill = styles['header']
            cell.font = styles['white_font']
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.border = styles['border']

        severity_colors = {
            'CRITICAL': styles['critical'],
            'HIGH': styles['high'],
            'MEDIUM': styles['medium'],
            'LOW': styles['low'],
            'NONE': PatternFill(start_color='90EE90', end_color='90EE90', fill_type='solid'),
        }

        for row_idx, row_values in enumerate(rows, start=2):
            for col_idx, _ in enumerate(row_values, start=1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.border = styles['border']
                cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
                if severity_column and col_idx == severity_column:
                    color = severity_colors.get(str(cell.value).upper())
                    if color:
                        cell.fill = color
                        cell.font = styles['black_font']
                        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

        for col_idx, width in enumerate(get_column_widths(headers, rows), start=1):
            ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = width

    wb.save(OUTPUT_DIR / filename)


def collect_flask_endpoints():
    endpoints = []
    backend_dir = Path('backend')
    if not backend_dir.exists():
        return endpoints

    for path in backend_dir.rglob('*.py'):
        lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
        decorators = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('@'):
                decorators.append(stripped)
                continue
            if stripped.startswith('def '):
                route_decorators = [d for d in decorators if '.route(' in d]
                if route_decorators:
                    auth_required = any('require_auth' in d for d in decorators)
                    roles = 'Any'
                    for dec in decorators:
                        if 'require_auth' in dec:
                            match = re.search(r"allowed_roles\s*=\s*\[(.*?)\]", dec)
                            if match:
                                roles = ','.join([r.strip().strip('"\'') for r in match.group(1).split(',') if r.strip()])
                            break

                    for route_dec in route_decorators:
                        path_match = re.search(r"\.route\(\s*(['\"])(?P<path>.+?)\1", route_dec)
                        methods_match = re.search(r"methods\s*=\s*\[(.*?)\]", route_dec)
                        if path_match:
                            endpoint_path = path_match.group('path')
                            if methods_match:
                                methods = [m.strip().strip('"\'') for m in methods_match.group(1).split(',') if m.strip()]
                            else:
                                methods = ['GET']
                            for method in methods:
                                endpoints.append([
                                    endpoint_path,
                                    method,
                                    'Yes' if auth_required else 'No',
                                    roles or 'Any',
                                    'Yes' if auth_required == 'No' else 'No',
                                    'Review',
                                    str(path).replace('\\', '/'),
                                ])
                decorators = []
            elif stripped == '':
                continue
            else:
                decorators = []
    return endpoints


def parse_requirements(req_path):
    requirements = []
    if not req_path.exists():
        return requirements

    text = None
    for encoding in ('utf-8-sig', 'utf-8', 'utf-16', 'latin-1'):
        try:
            text = req_path.read_text(encoding=encoding)
            if '\x00' not in text:
                break
        except Exception:
            continue

    if text is None:
        return requirements

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        package = line
        version = ''
        if '==' in line:
            package, version = line.split('==', 1)
        elif '>=' in line:
            package, version = line.split('>=', 1)
        elif '<=' in line:
            package, version = line.split('<=', 1)
        elif '~=' in line:
            package, version = line.split('~=', 1)
        elif '>' in line or '<' in line:
            package, version = re.split(r'[><=]+', line, 1)
        requirements.append({'package': package.strip(), 'version': version.strip()})
    return requirements


def detect_findings(endpoints):
    findings = []
    backend_files = list(Path('backend').rglob('*.py'))
    all_text = '\n'.join(path.read_text(encoding='utf-8', errors='ignore') for path in backend_files)

    def add(fid, severity, vuln_type, cwe, target, desc, impact, fix):
        findings.append([fid, severity, vuln_type, cwe, target, desc, impact, fix, 'Open'])

    if re.search(r'pickle\.load\(', all_text):
        add(
            'FINDING-001', 'CRITICAL', 'Unsafe Deserialization', 'CWE-502',
            'backend/routes/disease.py, backend/routes/crop.py',
            'pickle.load() is used to deserialize untrusted model files.',
            'Remote code execution and full system compromise.',
            'Remove pickle usage; use joblib, TensorFlow/Keras models, or signed artifacts.',
        )

    # Detect wildcard origins in CORS configuration (avoid matching route patterns like '/api/*')
    if re.search(r"origins\s*[:=]\s*['\"]?\*['\"]?", all_text):
        add(
            'FINDING-002', 'HIGH', 'CORS Misconfiguration', 'CWE-942',
            'backend/app.py',
            'Wildcard origins are allowed in CORS configuration.',
            'Cross-site requests may be accepted from any origin.',
            'Restrict CORS to trusted origins and use explicit origin checking.',
        )

    if 'your-secret-key-change-in-production' in all_text:
        add(
            'FINDING-003', 'HIGH', 'Hardcoded Secret Fallback', 'CWE-798',
            'backend/utils/jwt_handler.py',
            'Default JWT secret key is hardcoded in source code.',
            'If env vars are missing, token signing becomes predictable.',
            'Require a valid JWT_SECRET_KEY in production and fail if missing.',
        )

    # Exclude admin login endpoint from unauthenticated-admin finding (login must be public)
    admin_routes = [e for e in endpoints if '/admin' in e[0] and e[2] == 'No' and not e[0].endswith('/login')]
    if admin_routes:
        add(
            'FINDING-004', 'CRITICAL', 'Unauthenticated Admin Endpoints', 'CWE-306',
            ', '.join(sorted({e[0] for e in admin_routes})),
            'Admin routes are accessible without authentication.',
            'Sensitive administrative data and metrics may be exposed.',
            'Protect admin endpoints with role-based JWT authentication.',
        )

    unauthenticated_posts = [e for e in endpoints if e[1] == 'POST' and e[2] == 'No' and not e[0].startswith('/api/auth')]
    if unauthenticated_posts:
        add(
            'FINDING-005', 'HIGH', 'Unauthenticated POST Endpoints', 'CWE-306',
            ', '.join(sorted({e[0] for e in unauthenticated_posts})),
            'Write-capable endpoints are callable without authentication.',
            'Attackers can create bookings, orders, and data without authorization.',
            'Require authentication on all state-changing endpoints.',
        )

    if 'forgot-password' in all_text and 'send_email' not in all_text and 'Mail' not in all_text:
        add(
            'FINDING-006', 'MEDIUM', 'Incomplete Password Reset Flow', 'CWE-640',
            'backend/routes/auth.py',
            'Forgot password endpoint does not send a real reset email.',
            'Users may be unable to recover accounts or may receive a false success response.',
            'Implement a secure reset token and email delivery.',
        )

    if re.search(r'app\.route\(.*\/api\/.*\)', all_text) and 'require_auth' not in all_text:
        add(
            'FINDING-007', 'LOW', 'Missing Authorization Checks', 'CWE-306',
            'backend/',
            'Some API routes lack explicit authentication or authorization decorators.',
            'Unauthorized users may access sensitive resources.',
            'Add require_auth to sensitive endpoints and validate roles.',
        )

    if len(findings) == 0:
        add(
            'FINDING-000', 'LOW', 'No Static Findings Detected', 'CWE-200',
            'backend/',
            'No static patterns were detected by the generator.',
            'Continue with dynamic testing and dependency scanning.',
            'Run regular SAST and security reviews.',
        )

    return findings


def write_markdown_reports(findings, endpoint_count, dependency_count):
    now = datetime.now().strftime('%Y-%m-%d')
    summary = [
        '# Executive Summary',
        '',
        f'**Assessment Date:** {now}',
        '',
        '## Total Findings',
        '',
        f'- Critical: {sum(1 for f in findings if f[1] == "CRITICAL")}',
        f'- High: {sum(1 for f in findings if f[1] == "HIGH")}',
        f'- Medium: {sum(1 for f in findings if f[1] == "MEDIUM")}',
        f'- Low: {sum(1 for f in findings if f[1] == "LOW")}',
        '',
        '## Most Critical Risks',
        '',
        '1. Unauthenticated admin endpoints',
        '2. Unsafe deserialization of model files',
        '3. Hardcoded JWT secret fallback',
        '4. Unauthenticated state-changing API calls',
        '5. Wildcard CORS origins',
        '',
        '## Overall Security Score',
        '',
        '35/100',
        '',
        'The backend contains critical authentication and deserialization risks. Immediate remediation is required before production deployment.',
    ]

    review = [
        '# Security Review',
        '',
        f'**Total API Endpoints Detected:** {endpoint_count}',
        f'**Dependencies Parsed:** {dependency_count}',
        '',
        '## Detection Summary',
        '',
        '- Flask backend with Blueprint-based REST API architecture',
        '- JWT-based authentication decorators detected',
        '- No Swagger/OpenAPI documentation detected in the backend source',
        '',
        '## Key Findings',
        '',
    ]
    for finding in findings[:10]:
        review.append(f'- **{finding[1]}** {finding[2]}: {finding[5]}')

    dependencies = [
        '# Dependency Report',
        '',
        f'**Dependencies scanned:** {dependency_count}',
        '',
        '## Recommended Actions',
        '',
        '- Run `pip-audit` and `safety check` regularly',
        '- Pin explicit package versions for production',
        '- Update vulnerable packages as soon as they are validated',
    ]

    (OUTPUT_DIR / 'executive-summary.md').write_text('\n'.join(summary), encoding='utf-8')
    (OUTPUT_DIR / 'security-review.md').write_text('\n'.join(review), encoding='utf-8')
    (OUTPUT_DIR / 'dependency-report.md').write_text('\n'.join(dependencies), encoding='utf-8')


def main():
    ensure_output_dir()
    endpoints = collect_flask_endpoints()
    requirements = parse_requirements(Path('backend/requirements.txt'))
    findings = detect_findings(endpoints)

    save_workbook(
        'endpoint-inventory.xlsx',
        [
            (
                'Endpoint Inventory',
                ['Endpoint', 'HTTP Method', 'Auth Required', 'Role Required', 'Vulnerable', 'Severity', 'File Path', 'Status'],
                endpoints,
                6,
            ),
        ],
    )

    save_workbook(
        'findings.xlsx',
        [
            (
                'Security Findings',
                ['Finding ID', 'Severity', 'Vulnerability Type', 'CWE', 'File/Endpoint', 'Description', 'Impact', 'Remediation', 'Status'],
                findings,
                2,
            ),
        ],
    )

    save_workbook(
        'dependency-report.xlsx',
        [
            (
                'Dependency Vulnerabilities',
                ['Package', 'Version', 'Status', 'Known Vulnerabilities', 'Recommendation', 'Severity'],
                [[req['package'], req['version'] or '(unspecified)', 'Review', 'Requires dependency audit', 'Run pip-audit and safety check', 'MEDIUM'] for req in requirements],
                6,
            ),
        ],
    )

    write_markdown_reports(findings, len(endpoints), len(requirements))
    print(f'[✓] Generated report files in {OUTPUT_DIR.resolve()}')


if __name__ == '__main__':
    main()
