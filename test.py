from io import StringIO
import unittest.mock
import os

from directory_tree import DirectoryTree
from directory_tree_db import DirectoryTreeDB


class MainTest(unittest.TestCase):
    def setUp(self):
        self.db_name = "test_directory_tree.db"

        self.input_value = """
        CREATE fruits
        CREATE vegetables
        CREATE grains
        CREATE fruits/apples
        CREATE fruits/apples/fuji
        LIST
        CREATE grains/squash
        MOVE grains/squash vegetables
        CREATE foods
        MOVE grains foods
        MOVE fruits foods
        MOVE vegetables foods
        LIST
        DELETE fruits/apples
        DELETE foods/fruits/apples
        LIST
        """

        self.expected_output = """CREATE fruits
CREATE vegetables
CREATE grains
CREATE fruits/apples
CREATE fruits/apples/fuji
LIST
fruits
  apples
    fuji
grains
vegetables
CREATE grains/squash
MOVE grains/squash vegetables
CREATE foods
MOVE grains foods
MOVE fruits foods
MOVE vegetables foods
LIST
foods
  fruits
    apples
      fuji
  grains
  vegetables
    squash
DELETE fruits/apples
Cannot delete fruits/apples - fruits does not exist
DELETE foods/fruits/apples
LIST
foods
  fruits
  grains
  vegetables
    squash"""

        os.environ["PYTEST_DIRECTORY_TREE"] = "True"

    def tearDown(self):
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

    @unittest.mock.patch('sys.stdout', new_callable=StringIO)
    def test_basic(self, mock_stdout):
        directory_tree = DirectoryTree()

        for line in self.input_value.split('\n'):
            arguments = line.strip().split()
            if arguments:
                action, params = arguments[0], arguments[1:]
                directory_tree.handlers[action](*params)
        directory_tree.close()

        assert mock_stdout.getvalue().strip() == self.expected_output.strip()


class DtDbFunctionalityTest(unittest.TestCase):
    def setUp(self):
        self.db_name = "test_directory_tree.db"
        os.environ["PYTEST_DIRECTORY_TREE"] = "True"
        self.directory_db = DirectoryTreeDB()

    def tearDown(self):
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

    def test_create_table(self):
        self.directory_db.create_table()
        tables = self.directory_db.cursor.execute("""SELECT tbl_name FROM sqlite_master WHERE type='table'
  AND tbl_name='DIRECTORY'; """).fetchall()
        assert len(tables) == 1, "Table was not created"

        self.directory_db.create_table()
        assert len(tables) == 1, "Duplicate table created"

    def test_create_directory(self):
        self.directory_db.create_table()
        self.directory_db.create_directory("Test", None)
        folder = self.directory_db.cursor.execute("""SELECT * FROM DIRECTORY WHERE folder_name=? AND parent is NULL""",
                                                  ("Test",)).fetchall()
        assert len(folder) == 1
        assert folder[0][1] == "Test"
        assert folder[0][2] is None
        assert folder[0][0] is not None

        with self.assertRaises(AssertionError) as e:
            self.directory_db.create_directory("Test", None)
        assert e.exception.args[0] == "Folder already exists"

        self.directory_db.create_directory("Test", 1)
        folder = self.directory_db.cursor.execute("""SELECT * FROM DIRECTORY WHERE folder_name=? AND parent=?""",
                                                  ("Test", 1)).fetchall()
        assert len(folder) == 1, "No folder was created"
        assert folder[0][2] is not None

    def test_get_directory(self):
        self.directory_db.create_table()
        self.directory_db.create_directory("Test", None)
        dir_model = self.directory_db.get_directory("Test", None)
        assert dir_model
        assert dir_model.name == "Test"
        self.directory_db.create_directory("Test_2", 1)
        assert (dir_model := self.directory_db.get_directory("Test_2", 1))

        assert dir_model.name == "Test_2"
        dir_model = self.directory_db.get_directory("Test_3", None)
        assert not dir_model

    def test_delete_directory(self):
        self.directory_db.create_table()
        self.directory_db.create_directory("Test", None)

        assert (dir_model := self.directory_db.delete_directory("Test", None))
        assert dir_model.name == "Test"

        with self.assertRaises(AssertionError) as e:
            self.directory_db.delete_directory("Test", None)
        assert e.exception.args[0] == "Directory does not exist"

    def test_find_children_directories(self):
        self.directory_db.create_table()
        self.directory_db.create_directory("Test", None)
        self.directory_db.create_directory("Test_2", 1)
        self.directory_db.create_directory("Test_3", 1)
        self.directory_db.create_directory("Test_4", 2)
        self.directory_db.create_directory("Test_5", 2)
        self.directory_db.create_directory("Test_6", 2)

        children_directories = self.directory_db.find_children_directories(1)
        assert len(children_directories) == 2
        children_directories = self.directory_db.find_children_directories(2)
        assert len(children_directories) == 3

    def test_update_directory_parent(self):
        self.directory_db.create_table()
        self.directory_db.create_directory("Test", None)
        self.directory_db.create_directory("Test_2", 1)
        self.directory_db.create_directory("Test_3", 1)
        self.directory_db.create_directory("Test_4", 2)

        self.directory_db.update_directory_parent("Test_4", 2, 1)

        assert (dir_model := self.directory_db.get_directory("Test_4", 1))
        assert dir_model.name == "Test_4"
        assert dir_model.parent == 1

    def test_find_root_directories(self):
        self.directory_db.create_table()
        self.directory_db.create_directory("Test", None)
        self.directory_db.create_directory("Test_2", 1)
        self.directory_db.create_directory("Test_3", None)

        assert (dir_models := self.directory_db.find_root_directories())
        assert len(dir_models) == 2


