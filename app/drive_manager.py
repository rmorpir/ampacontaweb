from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import pandas as pd
import io
import os

class DriveManager:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/drive.file']
        self.FOLDER_ID = "127a8D2rw4SbucDdu-msPBQLlKWvraZZf"
        self.credentials = self._get_credentials()
        self.use_local_storage = self.credentials is None
        
        if not self.use_local_storage:
            self.service = build('drive', 'v3', credentials=self.credentials)
        else:
            # Create a local data directory if it doesn't exist
            if not os.path.exists('data'):
                os.makedirs('data')

    def _get_credentials(self):
        # Check if Google credentials are set
        if not os.getenv("GOOGLE_PRIVATE_KEY"):
            print("WARNING: Google Drive credentials not found. Using local storage mode.")
            return None
            
        # In production, use environment variables for credentials
        try:
            return service_account.Credentials.from_service_account_info({
                "type": "service_account",
                "project_id": os.getenv("GOOGLE_PROJECT_ID"),
                "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
                "private_key": os.getenv("GOOGLE_PRIVATE_KEY"),
                "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_CERT_URL")
            }, scopes=self.SCOPES)
        except Exception as e:
            print(f"ERROR: Failed to initialize Google Drive credentials: {e}")
            return None

    def save_data(self, data, filename):
        df = pd.DataFrame(data)
        
        if self.use_local_storage:
            # Save to local file
            local_path = os.path.join('data', filename)
            df.to_csv(local_path, index=False)
            return
        
        # Use Google Drive
        buffer = io.BytesIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        
        file_metadata = {
            'name': filename,
            'parents': [self.FOLDER_ID]
        }
        media = MediaIoBaseUpload(buffer, mimetype='text/csv', resumable=True)
        self.service.files().create(body=file_metadata, media_body=media).execute()

    def load_data(self, filename):
        if self.use_local_storage:
            # Load from local file
            local_path = os.path.join('data', filename)
            if not os.path.exists(local_path):
                return pd.DataFrame()
            return pd.read_csv(local_path)
        
        # Use Google Drive
        try:
            results = self.service.files().list(
                q=f"name='{filename}' and '{self.FOLDER_ID}' in parents",
                fields="files(id, name)").execute()
            files = results.get('files', [])
            
            if not files:
                return pd.DataFrame()
                
            file_id = files[0]['id']
            request = self.service.files().get_media(fileId=file_id)
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            buffer.seek(0)
            return pd.read_csv(buffer)
        except Exception as e:
            print(f"Error loading data from Google Drive: {e}")
            return pd.DataFrame()
