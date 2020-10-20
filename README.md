# Gapy

Gapy is a command line program that connects to the Google Drive API to perform backups and even 'mirror' a given filesystem by
using the watchdog library: when any of the following events are detected (on change, on create, on delete) the content 
is also sync to the cloud.

