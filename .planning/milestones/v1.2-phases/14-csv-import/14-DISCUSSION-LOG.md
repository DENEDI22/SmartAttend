# Phase 14: CSV Import - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-08
**Phase:** 14-csv-import
**Areas discussed:** CSV format & templates, Validation & error display, Upload flow & UI placement, Edge cases & conflicts

---

## CSV Format & Templates

| Option | Description | Selected |
|--------|-------------|----------|
| Semicolons | Matches existing CSV export. Excel German locale default. | |
| Commas | Standard CSV. German Excel may need config. | ✓ |
| You decide | Claude picks based on patterns. | |

**User's choice:** Commas
**Notes:** Standard comma delimiter chosen despite existing semicolon export pattern.

| Option | Description | Selected |
|--------|-------------|----------|
| Column in CSV | Admin puts plaintext password per row. Server hashes on import. | ✓ |
| Auto-generate | Server generates random passwords, shows in confirmation. | |
| You decide | Claude picks simpler approach. | |

**User's choice:** Column in CSV

| Option | Description | Selected |
|--------|-------------|----------|
| By name/email | Teacher by email, device by device_id string. Human-readable. | ✓ |
| By database ID | Precise but requires looking up IDs. | |
| You decide | Claude picks user-friendly approach. | |

**User's choice:** By name/email

---

## Validation & Error Display

| Option | Description | Selected |
|--------|-------------|----------|
| Table with row highlighting | All rows in table, invalid highlighted red with error message. | ✓ |
| Errors-only summary | Only error rows shown. Valid rows counted. | |
| Both | Full table plus error summary above. | |

**User's choice:** Table with row highlighting

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, skip invalid | Import valid rows, skip invalid. | |
| All or nothing | Any errors = nothing imported. Must fix all first. | ✓ |
| You decide | Claude picks based on requirements. | |

**User's choice:** All or nothing
**Notes:** Overrides CSV-03 requirement ("only valid rows committed") — user wants stricter behavior where all rows must be valid before any import.

---

## Upload Flow & UI Placement

| Option | Description | Selected |
|--------|-------------|----------|
| New 'Import' nav page | Separate /admin/import page. New nav link. | |
| Sections on existing pages | User import on /admin/users, schedule import on /admin/devices. | ✓ |
| You decide | Claude picks based on complexity. | |

**User's choice:** Sections on existing pages

| Option | Description | Selected |
|--------|-------------|----------|
| Two-step: upload then preview | Step 1: upload form. Step 2: validation table. Confirm or back. | ✓ |
| Three-step wizard | Choose type, upload, preview. More guided. | |
| You decide | Claude picks simpler approach. | |

**User's choice:** Two-step

---

## Edge Cases & Conflicts

| Option | Description | Selected |
|--------|-------------|----------|
| Mark as error | Duplicate email flagged invalid. No overwriting. | |
| Update existing user | Upsert: update fields if email exists. | ✓ |
| Skip silently | Ignore duplicates without error. | |

**User's choice:** Update existing user

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, flag overlaps as errors | Same validation as manual form. | ✓ |
| No overlap checking | Trust the admin. | |

**User's choice:** Flag overlaps as errors

| Option | Description | Selected |
|--------|-------------|----------|
| You decide | Claude picks reasonable limit. | ✓ |
| No limit | Accept any size. | |

**User's choice:** You decide (Claude's discretion)

---

## Claude's Discretion

- Max CSV file size limit
- CSV encoding handling (UTF-8 BOM detection)
- Template download details (example row content)

## Deferred Ideas

None.
