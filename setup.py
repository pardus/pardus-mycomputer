#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os, subprocess


def create_mo_files():
    podir = "po"
    mo = []
    for po in os.listdir(podir):
        if po.endswith(".po"):
            os.makedirs("{}/{}/LC_MESSAGES".format(podir, po.split(".po")[0]), exist_ok=True)
            mo_file = "{}/{}/LC_MESSAGES/{}".format(podir, po.split(".po")[0], "pardus-mycomputer.mo")
            msgfmt_cmd = 'msgfmt {} -o {}'.format(podir + "/" + po, mo_file)
            subprocess.call(msgfmt_cmd, shell=True)
            mo.append(("/usr/share/locale/" + po.split(".po")[0] + "/LC_MESSAGES",
                       ["po/" + po.split(".po")[0] + "/LC_MESSAGES/pardus-mycomputer.mo"]))
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
    ("/usr/share/applications/", ["tr.org.pardus.mycomputer.desktop"]),
    ("/usr/share/pardus/pardus-mycomputer/", ["pardus-mycomputer.svg"]),
    ("/usr/share/pardus/pardus-mycomputer/src", [
        "src/Main.py",
        "src/MainWindow.py",
        "src/DiskManager.py",
        "src/Unmount.py",
        "src/UserSettings.py",
        "src/__version__"
    ]),
    ("/usr/share/pardus/pardus-mycomputer/ui", ["ui/MainWindow.glade"]),
    ("/usr/share/pardus/pardus-mycomputer/autostart/", ["autostart/pardus-mycomputer-add-to-desktop"]),
    ("/usr/share/pardus/pardus-mycomputer/css/", ["css/style.css"]),
    ("/etc/xdg/autostart", ["autostart/pardus-mycomputer-add-to-desktop.desktop"]),
    ("/usr/bin/", ["pardus-mycomputer"]),
    ("/usr/share/icons/hicolor/scalable/apps/", [
        "pardus-mycomputer.svg",
        "pardus-mycomputer-emblem-pardus-symbolic.svg"
    ])
] + create_mo_files()

setup(
    name="pardus-mycomputer",
    version="0.6.3",
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
