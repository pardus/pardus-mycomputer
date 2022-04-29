#!/usr/bin/env python3
from setuptools import setup, find_packages
from shutil import copyfile

data_files = [
    ("/usr/share/applications/", ["tr.org.pardus.mycomputer.desktop"]),
    ("/usr/share/locale/tr/LC_MESSAGES/", ["translations/tr/LC_MESSAGES/pardus-mycomputer.mo"]),
    ("/usr/share/pardus/pardus-mycomputer/", ["pardus-mycomputer.svg"]),
    ("/usr/share/pardus/pardus-mycomputer/src", ["src/pardus-mycomputer", "src/MainWindow.py", "src/DiskManager.py"]),
    ("/usr/share/pardus/pardus-mycomputer/ui", ["ui/MainWindow.glade"]),
    ("/usr/bin/", ["pardus-mycomputer"]),
    ("/usr/share/icons/hicolor/scalable/apps/", ["pardus-mycomputer.svg"])
]

setup(
    name="pardus-mycomputer",
    version="0.1.0",
    packages=find_packages(),
    scripts=["pardus-mycomputer"],
    install_requires=["PyGObject"],
    data_files=data_files,
    author="Pardus Altyapı",
    author_email="altyapi@pardus.org.tr",
    description="My Computer, shows general information about your computer.",
    license="GPLv3",
    keywords="",
    url="https://www.pardus.org.tr",
)
