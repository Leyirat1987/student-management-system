"""
Google Drive API service for UTIS PDF System
Handles PDF upload, download, and management
"""

import os
import io
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from googleapiclient.errors import HttpError

class GoogleDriveService:
    def __init__(self, credentials_file='google-credentials.json'):
        """Initialize Google Drive service"""
        self.credentials_file = credentials_file
        self.service = None
        self.folder_id = None
        self._authenticate()
        self._setup_folders()
    
    def _authenticate(self):
        """Authenticate with Google Drive API"""
        try:
            # Load credentials from JSON file
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            
            # Build the service
            self.service = build('drive', 'v3', credentials=credentials)
            print("✅ Google Drive authentication successful")
            
        except Exception as e:
            print(f"❌ Google Drive authentication failed: {str(e)}")
            raise e
    
    def _setup_folders(self):
        """Create UTIS PDF folder in Google Drive if not exists"""
        try:
            # Search for existing UTIS PDF folder
            results = self.service.files().list(
                q="name='UTIS_PDF_Files' and mimeType='application/vnd.google-apps.folder'",
                spaces='drive'
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                # Folder exists
                self.folder_id = folders[0]['id']
                print(f"✅ Using existing UTIS folder: {self.folder_id}")
            else:
                # Create new folder
                folder_metadata = {
                    'name': 'UTIS_PDF_Files',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                
                folder = self.service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()
                
                self.folder_id = folder.get('id')
                print(f"✅ Created new UTIS folder: {self.folder_id}")
                
        except Exception as e:
            print(f"❌ Folder setup failed: {str(e)}")
            raise e
    
    def upload_pdf(self, file_path, utis_code, original_filename):
        """Upload PDF to Google Drive"""
        try:
            # File metadata
            file_metadata = {
                'name': f"{utis_code}_{original_filename}",
                'parents': [self.folder_id],
                'description': f"UTIS PDF for {utis_code}"
            }
            
            # Upload file
            media = MediaFileUpload(
                file_path,
                mimetype='application/pdf',
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size,createdTime'
            ).execute()
            
            file_id = file.get('id')
            print(f"✅ PDF uploaded to Drive: {file_id}")
            
            return {
                'drive_file_id': file_id,
                'drive_file_name': file.get('name'),
                'file_size': file.get('size'),
                'upload_time': file.get('createdTime')
            }
            
        except Exception as e:
            print(f"❌ PDF upload failed: {str(e)}")
            return None
    
    def get_download_link(self, file_id):
        """Get download link for PDF"""
        try:
            # Get file metadata
            file = self.service.files().get(fileId=file_id).execute()
            
            # Create download link
            download_link = f"https://drive.google.com/uc?id={file_id}&export=download"
            
            return {
                'download_link': download_link,
                'file_name': file.get('name'),
                'file_size': file.get('size')
            }
            
        except Exception as e:
            print(f"❌ Get download link failed: {str(e)}")
            return None
    
    def download_pdf(self, file_id):
        """Download PDF from Google Drive"""
        try:
            # Get file content
            request = self.service.files().get_media(fileId=file_id)
            
            file_io = io.BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            file_io.seek(0)
            return file_io
            
        except Exception as e:
            print(f"❌ PDF download failed: {str(e)}")
            return None
    
    def delete_pdf(self, file_id):
        """Delete PDF from Google Drive"""
        try:
            self.service.files().delete(fileId=file_id).execute()
            print(f"✅ PDF deleted from Drive: {file_id}")
            return True
            
        except Exception as e:
            print(f"❌ PDF deletion failed: {str(e)}")
            return False
    
    def get_folder_info(self):
        """Get UTIS folder information"""
        try:
            # Get folder details
            folder = self.service.files().get(
                fileId=self.folder_id,
                fields='id,name,createdTime,size'
            ).execute()
            
            # Get files count in folder
            results = self.service.files().list(
                q=f"'{self.folder_id}' in parents",
                fields="files(id)"
            ).execute()
            
            files_count = len(results.get('files', []))
            
            return {
                'folder_id': self.folder_id,
                'folder_name': folder.get('name'),
                'files_count': files_count,
                'created_time': folder.get('createdTime')
            }
            
        except Exception as e:
            print(f"❌ Get folder info failed: {str(e)}")
            return None

# Global instance
drive_service = None

def get_drive_service():
    """Get or create Google Drive service instance"""
    global drive_service
    if drive_service is None:
        try:
            drive_service = GoogleDriveService()
        except Exception as e:
            print(f"❌ Failed to initialize Google Drive service: {str(e)}")
            drive_service = None
    return drive_service 