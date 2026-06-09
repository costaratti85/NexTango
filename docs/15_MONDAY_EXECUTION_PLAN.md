# Monday Execution Plan

1. Create or replace the GitHub repo with this seed.
2. Run `python -m pytest` from repo root.
3. Run the local demo script.
4. Ask Codex to convert the neutral modules into a real Frappe app.
5. Keep ERPNext core untouched; install SistemaIndustrial as custom app.

Validation target: panel preset creates an ERPNext-style quotation payload and a pending cut part, then the pending part compiles into a DXF batch by thickness.
