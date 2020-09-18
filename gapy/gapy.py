from .service import get_service 
from rich.console import Console
from rich.table import Table
from rich.progress import track
from .utils import VALID_ORDERING, VALID_SPACES, rfc3339_to_human_readable, get_file_mimetype
from googleapiclient.http import MediaFileUpload


# TODO
# - [ ] Folders are created, verify if can be created under a given directory



class Gapy():
    def __init__(self):
        self.service = get_service()
        self.console = Console()


    def list_files(self, pageSize=None, orderBy=None, spaces=None):
        """
            Display the files (directories and folders) inside a table.
            pageSize: The response data will be split into pages of the given size
            spaces: List only the files inside a given space
        """
        result = self.service.files().list(pageSize=pageSize, orderBy=orderBy, spaces=spaces, fields="nextPageToken, files(id, createdTime, name, size, parents, spaces)").execute()
        
        files = result.get("files", [])
        
        if not files:
            self.console("No files were found")
        
        else:
            table = self.build_table()
            for file in files:
                _id = file["id"]
                created = rfc3339_to_human_readable(file["createdTime"])
                name = file["name"]
                try:
                    size = str(float(file["size"])*(1/1000))
                except KeyError: 
                    size = "-"
                parents = ", ".join([ self.get_filename_by_id(f) for f in file["parents"] ])  # list of parents id's
                spaces = ", ".join(file["spaces"])

                table.add_row(_id, created, name, size, spaces, parents)
            self.console.print(table)


    def create_file(self, file_name, path=None, parents_id=None, spaces=None, isFolder=False):
        """
            parents_id: (optional) a list containing the id's of the parent folders that will store
                        the file
                        default: My Drive folder
        """

        if self.find_file(file_name, parents_id=parents_id[0]):
            self.console.print("The folder {} already exist".format(file_name), style="bold red")
            return False

        body = { "name": file_name }

        if parents_id:
            body['parents'] = parents_id

        if isFolder:
            body["mimeType"] = "application/vnd.google-apps.folder"
            response = self.service.files().create(body=body, fields="id").execute()
            self.console.print("Folder created with id {}".format(response.get("id")), style="yellow")
            return response

        if spaces:
            if spaces not in VALID_SPACES:
                self.console.print("Invalid space name, must be one of {}".format(", ".join(VALID_SPACES)))
                raise Exception
            body['spaces'] = spaces

        file_extension = file_name.split(".")

        mimetype = get_file_mimetype(file_name)
        
        media = MediaFileUpload(f"{path}/{file_name}", mimetype=mimetype, resumable=True)
    
        response = self.service.files().create(body=body, media_body=media, fields="id").execute()

        self.console.print("File created with id {}".format(response.get("id")))


    def get_filename_by_id(self, file_id):
        response = self.service.files().get(fileId=file_id).execute()
        return response.get("name")
    

    def download_file(self, file_id):
        request = self.service.files().get_media(fileId=file_id).execute()


    def delete_file(self, file_id):
        self.service.files().delete(fileId=file_id)


    def update(self, file_id):
        self.service.update()


    def generate_ids(self, count=1):
        ids = self.service.files().generateIds(count=count).execute()
        return ids.get("ids")


    def find_file(self, file_name, parents_id=None):
        if parents_id:
            query = f"name='{file_name}' and parents='{parents_id}'"
        else:
            query = f"name='{file_name}'"
        response = self.service.files().list(
            q=query,
            fields="nextPageToken, files(id, name)",
            pageToken=None
        ).execute()
        if response.get("files", []):
            return True
        else:
            return False


    def build_table(self):
        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("ID", style="green", justify="center")
        table.add_column("Created Time", style="green", justify="center")
        table.add_column("Name", style="green", justify="center")
        table.add_column("Size (MB)", style="green", justify="center")
        table.add_column("Spaces", style="green", justify="center")
        table.add_column("Parents", style="green", justify="center")
        return table