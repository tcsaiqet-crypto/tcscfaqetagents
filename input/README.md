# Input Test Suite - Defective Program Files

This directory contains 5 sample program files with distinct software defects engineered for automated Quality Engineering & Testing (QET) agent analysis.

## Program Defect Inventory

| File Name | Defect Category | Primary Defect Description |
| :--- | :--- | :--- |
| `auth_service.py` | Security & Secrets | Hardcoded secret token (`SECRET_KEY`) & raw SQL string interpolation vulnerable to SQL Injection. |
| `financial_calculator.py` | Logic & Boundary | Off-by-one loop indexing (`range(0, len(list) + 1)`), zero-division crash on zero income, inverted eligibility condition. |
| `data_processor.py` | Resource & Exception | Unclosed file handles (`open()` without `with`), swallowed exceptions (`except Exception: pass`), silent success masking. |
| `user_profile.py` | Null Pointer & Types | Direct nested dictionary lookup (`dict['a']['b']['c']`) causing `KeyError`/`TypeError`, string-to-int comparison mismatch. |
| `inventory_manager.py` | State Mutation & Invariants | Global mutable dictionary modification, missing non-negative stock bounds, un-synchronized concurrent mutation. |

## Purpose
These programs serve as reference inputs to test:
- Automated Static Analysis & Vulnerability Detection
- Test Case Generation (Positive & Negative paths)
- Automated Defect Reporting & Summary Generation
