import io
from rich.table import Table
from rich.progress import track
from .service import get_service 
from rich.console import Console
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from .utils import VALID_ORDERING, VALID_SPACES, rfc3339_to_human_readable, get_file_mimetype
import logging


logging.basicConfig(
    level=logging.INFO,
    filename="./gapy/logs/gapy.log",
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


class Gapy():
    def __init__(self):
        self.service = get_service()
        self.console = Console()
        self.logger = logging.getLogger("gapy")


    def list_files(self, orderBy=None, spaces=None, _print=False):
        """
            Display the files (directories and folders) inside a table.
            pageSize: The response data will be split into pages of the given size
            spaces: List only the files inside a given space
        """

        result = self.service.files().list(orderBy=orderBy, spaces=spaces, fields="nextPageToken, files(id, createdTime, name, size, parents, spaces)").execute()
        
        files = result.get("files", [])
        
        if not files:
            self.console("No files were found")
        
        else:

            if _print:
                table = self.build_table()

                for file in files:
                    _id = file["id"]
                    created = rfc3339_to_human_readable(file["createdTime"])
                    name = file["name"]
                    try:
                        size = str(float(file["size"])*(1/1000))
                    except KeyError: 
                        size = "-"
                    try:
                        parents = ", ".join([ self.get_filename_by_id(f) for f in file["parents"] ])
                    except KeyError:
                        parents = [""]
                    spaces = ", ".join(file["spaces"])

                    table.add_row(_id, created, name, size, spaces, parents[0])
                self.console.print(table)
            else:
                return files


    def create_file(self, file_name, path=None, parents_id=None, spaces=None, isFolder=False):
        """
            file_name: file name
            path: Path to the file that will be uploaded
            parents_id: (optional) a list containing the id's of the parent folders that will store
                        the file
                        default: My Drive folder
            spaces: space(s) to upload the file see VALID_SPACES
                    default: drive
            isFolder: Whether the file is a folder or not

            Returns the ID of the recently created file
        """

        body = { "name": file_name }

        if parents_id:
            body['parents'] = parents_id

        if isFolder:
            body["mimeType"] = "application/vnd.google-apps.folder"
            response = self.service.files().create(body=body, fields="id").execute()
            self.logger.info("Folder created {} with id {}".format(file_name, response.get("id")))
            return response.get("id")

        if spaces:
            if spaces not in VALID_SPACES:
                self.logger.error("Invalid space name, must be one of {}".format(", ".join(VALID_SPACES)))
                raise Exception
            body['spaces'] = spaces

        file_extension = file_name.split(".")

        mimetype = get_file_mimetype(file_name)
        
        media = MediaFileUpload(f"{path}/{file_name}", mimetype=mimetype, resumable=True)
    
        response = self.service.files().create(body=body, media_body=media, fields="id").execute()

        self.logger.info("File created {} with id {}".format(file_name, response.get("id")))

        return response.get("id")


    def get_filename_by_id(self, file_id):
        """
            Returns the name of a file given its id
        """

        response = self.service.files().get(fileId=file_id).execute()
        
        return response.get("name")
    

    def download_file(self, file_id, path):
        """
            Download the file with the given id at the directory specified by path
            file_id: id of the file
            path: absolute path
        """
        
        file_name = self.get_filename_by_id(file_id)
        
        request = self.service.files().get_media(fileId=file_id)
        
        fh = io.BytesIO()
        
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        
        while done is False:
            status, done = downloader.next_chunk()
            self.console.print("Downloading {} : {}".format(file_name, int(status.progress()*100)))
        
        with open(path + "/" + file_name, "wb") as downloaded_file:
            downloaded_file.write(fh.getbuffer())

        self.logger.info("The file {} was downloaded".format(file_name))


    def delete_file(self, file_id):
        """
            Delete the file with the id provided
        """
        self.service.files().delete(fileId=file_id)     
        file_name = self.get_filename_by_id(file_id)
        self.logger.warn("The file {} was deleted from Google Drive".format(file_name))


    def update_file(self, file_id, path):
        """
            Update the file's content with the given id
        """
        file_name = self.get_filename_by_id(file_id)
        mimetype = get_file_mimetype(file_name)
        media = MediaFileUpload(f"{path}/{file_name}", mimetype=mimetype)
        body = { "name": file_name }

        self.service.files().update(fileId=file_id, body=body, media_body=media).execute()
        self.logger.info("The file {} was updated!".format(file_name))


    def generate_ids(self, count=1):
        """
            Generate ids that can be used to create files
        """
        ids = self.service.files().generateIds(count=count).execute()
        return ids.get("ids")


    def find_file(self, file_name, parents_id=None):
        """
            Find a file under the parents_id folders (if provided)
        """

        if parents_id:
            query = f"name='{file_name}' and parents='{parents_id}'"
        else:
            query = f"name='{file_name}'"

        response = self.service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, parents)",
            pageToken=None
        ).execute()

        if response.get("files", []):
            return response.get("files", [])
        else:
            return []


    def build_table(self):
        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("ID", style="green", justify="center")
        table.add_column("Created Time", style="green", justify="center")
        table.add_column("Name", style="green", justify="center")
        table.add_column("Size (MB)", style="green", justify="center")
        table.add_column("Spaces", style="green", justify="center")
        table.add_column("Parents", style="green", justify="center")
        return table