# Pencil.dev notes (design workspace)

This folder is reserved for Pencil `.pen` design files.

## Recommended workflow in Cursor + Pencil (MCP)

- Keep **business logic** in `src/` (UI-agnostic)
- Keep **UI** in `ui/` (Streamlit today; Pencil-generated UI later)
- When Pencil generates UI code, it should call into:
  - `src/application.py` (application/service layer)
  - `src/types.py` (domain types)

That way you can redesign/rebuild the UI without rewriting ingestion/analysis/reply logic.

