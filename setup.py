import pathlib

from setuptools import find_packages, setup

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name='jira_export',
    version='0.0.1',
    description='Small program for exporting issues from Jira to pdf or html',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lukaszmach/jira-export",
    author='Łukasz Machowski',
    author_email='macherek@o2.pl',
    packages=find_packages(),
    install_requires=[
        'configparser',
        'jira',
        'pdfkit',
        'pypandoc-binary',
    ],
)
