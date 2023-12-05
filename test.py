from io import StringIO
import unittest.mock
import os
from hashlib import md5

from directory_tree import DirectoryTree


class Test(unittest.TestCase):
    def setUp(self):
        self.db_file = "directory_tree.db"

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

    def tearDown(self):
        if os.path.exists(self.db_file):
            os.remove(self.db_file)

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


if __name__ == '__main__':
    unittest.main()
