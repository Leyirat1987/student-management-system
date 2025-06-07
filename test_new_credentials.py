"""
Test script for new Google Drive credentials
Bu script yeni Google Drive credentials-i test edir
"""

import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

def test_credentials(credentials_file):
    """Test Google Drive credentials"""
    try:
        print(f"🔧 Testing credentials file: {credentials_file}")
        
        # Check if file exists
        if not os.path.exists(credentials_file):
            print(f"❌ Credentials file not found: {credentials_file}")
            return False
        
        # Load credentials
        credentials = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        
        # Build service
        service = build('drive', 'v3', credentials=credentials)
        
        # Test API call - list files
        print("🔧 Testing Google Drive API connection...")
        results = service.files().list(pageSize=1).execute()
        
        # Get service account email
        with open(credentials_file, 'r') as f:
            creds_data = json.load(f)
            email = creds_data.get('client_email', 'Unknown')
        
        print(f"✅ Google Drive API test successful!")
        print(f"📧 Service Account Email: {email}")
        print(f"🔑 Project ID: {creds_data.get('project_id', 'Unknown')}")
        
        # Test folder creation
        print("🔧 Testing folder creation...")
        folder_metadata = {
            'name': 'UTIS_PDF_Files_Test',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        folder = service.files().create(
            body=folder_metadata,
            fields='id,name'
        ).execute()
        
        folder_id = folder.get('id')
        print(f"✅ Test folder created: {folder_id}")
        
        # Clean up - delete test folder
        service.files().delete(fileId=folder_id).execute()
        print("🧹 Test folder cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Credentials test failed: {str(e)}")
        return False

def generate_compact_json(credentials_file):
    """Generate compact JSON for environment variable"""
    try:
        with open(credentials_file, 'r') as f:
            creds = json.load(f)
        
        compact_json = json.dumps(creds, separators=(',', ':'))
        print("\n" + "="*80)
        print("📋 Copy this value for GOOGLE_CREDENTIALS_JSON environment variable:")
        print("="*80)
        print(compact_json)
        print("="*80)
        
    except Exception as e:
        print(f"❌ Failed to generate compact JSON: {str(e)}")

if __name__ == "__main__":
    print("🚀 Google Drive Credentials Test")
    print("="*50)
    
    # Test current credentials
    current_file = "google-credentials.json"
    if os.path.exists(current_file):
        print("Testing current credentials...")
        test_credentials(current_file)
        generate_compact_json(current_file)
    
    # Check for new credentials file
    new_files = [f for f in os.listdir('.') if f.endswith('.json') and 'utis' in f.lower() and f != current_file]
    
    if new_files:
        print(f"\n🔍 Found potential new credentials files: {new_files}")
        for new_file in new_files:
            print(f"\nTesting {new_file}...")
            if test_credentials(new_file):
                print(f"\n✅ {new_file} is working!")
                generate_compact_json(new_file)
                
                # Ask if user wants to replace
                print(f"\n❓ Do you want to replace current credentials with {new_file}?")
                print("   (You need to manually replace google-credentials.json)")
    else:
        print("\n📝 To add new credentials:")
        print("1. Download new JSON file from Google Cloud Console")
        print("2. Place it in this directory")
        print("3. Run this script again") 