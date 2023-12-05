import sqlite3
from typing import Optional, List, Tuple
from directory_tree_model import DirectoryModel


class DirectoryTreeDB:

    def __init__(self) -> None:
        self.connector = sqlite3.connect("directory_tree.db")
        self.cursor = self.connector.cursor()
        self.create_table()

    def create_table(self) -> None:

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS DIRECTORY(id INTEGER PRIMARY KEY, folder_name TEXT, parent INTEGER NULL, UNIQUE (folder_name, parent)) """)
        self.cursor.execute("""CREATE INDEX IF NOT EXISTS index_folder_name ON DIRECTORY(folder_name)""")

    def create_directory(self, folder_name: str, parent: Optional[int]) -> None:
        try:
            self.cursor.execute("""INSERT INTO DIRECTORY(folder_name, parent) VALUES(?, ?)""", (folder_name, parent))
            self.connector.commit()
        except sqlite3.IntegrityError as integrity_error:
            print("Error creating directory: ", integrity_error)

    def get_directory(self, folder_name: str, parent: Optional[int]) -> Optional[DirectoryModel]:
        try:
            query = """SELECT * FROM DIRECTORY WHERE folder_name=? AND parent=?"""
            params = (folder_name, parent)
            if not parent:
                query = """SELECT * FROM DIRECTORY WHERE folder_name=? AND parent IS NULL"""
                params = (folder_name,)
            directory: List = self.cursor.execute(query, params).fetchone()
            if directory:
                return DirectoryModel.from_db(directory)
        except sqlite3.IntegrityError as integrity_error:
            print("Error retrieving directory: ", integrity_error)

    def delete_directory(self, folder_name: str, parent: Optional[int]) -> DirectoryModel:
        try:
            directory: Optional[DirectoryModel] = self.get_directory(folder_name, parent)
            assert directory, "Directory does not exist"
            self.cursor.execute("""DELETE FROM DIRECTORY WHERE id=?""", (directory.id,))
            self.connector.commit()
            return directory
        except sqlite3.IntegrityError as integrity_error:
            print("Error deleting directory: ", integrity_error)

    def direct_delete_directory(self, _id: int) -> None:
        try:
            self.cursor.execute("""DELETE FROM DIRECTORY WHERE id=?""", (_id,))
            self.connector.commit()
        except sqlite3.IntegrityError as integrity_error:
            print("Error direct deleting directory: ", integrity_error)

    def find_children_directories(self, parent: int) -> List[DirectoryModel]:
        try:
            return [DirectoryModel.from_db(values) for values in
                    self.cursor.execute("""SELECT * FROM DIRECTORY WHERE parent=?""", (parent,)).fetchall()]
        except sqlite3.IntegrityError as integrity_error:
            print("Error deleting directory: ", integrity_error)

    def update_directory_parent(self, folder_name: str, parent: int, new_parent: int) -> None:
        query: str = """UPDATE DIRECTORY SET parent = ? WHERE folder_name=? AND parent=?"""
        params: Tuple[int, str, Optional[int]] = (new_parent, folder_name, parent)
        if not parent:
            query = """UPDATE DIRECTORY SET parent = ? WHERE folder_name=? AND parent IS NULL"""
            params = (new_parent, folder_name)
        try:
            self.cursor.execute(query, params)
            self.connector.commit()
        except sqlite3.IntegrityError as integrity_error:
            print("Error updating directory: ", integrity_error)

    def find_root_directories(self) -> List[DirectoryModel]:
        try:
            return [DirectoryModel.from_db(values) for values in
                    self.cursor.execute("""SELECT * FROM DIRECTORY WHERE parent IS NULL""").fetchall()]
        except sqlite3.IntegrityError as integrity_error:
            print("Error deleting directory: ", integrity_error)

    def close_db(self) -> None:
        self.connector.commit()
        self.cursor.close()
        self.connector.close()