# save_document(file), rename_document(old_name, new_name), delete_document(filename)
import shutil
import os


async def get_all_documents():
    # Get all files in the documents_storage directory
    files = os.listdir("documents_storage")
    return files




async def save_document(file):
    # Save the file to disk
    with open(f"documents_storage/{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)


async def rename_document(old_name, new_name):
    # Check if about to replace an existing file
    exists = os.path.isfile(f"documents_storage/{new_name}")
    if exists:
        raise FileExistsError(f"File {new_name} already exists")

    # Rename the file
    shutil.move(f"documents_storage/{old_name}", f"documents_storage/{new_name}")


async def delete_document(filename):
    # Delete the file
    os.remove(f"documents_storage/{filename}")
