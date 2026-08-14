"""Helper script to create a sample CFA Digital Journey codebase ZIP archive."""

import zipfile
from pathlib import Path

sample_dir = Path("sample_cfa_app")
sample_dir.mkdir(exist_ok=True)

files = {
    "src/pages/Login.tsx": """import React from 'react';

export const Login = () => {
    return (
        <form data-testid="login-form">
            <h2>CFA Applicant Portal Login</h2>
            <input data-testid="username" type="text" placeholder="Username / Email" />
            <input data-testid="password" type="password" placeholder="Password" />
            <button data-testid="login-btn" type="submit">Log In</button>
            <div data-testid="error-alert" style={{display: 'none'}}>Invalid credentials</div>
        </form>
    );
};
""",
    "src/pages/ApplicationForm.tsx": """import React from 'react';

export const ApplicationForm = () => {
    return (
        <form data-testid="cfa-application-form">
            <h2>CFA Digital Application Form</h2>
            <input data-testid="applicant-name" type="text" placeholder="Full Legal Name" />
            <input data-testid="annual-income" type="number" placeholder="Annual Income ($)" />
            <select data-testid="employment-status">
                <option value="Employed">Employed Full-Time</option>
                <option value="Self-Employed">Self-Employed</option>
            </select>
            <button data-testid="next-step-btn">Proceed to Document Upload</button>
            <div data-testid="income-validation-error">Annual income must be greater than $0</div>
        </form>
    );
};
""",
    "src/pages/DocumentUpload.tsx": """import React from 'react';

export const DocumentUpload = () => {
    return (
        <div data-testid="doc-upload-container">
            <h3>Upload Supporting Documents</h3>
            <input data-testid="doc-upload-input" type="file" accept=".pdf,.png,.jpg" />
            <button data-testid="upload-submit-btn">Upload Proof of Income</button>
        </div>
    );
};
""",
    "docs/cfa_digital_journey_requirements.md": """# CFA Digital Journey Application Requirements

## Functional Overview
The CFA Digital Journey application provides digital loan and credit intake for retail applicants.

### Core User Flows
1. **Authentication**: Applicants authenticate using email and password.
2. **Personal & Financial Intake**: Applicants submit full legal name, annual gross income, and employment status.
3. **Document Verification**: Applicants upload supporting PDF documents (proof of income, ID).
4. **Review & Electronic Signature**: Applicants review application summary and submit electronic signature.

### Security Constraints
- Unsupported file formats (.exe, .sh, .bat) must be blocked at upload.
- Negative income entries must trigger field-level validation errors.
"""
}

for rel_path, content in files.items():
    file_path = sample_dir / rel_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

zip_output = Path("cfa_digital_journey_sample.zip")
with zipfile.ZipFile(zip_output, "w") as zf:
    for rel_path in files.keys():
        zf.write(sample_dir / rel_path, arcname=rel_path)

print(f"Sample ZIP archive created successfully at {zip_output.resolve()}")
