# demo2 — Google Reviews Analyzer + Brand-Voice Reply Drafts

Local web app to:
- Analyze what’s going well vs not going well in your Google reviews
- Flag reputation risks in negative reviews
- Draft consistent, brand-voice responses for bad/neutral/good reviews

## Quick start (Windows / PowerShell)

```powershell
cd .\demo2
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r .\requirements.txt
streamlit run .\app.py
```

Then open the URL Streamlit prints (usually `http://localhost:8501`).

## Data you can use

- Upload a CSV export containing at least a **review text** column.
- Optional columns: **rating**, **date**, **reviewer name**.

If you don’t have a CSV, you can paste reviews directly in the app.

## Notes / safety

This app generates **drafts**. Always skim before posting.
It avoids certain risky phrases (admitting fault, legal statements, etc.) and prefers:
- Thanking the reviewer
- Showing empathy
- Offering a concrete next step
- Taking sensitive issues offline for negative reviews

## Architecture (separated logic)

- `src/`: business logic (UI-agnostic)
  - `src/application.py`: app/service layer (what UIs should call)
  - `src/ingest.py`: load/clean reviews
  - `src/analyze.py`: insights + risk flags
  - `src/respond.py`: response drafts + safeguards
- `ui/`: view layer (Streamlit right now)
  - `ui/streamlit_app.py`: Streamlit UI that calls `src/application.py`
- `design/`: reserved for Pencil `.pen` files and design notes

