import json

# Read the Google credentials file
with open('google-credentials.json', 'r') as f:
    creds = json.load(f)

# Print compact JSON for environment variable
compact_json = json.dumps(creds, separators=(',', ':'))
print("Copy this value for GOOGLE_CREDENTIALS_JSON environment variable:")
print("=" * 80)
print(compact_json)
print("=" * 80) 