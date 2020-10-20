# Gapy

Gapy is a command line program that connects to the Google Drive API to perform backups and even 'mirror' a given filesystem by using the watchdog library: when any of the following events are detected (on change, on create, on delete) the content is also synchronized to the cloud.


## Steps: 

1. Create a project in the Google Developer Console
2. Enable the Google Drive API in the libraries option
3. Create the client's credentials to use the API
4. Manage the application consent screen (externals users)
5. Enable the ".../auth/drive" permitions in order to be able to:
    + edit
    + create
    + delete
    + view 
6. Download the client's credentials as: "credential.json" and store them inside gapy/ folder.
7. Make a virtual environment: 
   ```
   $ python3 -m venv venv 
   ```
8. Activate the environment and install the requirements:
   ```
   $ source venv/bin/activate
   $ pip install -r requirements.txt
   ```
9. Make a backup folder somewhere in your file system
10. Add the path to your folder in .env file as PATH variable
11. Run the setup script:
    ```
    $ pip install --editable .
    ```
12. The script can now be started as:
    ```
    $ gdrivepy <commands>
    ``` 



## Documentation

[Google Drive Python API](https://googleapis.github.io/google-api-python-client/docs/dyn/drive_v3.files.html)
