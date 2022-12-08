from setuptools import find_packages, setup

setup(
    name="smbackend",
    version="221208",
    license="AGPLv3",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        p
        for p in open("requirements.txt", "rt").readlines()
        if p and not p.startswith("#")
    ],
    zip_safe=False,
)
