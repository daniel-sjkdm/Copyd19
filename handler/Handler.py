from watchdog.events import FileSystemEventHandler
from .utils import IGNORE_DIRS, IGNORE_FILES
from rich.logging import RichHandler
from rich.progress import track
from datetime import datetime
from gapy.gapy import Gapy
import logging
import json
import os
import re


# TODO
# [ ] Fix deleting a file


class FSHandler(FileSystemEventHandler):
    
    def __init__(self, path):
        self.logger = logging.getLogger(__name__)
        self.path = path
        self.gapy = Gapy()
        self.ignore_dirs = IGNORE_DIRS
        self.ignore_files = IGNORE_FILES
        self.fs_path = "handler/filesystem.json"
        if os.path.exists(self.fs_path):
            with open(self.fs_path, "r") as fs:
                self.filesystem = json.load(fs)
        else:
            self.upload_handler()


    def on_created(self, event):
        """
            Get the parent id ("if any") and create the file in that directory
        """
       
        file_name = os.path.basename(event.src_path)
        parent = os.path.dirname(event.src_path)
        parents_id = self.filesystem[parent]["id"]

        if event.is_directory:
            if file_name not in self.ignore_dirs:
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
                print(f"\nFile created: {file_name} at {datetime.now()}")

        self.update_fs()
        

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
                print(f"\nThe file {file_name} was modified and synchronized")


    def on_deleted(self, event):
        """
            If a directory or file is removed from the local system, the reference 
            in the filesystem dict is also deleted.
            Optional to remove it in Google Drive.
        """

        file_name = os.path.basename(event.src_path)
        self.gapy.logger.warn("The file {} was deleted from local system".format(file_name))
        print(f"\n\033[91m The file {file_name} was deleted from local system \033[0m")
        choice = input("\nDo you want to remove the file from Google Drive? [y/n]: ")
        
        if re.match("[yY]", choice):
            file_name = os.path.basename(event.src_path)
            parent = os.path.dirname(event.src_path)
            file_id = list(filter(lambda f:  f["name"] == file_name, self.filesystem[parent]["files"]))[0]["id"]
            self.gapy.delete_file(file_id)
            self.remove_from_filesystem(event.src_path)
            self.gapy.logger.warning("The file {} was removed from Google Drive".format(file_name))
            print(f"\n\033[91m The file {file_name} was also removed from Google Drive \033[0m")

        else:
            self.remove_from_filesystem(event.src_path)
            self.gapy.logger.warning("\nThe file {} is not removed from Google Drive".format(os.path.basename(event.src_path)))
        
        self.update_fs()


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
                print(f"\033[94m The directory {current_dir} was uploaded \033[0m")

            self.filesystem[root.rstrip("/")] = { "id":  root_id, "files": [] }
                
            if files:
                for f in files:
                    if f not in IGNORE_FILES and os.path.getsize(root+"/"+f) > 0:
                        file_id = self.gapy.create_file(f, path=root, parents_id=[root_id])
                        self.filesystem[root]["files"].append({ "name": f, "id": file_id})
                        print(f"\033[94m The file {f} was uploaded \033[0m")
        
        self.update_fs()


    def remove_from_filesystem(self, file_path, is_dir=False):
        """
            Remove the file from the filesystem and update the filesystem 
            by removing the file from the parent's directory
        """
        file_name = os.path.basename(file_path)
        if is_dir:
            self.filesystem = self.filesystem.pop(file_path, None)

        else:
            parent = os.path.dirname(file_path)
            self.filesystem[parent]["files"] = list(filter(lambda f: f["name"] != file_name, self.filesystem[parent]["files"]))
        
        self.gapy.logger.info("\nThe file {} was removed from the filesystem".format(file_name))

        self.update_fs()


    def create_fs(self):
        for root, dirs, files in os.walk(self.path):
            current_dir = os.path.basename(root)
            
            if files:
                for file in files:
                    self.filesystem[current_dir]["files"] 



    def update_fs(self):
        with open(self.fs_path, "w") as f:
            json.dump(self.filesystem, f, indent=4)