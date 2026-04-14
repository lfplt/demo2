# Deploy `demo2` to Streamlit Community Cloud

## 0) Prereqs (one-time)

You need **Git** installed.

- Install Git for Windows (recommended): download from `https://git-scm.com/download/win`

Optional (recommended): **GitHub CLI** (`gh`) to create/push repos from terminal:

- Install: `https://cli.github.com/`

## 1) Create a GitHub repo

### Option A — Using GitHub website (no `gh` required)

1. Create a new repo on GitHub (e.g. `demo2`).
2. Don’t add a README (we already have one).

### Option B — Using `gh` (fastest)

```powershell
gh auth login
```

## 2) Initialize git + push

From your workspace root:

```powershell
cd .\demo2

git init
git add .
git commit -m "Initial commit: demo2 streamlit reviews analyzer"

# If you created the repo on GitHub website:
git branch -M main
git remote add origin https://github.com/<YOUR_USER_OR_ORG>/<REPO_NAME>.git
git push -u origin main

# If you're using gh:
# gh repo create <REPO_NAME> --public --source . --remote origin --push
```

## 3) Deploy on Streamlit Community Cloud

1. Go to Streamlit Community Cloud and click **New app**
2. Select your GitHub repo
3. Set:
   - **Main file path**: `app.py`
   - **Branch**: `main`
4. Deploy

### Notes

- Python version is pinned via `runtime.txt` (`python-3.12`).
- Dependencies are in `requirements.txt`.
- Streamlit config lives in `.streamlit/config.toml`.

