from handler.Handler import FSHandler
from watchdog.observers import Observer
from gapy.gapy import Gapy
import os.path
import click
import time
import re


@click.command()
@click.option(
    "-p",
    "--path",
    help="Path to the directory to backup/download",
    required=True,
    type=click.types.Path(exists=True)
)
@click.option(
    "-w",
    "--watch",
    help="Watch the filesystem for events and keep in sync with Google Drive",
    required=False,
    is_flag=True
)
@click.option(
    "-wt",
    "--watch-time",
    help="Time to wait to listen for events",
    required=False,
    default=1
)
@click.option(
    "-f",
    "--files",
    help="Files to be downloaded/uploaded",
    required=False
)
@click.option(
    "-u",
    "--upload",
    help="Upload files from path to Google Drive",
    required=False,
    is_flag=True
)
@click.option(
    "-f",
    "--files",
    help="Files to be uploaded",
    required=False,
    multiple=True,
    type=click.Path(exists=True)
)
def main(path, watch, watch_time, upload, files):
    fsh = FSHandler(path)
    if watch:
        fsh.upload_handler()
        
        observer = Observer()
        observer.schedule(fsh, path, recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(watch_time)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    elif upload:
        fsh.upload_files(files)

        

if __name__ == "__main__":
    main()