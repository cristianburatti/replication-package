class MineException(Exception):
    """
    Base class for all exceptions in this module.
    """

    def __init__(self, cause):
        self.cause = cause


class MissingTagException(MineException):
    """
    Raised if it was not possible to identify a tag/snapshot inside the cloned repository
    """

    def __init__(self):
        self.cause = 'missing_tag'


class MissingJUnitException(MineException):
    """
    Raised if the project does not contain the JUnit dependency
    """

    def __init__(self):
        self.cause = 'missing_junit'


class NonBuildableException(MineException):
    """
    Raised if the project failed to build
    """

    def __init__(self):
        self.cause = 'non_buildable'


class TimeoutException(MineException):
    """
    Raised if building the project took too long (default: 90 minutes)
    """

    def __init__(self):
        self.cause = 'timeout'


class NoReportException(MineException):
    """
    Raised if the JaCoCo report was missing after the execution of the tests
    """

    def __init__(self):
        self.cause = 'no_report'


class InvalidProjectException(MineException):
    """
    Raised if the project is neither a Maven nor a Gradle project
    """

    def __init__(self):
        self.cause = 'invalid_project'
