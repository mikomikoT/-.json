
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Set access token
access_token = 'YOUR_ACCESS_TOKEN'
credentials = Credentials(token=access_token)

# Build Gmail API client
service = build('gmail', 'v1', credentials=credentials)

# Fetch messages
results = service.users().messages().list(userId='me').execute()
messages = results.get('messages', [])

if not messages:
    print("No messages found.")
else:
    print("Message snippets:")
    for message in messages[:5]:  # Display the first 5 email snippets
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        print(msg['snippet'])
