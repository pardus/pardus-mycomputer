#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 28 13:13:13 2022

@author: fatih
"""
import configparser
import json
import locale
import os.path
import subprocess
from locale import gettext as _
from pathlib import Path

from gi.repository import GLib

# Translation Constants:
APPNAME = "pardus-mycomputer"
TRANSLATIONS_PATH = "/usr/share/locale"
# SYSTEM_LANGUAGE = os.environ.get("LANG")

# Translation functions:
locale.bindtextdomain(APPNAME, TRANSLATIONS_PATH)
locale.textdomain(APPNAME)


# locale.setlocale(locale.LC_ALL, SYSTEM_LANGUAGE)

class UserSettings(object):
    def __init__(self):
        self.user_config_dir = Path.joinpath(Path(GLib.get_user_config_dir()), Path("pardus-mycomputer"))
        if not Path(self.user_config_dir).exists():
            self.user_config_dir = Path.joinpath(Path(GLib.get_user_config_dir()), Path("pardus/pardus-mycomputer"))
        self.user_config_file = Path.joinpath(self.user_config_dir, Path("settings.ini"))
        self.user_recent_servers_file = Path.joinpath(self.user_config_dir, Path("servers-recent"))
        self.user_saved_servers_file = Path.joinpath(self.user_config_dir, Path("servers-saved"))
        self.user_saved_places_file = Path.joinpath(self.user_config_dir, Path("places-saved"))

        self.desktop_file = "tr.org.pardus.mycomputer.desktop"

        self.config = configparser.ConfigParser(strict=False)

        # main configs
        self.config_closeapp_main = None
        self.config_closeapp_hdd = None
        self.config_closeapp_usb = None
        self.config_autorefresh = None
        self.config_autorefresh_time = None
        self.config_hide_places = None
        self.config_hide_desktopicon = None

        # window configs
        self.config_window_remember_size = None
        self.config_window_fullscreen = None
        self.config_window_width = None
        self.config_window_height = None
        self.config_window_use_darktheme = None

        # main defaults
        self.default_closeapp_main = False
        self.default_closeapp_hdd = False
        self.default_closeapp_usb = False
        self.default_autorefresh = False
        self.default_autorefresh_time = 1.5
        self.default_hide_places = False
        self.default_hide_desktopicon = False

        # window defaults
        self.default_window_remember_size = False
        self.default_window_fullscreen = False
        self.default_window_width = 700
        self.default_window_height = 550
        self.default_window_use_darktheme = False

    def createDefaultConfig(self, force=False):
        self.config['MAIN'] = {
            'CloseAppMain': self.default_closeapp_main,
            'CloseAppHDD': self.default_closeapp_hdd,
            'CloseAppUSB': self.default_closeapp_usb,
            'AutoRefresh': self.default_autorefresh,
            'AutoRefreshTime': self.default_autorefresh_time,
            'HidePlaces': self.default_hide_places,
            'HideDesktopIcon': self.default_hide_desktopicon
        }

        self.config['WINDOW'] = {
            'RememberWindowSize': self.default_window_remember_size,
            'FullScreen': self.default_window_fullscreen,
            'Width': self.default_window_width,
            'Height': self.default_window_height,
            'UseDarkTheme': self.default_window_use_darktheme
        }

        if not Path.is_file(self.user_config_file) or force:
            if self.createDir(self.user_config_dir):
                with open(self.user_config_file, "w") as cf:
                    self.config.write(cf)

    def readConfig(self):
        try:
            self.config.read(self.user_config_file)
            self.config_closeapp_main = self.config.getboolean('MAIN', 'CloseAppMain')
            self.config_closeapp_hdd = self.config.getboolean('MAIN', 'CloseAppHDD')
            self.config_closeapp_usb = self.config.getboolean('MAIN', 'CloseAppUSB')
            self.config_autorefresh = self.config.getboolean('MAIN', 'AutoRefresh')
            self.config_autorefresh_time = self.config.getfloat('MAIN', 'AutoRefreshTime')
            self.config_hide_places = self.config.getboolean('MAIN', 'HidePlaces')
            self.config_hide_desktopicon = self.config.getboolean('MAIN', 'HideDesktopIcon')
            self.config_window_remember_size = self.config.getboolean('WINDOW', 'RememberWindowSize')
            self.config_window_fullscreen = self.config.getboolean('WINDOW', 'FullScreen')
            self.config_window_width = self.config.getint('WINDOW', 'Width')
            self.config_window_height = self.config.getint('WINDOW', 'Height')
            self.config_window_use_darktheme = self.config.getboolean('WINDOW', 'UseDarkTheme')

        except Exception as e:
            print("{}".format(e))
            print("user config read error ! Trying create defaults")
            # if not read; try to create defaults
            self.config_closeapp_main = self.default_closeapp_main
            self.config_closeapp_hdd = self.default_closeapp_hdd
            self.config_closeapp_usb = self.default_closeapp_usb
            self.config_autorefresh = self.default_autorefresh
            self.config_autorefresh_time = self.default_autorefresh_time
            self.config_hide_places = self.default_hide_places
            self.config_hide_desktopicon = self.default_hide_desktopicon
            self.config_window_remember_size = self.default_window_remember_size
            self.config_window_fullscreen = self.default_window_fullscreen
            self.config_window_width = self.default_window_width
            self.config_window_height = self.default_window_height
            self.config_window_use_darktheme = self.default_window_use_darktheme
            try:
                self.createDefaultConfig(force=True)
            except Exception as e:
                print("self.createDefaultConfig(force=True) : {}".format(e))

    def writeConfig(self, closeappmain="", closeapphdd="", closeappusb="", autorefresh="", autorefreshtime="",
                    hideplaces="", hidedesktopicon="", rememberwindowsize="", fullscreen="",
                    width="", height="", usedarktheme=""):
        if closeappmain == "":
            closeappmain = self.config_closeapp_main
        if closeapphdd == "":
            closeapphdd = self.config_closeapp_hdd
        if closeappusb == "":
            closeappusb = self.config_closeapp_usb
        if autorefresh == "":
            autorefresh = self.config_autorefresh
        if autorefreshtime == "":
            autorefreshtime = self.config_autorefresh_time
        if hidedesktopicon == "":
            hidedesktopicon = self.config_hide_desktopicon
        if hideplaces == "":
            hideplaces = self.config_hide_places
        if rememberwindowsize == "":
            rememberwindowsize = self.config_window_remember_size
        if fullscreen == "":
            fullscreen = self.config_window_fullscreen
        if width == "":
            width = self.config_window_width
        if height == "":
            height = self.config_window_height
        if usedarktheme == "":
            usedarktheme = self.config_window_use_darktheme

        self.config['MAIN'] = {
            'CloseAppMain': closeappmain,
            'CloseAppHDD': closeapphdd,
            'CloseAppUSB': closeappusb,
            'AutoRefresh': autorefresh,
            'AutoRefreshTime': autorefreshtime,
            'HidePlaces': hideplaces,
            'HideDesktopIcon': hidedesktopicon
        }

        self.config['WINDOW'] = {
            'RememberWindowSize': rememberwindowsize,
            'FullScreen': fullscreen,
            'Width': width,
            'Height': height,
            'UseDarkTheme': usedarktheme
        }

        if self.createDir(self.user_config_dir):
            with open(self.user_config_file, "w") as cf:
                self.config.write(cf)
                return True
        return False

    def createDir(self, dir):
        try:
            Path(dir).mkdir(parents=True, exist_ok=True)
            return True
        except:
            print("{} : {}".format("mkdir error", dir))
            return False

    def addRecentServer(self, uri, name):
        server = "{} {}".format(uri, name).strip()

        def add():
            with open(self.user_recent_servers_file, "r+") as sf:
                for line in sf:
                    if server == line.strip("\n").strip():
                        break
                else:
                    sf.write("{}\n".format(server))

        if not Path.is_file(self.user_recent_servers_file):
            self.createDir(self.user_config_dir)
            self.user_recent_servers_file.touch(exist_ok=True)
            add()
        else:
            add()

    def removeRecentServer(self, server):
        if Path.is_file(self.user_recent_servers_file):
            with open(self.user_recent_servers_file, "r") as f:
                lines = f.readlines()
            with open(self.user_recent_servers_file, "w") as f:
                for line in lines:
                    if line.strip("\n").strip() != server:
                        f.write(line)

    def getRecentServer(self):
        servers = []
        if Path.is_file(self.user_recent_servers_file):
            with open(self.user_recent_servers_file, "r") as servf:
                for line in servf.readlines():
                    if line.strip("\n").strip() != "":
                        servers.append(line.strip("\n").strip())
        return servers

    def addSavedServer(self, uri, name):
        server = "{} {}".format(uri, name).strip()

        def add():
            with open(self.user_saved_servers_file, "r+") as sf:
                for line in sf:
                    if server == line.strip("\n").strip():
                        break
                else:
                    sf.write("{}\n".format(server))

        if not Path.is_file(self.user_saved_servers_file):
            self.createDir(self.user_config_dir)
            self.user_saved_servers_file.touch(exist_ok=True)
            add()
        else:
            add()

    def removeSavedServer(self, server):
        if Path.is_file(self.user_saved_servers_file):
            with open(self.user_saved_servers_file, "r") as f:
                lines = f.readlines()
            with open(self.user_saved_servers_file, "w") as f:
                for line in lines:
                    if line.strip("\n").strip() != server:
                        f.write(line)

    def getSavedServer(self):
        servers = []
        if Path.is_file(self.user_saved_servers_file):
            with open(self.user_saved_servers_file, "r") as servf:
                for line in servf.readlines():
                    if line.strip("\n").strip() != "":
                        server = line.strip("\n").strip()
                        if len(server.split(" ")) > 1:
                            uri, name = server.split(" ", 1)
                        else:
                            uri = server
                            name = ""
                        servers.append({"uri": uri, "name": name})
        return servers

    def getSavedPlaces(self):
        # sample saved place
        # {"path": "/home/fatih/Desktop/Office Folder", "name": "Office Folder", "icon": "folder-symbolic"}
        places = []
        if Path.is_file(self.user_saved_places_file):
            try:
                with open(self.user_saved_places_file, "r") as servp:
                    for line in servp.readlines():
                        try:
                            place = line.strip("\n").strip()
                            if not place.startswith("#") and place != "":
                                places.append(json.loads(place))
                        except Exception as e:
                            print("getSavedPlaces: {}".format(e))
                            pass
            except Exception as e:
                print("getSavedPlaces: {}".format(e))
        else:
            self.createDir(self.user_config_dir)
            self.user_saved_places_file.touch(exist_ok=True)
            samplefile = open(self.user_saved_places_file, "w")
            samplefile.writelines(_("# example line is as below") + "\n")
            samplefile.writelines(_("# note: remove the hash to make it appear") + "\n")
            samplefile.writelines(
                '#{"path": "' + GLib.get_home_dir() + '", "name": "' + _(
                    "Home") + '", "icon": "folder-symbolic"}' + "\n")
            samplefile.flush()
            samplefile.close()

        return places

    def addSavedPlaces(self, path, name, icon):
        place = '{"path": "' + path + '", "name": "' + name + '", "icon": "' + icon + '"}'

        def add():
            with open(self.user_saved_places_file, "r+") as savep:
                for line in savep:
                    if not line.startswith("#"):
                        try:
                            linejson = json.loads(line.strip("\n").strip())
                            if linejson["path"] == path:
                                print("{} already in places".format(path))
                                return False
                        except Exception as e:
                            print("addSavedPlaces: {}".format(e))
                            pass
                savep.writelines("{}\n".format(place))
                return True

        if not Path.is_file(self.user_saved_places_file):
            self.createDir(self.user_config_dir)
            self.user_saved_places_file.touch(exist_ok=True)
            return add()
        else:
            return add()

    def removeSavedPlaces(self, place):
        if Path.is_file(self.user_saved_places_file):
            with open(self.user_saved_places_file, "r") as f:
                lines = f.readlines()
            with open(self.user_saved_places_file, "w") as f:
                for line in lines:
                    if line.strip("\n").strip() != place:
                        f.write(line)

    def updateSavedPlaces(self, old_place, path, name, icon):
        if Path.is_file(self.user_saved_places_file):
            with open(self.user_saved_places_file, "r") as f:
                lines = f.readlines()
            with open(self.user_saved_places_file, "w") as f:
                for line in lines:
                    if line.strip("\n").strip() != old_place:
                        # write other lines again to file
                        f.write(line)
                    else:
                        # edit line to be changed
                        place = '{"path": "' + path + '", "name": "' + name + '", "icon": "' + icon + '"}'
                        f.write("{}\n".format(place))

    def set_hide_desktopicon(self, state):
        if state:
            subprocess.call(["/usr/share/pardus/pardus-mycomputer/autostart/pardus-mycomputer-add-to-desktop"])
            if os.path.exists(os.path.join(GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DESKTOP),
                                           self.desktop_file)):
                os.remove(os.path.join(GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DESKTOP),
                                       self.desktop_file))
        else:
            if Path.joinpath(self.user_config_dir, Path("desktop")).exists():
                Path.joinpath(self.user_config_dir, Path("desktop")).unlink(missing_ok=True)

            subprocess.call(["/usr/share/pardus/pardus-mycomputer/autostart/pardus-mycomputer-add-to-desktop"])
