
from directory_tree import DirectoryTree


if __name__ == '__main__':
    directory_tree = DirectoryTree()
    with open('input.txt', 'r') as f:
        for line in f.readlines():
            arguments = line.strip().split()
            action, params = arguments[0], arguments[1:]
            directory_tree.handlers[action](*params)
    directory_tree.close()



