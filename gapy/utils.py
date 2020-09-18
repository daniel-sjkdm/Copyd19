from pyrfc3339 import parse
import mimetypes


VALID_ORDERING = [ 
    'createdTime', 
    'folder', 
    'modifiedByMeTime', 
    'modifiedTime', 
    'name', 
    'name_natural', 
    'quotaBytesUsed', 
    'recency', 
    'sharedWithMeTime', 
    'starred', 
    'viewedByMeTime'
]

VALID_SPACES = [
    'drive', 
    'appDataFolder',
    'photos'
]


def rfc3339_to_human_readable(rfc3339_stamp):
        return parse(rfc3339_stamp).strftime("%Y-%m-%d %H:%M:%S")


def get_file_mimetype(file):
    return mimetypes.guess_type(file, strict=True)[0]