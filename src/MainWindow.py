import os, subprocess

import gi
gi.require_version("Notify", "0.7")
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk, Notify, Gdk, Pango

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

        # set os label and image
        self.set_os_label_img()

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

        # add recent connections to listbox_recent_server from file
        self.add_recents_from_file()

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

        # os label and image
        self.lbl_os = UI("lbl_os")
        self.img_os = UI("img_os")
        self.lbl_os_menu = UI("lbl_os_menu")
        self.img_os_menu = UI("img_os_menu")
        self.menu_aboutpardus = UI("menu_aboutpardus")

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
        # self.popover_dt_stack = UI("popover_dt_stack")
        self.popover_volume_actionbox = UI("popover_volume_actionbox")

        # Buttons
        self.btn_unmount = UI("btn_unmount")
        self.btn_defaults = UI("btn_defaults")

        # Main Stack
        self.stack_main = UI("stack_main")

        # Menu popover
        self.popover_menu = UI("popover_menu")

        # Settings switch buttons
        self.sw_closeapp_directories = UI("sw_closeapp_directories")
        self.sw_autorefresh = UI("sw_autorefresh")

        self.img_settings = UI("img_settings")

        # Mount dialog and popovers
        self.dialog_mount = UI("dialog_mount")
        self.dialog_mount_error = UI("dialog_mount_error")
        self.lbl_mount_message = UI("lbl_mount_message")
        self.entry_mount_username = UI("entry_mount_username")
        self.entry_mount_password = UI("entry_mount_password")
        self.entry_mount_domain = UI("entry_mount_domain")
        self.box_username = UI("box_username")
        self.box_domain = UI("box_domain")
        self.box_password = UI("box_password")
        self.box_password_options = UI("box_password_options")
        self.box_user_domain_pass = UI("box_user_domain_pass")
        self.box_anonym = UI("box_anonym")
        self.btn_mount_connect = UI("btn_mount_connect")
        self.mount_password_options = UI("mount_password_options")
        self.mount_anonym_options = UI("mount_anonym_options")
        self.popover_connect = UI("popover_connect")
        self.entry_addr = UI("entry_addr")
        self.popover_connect_examples = UI("popover_connect_examples")
        self.popover_recent_servers = UI("popover_recent_servers")
        self.stack_recent_servers = UI("stack_recent_servers")
        self.listbox_recent_servers = UI("listbox_recent_servers")
        self.stack_save_delete_removable = UI("stack_save_delete_removable")
        self.spinner_header = UI("spinner_header")
        self.spinner_harddrive = UI("spinner_harddrive")
        self.spinner_removable = UI("spinner_removable")

        self.mount_inprogress = False

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
        self.net_mounts = []
        # self.selected_mount_uri = ""
        # self.selected_mount_name = ""

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

        print("{} {}".format("config_closeapp_directories", self.UserSettings.config_closeapp_directories))
        print("{} {}".format("config_autorefresh", self.UserSettings.config_autorefresh))
        print("{} {}".format("config_autorefresh_time", self.UserSettings.config_autorefresh_time))

    def set_os_label_img(self):
        os_name = ""
        os_id = ""
        pixbuf = None
        if os.path.isfile("/etc/os-release"):
            with open("/etc/os-release") as osf:
                osfile = osf.read().strip()

            if "PRETTY_NAME" in osfile:
                for line in osfile.splitlines():
                    if line.startswith("PRETTY_NAME="):
                        os_name = line.split("PRETTY_NAME=")[1].strip(' "')
                        break
            elif "NAME" in osfile:
                for line in osfile.splitlines():
                    if line.startswith("NAME="):
                        os_name = line.split("NAME=")[1].strip(' "')
                        break
            else:
                print("name or prettyname not in /etc/os-release file")
                os_name = _("Unknown (/etc/os-release syntax error)")

            if "ID" in osfile:
                for line in osfile.splitlines():
                    if line.startswith("ID="):
                        os_id = line.split("ID=")[1].strip(' "').lower()
                        break
        else:
            print("/etc/os-release file not found")
            os_name = _("Unknown (/etc/os-release file not exists)")


        if os_id == "pardus":
            self.img_os.set_from_icon_name("emblem-pardus-symbolic", Gtk.IconSize.BUTTON)
            self.img_os_menu.set_from_icon_name("emblem-pardus-symbolic", Gtk.IconSize.BUTTON)
            self.lbl_os_menu.set_label("{}".format(_("About Pardus")))
        else:
            try:
                pixbuf = Gtk.IconTheme.get_default().load_icon("emblem-{}".format(os_id), 16,
                                                               Gtk.IconLookupFlags(16))
            except Exception as e:
                print("{}".format(e))
                try:
                    pixbuf = Gtk.IconTheme.get_default().load_icon("distributor-logo", 16, Gtk.IconLookupFlags(16))
                except Exception as e:
                    print("{}".format(e))
                    try:
                        pixbuf = Gtk.IconTheme.get_default().load_icon("image-missing", 16, Gtk.IconLookupFlags(16))
                    except Exception as e:
                        print("{}".format(e))
                        pixbuf = None

            if pixbuf is not None:
                self.img_os.set_from_pixbuf(pixbuf)
                self.img_os_menu.set_from_pixbuf(pixbuf)

            if os_id != "":
                self.lbl_os_menu.set_label("{} {}".format(_("About"), os_id.title()))
            else:
                self.lbl_os_menu.set_label("{}".format(_("About System")))

        self.lbl_os.set_label("{}".format(os_name))


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
        volume = vl._volume
        try:
            name = volume.get_drive().get_name()
        except:
            name = volume.get_name()

        try:
            mount_point = volume.get_mount().get_root().get_path()
        except:
            mount_point = volume.get_root().get_path()

        if vl._main_type == "network":
            try:
                display_name = volume.get_name()
            except:
                try:
                    display_name = volume.get_drive().get_name()
                except:
                    display_name = ""
        else:
            mount = volume.get_mount()
            display_name = self.get_display_name(mount)
            if display_name == "":
                try:
                    display_name = volume.get_name()
                except:
                    try:
                        display_name = volume.get_drive().get_name()
                    except:
                        display_name = ""

        self.dlg_lbl_name.set_markup("<b><big>{}</big></b>".format(display_name))
        self.dlg_lbl_model.set_label(name)

        file_info = DiskManager.get_file_info(mount_point, network=True if vl._main_type == "network" else False)

        if file_info is not None:

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

        if gm != None and not isinstance(vl, str):

            mount_point = gm.get_root().get_path()
            file_info = DiskManager.get_file_info(mount_point, network=True if row_volume._main_type == "network" else False)

            if row_volume._main_type == "network":
                display_name = vl.get_name()
            else:
                display_name = self.get_display_name(gm)
                if display_name == "":
                    display_name = vl.get_name()

            if file_info is not None:

                free_kb = int(file_info['free_kb'])
                total_kb = int(file_info['total_kb'])

                # Show values on UI
                row_volume._lbl_volume_name.set_markup(
                    f'<b>{display_name}</b> <span size="small">( { mount_point } )</span>')
                row_volume._lbl_volume_size_info.set_markup("<span size='small'><b>{:.2f} GB</b> {} {:.2f} GB</span>".format(
                    free_kb/1000/1000, _("is free of"),total_kb/1000/1000))
                row_volume._pb_volume_size.set_fraction(file_info["usage_percent"])

                # if volume usage >= 0.9 then add destructive color
                try:
                    if file_info["usage_percent"] >= 0.9:
                        row_volume._pb_volume_size.get_style_context().add_class("pardus-mycomputer-progress-90")
                except Exception as e:
                    print("progress css exception: {}".format(e))

            if row_volume._stack_mount.get_child_by_name("unmount"):
                row_volume._stack_mount.get_child_by_name("unmount").show()
                row_volume._stack_mount.set_visible_child_name("unmount")

            row_volume.show_all()
        else:

            if row_volume._stack_mount.get_child_by_name("mount"):
                row_volume._stack_mount.get_child_by_name("mount").show()
                row_volume._stack_mount.set_visible_child_name("mount")

            # name = vl if isinstance(vl, str) else vl.get_name()
            # print(f"can't mount the volume: {name}")

    
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
    
    def addVolumeRow(self, vl, listbox, is_removable, is_ejectable, main_type="", type="", mount_uri="", mount_name=""):
        # Prepare UI Containers:
        box_volume = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)

        img_volume = Gtk.Image.new_from_icon_name("drive-removable-media", Gtk.IconSize.DIALOG)

        if not is_removable:
            img_volume = Gtk.Image.new_from_icon_name("drive-harddisk", Gtk.IconSize.DIALOG)
        else:
            if main_type == "drive":
                if type == "usbdrive":
                    img_volume = Gtk.Image.new_from_icon_name("media-removable", Gtk.IconSize.DIALOG)
                elif type == "card":
                    img_volume = Gtk.Image.new_from_icon_name("media-flash", Gtk.IconSize.DIALOG)
                elif type == "optical":
                    img_volume = Gtk.Image.new_from_icon_name("media-optical", Gtk.IconSize.DIALOG)
            elif main_type == "volume":
                if type == "image":
                    img_volume = Gtk.Image.new_from_icon_name("media-optical", Gtk.IconSize.DIALOG)
                elif type == "phone":
                    img_volume = Gtk.Image.new_from_icon_name("phone", Gtk.IconSize.DIALOG)
            elif main_type == "network":
                img_volume = Gtk.Image.new_from_icon_name("network-server", Gtk.IconSize.DIALOG)
            elif main_type == "saved":
                img_volume = Gtk.Image.new_from_icon_name("user-bookmarks", Gtk.IconSize.DIALOG)


        box_volume_info = Gtk.Box.new(Gtk.Orientation.VERTICAL, 3)

        # Volume infos
        if isinstance(vl, str):
            name = vl
        else:
            if main_type == "network":
                name = vl.get_name()
            else:
                name = self.get_display_name(vl.get_mount())
                if name == "":
                    name = vl.get_name()

        lbl_volume_name = Gtk.Label.new()
        lbl_volume_name.set_markup("<b>{}</b><small> ( {} )</small>".format(
            name,_("Disk is available, click to mount.")))
        lbl_volume_name.set_halign(Gtk.Align.START)
        lbl_volume_name.set_ellipsize(Pango.EllipsizeMode.END)

        pb_volume_size = Gtk.ProgressBar.new()
        pb_volume_size.set_valign(Gtk.Align.CENTER)
        pb_volume_size.set_margin_end(7)

        lbl_volume_size_info = Gtk.Label.new()
        lbl_volume_size_info.set_markup(
            f"<span size=\"small\"> </span>")
        lbl_volume_size_info.set_halign(Gtk.Align.START)

        # Add widgets to box:
        box_volume_info.add(lbl_volume_name)
        box_volume_info.add(pb_volume_size)
        box_volume_info.add(lbl_volume_size_info)        

        # Add Disk settings button


        stack_mount = Gtk.Stack.new()

        btn_mount = Gtk.Button.new()
        btn_mount.set_image(Gtk.Image.new_from_icon_name("media-playback-start-symbolic", Gtk.IconSize.BUTTON  ))
        btn_mount.set_relief(Gtk.ReliefStyle.NONE)
        btn_mount.set_valign(Gtk.Align.CENTER)
        btn_mount.set_tooltip_text(_("Mount"))
        btn_mount._volume = vl
        btn_mount._is_removable = is_removable
        btn_mount._main_type = main_type
        btn_mount._type = type
        btn_mount._mount_uri = mount_uri
        btn_mount._mount_name = mount_name
        btn_mount._lbl_volume_name = lbl_volume_name
        btn_mount._lbl_volume_size_info = lbl_volume_size_info
        btn_mount._pb_volume_size = pb_volume_size
        btn_mount._stack_mount = stack_mount
        btn_mount.connect("clicked", self.on_btn_mount_clicked)

        btn_unmount = Gtk.Button.new()
        btn_unmount.set_image(Gtk.Image.new_from_icon_name("media-playback-stop-symbolic", Gtk.IconSize.BUTTON  ))
        btn_unmount.set_relief(Gtk.ReliefStyle.NONE)
        btn_unmount.set_valign(Gtk.Align.CENTER)
        btn_unmount.set_tooltip_text(_("Unmount"))
        btn_unmount._volume = vl
        btn_unmount._is_removable = is_removable
        btn_unmount._main_type = main_type
        btn_unmount._type = type
        btn_unmount._mount_uri = mount_uri
        btn_unmount._mount_name = mount_name
        btn_unmount._lbl_volume_name = lbl_volume_name
        btn_unmount._lbl_volume_size_info = lbl_volume_size_info
        btn_unmount._pb_volume_size = pb_volume_size
        btn_unmount._stack_mount = stack_mount
        if self.mount_inprogress:
            btn_unmount.set_sensitive(False)
        else:
            btn_unmount.set_sensitive(True)
        btn_unmount.connect("clicked", self.on_btn_unmount_clicked)

        stack_mount.add_named(btn_mount, "mount")
        stack_mount.add_named(btn_unmount, "unmount")
        stack_mount.get_child_by_name("mount").show()
        stack_mount.get_child_by_name("unmount").show()



        btn_eject = Gtk.Button.new()
        btn_eject.set_image(Gtk.Image.new_from_icon_name("media-eject-symbolic", Gtk.IconSize.BUTTON  ))
        btn_eject.set_relief(Gtk.ReliefStyle.NONE)
        btn_eject.set_valign(Gtk.Align.CENTER)
        btn_eject.set_tooltip_text(_("Eject"))
        btn_eject._volume = vl
        btn_eject._is_removable = is_removable
        btn_eject._main_type = main_type
        btn_eject._type = type
        btn_eject._mount_uri = mount_uri
        btn_eject._mount_name = mount_name
        btn_eject._lbl_volume_name = lbl_volume_name
        btn_eject._lbl_volume_size_info = lbl_volume_size_info
        btn_eject._pb_volume_size = pb_volume_size
        btn_eject.set_name("eject")
        if self.mount_inprogress:
            btn_eject.set_sensitive(False)
        else:
            btn_eject.set_sensitive(True)
        btn_eject.connect("clicked", self.on_btn_eject_clicked)



        stack_bookmark = Gtk.Stack.new()

        btn_bookmark_add = Gtk.Button.new()
        btn_bookmark_add.set_image(Gtk.Image.new_from_icon_name("bookmark-new-symbolic", Gtk.IconSize.BUTTON  ))
        btn_bookmark_add.set_relief(Gtk.ReliefStyle.NONE)
        btn_bookmark_add.set_valign(Gtk.Align.CENTER)
        btn_bookmark_add.set_tooltip_text(_("Add Bookmark"))
        btn_bookmark_add._volume = vl
        btn_bookmark_add._mount_uri = mount_uri
        btn_bookmark_add._mount_name = mount_name
        btn_bookmark_add._stack_bookmark = stack_bookmark
        btn_bookmark_add.connect("clicked", self.on_btn_save_othermount_clicked)

        btn_bookmark_delete = Gtk.Button.new()
        btn_bookmark_delete.set_image(Gtk.Image.new_from_icon_name("edit-delete-symbolic", Gtk.IconSize.BUTTON  ))
        btn_bookmark_delete.set_relief(Gtk.ReliefStyle.NONE)
        btn_bookmark_delete.set_valign(Gtk.Align.CENTER)
        btn_bookmark_delete.set_tooltip_text(_("Remove Bookmark"))
        btn_bookmark_delete._volume = vl
        btn_bookmark_delete._mount_uri = mount_uri
        btn_bookmark_delete._mount_name = mount_name
        btn_bookmark_delete._stack_bookmark = stack_bookmark
        btn_bookmark_delete.connect("clicked", self.on_btn_delete_othermount_clicked)

        stack_bookmark.add_named(btn_bookmark_add, "add")
        stack_bookmark.add_named(btn_bookmark_delete, "delete")
        stack_bookmark.get_child_by_name("add").show()
        stack_bookmark.get_child_by_name("delete").show()

        if main_type == "network" or main_type == "saved":
            servers = self.UserSettings.getSavedServer()
            if mount_uri == "":
                mount_uri = vl.get_root().get_uri().strip()
            if any(d["uri"] == mount_uri for d in servers):
                stack_bookmark.set_visible_child_name("delete")
            else:
                stack_bookmark.set_visible_child_name("add")

        show_info = True
        if is_removable:
            if main_type == "saved":
                show_info = False
            elif main_type == "drive" or main_type == "volume":
                if not vl.get_mount():
                    show_info = False
        else:
            if not vl.get_mount():
                show_info = False


        btn_info = Gtk.Button.new()
        btn_info.set_image(Gtk.Image.new_from_icon_name("dialog-information-symbolic", Gtk.IconSize.BUTTON  ))
        btn_info.set_relief(Gtk.ReliefStyle.NONE)
        btn_info.set_valign(Gtk.Align.CENTER)
        btn_info.set_tooltip_text(_("Information"))
        btn_info._lbl_volume_name = lbl_volume_name
        btn_info._lbl_volume_size_info = lbl_volume_size_info
        btn_info._pb_volume_size = pb_volume_size
        btn_info._stack_mount = stack_mount
        btn_info._volume = vl
        btn_info._is_removable = is_removable
        btn_info._main_type = main_type
        btn_info._type = type
        btn_info._mount_uri = mount_uri
        btn_info._mount_name = mount_name
        btn_info.connect("clicked", self.on_btn_volume_info_clicked)




        box_volume.add(img_volume)
        box_volume.pack_start(box_volume_info, True, True, 0)
        box_volume.pack_start(stack_mount, False, True, 0)
        if is_ejectable and type != "card":
            box_volume.pack_start(btn_eject, False, True, 0)
        if main_type == "network" or main_type == "saved":
            box_volume.pack_start(stack_bookmark, False, True, 0)
        if show_info:
            box_volume.pack_start(btn_info, False, True, 0)
        # box_volume.pack_end(btn_volume_settings, False, True, 0)
        box_volume.props.margin = 8


        # Add to listbox
        listbox.prepend(box_volume)
        row = listbox.get_row_at_index(0)
        row.set_can_focus(False)
        row._volume = vl
        row._main_type = main_type
        row._type = type
        row._lbl_volume_name = lbl_volume_name
        row._lbl_volume_size_info = lbl_volume_size_info
        row._pb_volume_size = pb_volume_size

        row._mount_uri = mount_uri
        row._mount_name = mount_name

        row._stack_mount = stack_mount

        # Disable asking mount on app startup
        # self.tryMountVolume(row)
        self.showVolumeSizes(row)

    def addDisksToGUI(self):
        # Home:
        home_info = DiskManager.get_file_info(GLib.get_home_dir())
        self.lbl_home_path.set_markup("<small>( {} )</small>".format(GLib.get_home_dir()))
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

                # Volume ListBox
                listbox = Gtk.ListBox.new()
                listbox.set_selection_mode(Gtk.SelectionMode.NONE)
                listbox.connect("row-activated", self.on_volume_row_activated)
                listbox.get_style_context().add_class("pardus-mycomputer-listbox")
                # frame.add(listbox)

                # Add Volumes to the ListBox:
                for vl in dr.get_volumes():
                    try:
                        ejectable = vl.can_eject()
                    except:
                        ejectable = False
                    self.addVolumeRow(vl, listbox, False, ejectable)

                #self.box_drives.add(lbl_drive_name)
                self.box_drives.add(listbox)

        self.box_drives.show_all()
        
    def addRemovableDevicesToList(self):
        self.box_removables.foreach(lambda child: self.box_removables.remove(child))

        connected_drives = self.vm.get_connected_drives()

        # usb stick, card, optical drive
        for dr in connected_drives:
            if dr.has_volumes() and dr.is_removable():
                # print("{} {}".format(dr.get_name(), dr.can_eject()))
                # print("{} {}".format(dr.get_name(), dr.get_icon().to_string()))
                # print("{} {}".format(dr.get_name(), dr.get_identifier(Gio.VOLUME_IDENTIFIER_KIND_UNIX_DEVICE)))

                # Volume ListBox
                listbox = Gtk.ListBox.new()
                listbox.set_selection_mode(Gtk.SelectionMode.NONE)
                listbox.connect("row-activated", self.on_volume_row_activated)
                listbox.get_style_context().add_class("pardus-mycomputer-listbox")

                # Add Volumes to the ListBox:
                for vl in dr.get_volumes():
                    try:
                        ejectable = vl.can_eject()
                    except:
                        ejectable = False
                    self.addVolumeRow(vl, listbox, True, ejectable, main_type="drive", type=self.control_drive_type(vl))
                    try:
                        if vl.get_mount():
                            self.mount_paths.append(vl.get_mount().get_root().get_path())
                    except Exception as e:
                        print("mount_paths append error: {}".format(e))
                
                self.box_removables.add(listbox)


        # disk images, phones
        drives = []
        for cd in connected_drives:
            if cd.get_volumes():
                for gvcd in cd.get_volumes():
                    drives.append(gvcd)
        all_volumes = self.vm.get_volumes()
        volumes = [vol for vol in all_volumes if vol not in drives]

        for volume in volumes:
            if volume.get_drive() is None:

                # print("{} {}".format(volume.get_name(), volume.get_icon().to_string()))
                # print("{} {}".format(volume.get_name(), volume.get_identifier(Gio.VOLUME_IDENTIFIER_KIND_UNIX_DEVICE)))

                # Volume ListBox
                listbox = Gtk.ListBox.new()
                listbox.set_selection_mode(Gtk.SelectionMode.NONE)
                listbox.connect("row-activated", self.on_volume_row_activated)
                listbox.get_style_context().add_class("pardus-mycomputer-listbox")

                try:
                    ejectable = volume.can_eject()
                except:
                    ejectable = False

                # Add Volumes to the ListBox:
                self.addVolumeRow(volume, listbox, True, ejectable, main_type="volume", type=self.control_volume_type(volume))

                try:
                    if volume.get_mount():
                        self.mount_paths.append(volume.get_mount().get_root().get_path())
                except Exception as e:
                    print("mount_paths append error: {}".format(e))

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

                    # Volume ListBox
                    listbox = Gtk.ListBox.new()
                    listbox.set_selection_mode(Gtk.SelectionMode.NONE)
                    listbox.connect("row-activated", self.on_volume_row_activated)
                    listbox.get_style_context().add_class("pardus-mycomputer-listbox")

                    try:
                        ejectable = mount.can_eject()
                    except:
                        ejectable = False

                    # Add Volumes to the ListBox:
                    self.addVolumeRow(mount, listbox, True, ejectable, main_type="network")

                    self.box_removables.add(listbox)

                    uri = mount.get_root().get_uri()
                    name = mount.get_name()
                    self.net_mounts.append({"uri": uri, "name": name})

        # saved servers
        saveds = self.UserSettings.getSavedServer()
        for saved in saveds:

            if not any(d["uri"] == saved["uri"] for d in self.net_mounts):

                # Volume ListBox
                listbox = Gtk.ListBox.new()
                listbox.set_selection_mode(Gtk.SelectionMode.NONE)
                listbox.connect("row-activated", self.on_volume_row_activated)
                listbox.get_style_context().add_class("pardus-mycomputer-listbox")

                # Add Volumes to the ListBox:
                self.addVolumeRow(saved["uri"], listbox, True, False, main_type="saved", mount_uri=saved["uri"], mount_name=saved["name"])

                # self.box_removables.add(lbl_drive_name)
                self.box_removables.add(listbox)
            # else:
            #     print("saved {} mount uri already in net_mounts".format(saved["uri"]))
        
        self.box_removables.show_all()


    def control_drive_type(self, volume):

        if self.is_usbdrive(volume):
            return "usbdrive"
        elif self.is_card(volume):
            return "card"
        elif self.is_optical(volume):
            return "optical"

    def is_usbdrive(self, volume):
        usbstick = False
        try:
            if "{}".format(volume.get_identifier(Gio.VOLUME_IDENTIFIER_KIND_UNIX_DEVICE)).startswith("/dev/sd"):
                usbstick = True
        except Exception as e:
            print("Error in get_identifier(): {}".format(e))

        try:
            iconstring = volume.get_icon().to_string()
            if "media-removable" in iconstring or "drive-removable" in iconstring:
                usbstick = True
        except Exception as e:
                print("Error in get_symbolic_icon(): {}".format(e))

        return usbstick

    def is_card(self, volume):
        card = False
        try:
            if "{}".format(volume.get_identifier(Gio.VOLUME_IDENTIFIER_KIND_UNIX_DEVICE)).startswith("/dev/mmc"):
                card = True
        except Exception as e:
            print("Error in get_identifier(): {}".format(e))

        try:
            if "flash" in volume.get_icon().to_string():
                card = True
        except Exception as e:
                print("Error in get_icon(): {}".format(e))

        return card

    def is_optical(self, volume):
        optical = False
        try:
            if "{}".format(volume.get_identifier(Gio.VOLUME_IDENTIFIER_KIND_UNIX_DEVICE)).startswith("/dev/sr"):
                optical = True
        except Exception as e:
            print("Error in get_identifier(): {}".format(e))

        try:
            if "optical" in volume.get_icon().to_string():
                optical = True
        except Exception as e:
                print("Error in get_symbolic_icon(): {}".format(e))

        return optical

    def control_volume_type(self, volume):
        if not self.is_phone(volume):
            return "image"
        else:
            return "phone"

    def is_phone(self, volume):
        phone = False
        try:
            if "/usb/" in volume.get_identifier(Gio.VOLUME_IDENTIFIER_KIND_UNIX_DEVICE):
                phone = True
        except Exception as e:
            print("Error in get_identifier(): {}".format(e))

        try:
            if "phone" in volume.get_icon().to_string():
                phone = True
        except Exception as e:
                print("Error in get_symbolic_icon(): {}".format(e))

        return phone

    def add_recents_from_file(self):
        servers = self.UserSettings.getRecentServer()
        if servers:
            for server in servers:
                if len(server.split(" ")) > 1:
                    uri, name = server.split(" ", 1)
                else:
                    uri = server
                    name = ""
                self.add_to_recent_listbox(uri, name)
            self.listbox_recent_servers.show_all()

    def get_display_name(self, mount):
        try:
            name = mount.get_root().query_info(Gio.FILE_ATTRIBUTE_STANDARD_DISPLAY_NAME, Gio.FileQueryInfoFlags.NONE,
                                           None).get_attribute_as_string(Gio.FILE_ATTRIBUTE_STANDARD_DISPLAY_NAME)
        except:
            name = ""

        return name

    # Window methods:
    def onDestroy(self, action):
        self.window.get_application().quit()



    # SIGNALS:
    def on_lb_home_row_activated(self, listbox, row):
        subprocess.run(["xdg-open", GLib.get_home_dir()])
        if self.UserSettings.config_closeapp_directories:
            self.onDestroy(listbox)

    def on_lb_root_row_activated(self, listbox, row):
        subprocess.run(["xdg-open", "/"])
        if self.UserSettings.config_closeapp_directories:
            self.onDestroy(listbox)

    def on_btn_mount_clicked(self, button):
        try:
            mount  = button._volume.get_mount()
        except:
            mount = button._volume

        if mount == None:
            self.tryMountVolume(button)
        else:
            if isinstance(mount, str):
                self.on_btn_mount_connect_clicked(button=None, from_saved=True, saved_uri=mount)
            else:
                subprocess.run(["xdg-open", mount.get_root().get_path()])


    def on_btn_unmount_clicked(self, button):
        self.actioned_volume = button

        self.disable_unmount_eject_buttons()

        body = ""
        summary = _("Please wait")

        if button._main_type == "network":
            body = _("Network device is unmounting.")
            mount_point = button._volume.get_root().get_path()
            mount = button._volume
        else:
            mount_point = button._volume.get_mount().get_root().get_path()
            mount = button._volume.get_mount()
            if not button._is_removable:
                body = _("Disk is unmounting.")
            else:
                if button._main_type == "drive":
                    if button._type == "usbdrive":
                        body = _("USB disk is unmounting.")
                    elif button._type == "card":
                        body = _("Card drive is unmounting.")
                    elif button._type == "optical":
                        body = _("Optical disk is unmounting.")
                elif button._main_type == "volume":
                    if button._type == "image":
                        body = _("Optical drive is unmounting.")
                    elif button._type == "phone":
                        body = _("Phone is unmounting.")

        if button._main_type == "network":
            try:
                display_name = mount.get_name()
            except:
                display_name = ""
        else:
            display_name = self.get_display_name(mount)
        if display_name != "":
            body = "{}\n({})".format(body, display_name)

        self.notify(summary, body, "emblem-synchronizing-symbolic")

        command = [os.path.dirname(os.path.abspath(__file__)) + "/Unmount.py", "unmount", mount_point]
        self.startProcess(command)


    def on_btn_eject_clicked(self, button):
        self.actioned_volume = button

        self.disable_unmount_eject_buttons()

        if button._volume.get_mount():
            mount_point = button._volume.get_mount().get_root().get_path()
            mount = button._volume.get_mount()

            body = ""
            summary = _("Please wait")
            if button._main_type == "drive":
                if button._type == "usbdrive":
                    body = _("USB disk is unmounting.")
                elif button._type == "card":
                    body = _("Card drive is unmounting.")
                elif button._type == "optical":
                    body = _("Optical disk is unmounting.")
            elif button._main_type == "volume":
                if button._type == "image":
                    body = _("Optical drive is unmounting.")
                elif button._type == "phone":
                    body = _("Phone is unmounting.")

            display_name = self.get_display_name(mount)
            if display_name != "":
                body = "{}\n({})".format(body, display_name)

            print("{} is mounted, will be ejected after unmount".format(display_name))

            self.notify(summary, body, "emblem-synchronizing-symbolic")

            command = [os.path.dirname(os.path.abspath(__file__)) + "/Unmount.py", "unmount", mount_point]
            self.startEjectProcess(command)

        else:
            summary = _("Device ejected.")
            body = button._volume.get_name()
            print("{} is not mounted, ejecting".format(body))
            def on_ejected(volume, task):
                try:
                    volume.eject_with_operation_finish(task)
                    self.notify(summary, body, "emblem-ok-symbolic")
                    print("{} successfully ejected".format(body))
                    self.mount_inprogress = False
                    if self.actioned_volume._is_removable:
                        self.spinner_removable.stop()
                    else:
                        self.spinner_harddrive.stop()
                    return True
                except Exception as e:
                    self.mount_inprogress = False
                    self.addDisksToGUI()
                    if self.actioned_volume._is_removable:
                        self.spinner_removable.stop()
                    else:
                        self.spinner_harddrive.stop()
                    print("{}".format(e))
                    return False
            button._volume.eject_with_operation(Gio.MountUnmountFlags.FORCE, self.mount_operation, None, on_ejected)

    def disable_unmount_eject_buttons(self):

        if self.actioned_volume._is_removable:
            self.spinner_removable.start()
        else:
            self.spinner_harddrive.start()

        for row in self.box_removables:
            for child in row.get_children()[0].get_children()[0]:
                if child.get_name() == "eject":
                    child.set_sensitive(False)
                    self.mount_inprogress = True
            if row.get_children()[0].get_children()[0].get_children()[2].get_visible_child_name() == "unmount":
                row.get_children()[0].get_children()[0].get_children()[2].get_children()[1].set_sensitive(False)
                self.mount_inprogress = True

        for row in self.box_drives:
            for child in row.get_children()[0].get_children()[0]:
                if child.get_name() == "eject":
                    child.set_sensitive(False)
                    self.mount_inprogress = True
            if row.get_children()[0].get_children()[0].get_children()[2].get_visible_child_name() == "unmount":
                row.get_children()[0].get_children()[0].get_children()[2].get_children()[1].set_sensitive(False)
                self.mount_inprogress = True

    def on_volume_row_activated(self, listbox, row):
        try:
            mount  = row._volume.get_mount()
        except:
            mount = row._volume

        if mount == None:
            self.tryMountVolume(row)
        else:
            if isinstance(mount, str):
                self.on_btn_mount_connect_clicked(button=None, from_saved=True, saved_uri=mount)
            else:
                th = subprocess.Popen("xdg-open {} &".format(mount.get_root().get_path()), shell=True)
                th.communicate()

                # some times phone's disk usage infos not showing on first mount,
                # we can update this values on phone row clicked
                # fix this late
                if row._type == "phone":
                    self.showVolumeSizes(row)

            if not isinstance(row._volume, str):
                self.onDestroy(row)

    def on_btn_volume_info_clicked(self, button):
        # clear all disk info labels
        self.dlg_lbl_name.set_label("")
        self.dlg_lbl_model.set_label("")
        self.dlg_lbl_dev.set_label("")
        self.dlg_lbl_mountpoint.set_label("")
        self.dlg_lbl_used_gb.set_label("")
        self.dlg_lbl_free_gb.set_label("")
        self.dlg_lbl_total_gb.set_label("")
        self.dlg_lbl_filesystem_type.set_label("")

        self.popover_volume_actionbox.foreach(lambda child: self.popover_volume_actionbox.remove(child))

        # disable auto refreshing because the popover is closing when auto refresh while open
        if self.autorefresh_glibid:
            GLib.source_remove(self.autorefresh_glibid)

        self.popover_volume.set_relative_to(button)
        self.popover_volume.set_position(Gtk.PositionType.LEFT)
        self.popover_volume.popup()

        try:
            mount = button._volume.get_mount()
        except:
            mount = button._volume
        if mount == None:
            # self.tryMountVolume(button)
            return

        def add_button_for_usb():
            btn_format = Gtk.Button.new()
            btn_format.set_label(_("Format"))
            btn_format._volume = button._volume
            btn_format.connect("clicked", self.on_btn_format_removable_clicked)
            self.popover_volume_actionbox.add(btn_format)
            self.popover_volume_actionbox.show_all()

        def add_button_for_disk():
            btn_mount_on_startup = Gtk.CheckButton.new()
            btn_mount_on_startup.set_label(_("Mount on Startup"))
            btn_mount_on_startup._volume = button._volume

            mount_point = mount.get_root().get_path()
            selected_volume_info = DiskManager.get_file_info(mount_point, network=True if button._main_type == "network" else False)
            btn_mount_on_startup.set_active(DiskManager.is_drive_automounted(selected_volume_info["device"]))
            btn_mount_on_startup._device = selected_volume_info["device"]

            btn_mount_on_startup.connect("clicked", self.on_button_mount_on_startup_clicked)
            self.popover_volume_actionbox.add(btn_mount_on_startup)
            self.popover_volume_actionbox.show_all()

        if not button._is_removable:
            add_button_for_disk()
        else:
            if button._main_type == "drive" and button._type == "usbdrive":
                add_button_for_usb()

        if not isinstance(mount, str):
            self.showDiskDetailsDialog(button)

            # some times phone's disk usage infos not showing on first mount,
            # we can update this values on phone info button clicked
            # fix this later
            if button._type == "phone":
                self.showVolumeSizes(button)
        else:
           print("saved drive")

    def on_popover_volume_closed(self, popover):
        # auto refresh control of disks
        self.autorefresh()

    def on_btn_refresh_clicked(self, button):
        print("Manually refreshing disks")
        self.addDisksToGUI()

    def on_sw_closeapp_directories_state_set(self, switch, state):
        user_config_closeapp_directories = self.UserSettings.config_closeapp_directories
        if state != user_config_closeapp_directories:
            print("Updating close app directories state")
            try:
                self.UserSettings.writeConfig(state,
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
                self.UserSettings.writeConfig(self.UserSettings.config_closeapp_directories,
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
    def on_button_mount_on_startup_clicked(self, button):
        DiskManager.set_automounted(button._device, button.get_active())

    # def on_cb_mount_on_startup_released(self, cb):
    #     DiskManager.set_automounted(self.selected_volume_info["device"], cb.get_active())
    
    def on_btn_format_removable_clicked(self, button):
        mount_point = button._volume.get_mount().get_root().get_path()
        file_info = DiskManager.get_file_info(mount_point)
        self.popover_volume.popdown()

        subprocess.Popen(["pardus-usb-formatter", file_info["device"]])

    def on_mount_added(self, volumemonitor, mount):
        self.addHardDisksToList()
        self.addRemovableDevicesToList()
        self.mount_paths.clear()
        self.net_mounts.clear()
        # print("on_mount_added")

    def on_mount_removed(self, volumemonitor, mount):
        GLib.idle_add(self.addHardDisksToList)
        GLib.idle_add(self.addRemovableDevicesToList)
        GLib.idle_add(self.mount_paths.clear)
        GLib.idle_add(self.net_mounts.clear)
        # print("on_mount_removed")

    def on_btn_save_othermount_clicked(self, button):
        uri = button._volume.get_root().get_uri().strip()
        name = button._volume.get_name().strip()
        print("saving server: {} {}".format(uri, name))
        self.UserSettings.addSavedServer(uri, name)
        self.control_save_server_button(button, uri, name)

    def on_btn_delete_othermount_clicked(self, button):
        uri = button._mount_uri
        name = button._mount_name
        refresh = True
        try:
            if uri == "":
                uri = button._volume.get_root().get_uri().strip()
                refresh = False
            if name == "":
                name = button._volume.get_name().strip()
        except:
            pass

        print("deleting saved server: {} {}".format(uri, name))
        self.UserSettings.removeSavedServer("{} {}".format(uri, name).strip())
        self.control_save_server_button(button, uri, name)

        if refresh:
            GLib.idle_add(self.addHardDisksToList)
            GLib.idle_add(self.addRemovableDevicesToList)
            GLib.idle_add(self.mount_paths.clear)
            GLib.idle_add(self.net_mounts.clear)


    def control_save_server_button(self, button, uri, name):
        servers = self.UserSettings.getSavedServer()
        # self.btn_save_removable.set_sensitive(not any(d["uri"] == uri for d in servers))

        if any(d["uri"] == uri for d in servers):
            button._stack_bookmark.set_visible_child_name("delete")
        else:
            button._stack_bookmark.set_visible_child_name("add")


    def network_mount_success(self, uri, name):
        in_list = False
        for row in self.listbox_recent_servers:
            if row.get_children()[0].name == "{} {}".format(uri, name).strip():
                in_list = True
                print("{} {} already in recent list".format(uri, name).strip())
        if not in_list:
            self.add_to_recent_listbox(uri, name)
            self.UserSettings.addRecentServer(uri, name)

        self.listbox_recent_servers.show_all()

        subprocess.run(["xdg-open", uri])

        self.entry_addr.set_text("")

    def add_to_recent_listbox(self, uri, name):
        label = Gtk.Label.new()
        label.set_markup("<b>{}</b>\n<small>{}</small>".format(
            GLib.markup_escape_text(name if name != "" else uri, -1), GLib.markup_escape_text(uri, -1)))
        button = Gtk.Button.new()
        button.name = "{} {}".format(uri, name).strip()
        button.connect("clicked", self.remove_from_recent_clicked)
        button.props.valign = Gtk.Align.CENTER
        button.props.halign = Gtk.Align.CENTER
        button.props.always_show_image = True
        button.set_image(Gtk.Image.new_from_icon_name("edit-delete-symbolic", Gtk.IconSize.BUTTON))
        button.set_relief(Gtk.ReliefStyle.NONE)
        box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
        box.set_margin_top(5)
        box.set_margin_bottom(5)
        box.set_margin_start(5)
        box.set_margin_end(5)
        box.pack_start(label, False, True, 0)
        box.pack_end(button, False, True, 0)
        box.name = "{} {}".format(uri, name).strip()
        self.listbox_recent_servers.add(box)

    def remove_from_recent_clicked(self, button):
        for row in self.listbox_recent_servers:
            if row.get_children()[0].name == button.name:
                self.listbox_recent_servers.remove(row)

        self.UserSettings.removeRecentServer(button.name)

    def on_btn_mount_connect_clicked(self, button, from_saved=False, saved_uri=""):
        def get_uri_name(source_object):
            try:
                uri = source_object.get_uri()
            except:
                if not from_saved:
                    uri = self.entry_addr.get_text()
                else:
                    uri = ""

            try:
                name = source_object.query_info(Gio.FILE_ATTRIBUTE_STANDARD_DISPLAY_NAME, Gio.FileQueryInfoFlags.NONE,
                                                None).get_attribute_as_string(Gio.FILE_ATTRIBUTE_STANDARD_DISPLAY_NAME)
            except:
                try:
                    name = source_object.get_uri()
                except:
                    if not from_saved:
                        name = self.entry_addr.get_text()
                    else:
                        name = ""

            return uri, name

        def on_mounted(source_object, res):
            self.spinner_header.stop()
            try:
                source_object.mount_enclosing_volume_finish(res)
                uri,name = get_uri_name(source_object)
                self.network_mount_success(uri, name)
                return True
            except GLib.GError as err:
                if err.code == Gio.IOErrorEnum.ALREADY_MOUNTED:
                    uri, name = get_uri_name(source_object)
                    self.network_mount_success(uri, name)
                    return True
                elif err.code == Gio.IOErrorEnum.FAILED_HANDLED:
                    print("operation cancelled")
                else:
                    self.dialog_mount_error.set_markup("<big><b>{}</b></big>".format(_("Error")))
                    self.dialog_mount_error.format_secondary_markup("{}".format(_(err.message)))
                    self.dialog_mount_error.run()
                    self.dialog_mount_error.hide()
                    print("{}".format(err.message))

        def ask_password_cb(mount_operation, message, default_user, default_domain, flags):
            print(message)
            print(flags)

            if Gio.AskPasswordFlags.ANONYMOUS_SUPPORTED & flags:
                self.box_anonym.set_visible(True)
                self.box_user_domain_pass.set_sensitive(not self.mount_anonym_options.get_active())
                self.box_password_options.set_sensitive(not self.mount_anonym_options.get_active())
            else:
                self.box_anonym.set_visible(False)

            if Gio.AskPasswordFlags.NEED_USERNAME & flags:
                self.box_username.set_visible(True)
            else:
                self.box_username.set_visible(False)

            if Gio.AskPasswordFlags.NEED_DOMAIN & flags:
                self.box_domain.set_visible(True)
            else:
                self.box_domain.set_visible(False)

            if Gio.AskPasswordFlags.NEED_PASSWORD & flags:
                self.box_password.set_visible(True)
                self.box_password_options.set_visible(True)
            else:
                self.box_password.set_visible(False)
                self.box_password_options.set_visible(False)

            if Gio.AskPasswordFlags.SAVING_SUPPORTED  & flags:
                self.box_password_options.set_visible(True)
            else:
                self.box_password_options.set_visible(False)

            passwd_option = 1
            self.lbl_mount_message.set_markup("<b>{}</b>".format(_(message)))
            self.entry_mount_username.set_text(default_user)
            self.entry_mount_password.set_text("")
            self.entry_mount_domain.set_text(default_domain)
            response = self.dialog_mount.run()
            self.dialog_mount.hide()
            self.lbl_mount_message.grab_focus()

            if response == Gtk.ResponseType.OK:
                for radio in self.mount_password_options.get_group():
                    if radio.get_active():
                        passwd_option = int(radio.get_name())

                if Gio.AskPasswordFlags.ANONYMOUS_SUPPORTED & flags:
                    mount_operation.set_anonymous(self.mount_anonym_options.get_active())

                if Gio.AskPasswordFlags.NEED_USERNAME & flags:
                    mount_operation.set_username(self.entry_mount_username.get_text())

                if Gio.AskPasswordFlags.NEED_PASSWORD & flags:
                    mount_operation.set_password(self.entry_mount_password.get_text())

                if Gio.AskPasswordFlags.SAVING_SUPPORTED & flags:
                    mount_operation.set_password_save(Gio.PasswordSave(passwd_option))

                if Gio.AskPasswordFlags.NEED_DOMAIN & flags:
                    mount_operation.set_domain(self.entry_mount_domain.get_text())
                mount_operation.reply(Gio.MountOperationResult.HANDLED)


            elif response == Gtk.ResponseType.CANCEL:
                mount_operation.reply(Gio.MountOperationResult.ABORTED)

        def ask_question_cb(mount_operation, message, choices):
            print("in ask_question_cb")
            print(message)
            print(choices)
            # set as 0 for now
            # FIXME
            # add dialog for this too
            mount_operation.set_choice(0)
            mount_operation.reply(Gio.MountOperationResult.HANDLED)

        if not from_saved:

            self.popover_connect.popdown()
            addr = self.entry_addr.get_text()

            file = Gio.File.new_for_commandline_arg(addr)
            mount_operation = Gio.MountOperation()
            # mount_operation.set_domain(addr)
            mount_operation.connect("ask-password", ask_password_cb)
            mount_operation.connect("ask-question", ask_question_cb)
            file.mount_enclosing_volume(Gio.MountMountFlags.NONE, mount_operation, None, on_mounted)
        else:
            file = Gio.File.new_for_commandline_arg(saved_uri)
            mount_operation = Gio.MountOperation()
            mount_operation.connect("ask-password", ask_password_cb)
            mount_operation.connect("ask-question", ask_question_cb)
            file.mount_enclosing_volume(Gio.MountMountFlags.NONE, mount_operation, None, on_mounted)

        self.spinner_header.start()


    def on_mount_anonym_options_toggled(self, widget):
        self.box_user_domain_pass.set_sensitive(not widget.get_active())
        self.box_password_options.set_sensitive(not widget.get_active())

    def on_entry_mount_password_icon_press(self, entry, icon_pos, event):
        entry.set_visibility(True)
        entry.set_icon_from_icon_name(Gtk.EntryIconPosition(1), "view-conceal-symbolic")

    def on_entry_mount_password_icon_release(self, entry, icon_pos, event):
        entry.set_visibility(False)
        entry.set_icon_from_icon_name(Gtk.EntryIconPosition(1), "view-reveal-symbolic")

    def on_btn_mount_connect_ok_clicked(self, button):
        self.dialog_mount.response(Gtk.ResponseType.OK)

    def on_btn_mount_cancel_clicked(self, button):
        self.dialog_mount.hide()
        self.dialog_mount.response(Gtk.ResponseType.CANCEL)

    def on_entry_addr_changed(self, editable):
        if editable.get_text().strip() != "":
            self.btn_mount_connect.set_sensitive(True)
        else:
            self.btn_mount_connect.set_sensitive(False)

    def on_entry_addr_icon_press(self, entry, icon_pos, event):
        self.popover_connect_examples.popup()

    def on_btn_server_list_toggled(self, widget):
        if len(self.listbox_recent_servers) > 0:
            self.stack_recent_servers.set_visible_child_name("list")
        else:
            self.stack_recent_servers.set_visible_child_name("empty")

    def on_listbox_recent_servers_row_activated(self, list_box, row):
        self.entry_addr.set_text("{}".format(row.get_children()[0].name.split(" ")[0]))
        self.popover_recent_servers.popdown()

    def on_btn_settings_clicked(self, button):
        if self.stack_main.get_visible_child_name() == "settings":
            self.stack_main.set_visible_child_name("home")
            self.img_settings.set_from_icon_name("preferences-system-symbolic", Gtk.IconSize.BUTTON)
        elif self.stack_main.get_visible_child_name() == "home":
            self.sw_closeapp_directories.set_state(self.UserSettings.config_closeapp_directories)
            self.sw_autorefresh.set_state(self.UserSettings.config_autorefresh)
            self.stack_main.set_visible_child_name("settings")
            self.img_settings.set_from_icon_name("user-home-symbolic", Gtk.IconSize.BUTTON)
            self.control_defaults()

    def on_btn_defaults_clicked(self, button):
        self.UserSettings.createDefaultConfig(force=True)
        self.user_settings()
        self.sw_closeapp_directories.set_state(self.UserSettings.config_closeapp_directories)
        self.sw_autorefresh.set_state(self.UserSettings.config_autorefresh)

    def control_defaults(self):
        if self.UserSettings.config_closeapp_directories != self.UserSettings.default_closeapp_directories or \
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
            print("{}".format(e))
            try:
                subprocess.Popen(["gnome-control-center", "info-overview"])
            except Exception as e:
                print("{}".format(e))
                try:
                    subprocess.Popen(["xfce4-about"])
                except Exception as e:
                    print("{}".format(e))
                    try:
                        subprocess.Popen(["cinnamon-settings", "info"])
                    except Exception as e:
                        print("{}".format(e))
                        try:
                            subprocess.Popen(["mate-about"])
                        except Exception as e:
                            print("{}".format(e))
                            print("no about app found")

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
        self.mount_inprogress = False

        if self.actioned_volume._is_removable:
            self.spinner_removable.stop()
        else:
            self.spinner_harddrive.stop()

        body = ""
        summary = _("Unmounting process is done")

        if self.actioned_volume._main_type == "network":
            mount = self.actioned_volume._volume
            body = _("You can eject the network device.")
            self.net_mounts.clear()
        else:
            mount = self.actioned_volume._volume.get_mount()
            if not self.actioned_volume._is_removable:
                body = _("You can eject the disk.")
            else:
                if self.actioned_volume._main_type == "drive":
                    if self.actioned_volume._type == "usbdrive":
                        body = _("You can eject the USB disk.")
                    elif self.actioned_volume._type == "card":
                        body = _("You can eject the card drive.")
                    elif self.actioned_volume._type == "optical":
                        body = _("You can eject the optical disk.")
                elif self.actioned_volume._main_type == "volume":
                    if self.actioned_volume._type == "image":
                        body = _("You can eject the optical drive.")
                    elif self.actioned_volume._type == "phone":
                        body = _("You can eject the phone.")

        if self.actioned_volume._main_type == "network":
            try:
                display_name = mount.get_name()
            except:
                display_name = ""
        else:
            display_name = self.get_display_name(mount)
        if display_name != "":
            body = "{}\n({})".format(body, display_name)

        def on_unmounted(mount, task):
            try:
                mount.unmount_with_operation_finish(task)
                self.notify(summary, body, "emblem-ok-symbolic")
                print("{} successfully unmounted".format(display_name))
                return True
            except Exception as e:
                self.addDisksToGUI()
                print("{}".format(e))
                return False

        mount.unmount_with_operation(Gio.MountUnmountFlags.FORCE, self.mount_operation, None, on_unmounted)



    def startEjectProcess(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.onEjectProcessStdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.onEjectProcessStderr)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, self.onEjectProcessExit)

        return pid

    def onEjectProcessStdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        print(line)
        return True

    def onEjectProcessStderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        print(line)
        return True

    def onEjectProcessExit(self, pid, status):
        # print(f'pid, status: {pid, status}')
        self.mount_inprogress = False

        if self.actioned_volume._is_removable:
            self.spinner_removable.stop()
        else:
            self.spinner_harddrive.stop()

        summary = _("Device ejected.")
        body = ""

        mount = self.actioned_volume._volume.get_mount()

        display_name = self.get_display_name(mount)
        if display_name != "":
            body = "{}\n({})".format(body, display_name)

        def on_ejected(volume, task):
            try:
                volume.eject_with_operation_finish(task)
                self.notify(summary, body, "emblem-ok-symbolic")
                print("{} successfully ejected".format(display_name))
                return True
            except Exception as e:
                self.mount_inprogress = False
                self.addDisksToGUI()
                print("{}".format(e))
                return False

        self.actioned_volume._volume.eject_with_operation(Gio.MountUnmountFlags.FORCE, self.mount_operation, None, on_ejected)

    def notify(self, message_summary="", message_body="", icon="pardus-mycomputer"):
        try:
            if Notify.is_initted():
                Notify.uninit()

            Notify.init(message_summary)
            notification = Notify.Notification.new(message_summary, message_body, icon)
            notification.show()
        except Exception as e:
            print("{}".format(e))
