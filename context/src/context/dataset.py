from enum import Enum


class Dataset(Enum):
    complete = 'complete'
    javadoc = 'javadoc'

    def __str__(self):
        return self.value

    def __eq__(self, other):
        return self.value == other.value
