import os

os.environ["LOG_LEVEL"] = "debug"
from .test_azure_types import *
from .test_multi_series_parser import *
from .test_repository import *
from .test_series_parsers import *
