Quick and dirty script to search gmail and stick some basic metadata about matching messages into a sqlite table for use with datasette.

You'll need to enable the GMail API in the Google Cloud console, and create and download some OAuth credentials. The script expects these to live in credentials.json

Script will download and cache in a pickle file all the messages with their id and threadId, the only things returned from the messages.list() method.  Than it needs to go one by one getting extended details for each message. This is unsurprisingly slow.
