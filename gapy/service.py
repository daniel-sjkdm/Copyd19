import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


SCOPES = [
    "https://www.googleapis.com/auth/drive"
]


def get_service():
    print(os.getcwd())
    creds = None
    if os.path.exists("./gapy/token.pickle"):
        with open("./gapy/token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("./gapy/credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("./gapy/token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("drive", "v3", credentials=creds)
    return service