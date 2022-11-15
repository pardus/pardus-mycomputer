import os, subprocess

import gi
gi.require_version("Notify", "0.7")
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk, Notify, Gdk

import DiskManager

from UserSettings import UserSettings

import locale
from locale import gettext as _

# Translation Constants:
APPNAME = "pardus-mycomputer"
TRANSLATIONS_PATH = "/usr/share/locale"
# SYSTEM_LANGUAGE = os.environ.get("LANG")

# Translation functions:
locale.bindtextdomain(APPNAME, TRANSLATIONS_PATH)
locale.textdomain(APPNAME)
# locale.setlocale(locale.LC_ALL, SYSTEM_LANGUAGE)
        

class MainWindow:
    def __init__(self, application):
        # Gtk Builder
        self.builder = Gtk.Builder()

        # Translate things on glade:
        self.builder.set_translation_domain(APPNAME)

        # Import UI file:
        self.builder.add_from_file(os.path.dirname(os.path.abspath(__file__)) + "/../ui/MainWindow.glade")
        self.builder.connect_signals(self)

        # Window
        self.window = self.builder.get_object("window")
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_application(application)
        self.window.connect("destroy", self.onDestroy)

        # Set application:
        self.application = application

        # Global Definings
        self.defineComponents()
        self.defineVariables()

        # load user settings
        self.user_settings()

        # Add Disks to GUI
        self.addDisksToGUI()

        cssProvider = Gtk.CssProvider()
        cssProvider.load_from_path(os.path.dirname(os.path.abspath(__file__)) + "/../css/style.css")
        screen = Gdk.Screen.get_default()
        styleContext = Gtk.StyleContext()
        styleContext.add_provider_for_screen(screen, cssProvider,
                                             Gtk.STYLE_PROVIDER_PRIORITY_USER)

        # Copy desktop file to user's desktop
        self.add_to_desktop()

        # auto refresh control of disks
        self.autorefresh()

        # Show Screen:
        self.window.show_all()

    def defineComponents(self):
        def UI(str):
            return self.builder.get_object(str)

        # Home
        self.lbl_home_path = UI("lbl_home_path")
        self.lbl_home_size = UI("lbl_home_size")

        # Root
        self.pb_root_usage = UI("pb_root_usage")
        self.lbl_root_free = UI("lbl_root_free")
        self.lbl_root_total = UI("lbl_root_total")

        # Drives
        self.box_drives = UI("box_drives")
        # Removables
        self.box_removables = UI("box_removables")

        # Popover
        self.popover_volume = UI("popover_volume")
        self.popover_removable = UI("popover_removable")
        self.cb_mount_on_startup = UI("cb_mount_on_startup")

        # Detail Dialog
        self.dialog_disk_details = UI("dialog_disk_details")
        self.dlg_lbl_name = UI("dlg_lbl_name")
        self.dlg_lbl_model = UI("dlg_lbl_model")
        self.dlg_lbl_dev = UI("dlg_lbl_dev")
        self.dlg_lbl_mountpoint = UI("dlg_lbl_mountpoint")
        self.dlg_lbl_used_gb = UI("dlg_lbl_used_gb")
        self.dlg_lbl_free_gb = UI("dlg_lbl_free_gb")
        self.dlg_lbl_total_gb = UI("dlg_lbl_total_gb")
        self.dlg_lbl_filesystem_type = UI("dlg_lbl_filesystem_type")

        # Device Type Stack
        self.popover_dt_stack = UI("popover_dt_stack")

        # Buttons
        self.btn_unmount = UI("btn_unmount")
        self.btn_defaults = UI("btn_defaults")

        # Unmount progress Stack
        self.stack_unmount = UI("stack_unmount")

        # Main Stack
        self.stack_main = UI("stack_main")

        # Menu popover
        self.popover_menu = UI("popover_menu")

        # Settings switch buttons
        self.sw_closeapp_pardus = UI("sw_closeapp_pardus")
        self.sw_closeapp_hdd = UI("sw_closeapp_hdd")
        self.sw_closeapp_usb = UI("sw_closeapp_usb")
        self.sw_autorefresh = UI("sw_autorefresh")

        self.img_settings = UI("img_settings")

        # About dialog
        self.dialog_about = UI("dialog_about")
        self.dialog_about.set_program_name(_("Pardus My Computer"))
        # Set version
        # If not getted from __version__ file then accept version in MainWindow.glade file
        try:
            version = open(os.path.dirname(os.path.abspath(__file__)) + "/__version__").readline()
            self.dialog_about.set_version(version)
        except:
            pass

    def defineVariables(self):
        self.mount_operation = Gio.MountOperation.new()
        self.selected_volume = None
        self.selected_volume_info = None
        self.actioned_volume = None
        self.autorefresh_glibid = None
        self.mount_paths = []

        # VolumeMonitor
        self.vm = Gio.VolumeMonitor.get()
        self.vm.connect('mount-added', self.on_mount_added)
        self.vm.connect('mount-removed', self.on_mount_removed)
        self.vm.connect('volume-added', self.on_mount_added)
        self.vm.connect('volume-removed', self.on_mount_removed)
        self.vm.connect('drive-connected', self.on_mount_added)
        self.vm.connect('drive-disconnected', self.on_mount_removed)

    def add_to_desktop(self):
        # Copy app's desktop file to user's desktop path on first run
        user_home = GLib.get_home_dir()
        user_desktopcontrol_file = os.path.join(user_home, ".config/pardus-mycomputer/desktop")
        if not os.path.isfile(user_desktopcontrol_file):
            print("{} {}".format("Desktop file copying to",
                                 GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DESKTOP)))
            try:
                subprocess.Popen(["/bin/bash",
                                  "/usr/share/pardus/pardus-mycomputer/autostart/pardus-mycomputer-add-to-desktop"])
            except Exception as e:
                print("{}".format(e))
                try:
                    subprocess.Popen(["/usr/bin/bash",
                                      "/usr/share/pardus/pardus-mycomputer/autostart/pardus-mycomputer-add-to-desktop"])
                except Exception as e:
                    print("{}".format(e))

    def user_settings(self):
        self.UserSettings = UserSettings()
        self.UserSettings.createDefaultConfig()
        self.UserSettings.readConfig()

        print("{} {}".format("config_closeapp_pardus", self.UserSettings.config_closeapp_pardus))
        print("{} {}".format("config_closeapp_hdd", self.UserSettings.config_closeapp_hdd))
        print("{} {}".format("config_closeapp_usb", self.UserSettings.config_closeapp_usb))
        print("{} {}".format("config_autorefresh", self.UserSettings.config_autorefresh))
        print("{} {}".format("config_autorefresh_time", self.UserSettings.config_autorefresh_time))

    def autorefresh(self):
        if self.UserSettings.config_autorefresh:
            self.autorefresh_glibid = GLib.timeout_add(self.UserSettings.config_autorefresh_time * 1000,
                                                       self.autorefresh_disks)

    def autorefresh_disks(self):
        self.addDisksToGUI()
        print("auto refreshing disks on every {} seconds with glib id: {}".format(
            self.UserSettings.config_autorefresh_time, self.autorefresh_glibid))
        return self.UserSettings.config_autorefresh

    def showDiskDetailsDialog(self, vl):
        try:
            name = vl.get_drive().get_name()
        except:
            name = vl.get_name()

        dr = vl.get_drive()
        try:
            mount_point = vl.get_mount().get_root().get_path()
        except:
            mount_point = vl.get_root().get_path()

        file_info = DiskManager.get_file_info(mount_point)

        self.dlg_lbl_name.set_markup("<b><big>{}</big></b>".format(vl.get_name()))
        self.dlg_lbl_model.set_label(name)

        self.dlg_lbl_dev.set_label(file_info["device"])
        self.dlg_lbl_mountpoint.set_label(mount_point)

        self.dlg_lbl_used_gb.set_label(f"{int(file_info['usage_kb'])/1000/1000:.2f} GB (%{file_info['usage_percent']*100:.2f})")
        self.dlg_lbl_free_gb.set_label(f"{int(file_info['free_kb'])/1000/1000:.2f} GB (%{file_info['free_percent']*100:.2f})")
        self.dlg_lbl_total_gb.set_label(f"{int(file_info['total_kb'])/1000/1000:.2f} GB")

        self.dlg_lbl_filesystem_type.set_label(DiskManager.get_filesystem_of_partition(file_info["device"]))


    def showVolumeSizes(self, row_volume):
        vl = row_volume._volume

        try:
            gm = vl.get_mount()
        except:
            gm = vl

        if gm != None:
            # print("{} {} {}".format(vl.get_name(), vl.get_mount(), vl.get_mount().get_root().get_path()))
            mount_point = gm.get_root().get_path()
            file_info = DiskManager.get_file_info(mount_point)

            try:
                free_kb = int(file_info['free_kb'])
            except:
                free_kb = 0

            try:
                total_kb = int(file_info['total_kb'])
            except:
                total_kb = 0

            # Show values on UI
            row_volume._lbl_volume_name.set_markup(
                f'<b>{row_volume._volume.get_name()}</b> <span size="small">( { mount_point } )</span>')
            # row_volume._lbl_volume_size_info.set_markup(
            #     f'<span size="small"><b>{int(file_info["free_kb"])/1000/1000:.2f} GB</b> {_("is free of")} {int(file_info["total_kb"])/1000/1000:.2f} GB</span>')
            row_volume._lbl_volume_size_info.set_markup("<span size='small'><b>{:.2f} GB</b> {} {:.2f} GB</span>".format(
                free_kb/1000/1000, _("is free of"),total_kb/1000/1000))
            # row_volume._lbl_volume_dev_directory.set_markup(
            #     f'<span size="small" alpha="75%">{ file_info["device"] }</span>')
            row_volume._pb_volume_size.set_fraction(file_info["usage_percent"])

            # if volume usage >= 0.9 then add destructive color
            try:
                if file_info["usage_percent"] >= 0.9:
                    row_volume._pb_volume_size.get_style_context().add_class("pardus-mycomputer-progress-90")
            except Exception as e:
                print("progress css exception: {}".format(e))

            row_volume._btn_volume_settings.set_sensitive(True)
            row_volume.show_all()
        else:
            print(f"can't mount the volume: {vl.get_name()}")

    
    def tryMountVolume(self, row_volume):
        vl = row_volume._volume
        if not vl.can_mount() and vl.get_mount() == None:
            print(f"can't mount the volume: {vl.get_name()}")
            return False

        if vl.get_mount() == None:
            def on_mounted(vl, task, row_volume):
                try:
                    vl.mount_finish(task)
                    
                    self.showVolumeSizes(row_volume)
                    return True
                except GLib.Error:
                    return False
            
            
            vl.mount(Gio.MountMountFlags.NONE, self.mount_operation, None, on_mounted, row_volume)
        else:
            self.showVolumeSizes(row_volume)
            return True
    
    def addVolumeRow(self, vl, listbox, is_removable, media=False, phone=False, card=False, othermount=False):
        # Prepare UI Containers:
        box_volume = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 7)
        if not media:
            img_volume = Gtk.Image.new_from_icon_name(
                "media-removable" if is_removable else "drive-harddisk", Gtk.IconSize.DIALOG)
            if othermount:
                img_volume = Gtk.Image.new_from_icon_name("network-server", Gtk.IconSize.DIALOG)
        else:
            if not phone:
                if not card:
                    img_volume = Gtk.Image.new_from_icon_name("media-optical", Gtk.IconSize.DIALOG)
                else:
                    img_volume = Gtk.Image.new_from_icon_name("media-flash", Gtk.IconSize.DIALOG)
            else:
                img_volume = Gtk.Image.new_from_icon_name("phone", Gtk.IconSize.DIALOG)


        box_volume_info = Gtk.Box.new(Gtk.Orientation.VERTICAL, 3)

        # Volume infos
        lbl_volume_name = Gtk.Label.new()
        lbl_volume_name.set_markup("<b>{}</b><small> ( {} )</small>".format(
            vl.get_name(),_("Disk is available, click to mount.")))
        lbl_volume_name.set_halign(Gtk.Align.START)

        # lbl_volume_dev_directory = Gtk.Label.new()
        # lbl_volume_dev_directory.set_markup(
        #     f'<span size="small"> </span>')
        # lbl_volume_dev_directory.set_halign(Gtk.Align.START)

        pb_volume_size = Gtk.ProgressBar.new()
        pb_volume_size.set_valign(Gtk.Align.CENTER)
        pb_volume_size.set_margin_end(7)

        lbl_volume_size_info = Gtk.Label.new()
        lbl_volume_size_info.set_markup(
            f"<span size=\"small\"> </span>")
        lbl_volume_size_info.set_halign(Gtk.Align.START)

        # Add widgets to box:
        box_volume_info.add(lbl_volume_name)
        # box_volume_info.add(lbl_volume_name)
        # box_volume_info.add(lbl_volume_dev_directory)
        box_volume_info.add(pb_volume_size)
        box_volume_info.add(lbl_volume_size_info)        

        # Add Disk settings button
        btn_volume_settings = Gtk.MenuButton.new()
        btn_volume_settings.set_image(Gtk.Image.new_from_icon_name("view-more-symbolic", Gtk.IconSize.LARGE_TOOLBAR  ))
        btn_volume_settings.set_relief(Gtk.ReliefStyle.NONE)
        btn_volume_settings.set_valign(Gtk.Align.CENTER)
        btn_volume_settings._volume = vl
        btn_volume_settings._lbl_volume_name = lbl_volume_name
        btn_volume_settings._lbl_volume_size_info = lbl_volume_size_info
        btn_volume_settings._pb_volume_size = pb_volume_size
        btn_volume_settings._is_removable = is_removable
        # btn_volume_settings._lbl_volume_dev_directory = lbl_volume_dev_directory

        btn_volume_settings.connect("released", self.on_btn_volume_settings_clicked)

        btn_volume_settings.set_popover(self.popover_volume)
        btn_volume_settings.set_sensitive(False)

        box_volume.add(img_volume)
        box_volume.pack_start(box_volume_info, True, True, 0)
        box_volume.pack_end(btn_volume_settings, False, True, 0)
        box_volume.props.margin = 7


        # Add to listbox
        listbox.prepend(box_volume)
        row = listbox.get_row_at_index(0)
        row._volume = vl
        row._btn_volume_settings = btn_volume_settings
        row._lbl_volume_name = lbl_volume_name
        row._lbl_volume_size_info = lbl_volume_size_info
        row._pb_volume_size = pb_volume_size
        # row._lbl_volume_dev_directory = lbl_volume_dev_directory

        # Disable asking mount on app startup
        # self.tryMountVolume(row)
        self.showVolumeSizes(row)

    def addDisksToGUI(self):
        # Home:
        home_info = DiskManager.get_file_info(GLib.get_home_dir())
        self.lbl_home_path.set_markup("<small>( {} )</small>".format(GLib.get_home_dir()))
        home_info = DiskManager.get_file_info(GLib.get_home_dir())
        self.lbl_home_size.set_label(f"{int(home_info['usage_kb'])/1000/1000:.2f} GB")

        # Root:
        root_info = DiskManager.get_file_info("/")
        self.lbl_root_free.set_label(f"{int(root_info['free_kb'])/1000/1000:.2f} GB")
        self.lbl_root_total.set_label(f"{int(root_info['total_kb'])/1000/1000:.2f} GB")
        self.pb_root_usage.set_fraction( root_info["usage_percent"] )

        # if root usage >= 0.9 then add destructive color
        try:
            if root_info["usage_percent"] >= 0.9:
                self.pb_root_usage.get_style_context().add_class("pardus-mycomputer-progress-90")
        except Exception as e:
            print("progress css exception: {}".format(e))

        # Hard Drives
        self.addHardDisksToList()

        # RemovableDevices
        self.addRemovableDevicesToList()
        
    def addHardDisksToList(self):
        self.box_drives.foreach(lambda child: self.box_drives.remove(child))

        # Hard Drives
        drives = self.vm.get_connected_drives()
        for dr in drives:
            if dr.has_volumes() and not dr.is_removable():
                # Drive Label
                lbl_drive_name = Gtk.Label.new()
                lbl_drive_name.set_markup(f'<span size="medium">{dr.get_name()}</span>')
                lbl_drive_name.set_halign(Gtk.Align.START)

                # Drive Frame
                # frame = Gtk.Frame.new()
                # frame.set_shadow_type(Gtk.ShadowType.IN)

                # Volume ListBox
                listbox = Gtk.ListBox.new()
                listbox.set_selection_mode(Gtk.SelectionMode.NONE)
                listbox.connect("row-activated", self.on_volume_row_activated)
                listbox.get_style_context().add_class("pardus-mycomputer-listbox")
                # frame.add(listbox)
                
                # Add Volumes to the ListBox:
                for vl in dr.get_volumes():
                    self.addVolumeRow(vl, listbox, False)

                #self.box_drives.add(lbl_drive_name)
                self.box_drives.add(listbox)

        self.box_drives.show_all()
        
    def addRemovableDevicesToList(self):
        self.box_removables.foreach(lambda child: self.box_removables.remove(child))

        connected_drives = self.vm.get_connected_drives()

        for dr in connected_drives:
            if dr.has_volumes() and dr.is_removable():
                # print("{} {}".format(dr.get_name(), dr.get_icon().to_string()))
                # print("{} {}".format(dr.get_name(), dr.is_media_removable()))
                # print("{} {}".format(dr.get_name(), dr.get_identifier(Gio.VOLUME_IDENTIFIER_KIND_UNIX_DEVICE)))

                # Drive Label
                lbl_drive_name = Gtk.Label.new()
                lbl_drive_name.set_markup(f'<span size="medium">{dr.get_name()}</span>')
                lbl_drive_name.set_halign(Gtk.Align.START)

                # Volume ListBox
                listbox = Gtk.ListBox.new()
                listbox.set_selection_mode(Gtk.SelectionMode.NONE)
                listbox.connect("row-activated", self.on_volume_row_activated)
                listbox.get_style_context().add_class("pardus-mycomputer-listbox")

                # Add Volumes to the ListBox:
                for vl in dr.get_volumes():
                    self.addVolumeRow(vl, listbox, True,
                                      media=dr.is_media_removable() if dr.is_media_removable() else False,
                                      card=self.is_card(vl))
                    try:
                        if vl.get_mount():
                            self.mount_paths.append(vl.get_mount().get_root().get_path())
                    except Exception as e:
                        print("mount_paths append error: {}".format(e))

                
                #self.box_removables.add(lbl_drive_name)
                self.box_removables.add(listbox)


        # disk images, phones
        drives = []
        for cd in connected_drives:
            if cd.get_volumes():
                for gvcd in cd.get_volumes():
                    drives.append(gvcd)
        volumes = self.vm.get_volumes()
        others = [volume for volume in volumes if volume not in drives]

        for other in others:
            if other.get_drive() is None:

                # Drive Label
                lbl_drive_name = Gtk.Label.new()
                lbl_drive_name.set_markup(f'<span size="medium">{other.get_name()}</span>')
                lbl_drive_name.set_halign(Gtk.Align.START)

                # Volume ListBox
                listbox = Gtk.ListBox.new()
                listbox.set_selection_mode(Gtk.SelectionMode.NONE)
                listbox.connect("row-activated", self.on_volume_row_activated)
                listbox.get_style_context().add_class("pardus-mycomputer-listbox")

                # Add Volumes to the ListBox:
                self.addVolumeRow(other, listbox, True, media=True, phone=self.is_phone(other))

                try:
                    if other.get_mount():
                        self.mount_paths.append(other.get_mount().get_root().get_path())
                except Exception as e:
                    print("mount_paths append error: {}".format(e))

                # self.box_removables.add(lbl_drive_name)
                self.box_removables.add(listbox)


        # smb, sftp vs..
        connected_mounts = []
        for cd in connected_drives:
            if cd.get_volumes():
                for gvcd in cd.get_volumes():
                    if gvcd.get_mount():
                        connected_mounts.append(gvcd.get_mount())
        all_mounts = self.vm.get_mounts()
        mounts = [mount for mount in all_mounts if mount not in connected_mounts]
        for mount in mounts:
            if mount.get_volume() is None:

                if mount.get_root().get_path() not in self.mount_paths:
                    # Drive Label
                    lbl_drive_name = Gtk.Label.new()
                    lbl_drive_name.set_markup(f'<span size="medium">{mount.get_name()}</span>')
                    lbl_drive_name.set_halign(Gtk.Align.START)

                    # Volume ListBox
                    listbox = Gtk.ListBox.new()
                    listbox.set_selection_mode(Gtk.SelectionMode.NONE)
                    listbox.connect("row-activated", self.on_volume_row_activated)
                    listbox.get_style_context().add_class("pardus-mycomputer-listbox")

                    # Add Volumes to the ListBox:
                    self.addVolumeRow(mount, listbox, True, othermount=True)

                    # self.box_removables.add(lbl_drive_name)
                    self.box_removables.add(listbox)
        
        self.box_removables.show_all()


    def is_phone(self, volume):
        usb = False
        phone = False
        drive = False
        try:
            if "/usb/" in volume.get_identifier(Gio.VOLUME_IDENTIFIER_KIND_UNIX_DEVICE):
                usb = True
        except Exception as e:
            print("Error in get_identifier(): {}".format(e))

        try:
            if "phone" in volume.get_icon().to_string():
                phone = True
            if "drive" in volume.get_icon().to_string():
                drive = True
        except Exception as e:
                print("Error in get_symbolic_icon(): {}".format(e))

        if phone:
            return True
        else:
            if not drive and usb:
                return True

        return False

    def is_card(self, volume):
        mmc = False
        card = False
        drive = False
        try:
            if "/dev/mmc" in volume.get_identifier(Gio.VOLUME_IDENTIFIER_KIND_UNIX_DEVICE):
                mmc = True
        except Exception as e:
            print("Error in get_identifier(): {}".format(e))

        try:
            if "flash" in volume.get_icon().to_string():
                card = True
            if "media-removable" in volume.get_icon().to_string():
                drive = True
        except Exception as e:
                print("Error in get_symbolic_icon(): {}".format(e))

        if card:
            return True
        else:
            if not drive and mmc:
                return True

        return False
    # Window methods:
    def onDestroy(self, action):
        self.window.get_application().quit()



    # SIGNALS:
    def on_lb_home_row_activated(self, listbox, row):
        subprocess.run(["xdg-open", GLib.get_home_dir()])
        if self.UserSettings.config_closeapp_pardus:
            self.onDestroy(listbox)

    def on_lb_root_row_activated(self, listbox, row):
        subprocess.run(["xdg-open", "/"])
        if self.UserSettings.config_closeapp_pardus:
            self.onDestroy(listbox)

    def on_volume_row_activated(self, listbox, row):
        try:
            mount  = row._volume.get_mount()
        except:
            mount = row._volume

        if mount == None:
            self.tryMountVolume(row)
        else:
            subprocess.run(["xdg-open", mount.get_root().get_path()])

        if row._volume.get_drive():
            if row._volume.get_drive().is_removable():
                if self.UserSettings.config_closeapp_usb:
                    self.onDestroy(listbox)
            else:
                if self.UserSettings.config_closeapp_hdd:
                    self.onDestroy(listbox)
        else:
            if self.UserSettings.config_closeapp_usb:
                self.onDestroy(listbox)
    
    def on_btn_volume_settings_clicked(self, btn):

        # disable auto refreshing because the popover is closing when auto refresh while open
        if self.autorefresh_glibid:
            GLib.source_remove(self.autorefresh_glibid)

        self.popover_volume.set_relative_to(btn)
        self.popover_volume.set_position(Gtk.PositionType.LEFT)

        if btn._is_removable:
            self.popover_dt_stack.set_visible_child_name("usb")
        else:
            self.popover_dt_stack.set_visible_child_name("disk")

        try:
            mount = btn._volume.get_mount()
        except:
            mount = btn._volume
        if mount == None:
            self.tryMountVolume(btn)
            return

        self.selected_volume = btn._volume

        # self.popover_removable.set_sensitive(True)
        self.popover_volume.set_sensitive(True)

        mount_point = mount.get_root().get_path()
        self.selected_volume_info = DiskManager.get_file_info(mount_point)

        self.cb_mount_on_startup.set_active(DiskManager.is_drive_automounted(self.selected_volume_info["device"]))

        self.showDiskDetailsDialog(self.selected_volume)

    def on_popover_volume_closed(self, popover):
        # auto refresh control of disks
        self.autorefresh()

    def on_sw_closeapp_pardus_state_set(self, switch, state):
        user_config_closeapp_pardus = self.UserSettings.config_closeapp_pardus
        if state != user_config_closeapp_pardus:
            print("Updating close app pardus state")
            try:
                self.UserSettings.writeConfig(state,
                                              self.UserSettings.config_closeapp_hdd,
                                              self.UserSettings.config_closeapp_usb,
                                              self.UserSettings.config_autorefresh,
                                              self.UserSettings.config_autorefresh_time
                                              )
                self.user_settings()
            except Exception as e:
                print("{}".format(e))
        self.control_defaults()

    def on_sw_closeapp_hdd_state_set(self, switch, state):
        user_config_closeapp_hdd = self.UserSettings.config_closeapp_hdd
        if state != user_config_closeapp_hdd:
            print("Updating close app hdd state")
            try:
                self.UserSettings.writeConfig(self.UserSettings.config_closeapp_pardus,
                                              state,
                                              self.UserSettings.config_closeapp_usb,
                                              self.UserSettings.config_autorefresh,
                                              self.UserSettings.config_autorefresh_time
                                              )
                self.user_settings()
            except Exception as e:
                print("{}".format(e))
        self.control_defaults()

    def on_sw_closeapp_usb_state_set(self, switch, state):
        user_config_closeapp_usb = self.UserSettings.config_closeapp_usb
        if state != user_config_closeapp_usb:
            print("Updating close app usb state")
            try:
                self.UserSettings.writeConfig(self.UserSettings.config_closeapp_pardus,
                                              self.UserSettings.config_closeapp_hdd,
                                              state,
                                              self.UserSettings.config_autorefresh,
                                              self.UserSettings.config_autorefresh_time
                                              )
                self.user_settings()
            except Exception as e:
                print("{}".format(e))
        self.control_defaults()

    def on_sw_autorefresh_state_set(self, switch, state):
        user_config_autorefresh = self.UserSettings.config_autorefresh
        if state != user_config_autorefresh:
            print("Updating autorefresh state")
            try:
                self.UserSettings.writeConfig(self.UserSettings.config_closeapp_pardus,
                                              self.UserSettings.config_closeapp_hdd,
                                              self.UserSettings.config_closeapp_usb,
                                              state,
                                              self.UserSettings.config_autorefresh_time
                                              )
                self.user_settings()
                if state:
                    self.autorefresh()
                else:
                    GLib.source_remove(self.autorefresh_glibid)
                    self.autorefresh_glibid = None
            except Exception as e:
                print("{}".format(e))
        self.control_defaults()

    # Popover Menu Buttons:
    def on_cb_mount_on_startup_released(self, cb):
        DiskManager.set_automounted(self.selected_volume_info["device"], cb.get_active())
    
    def on_btn_format_removable_clicked(self, btn):
        mount_point = self.selected_volume.get_mount().get_root().get_path()
        file_info = DiskManager.get_file_info(mount_point)

        self.popover_volume.popdown()

        subprocess.Popen(["pardus-usb-formatter", file_info["device"]])

    def on_btn_unmount_clicked(self, btn):
        self.actioned_volume = self.selected_volume

        try:
            network_device = False
            mount_point = self.actioned_volume.get_mount().get_root().get_path()
        except:
            network_device = True
            mount_point = self.actioned_volume.get_root().get_path()

        command = [os.path.dirname(os.path.abspath(__file__)) + "/Unmount.py", "unmount", mount_point]

        summary = _("Please wait")
        if network_device:
            body = _("Device is unmounting.")
        else:
            if self.actioned_volume.get_drive():
                if self.actioned_volume.get_drive().is_removable():
                    if self.actioned_volume.get_drive().is_media_removable():
                        if self.is_card(self.actioned_volume):
                            body = _("Card drive is unmounting.")
                        else:
                            body = _("Optical disk is unmounting.")
                    else:
                        body = _("USB disk is unmounting.")
                else:
                    body = _("Disk is unmounting.")
            else:
                if self.is_phone(self.actioned_volume):
                    body = _("Phone is unmounting.")
                else:
                    if self.is_card(self.actioned_volume):
                        body = _("Card drive is unmounting.")
                    else:
                        body = _("Optical drive is unmounting.")

        self.notify(summary, body, "emblem-synchronizing-symbolic")

        self.stack_unmount.set_visible_child_name("spinner")
        self.startProcess(command)

    def on_mount_added(self, volumemonitor, mount):
        self.addHardDisksToList()
        self.addRemovableDevicesToList()
        self.mount_paths.clear()

    def on_mount_removed(self, volumemonitor, mount):
        self.addHardDisksToList()
        self.addRemovableDevicesToList()
        self.mount_paths.clear()

    def on_btn_volume_details_clicked(self, btn):
        self.showDiskDetailsDialog(self.selected_volume)

        self.dialog_disk_details.run()
        self.dialog_disk_details.hide()

    def on_btn_refresh_clicked(self, button):
        print("Manually refreshing disks")
        self.addDisksToGUI()

    def on_btn_settings_clicked(self, button):
        if self.stack_main.get_visible_child_name() == "settings":
            self.stack_main.set_visible_child_name("home")
            self.img_settings.set_from_icon_name("preferences-system-symbolic", Gtk.IconSize.BUTTON)
        elif self.stack_main.get_visible_child_name() == "home":
            self.sw_closeapp_pardus.set_state(self.UserSettings.config_closeapp_pardus)
            self.sw_closeapp_hdd.set_state(self.UserSettings.config_closeapp_hdd)
            self.sw_closeapp_usb.set_state(self.UserSettings.config_closeapp_usb)
            self.sw_autorefresh.set_state(self.UserSettings.config_autorefresh)
            self.stack_main.set_visible_child_name("settings")
            self.img_settings.set_from_icon_name("user-home-symbolic", Gtk.IconSize.BUTTON)
            self.control_defaults()

    def on_btn_defaults_clicked(self, button):
        self.UserSettings.createDefaultConfig(force=True)
        self.user_settings()
        self.sw_closeapp_pardus.set_state(self.UserSettings.config_closeapp_pardus)
        self.sw_closeapp_hdd.set_state(self.UserSettings.config_closeapp_hdd)
        self.sw_closeapp_usb.set_state(self.UserSettings.config_closeapp_usb)
        self.sw_autorefresh.set_state(self.UserSettings.config_autorefresh)

    def control_defaults(self):
        if self.UserSettings.config_closeapp_pardus != self.UserSettings.default_closeapp_pardus or \
                self.UserSettings.config_closeapp_hdd != self.UserSettings.default_closeapp_hdd or \
                self.UserSettings.config_closeapp_usb != self.UserSettings.default_closeapp_usb or \
                self.UserSettings.config_autorefresh != self.UserSettings.default_autorefresh or \
                self.UserSettings.config_autorefresh_time != self.UserSettings.default_autorefresh_time:
            self.btn_defaults.set_sensitive(True)
        else:
            self.btn_defaults.set_sensitive(False)

    def on_menu_aboutapp_clicked(self, button):
        self.popover_menu.popdown()
        self.dialog_about.run()
        self.dialog_about.hide()

    def on_menu_aboutpardus_clicked(self, button):
        self.popover_menu.popdown()
        try:
            subprocess.Popen(["pardus-about"])
        except Exception as e:
            print("on_menu_aboutpardus_clicked Exception: {}".format(e))

    def startProcess(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.onProcessStdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.onProcessStderr)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, self.onProcessExit)

        return pid

    def onProcessStdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        print(line)
        return True

    def onProcessStderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        print(line)
        return True

    def onProcessExit(self, pid, status):
        # print(f'pid, status: {pid, status}')

        try:
            network_device = False
            vl = self.actioned_volume.get_mount()
        except:
            network_device = True
            vl = self.actioned_volume
        dr = self.actioned_volume.get_drive()

        summary = _("Unmounting process is done")
        if network_device:
            body = _("You can eject the device.")
        else:
            if dr:
                if dr.is_removable():
                    if dr.is_media_removable():
                        if self.is_card(dr):
                            body = _("You can eject the card drive.")
                        else:
                            body = _("You can eject the Optical drive.")
                    else:
                        body = _("You can eject the USB disk.")
                else:
                    body = _("You can eject the disk.")
            else:
                if self.is_phone(self.actioned_volume):
                    body = _("You can eject the phone.")
                else:
                    if self.is_card(self.actioned_volume):
                        body = _("You can eject the card drive.")
                    else:
                        body = _("You can eject the optical drive.")

        def on_unmounted(vl, task):
            try:
                vl.unmount_with_operation_finish(task)
                self.notify(summary, body, "emblem-ok-symbolic")
                return True
            except Exception as e:
                print("{}".format(e))
                return False

        vl.unmount_with_operation(Gio.MountUnmountFlags.FORCE, self.mount_operation, None, on_unmounted)

        self.stack_unmount.set_visible_child_name("unmount")

    def notify(self, message_summary="", message_body="", icon="pardus-mycomputer"):
        try:
            if Notify.is_initted():
                Notify.uninit()

            Notify.init(message_summary)
            notification = Notify.Notification.new(message_summary, message_body, icon)
            notification.show()
        except Exception as e:
            print("{}".format(e))
