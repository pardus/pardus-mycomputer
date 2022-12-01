#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 28 13:13:13 2022

@author: fatih
"""
from pathlib import Path
import configparser


class UserSettings(object):
    def __init__(self):

        self.user_home = Path.home()
        self.user_config_dir = Path.joinpath(self.user_home, Path(".config/pardus-mycomputer"))
        self.user_config_file = Path.joinpath(self.user_config_dir, Path("settings.ini"))
        self.user_recent_servers_file = Path.joinpath(self.user_config_dir, Path("servers-recent"))
        self.user_saved_servers_file = Path.joinpath(self.user_config_dir, Path("servers-saved"))

        self.config = configparser.ConfigParser(strict=False)

        # main configs
        self.config_closeapp_main = None
        self.config_closeapp_hdd = None
        self.config_closeapp_usb = None
        self.config_autorefresh = None
        self.config_autorefresh_time = None

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
            'AutoRefreshTime': self.default_autorefresh_time
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
                    rememberwindowsize="", fullscreen="", width="", height="", usedarktheme=""):
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
            'AutoRefreshTime': autorefreshtime
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
            with open(self.user_recent_servers_file, "a+") as sf:
                for line in sf:
                    if server == line:
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
            with open(self.user_saved_servers_file, "a+") as sf:
                for line in sf:
                    if server == line:
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
