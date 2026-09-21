#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 22 00:13:34 2026

@author: fatih
"""

import os
import stat
import sys
import tempfile


FSTAB_PATH = "/etc/fstab"


def write_fstab(content):
    file_stat = os.stat(FSTAB_PATH)

    fd, temp_path = tempfile.mkstemp(
        dir="/etc",
        prefix=".fstab.",
        text=True,
    )

    try:
        os.fchmod(fd, stat.S_IMODE(file_stat.st_mode))
        os.fchown(fd, file_stat.st_uid, file_stat.st_gid)

        with os.fdopen(fd, "w") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_path, FSTAB_PATH)

    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


if __name__ == "__main__":
    write_fstab(sys.stdin.read())