class DtFunctionalityTest(unittest.TestCase):
    def setUp(self):
        self.db_name = "test_directory_tree.db"
        os.environ["PYTEST_DIRECTORY_TREE"] = "True"
        self.directory_tree = DirectoryTree()

    def tearDown(self):
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

    def __create_tree__(self):
        self.directory_tree.create_directory("Test")
        self.directory_tree.create_directory("Test/Test_5")
        self.directory_tree.create_directory("Test/Test_2")
        self.directory_tree.create_directory("Test/Test_2/Test_3")
        self.directory_tree.create_directory("Test/Test_2/Test_4")

    @unittest.mock.patch('sys.stdout', new_callable=StringIO)
    def test_create_directory(self, mock_stdout):
        self.directory_tree.create_directory("Test")
        assert (dir_model := self.directory_tree.database.get_directory("Test", None))
        assert dir_model.name == "Test"

        self.directory_tree.create_directory("Test/Test_2")
        assert (dir_model := self.directory_tree.database.get_directory("Test_2", 1))
        assert dir_model.name == "Test_2"
        assert dir_model.parent == 1

        self.directory_tree.create_directory("Test")
        assert 'Directory Test already exists' in mock_stdout.getvalue()

        self.directory_tree.create_directory("Test/random/Test_2")
        assert 'random does not exist' in mock_stdout.getvalue()

    @unittest.mock.patch('sys.stdout', new_callable=StringIO)
    def test_list_directory(self, mock_stdout):
        self.__create_tree__()

        self.directory_tree.list_directories()
        list_result = mock_stdout.getvalue().strip().split("LIST")[-1]
        expected_value = """
Test
  Test_2
    Test_3
    Test_4
  Test_5"""
        assert list_result == expected_value

    @unittest.mock.patch('sys.stdout', new_callable=StringIO)
    def test_delete_directory(self, mock_stdout):
        self.__create_tree__()

        self.directory_tree.delete_directory("Test/Test_2/Test_4")
        self.directory_tree.list_directories()
        list_result = mock_stdout.getvalue().strip().split("LIST")[-1]
        expected_value = """
Test
  Test_2
    Test_3
  Test_5"""
        assert list_result == expected_value

        self.directory_tree.delete_directory("Test_6")
        assert "Cannot delete Test_6 - Directory does not exist" in mock_stdout.getvalue()

        self.directory_tree.delete_directory("Test/Test_2")
        self.directory_tree.list_directories()

        list_result = mock_stdout.getvalue().strip().split("LIST")[-1]
        expected_value = """
Test
  Test_5"""
        assert list_result == expected_value

    @unittest.mock.patch('sys.stdout', new_callable=StringIO)
    def test_move_directory(self, mock_stdout):
        self.__create_tree__()
        self.directory_tree.list_directories()
        list_result = mock_stdout.getvalue().strip().split("LIST")[-1]
        expected_value = """
Test
  Test_2
    Test_3
    Test_4
  Test_5"""
        assert list_result == expected_value

        self.directory_tree.move_directory("Test/Test_2/Test_3", "Test")

        self.directory_tree.list_directories()
        list_result = mock_stdout.getvalue().strip().split("LIST")[-1]
        expected_value = """
Test
  Test_2
    Test_4
  Test_3
  Test_5"""
        assert list_result == expected_value

        self.directory_tree.move_directory("Test/Test_2/Test_3", "Test_1")
        assert "Cannot move Test/Test_2/Test_3 - Test_1 does not exist" in mock_stdout.getvalue()



if __name__ == '__main__':
    unittest.main()
