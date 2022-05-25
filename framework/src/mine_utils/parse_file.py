from mine_utils.mine_exceptions import MissingJUnitException
from xml.etree import ElementTree


def parse_mvn(pom_file):
    """
    Parse the pom file to ensure `junit` is in the dependencies
    :param pom_file: the path to the pom.xml file
    :raise MissingJUnitException: if the `junit` dependency is not found
    :return: the list of the dependencies found in the pom file
    """

    namespaces = {'xmlns': 'http://maven.apache.org/POM/4.0.0'}

    try:
        tree = ElementTree.parse(pom_file)
        root = tree.getroot()

        dependencies = root.findall(".//xmlns:dependency", namespaces=namespaces)
        dependencies = [d.find("xmlns:artifactId", namespaces=namespaces) for d in dependencies]
        dependencies = [d.text for d in dependencies if d is not None]
        for dependency in dependencies:
            if 'junit' in dependency:
                return dependencies

    except ElementTree.ParseError:
        pass

    raise MissingJUnitException()


def parse_gradle(gradle_file):
    """
    Parse the gradle file to ensure `junit` is in the dependencies
    :param gradle_file: the path to the gradle file
    :raise MissingJUnitException: if the `junit` dependency is not found
    """

    with open(gradle_file, 'r') as f:
        for line in f:
            if 'junit' in line:
                return

        raise MissingJUnitException()
