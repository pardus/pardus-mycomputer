import os, subprocess

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk

import locale
from locale import gettext as tr

# Translation Constants:
APPNAME = "pardus-mycomputer"
TRANSLATIONS_PATH = "/usr/share/locale"
SYSTEM_LANGUAGE = os.environ.get("LANG")

# Translation functions:
locale.bindtextdomain(APPNAME, TRANSLATIONS_PATH)
locale.textdomain(APPNAME)
locale.setlocale(locale.LC_ALL, SYSTEM_LANGUAGE)
        

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

        # Global Definings
        self.defineComponents()
        self.defineVariables()

        # Add Disks to GUI
        self.addDisksToGUI()
        
        # Set application:
        self.application = application

        # Show Screen:
        self.window.show_all()

    def defineComponents(self):
        def UI(str):
            return self.builder.get_object(str)

        # Home
        self.lbl_home_path = UI("lbl_home_path")
        self.lbl_home_dev = UI("lbl_home_dev")
        self.lbl_home_size = UI("lbl_home_size")

        # Root
        self.lbl_root_dev = UI("lbl_root_dev")
        self.pb_root_usage = UI("pb_root_usage")
        self.lbl_root_free = UI("lbl_root_free")
        self.lbl_root_total = UI("lbl_root_total")

        
        # Drives
        self.box_drives = UI("box_drives")
        # Removables
        self.box_removables = UI("box_removables")

        # Popover
        self.drive_popover = UI("drive_popover")
    
    def defineVariables(self):
        self.mount_operation = Gio.MountOperation.new()


    def get_file_info(self, file):
        process = subprocess.run(f"df {file} --block-size=1000 | awk 'NR==1 {{next}} {{print $1,$2,$3,$4,$6; exit}}'", shell=True, capture_output=True)

        keys = ["device", "total_kb", "usage_kb", "free_kb", "mountpoint"]
        obj = dict(zip(keys, process.stdout.decode("utf-8").strip().split(" ")))
        obj["usage_percent"] = int(obj['usage_kb']) / int(obj['total_kb'])

        return obj
    

    def showVolumeSizes(self, vl, lbl_volume_name, lbl_volume_size_info, pb_volume_size, lbl_volume_dev_directory):
        fs_root = vl.get_mount().get_root()

        filesystem_size = fs_root.query_filesystem_info(Gio.FILE_ATTRIBUTE_FILESYSTEM_SIZE).get_attribute_uint64(Gio.FILE_ATTRIBUTE_FILESYSTEM_SIZE)
        filesystem_size_gb = filesystem_size/1000/1000/1000

        filesystem_size_free = fs_root.query_filesystem_info(Gio.FILE_ATTRIBUTE_FILESYSTEM_FREE).get_attribute_uint64(Gio.FILE_ATTRIBUTE_FILESYSTEM_FREE)
        filesystem_size_free_gb = filesystem_size_free/1000/1000/1000

        # Show values on UI
        lbl_volume_name.set_markup(
            f'<b>{vl.get_name()}</b> <span size="small" alpha="75%">{ vl.get_mount().get_root().get_parse_name() }</span>')
        pb_volume_size.set_fraction((filesystem_size - filesystem_size_free)/filesystem_size)
        lbl_volume_size_info.set_markup(f'<span size="small"><b>{filesystem_size_free_gb:.2f} GB</b> is free of {filesystem_size_gb:.2f} GB</span>')
        lbl_volume_dev_directory.set_markup(f'<span size="small" alpha="75%">{ vl.get_identifier(Gio.VOLUME_IDENTIFIER_KIND_UNIX_DEVICE) }</span>')

    
    def tryMountVolume(self, vl, lbl_volume_name, lbl_volume_size_info, pb_volume_size, lbl_volume_dev_directory):
        if not vl.can_mount() and vl.get_mount() == None:
            print("can't mount!")
            return False

        if vl.get_mount() == None:
            def on_mounted(vl, task, lbl_volume_size_info, pb_volume_size, lbl_volume_dev_directory):
                try:
                    vl.mount_finish(task)
                    
                    self.showVolumeSizes(vl, lbl_volume_name, lbl_volume_size_info, pb_volume_size, lbl_volume_dev_directory)
                    
                    return True
                except GLib.Error:
                    return False
            
            
            vl.mount(Gio.MountMountFlags.NONE, self.mount_operation, None, on_mounted, lbl_volume_size_info, pb_volume_size, lbl_volume_dev_directory)
        else:
            self.showVolumeSizes(vl, lbl_volume_name, lbl_volume_size_info, pb_volume_size, lbl_volume_dev_directory)
            return True
    
    def addVolumeToGUI(self, vl, listbox, is_removable):
        # Prepare UI Containers:
        box_volume = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 7)
        img_volume = Gtk.Image.new_from_icon_name(
            "drive-removable-media" if is_removable else "drive-harddisk",
            Gtk.IconSize.DIALOG)

        box_volume_info = Gtk.Box.new(Gtk.Orientation.VERTICAL, 3)

        # Volume infos
        lbl_volume_name = Gtk.Label.new()
        lbl_volume_name.set_markup(
            f'<b>{vl.get_name()}</b>')
        lbl_volume_name.set_halign(Gtk.Align.START)

        lbl_volume_dev_directory = Gtk.Label.new()
        lbl_volume_dev_directory.set_markup(
            f'<span size="small"> </span>')
        lbl_volume_dev_directory.set_halign(Gtk.Align.START)

        pb_volume_size = Gtk.ProgressBar.new()
        pb_volume_size.set_valign(Gtk.Align.CENTER)
        pb_volume_size.set_margin_end(7)

        lbl_volume_size_info = Gtk.Label.new()
        lbl_volume_size_info.set_markup(
            f"<span size=\"small\"> </span>")
        lbl_volume_size_info.set_halign(Gtk.Align.START)

        # Add widgets to box:
        box_volume_info.add(lbl_volume_name)
        box_volume_info.add(lbl_volume_dev_directory)
        box_volume_info.add(pb_volume_size)
        box_volume_info.add(lbl_volume_size_info)

        # Add Disk settings button
        btn_settings = Gtk.Button.new_from_icon_name(
            "view-more-symbolic", Gtk.IconSize.BUTTON)
        btn_settings.set_relief(Gtk.ReliefStyle.NONE)
        btn_settings.set_valign(Gtk.Align.START)
        btn_settings.connect(
            "clicked", self.on_volume_btn_settings_clicked)
        btn_settings._volume = vl

        box_volume.add(img_volume)
        box_volume.pack_start(box_volume_info, True, True, 0)
        box_volume.add(btn_settings)
        box_volume.props.margin = 7

        # Add to listbox
        listbox.prepend(box_volume)
        row = listbox.get_row_at_index(0)
        row._volume = vl
        row._lbl_volume_size_info = lbl_volume_size_info
        row._pb_volume_size = pb_volume_size
        row._lbl_volume_dev_directory = lbl_volume_dev_directory

        self.tryMountVolume(vl, lbl_volume_name, lbl_volume_size_info, pb_volume_size, lbl_volume_dev_directory)

    def addDisksToGUI(self):
        # Home:
        home_info = self.get_file_info(GLib.get_home_dir())
        self.lbl_home_path.set_label(GLib.get_home_dir())
        self.lbl_home_dev.set_label(home_info["device"])

        # Root:
        root_info = self.get_file_info("/")
        self.lbl_root_dev.set_label(root_info["device"])
        self.lbl_root_free.set_label(f"{int(root_info['free_kb'])/1000/1000:.2f} GB")
        self.lbl_root_total.set_label(f"{int(root_info['total_kb'])/1000/1000:.2f} GB")
        self.pb_root_usage.set_fraction( root_info["usage_percent"] )

        # VolumeMonitor
        self.vm = Gio.VolumeMonitor.get()
        self.vm.connect('volume-added', lambda vm,vl: print("Volume Added:", vm, vl))
        self.vm.connect('mount-added', lambda vm,mnt: print("Mount Added:", vm, mnt))
        self.vm.connect('drive-connected', lambda vm,dr: print("Drive Added:", vm, dr))


        # Hard Drives
        drives = self.vm.get_connected_drives()
        for dr in drives:
            if dr.has_volumes() and not dr.is_removable():
                # Drive Label
                lbl_drive_name = Gtk.Label.new()
                lbl_drive_name.set_markup(f'<span size="medium">{dr.get_name()}</span>')
                lbl_drive_name.set_halign(Gtk.Align.START)

                # Drive Frame
                frame = Gtk.Frame.new()
                frame.set_shadow_type(Gtk.ShadowType.IN)

                # Volume ListBox
                listbox = Gtk.ListBox.new()
                listbox.set_selection_mode(Gtk.SelectionMode.NONE)
                listbox.connect("row-activated", self.on_volume_row_activated)
                frame.add(listbox)
                
                # Add Volumes to the ListBox:
                for vl in dr.get_volumes():
                    #print(vl.get_name(), vl.can_mount(), vl.can_eject(), vl.get_drive())
                    self.addVolumeToGUI(vl, listbox, False)
                    #print(vl.get_name(), vl.can_mount(), vl.can_eject(), vl.get_drive())
                
                #self.box_drives.add(lbl_drive_name)
                self.box_drives.add(frame)
        
        # Removable Devices
        for dr in drives:
            if dr.has_volumes() and dr.is_removable():
                # Drive Label
                lbl_drive_name = Gtk.Label.new()
                lbl_drive_name.set_markup(f'<span size="medium">{dr.get_name()}</span>')
                lbl_drive_name.set_halign(Gtk.Align.START)

                # Drive Frame
                frame = Gtk.Frame.new()
                frame.set_shadow_type(Gtk.ShadowType.IN)

                # Volume ListBox
                listbox = Gtk.ListBox.new()
                listbox.set_selection_mode(Gtk.SelectionMode.NONE)
                listbox.connect("row-activated", self.on_volume_row_activated)
                frame.add(listbox)
                
                # Add Volumes to the ListBox:
                for vl in dr.get_volumes():
                    # print(vl.get_name(), vl.can_mount(), vl.can_eject(), vl.get_drive())
                    self.addVolumeToGUI(vl, listbox, True)
                    #print(vl.get_name(), vl.can_mount(), vl.can_eject(), vl.get_drive())
                
                #self.box_removables.add(lbl_drive_name)
                self.box_removables.add(frame)
        

    
    # Window methods:
    def onDestroy(self, action):
        self.window.get_application().quit()

        

    # SIGNALS:
    def on_lb_home_row_activated(self, listbox, row):
        subprocess.run(["xdg-open", GLib.get_home_dir()])

    def on_lb_root_row_activated(self, listbox, row):
        subprocess.run(["xdg-open", "/"])
    
    def on_volume_row_activated(self, listbox, row):
        # print("row._volume: ", row._volume.get_name())
        # self.tryMountVolume(row._volume, row._lbl_volume_size_info, row._pb_volume_size, row._lbl_volume_dev_directory)
        subprocess.run(["xdg-open", row._volume.get_mount().get_root().get_parse_name()])
    
    def on_volume_btn_settings_clicked(self, btn):
        self.selected_volume = btn._volume
        
        self.drive_popover.set_relative_to(btn)
        self.drive_popover.show_all()
        self.drive_popover.popup()
    
    def on_cb_mount_on_startup_toggled(self, cb):
        print(cb)