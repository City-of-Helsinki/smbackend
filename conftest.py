from hypothesis import settings, Verbosity, HealthCheck

settings.register_profile("ci", settings(
    max_examples=1000,
    suppress_health_check=[HealthCheck.too_slow]))
settings.register_profile("dev", settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow]))
settings.register_profile("debug", settings(max_examples=10, verbosity=Verbosity.verbose, suppress_health_check=[HealthCheck.too_slow]))


def pytest_addoption(parser):
    parser.addoption("--data-integrity", action="store_true",
                     help="run data integrity tests")
