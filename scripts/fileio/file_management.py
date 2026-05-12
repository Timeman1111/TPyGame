"""
This script demonstrates the usage of the FileManager class for file and folder operations.
"""
from tpygame.file import FileManager
import os

def main():
    """
    Main function to execute the file management demonstration.
    """
    print("Starting file management script...")


    print("Creating FileManager instance...")
    fm = FileManager()
    print(fm)

    txt_res = fm.create_file("test.txt")

    if txt_res:
        print("File created successfully.")


    print(fm.created_files)

    for file in fm.created_files:
        print(file)
        os.remove(file)

    print("Finished...")
    return

if __name__ == "__main__":
    main()