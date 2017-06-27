import pytest


def pytest_addoption(parser):
    parser.addoption("--data-integrity", action="store_true",
                     help="run data integrity tests")
