# MessMind — corrected login starter

## Run locally (Windows)
1. Install Python 3.10 or newer.
2. Open Command Prompt in this folder.
3. Run `py -m venv .venv`
4. Run `.venv\\Scripts\\activate`
5. Run `pip install -r requirements.txt`
6. Run `python app.py`
7. Open `http://127.0.0.1:5000`

## Initial test accounts
All four accounts are created automatically on the first run with the temporary password `ChangeMe@123`:

| Person | MessMind ID | Role |
|---|---|---|
| Ganesh Reddy | LPU001 | Admin |
| Rohith | LPU002 | Member |
| HarinathReddy | LPU003 | Member |
| Tharun | LPU004 | Member |

Change the temporary password before putting this app on the public internet. Set `MESSMIND_INITIAL_PASSWORD` before the first run to use a different initial password. Existing accounts are not overwritten when the app restarts. If you need to reset this local test database, stop the server and delete `messmind.db`; this deletes its records and accounts, then restart.

## Security notes
- Login is checked by Flask; passwords are stored as password hashes.
- The browser no longer stores a fake login object in localStorage.
- Members can read only their own records. Admin can read all records.
- This starter uses SQLite for local testing. Do not deploy publicly until you configure a strong `MESSMIND_SECRET_KEY`, persistent production database, HTTPS, backups, and proper password-change flow. Face recognition/camera capture is not connected yet; the camera tile remains a demo placeholder.
