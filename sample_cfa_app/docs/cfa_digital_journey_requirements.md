# CFA Digital Journey Application Requirements

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
