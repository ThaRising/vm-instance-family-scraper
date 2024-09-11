import logging
import signal
import time
import typing as t
import unittest
from pathlib import Path

from src import constants
from src.documents import DocumentDescriptor
from src.repository import DocsSourceRepository

TEST_SUITES: t.Dict[str, t.List[t.Type[unittest.TestCase]]] = {}


def tag(name: str):
    def wrapper(cls):
        TEST_SUITES.setdefault(name, [])
        TEST_SUITES[name].append(cls)
        return cls

    return wrapper


class BaseTestCase(unittest.TestCase):
    repository: t.ClassVar[DocsSourceRepository]
    logger: t.ClassVar[logging.Logger]

    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = DocsSourceRepository(
            constants.MS_REPOSITORY_URL,
            constants.MS_REPOSITORY_NAME,
            constants.MS_REPOSITORY_PATH,
        )
        cls.logger = logging.getLogger(__name__)

    def setUp(self) -> None:
        self.cls = DocumentDescriptor
        current_path = Path(__file__).parent
        clone_basepath = current_path / "data"
        self.documents_path = clone_basepath / "documents"
        if not (clone_basepath / self.repository.repo_name).exists():
            self.repository_workdir = self.repository.clone_repository(clone_basepath)
        else:
            self.logger.debug("Repo already exists, not cloning again")
            self.repository.setup_repository(clone_basepath / self.repository.repo_name)
            self.repository_workdir = (
                clone_basepath
                / self.repository.repo_name
                / self.repository.repo_relative_path
            )
            self.repository.repo_workdir_abs_path = self.repository_workdir

    def tearDown(self):
        if hasattr(self._outcome, "errors"):
            # Python 3.4 - 3.10  (These two methods have no side effects)
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, self._outcome.errors)
        else:
            # Python 3.11+
            result = self._outcome.result
        ok = all(test != self for test, text in result.errors + result.failures)

        # Demo output:  (print short info immediately - not important)
        if ok:
            print("\nOK: %s" % (self.id(),))
        for typ, errors in (("ERROR", result.errors), ("FAIL", result.failures)):
            for test, text in errors:
                if test.id() == self.id():
                    #  the full traceback is in the variable `text`
                    msg = [x for x in text.split("\n")[1:] if not x.startswith(" ")][0]
                    print("\n\n%s: %s\n     %s" % (typ, self.id(), msg))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.repository.cleanup()
        signal.alarm(1)
        time.sleep(1)
