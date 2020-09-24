from handler.Handler import FSHandler
from watchdog.observers import Observer
from gapy.gapy import Gapy
import os.path
import click
import time
import re


@click.group()
def main():
    pass


@main.command()
@click.option(
    "-p",
    "--path",
    help="Path to filesystem to be observed",
    type=click.types.Path(exists=True),
    required=True
)
@click.option(
    "-wt",
    "--watch-time",
    help="Time to be observed",
    type=click.types.INT,
    required=False,
    default=1
)
def watch(path, watch_time):
    """
        Watch the filesystem for changes to sync to Google Drive
    """

    fsh = FSHandler(path)
    # create = input("\nDo you want to upload the directory? [y/n]: ")

    # if re.fullmatch("[yY]", create):
    #     fsh.upload_handler()
    # elif re.fullmatch("[nN]", create):
    #     pass
    #     if not fsh.filesystem:
    #         print("Creating the filesystem")
    #         # fsh.create_fs()
    # else:
        # raise Exception("\nInvalid choice")
    
    click.secho("\nObserving {} every {} seconds".format(path, watch_time), fg="green")
    observer = Observer()
    observer.schedule(fsh, path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(watch_time)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


@main.command()
def listfiles():
    """
        Display the available files at Google Drive
    """
    gapy = Gapy()
    gapy.list_files(_print=True)


@main.command()
@click.option(
    "-t",
    "--to",
    help="Where to download the files",
    type=click.types.Path(exists=True),
    required=True
)
def download(to):
    """
        Download the selected files to the target directory
    """
    print(f"\nDownloading files to {to}")


@main.command()
@click.argument(
    "files",
    nargs=-1,
    type=click.types.Path(exists=True)
)
def upload(files):
    """
        Upload the files to google drive
    """
    gapy = Gapy()
    with click.progressbar(files, label="Uploading files") as bar:
        for f in bar:
            gapy.create_file(f, path=os.path.dirname(f))



if __name__ == "__main__":
    main()