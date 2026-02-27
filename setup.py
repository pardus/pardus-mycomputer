#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess

from setuptools import setup, find_packages


def create_mo_files():
    podir = "po"
    mo = []
    for po in os.listdir(podir):
        if po.endswith(".po"):
            lang = po[:-3]
            local_dir = os.path.join(podir, lang, "LC_MESSAGES")
            os.makedirs(local_dir, exist_ok=True)
            mo_file = os.path.join(local_dir, "pardus-mycomputer.mo")

            subprocess.call(["msgfmt", os.path.join(podir, po), "-o", mo_file])
            mo.append((f"/usr/share/locale/{lang}/LC_MESSAGES", [mo_file]))
    return mo


changelog = "debian/changelog"
if os.path.exists(changelog):
    head = open(changelog).readline()
    try:
        version = head.split("(")[1].split(")")[0]
    except:
        print("debian/changelog format is wrong for get version")
        version = ""
    f = open("src/__version__", "w")
    f.write(version)
    f.close()

data_files = [
                 ("/usr/share/applications/",
                  ["tr.org.pardus.mycomputer.desktop"]),
                 ("/usr/share/pardus/pardus-mycomputer/",
                  ["pardus-mycomputer.svg"]),
                 ("/usr/share/pardus/pardus-mycomputer/src", [
                     "src/Main.py",
                     "src/MainWindow.py",
                     "src/DiskManager.py",
                     "src/Unmount.py",
                     "src/UserSettings.py",
                     "src/__version__"
                 ]),
                 ("/usr/share/pardus/pardus-mycomputer/ui",
                  ["ui/MainWindow.glade"]),
                 ("/usr/share/pardus/pardus-mycomputer/autostart/",
                  ["autostart/pardus-mycomputer-add-to-desktop"]),
                 ("/usr/share/pardus/pardus-mycomputer/css/",
                  ["css/style.css"]),
                 ("/etc/xdg/autostart",
                  ["autostart/pardus-mycomputer-add-to-desktop.desktop"]),
                 ("/usr/bin/",
                  ["pardus-mycomputer"]),
                 ("/usr/share/icons/hicolor/scalable/apps/", [
                     "pardus-mycomputer.svg",
                     "pardus-mycomputer-emblem-pardus-symbolic.svg"
                 ])
             ] + create_mo_files()

setup(
    name="pardus-mycomputer",
    version="0.1.0",
    packages=find_packages(),
    scripts=["pardus-mycomputer"],
    install_requires=["PyGObject"],
    data_files=data_files,
    author="Pardus Altyapı",
    author_email="dev@pardus.org.tr",
    description="My Computer, UI for information and management of disks on your computer.",
    license="GPLv3",
    keywords="",
    url="https://www.pardus.org.tr",
)
