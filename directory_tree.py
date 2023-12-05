from typing import Optional, List, Set, Tuple
from utils import sanitize_upper_input
from directory_tree_db import DirectoryTreeDB
from directory_tree_model import DirectoryModel, DirectoryTreeModel

CREATE: str = "CREATE"
LIST: str = "LIST"
MOVE: str = "MOVE"
DELETE: str = "DELETE"


class DirectoryTree:

    def __init__(self):
        self.handlers = {
            CREATE: self.create_directory,
            LIST: self.list_directories,
            MOVE: self.move_directory,
            DELETE: self.delete_directory
        }
        self.database = DirectoryTreeDB()

    def __find_directory__(self, directory: str) -> Tuple[str, int | None]:
        folders: List[str] = sanitize_upper_input(directory).split("/")
        parent_reference: Optional[int] = None
        if len(folders) > 1:
            parents: List[str] = folders[:-1]
            for parent in parents:
                directory: Optional[DirectoryModel] = self.database.get_directory(parent, parent_reference)
                assert directory, f"{parent}"
                parent_reference = directory.id
        folder_name: str = folders[-1]
        return folder_name, parent_reference

    def create_directory(self, directory: str) -> None:
        folder_name, parent_reference = self.__find_directory__(directory)
        self.database.create_directory(folder_name=folder_name, parent=parent_reference)
        print(f"{CREATE} {directory}")

    def list_directories(self) -> None:
        print(f"{LIST}")
        visited_folders: Set[int] = set()
        directory_trees: List[DirectoryTreeModel] = []

        def print_directory_tree(tree, level=0):
            if tree is not None:
                print('  ' * level + str(tree.value))
                if tree.children:
                    for node in sorted(tree.children):
                        print_directory_tree(node, level + 1)

        def find_children(directory: DirectoryModel, current_node: DirectoryTreeModel) -> Optional[DirectoryTreeModel]:
            if not directory:
                return None
            children = self.database.find_children_directories(directory.id)
            for child in children:
                visited_folders.add(child.id)
                child_tree: DirectoryTreeModel = find_children(child, DirectoryTreeModel(child.name))
                if child_tree:
                    current_node.add_child(child_tree)
            return current_node

        for directory_model in self.database.find_root_directories():
            if directory_model.id not in visited_folders:
                visited_folders.add(directory_model.id)
                tree_model: DirectoryTreeModel = find_children(directory=directory_model,
                                                               current_node=DirectoryTreeModel(directory_model.name))
                directory_trees.append(tree_model)
        for directory_tree in sorted(directory_trees):
            print_directory_tree(directory_tree, 0)

    def delete_directory(self, directory: str) -> None:
        print(f"{DELETE} {directory}")
        try:
            folder_name, parent_reference = self.__find_directory__(directory)
            directory_model: DirectoryModel = self.database.delete_directory(folder_name, parent_reference)
        except AssertionError as e:
            print(f"Cannot delete {directory} - {e} does not exist")
            return

        def delete_children(parent_directory: DirectoryModel) -> None:
            for child in self.database.find_children_directories(parent_directory.id):
                self.database.direct_delete_directory(child.id)
                delete_children(child)

        delete_children(directory_model)

    def move_directory(self, from_directory: str, to_directory: str) -> None:
        from_folder_name, from_parent_reference = self.__find_directory__(from_directory)
        to_folder_name, to_parent_reference = self.__find_directory__(to_directory)
        to_directory = self.database.get_directory(to_folder_name, to_parent_reference)
        self.database.update_directory_parent(from_folder_name, from_parent_reference, to_directory.id)
        print(f"{MOVE} {from_directory} {to_directory}")

    def close(self) -> None:
        self.database.close_db()
