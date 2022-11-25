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
        self.config_remember_window_size = None
        self.config_closeapp_pardus = None
        self.config_closeapp_hdd = None
        self.config_closeapp_usb = None
        self.config_autorefresh = None
        self.config_autorefresh_time = None

        self.default_remember_window_size = [True, False, 700, 550]
        self.default_closeapp_pardus = False
        self.default_closeapp_hdd = False
        self.default_closeapp_usb = False
        self.default_autorefresh = False
        self.default_autorefresh_time = 1.5


    def createDefaultConfig(self, force=False):
        self.config['MAIN'] = {
            'RememberWindowSize': 'yes, no, 700, 550',
            'CloseAppPardus': 'no',
            'CloseAppHDD': 'no',
            'CloseAppUSB': 'no',
            'AutoRefresh': 'no',
            'AutoRefreshTime': 1.5
        }

        if not Path.is_file(self.user_config_file) or force:
            if self.createDir(self.user_config_dir):
                with open(self.user_config_file, "w") as cf:
                    self.config.write(cf)

    def readConfig(self):
        try:
            self.config.read(self.user_config_file)

            # "config_remember_window_size" setting is a list.
            # It is processed by using the following code.
            remember_window_size = self.config.get('MAIN', 'RememberWindowSize').strip("[]").split(", ")
            remember_window_size_converted = []
            for i, value in enumerate(remember_window_size):
                if i == 0 or i == 1:
                    if value == "True":
                        remember_window_size_converted.append(True)
                    else:
                        remember_window_size_converted.append(False)
                if i == 2 or i == 3:
                    remember_window_size_converted.append(int(value))

            self.config_remember_window_size = remember_window_size_converted
            self.config_closeapp_pardus = self.config.getboolean('MAIN', 'CloseAppPardus')
            self.config_closeapp_hdd = self.config.getboolean('MAIN', 'CloseAppHDD')
            self.config_closeapp_usb = self.config.getboolean('MAIN', 'CloseAppUSB')
            self.config_autorefresh = self.config.getboolean('MAIN', 'AutoRefresh')
            self.config_autorefresh_time = self.config.getfloat('MAIN', 'AutoRefreshTime')

        except Exception as e:
            print("{}".format(e))
            print("user config read error ! Trying create defaults")
            # if not read; try to create defaults
            self.config_remember_window_size = self.default_remember_window_size
            self.config_closeapp_pardus = self.default_closeapp_pardus
            self.config_closeapp_hdd = self.default_closeapp_hdd
            self.config_closeapp_usb = self.default_closeapp_usb
            self.config_autorefresh = self.default_autorefresh
            self.config_autorefresh_time = self.default_autorefresh_time
            try:
                self.createDefaultConfig(force=True)
            except Exception as e:
                print("self.createDefaultConfig(force=True) : {}".format(e))

    def writeConfig(self, rememberwindowsize, closeapppardus, closeapphdd, closeappusb, autorefresh, autorefreshtime):
        self.config['MAIN'] = {
            'RememberWindowSize': rememberwindowsize,
            'CloseAppPardus': closeapppardus,
            'CloseAppHDD': closeapphdd,
            'CloseAppUSB': closeappusb,
            'AutoRefresh': autorefresh,
            'AutoRefreshTime': autorefreshtime
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
