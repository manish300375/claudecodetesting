"""Upload a file to Google Drive (folder from DRIVE_FOLDER_ID in .env) and print its link.

Usage: python tools/upload_to_drive.py <file>
Needs credentials.json (OAuth client); token.json is created on first run.
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = Path(__file__).resolve().parent.parent
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def get_creds() -> Credentials:
    token = ROOT / "token.json"
    creds = Credentials.from_authorized_user_file(token, SCOPES) if token.exists() else None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        creds = InstalledAppFlow.from_client_secrets_file(ROOT / "credentials.json", SCOPES).run_local_server(port=0)
    token.write_text(creds.to_json())
    return creds


def upload(path: Path) -> str:
    load_dotenv(ROOT / ".env")
    meta = {"name": path.name}
    if os.getenv("DRIVE_FOLDER_ID"):
        meta["parents"] = [os.environ["DRIVE_FOLDER_ID"]]
    svc = build("drive", "v3", credentials=get_creds())
    f = svc.files().create(body=meta, media_body=MediaFileUpload(str(path)), fields="webViewLink").execute()
    return f["webViewLink"]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    print(upload(Path(sys.argv[1])))
