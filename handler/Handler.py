from watchdog.events import FileSystemEventHandler
from rich.logging import RichHandler
from .utils import IGNORE_DIRS, IGNORE_FILES
from gapy.gapy import Gapy
import json
import os
import re
import logging



class FSHandler(FileSystemEventHandler):
    def __init__(self, path):
        self.logger = logging.getLogger(__name__)
        self.path = path
        self.gapy = Gapy()
        self.ignore_dirs = IGNORE_DIRS
        self.ignore_files = IGNORE_FILES
        if os.path.exists("./filesystem.json"):
            with open("filesystem.json", "r") as fs:
                self.filesystem = json.load(fs)
        else:
            self.filesystem = {}


    def on_created(self, event):
        """
            Get the parent id ("if any") and create the file in that directory
        """
        
        file_name = os.path.basename(event.src_path)
        parent = os.path.dirname(event.src_path)
        parents_id = self.filesystem[parent]["id"]

        if event.is_directory:
            file_id = self.gapy.create_file(file_name, path=parent, parents_id=[parents_id], isFolder=True)
            self.filesystem[file_name.rstrip("/")] = file_id 
            self.gapy.logger.info("The directory {} was created with id {}".format(file_name, file_id))
        else:
            if file_name not in self.ignore_files:
                with open(event.src_path, "w") as empty_file:
                    empty_file.write("\t")
                file_id = self.gapy.create_file(file_name, path=parent, parents_id=[parents_id])
                self.filesystem[parent.rstrip("/")]["files"].append({"name": file_name, "id": file_id}) 
                self.gapy.logger.info("The file {} was created with id {}".format(file_name, file_id))
        

    def on_modified(self, event):
        """
            Get the file id that was modified and update its content
            The file must exists at the google drive folder
        """
        
        if not event.is_directory: 

            file_name = os.path.basename(event.src_path)
            
            if file_name not in self.ignore_files:
                parent = os.path.dirname(event.src_path)
                file_id = list(filter(lambda f: f["name"] == file_name, self.filesystem[parent]["files"]))[0]["id"]
                self.gapy.update_file(file_id, path=parent)
                self.gapy.logger.info("The file {} was modified, the content was updated".format(file_name, parent))


    def on_deleted(self, event):
        """
            If a directory or file is removed from the local system, the reference 
            in the filesystem dict is also deleted.
            Optional to remove it in Google Drive.
        """

        file_name = os.path.basename(event.src_path)
        self.gapy.logger.warn("The file {} was deleted from local system".format(file_name))
        choice = input("Do you wan't to remove the file from Google Drive? [y/n]")
        
        while True:
            if re.fullmatch("[yY]", choice):
                self.remove_from_filesystem(event.src_path)
                self.gapy.logger.warning("The file {} was removed from Google Drive".format(file_name))
                return False
            elif re.fullmatch("[nN]", choice):
                self.remove_from_filesystem(event.src_path)
                self.gapy.logger.warning("The file {} is not removed from Google Drive".format(os.path.basename(event.src_path)))
                return False
            else:
                print("Invalid option, select a valid one")


    def upload_handler(self):
        """
            Upload the directory indicated by path
            * If there are empty files they're ignored since an HttpError is raised
            * Files and dirs can be ignored by placing their names in IGNORE_DIRS and IGNORE_FILES
        """
        
        for root, dirs, files in os.walk(self.path):

            current_dir = os.path.basename(root)
        
            if root == self.path:
                root_id = self.gapy.create_file(current_dir, path=root, isFolder=True)
            else:
                parents_id = self.filesystem[os.path.dirname(root)]["id"]
                root_id = self.gapy.create_file(current_dir, path=root, isFolder=True, parents_id=[parents_id])

            self.filesystem[root.rstrip("/")] = { "id":  root_id, "files": [] }
                
            if files:
                for file in files:
                    if file not in IGNORE_FILES and os.path.getsize(root+"/"+file) > 0:
                        file_id = self.gapy.create_file(file, path=root, parents_id=[root_id])
                        self.filesystem[root]["files"].append({ "name": file, "id": file_id})
        
        with open("./handler/filesystem.json", "a") as fs:
            json.dump(self.filesystem, fs, indent=4)


    def upload_files(self, files):
        """
            Receive a list of files and upload them
        """
        for file in files:
            file_name = os.path.basename(file)
            path = os.path.dirname(file)
            self.gapy.create_file(file_name, path=path)


    def download_handler(self):
        files = self.gapy.list_files()
        self.gapy.console.print(files)
        


    def remove_from_filesystem(self, file_path, is_dir=False):
        """
            Remove the file from the filesystem and update the filesystem 
            by removing the file from the parent's directory
        """
        if is_dir:
            self.filesystem = self.filesystem.pop(file_path, None)
        else:
            file_name = os.path.basename(file_path)
            parent = os.path.dirname(file_path)
            self.filesystem[parent]["files"] = list(filter(lambda file: file["name"] != file_name, self.filesystem[parent]["files"]))
        with open("./handler/filesystem.json", "a") as fs:
            json.dump(self.filesystem, fs, indent=4)