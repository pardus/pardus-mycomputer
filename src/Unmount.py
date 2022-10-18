#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import subprocess
import sys


def main():
    def unmount(path):
        p1 = subprocess.Popen(["/usr/bin/sync", "-f", path])
        p1.wait()
        # subprocess.call(["/usr/bin/umount", path])

    if len(sys.argv) > 1:
        if sys.argv[1] == "unmount":
            unmount(sys.argv[2])
        else:
            print("unknown argument error")
    else:
        print("no argument passed")


if __name__ == "__main__":
    main()
