from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

flow = InstalledAppFlow.from_client_secrets_file(
    'credentials.json',  # The file you downloaded
    SCOPES
)

print("\n=== Gmail OAuth Token Generator ===")
print("Opening browser for authentication...\n")

creds = flow.run_local_server(port=8080, open_browser=False)

# Save the credentials for the next run
with open('token.json', 'w') as token_file:
    token_file.write(creds.to_json())

print("\n✓ Authentication successful!")
print("\nYour token has been saved to 'token.json'.")
print("The fetch script will automatically use this file and refresh the token when needed.")
