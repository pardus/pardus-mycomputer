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
        self.config_closeapp_directories = None
        self.config_autorefresh = None
        self.config_autorefresh_time = None

        self.default_closeapp_directories = False
        self.default_autorefresh = False
        self.default_autorefresh_time = 1.5


    def createDefaultConfig(self, force=False):
        self.config['MAIN'] = {
            'CloseAppDirectories': 'no',
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
            self.config_closeapp_directories = self.config.getboolean('MAIN', 'CloseAppDirectories')
            self.config_autorefresh = self.config.getboolean('MAIN', 'AutoRefresh')
            self.config_autorefresh_time = self.config.getfloat('MAIN', 'AutoRefreshTime')

        except Exception as e:
            print("{}".format(e))
            print("user config read error ! Trying create defaults")
            # if not read; try to create defaults
            self.config_closeapp_directories = self.default_closeapp_directories
            self.config_autorefresh = self.default_autorefresh
            self.config_autorefresh_time = self.default_autorefresh_time
            try:
                self.createDefaultConfig(force=True)
            except Exception as e:
                print("self.createDefaultConfig(force=True) : {}".format(e))

    def writeConfig(self, closeappdirectories, autorefresh, autorefreshtime):
        self.config['MAIN'] = {
            'CloseAppDirectories': closeappdirectories,
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
