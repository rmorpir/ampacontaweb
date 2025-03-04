from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import pandas as pd
import io
import os

class DriveManager:
    def __init__(self):
        self.shared_folder_id = "TU_ID_DE_CARPETA"  # ID de la carpeta compartida
        self.local_data_dir = "data"

        try:
            self.credentials = self._get_credentials()
            self.service = build('drive', 'v3', credentials=self.credentials)
            print("Google Drive connection established")
        except Exception as e:
            print(f"WARNING: Google Drive credentials not found. Using local storage mode. Error: {str(e)}")
            self.service = None

        # Ensure local data directory exists
        if not os.path.exists(self.local_data_dir):
            os.makedirs(self.local_data_dir)

    def _get_credentials(self):
        # Check for environment variables first
        if all(os.getenv(key) for key in [
            "GCP_PROJECT_ID", "GCP_PRIVATE_KEY_ID", "GCP_PRIVATE_KEY", 
            "GCP_CLIENT_EMAIL", "GCP_CLIENT_ID", "GCP_CLIENT_X509_CERT_URL"
        ]):
            service_account_info = {
                "type": "service_account",
                "project_id": os.getenv("GCP_PROJECT_ID"),
                "private_key_id": os.getenv("GCP_PRIVATE_KEY_ID"),
                "private_key": os.getenv("GCP_PRIVATE_KEY").replace('\\n', '\n'),
                "client_email": os.getenv("GCP_CLIENT_EMAIL"),
                "client_id": os.getenv("GCP_CLIENT_ID"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.getenv("GCP_CLIENT_X509_CERT_URL")
            }

            return service_account.Credentials.from_service_account_info(service_account_info)
        else:
            raise ValueError("Missing required service account values in environment variables")

    def _find_file_in_drive(self, file_name):
        """Find a file in the shared folder by name"""
        if not self.service:
            return None

        try:
            results = self.service.files().list(
                q=f"name='{file_name}' and '{self.shared_folder_id}' in parents and trashed=false",
                fields="files(id, name)"
            ).execute()

            files = results.get('files', [])
            if files:
                return files[0]
            return None
        except Exception as e:
            print(f"Error finding file in Drive: {str(e)}")
            return None

    def load_data(self, file_name):
        """Load data from Google Drive or local storage"""
        local_path = os.path.join(self.local_data_dir, file_name)

        try:
            if self.service:
                # Try to load from Google Drive
                file_metadata = self._find_file_in_drive(file_name)

                if file_metadata:
                    file_id = file_metadata['id']
                    request = self.service.files().get_media(fileId=file_id)

                    file_content = io.BytesIO()
                    downloader = MediaIoBaseDownload(file_content, request)
                    done = False

                    while not done:
                        status, done = downloader.next_chunk()

                    file_content.seek(0)
                    # Save a local copy for backup
                    with open(local_path, 'wb') as f:
                        f.write(file_content.getvalue())

                    return pd.read_csv(io.StringIO(file_content.getvalue().decode('utf-8')))
                else:
                    print(f"File {file_name} not found in Drive. Using local file if available.")
        except Exception as e:
            print(f"Error loading from Drive: {str(e)}. Using local storage.")

        # Fallback to local storage
        if os.path.exists(local_path):
            return pd.read_csv(local_path)
        else:
            return pd.DataFrame()

    def save_data(self, data, file_name):
        """Save data to Google Drive and local storage"""
        local_path = os.path.join(self.local_data_dir, file_name)

        # Convert to DataFrame if it's not already
        df = pd.DataFrame(data) if not isinstance(data, pd.DataFrame) else data

        # Always save locally as backup
        df.to_csv(local_path, index=False)

        if self.service:
            try:
                # Convert DataFrame to CSV content
                csv_content = df.to_csv(index=False).encode('utf-8')

                # Check if file already exists in Drive
                file_metadata = self._find_file_in_drive(file_name)

                media = MediaIoBaseUpload(
                    io.BytesIO(csv_content),
                    mimetype='text/csv',
                    resumable=True
                )

                if file_metadata:
                    # Update existing file
                    self.service.files().update(
                        fileId=file_metadata['id'],
                        media_body=media
                    ).execute()
                else:
                    # Create new file in the shared folder
                    file_metadata = {
                        'name': file_name,
                        'parents': [self.shared_folder_id]
                    }
                    self.service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id'
                    ).execute()

                print(f"Successfully saved {file_name} to Google Drive")
            except Exception as e:
                print(f"Error saving to Drive: {str(e)}. Data saved locally only.")