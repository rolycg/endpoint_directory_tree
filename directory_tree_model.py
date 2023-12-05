from dataclasses import dataclass
from functools import total_ordering
from typing import List


@dataclass
class DirectoryModel:
    id: int
    name: str
    parent: int

    @staticmethod
    def from_db(values: List) -> "DirectoryModel":
        return DirectoryModel(id=int(values[0]), name=values[1], parent=values[2])

    def __str__(self):
        return self.name


@total_ordering
class DirectoryTreeModel:
    def __init__(self, value: str):
        self.value: str = value
        self.children: List["DirectoryTreeModel"] = []

    def add_child(self, child_node: "DirectoryTreeModel"):
        self.children.append(child_node)

    def __lt__(self, obj):
        return self.value < obj.value

    def __gt__(self, obj):
        return self.value > obj.value

    def __le__(self, obj):
        return self.value <= obj.value

    def __ge__(self, obj):
        return self.value >= obj.value

    def __eq__(self, obj):
        return self.value == obj.value
