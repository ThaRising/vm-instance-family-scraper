import os
import sys
import unittest

if __name__ == "__main__":
    test_suites = sys.argv[1:]
    os.environ["LOG_LEVEL"] = "debug"
    if not test_suites:
        from .shared import TEST_SUITES

        test_suites = list(TEST_SUITES.keys())
    assert test_suites
    for test_suite in test_suites:
        from .shared import TEST_SUITES

        test_cases = TEST_SUITES[test_suite]
        suite = unittest.TestSuite()
        suite.addTests(
            [
                unittest.defaultTestLoader.loadTestsFromTestCase(case)
                for case in test_cases
            ]
        )
        unittest.TextTestRunner().run(suite)
