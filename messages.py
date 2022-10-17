import os
import sqlite_utils
from sqlite_utils.db import NotFoundError
import datetime
import pickle
import datetime
import email.utils
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# return db handle, create if doesn't exist
def open_database():
    db = sqlite_utils.Database("messages.db")
    return db

# call Gmail list API with `query`
def search_messages(service, query):
    result = service.users().messages().list(userId='me',q=query).execute()
    messages = [ ]
    if 'messages' in result:
        messages.extend(result['messages'])
    while 'nextPageToken' in result:
        page_token = result['nextPageToken']
        result = service.users().messages().list(userId='me',q=query, pageToken=page_token).execute()
        if 'messages' in result:
            messages.extend(result['messages'])
    return messages

def cache_messages(messages):
    with open("messages.pickle", "wb") as cache:
        pickle.dump(messages, cache)

def load_cached_messages():
    messages = []
    with open("messages.pickle", "rb") as cache:
        messages = pickle.load(cache)
    return messages

# fetch details for a message
def fetch_message(service, id):
    msg = service.users().messages().get(userId='me', id=id, format='full').execute()
    return msg

def gmail_authenticate():
    SCOPES = ['https://mail.google.com/']

    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def message_exists_in_db(db, msg):
    try:
        # row exists?
        row = db["messages"].get(msg["id"])
        return row
    except NotFoundError:
        return None

def insert_message_into_db(db, msg):

    insert = {
        'id' : msg['id'],
        'threadId' : msg['threadId'],
        'snippet' : msg['snippet'],
    }

    for h in msg['payload']['headers']:
        if h['name'] in ('From', 'date', 'Date', 'Subject', 'To'):
            insert[h['name'].lower()] = h['value']

    insert['date'] = email.utils.parsedate_to_datetime(insert['date']).isoformat(sep=' ')

    db["messages"].insert(insert, pk="id")


if __name__ == '__main__':
    db = open_database()
    service = gmail_authenticate()
    #messages = search_messages(service, "label:exec-recruiting")
    #cache_messages(messages)
    messages = load_cached_messages()

    for msg in messages:
        if not message_exists_in_db(db, msg):
            msg = fetch_message(service, msg['id'])
            if msg:
                insert_message_into_db(db, msg)

