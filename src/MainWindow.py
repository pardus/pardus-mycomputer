import os, subprocess

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk

import DiskManager

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

        # Set application:
        self.application = application

        # Global Definings
        self.defineComponents()
        self.defineVariables()

        # Add Disks to GUI
        self.addDisksToGUI()

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

    
    def defineVariables(self):
        self.mount_operation = Gio.MountOperation.new()
        self.selected_volume = None
        self.selected_volume_info = None

    
    def showDiskDetailsDialog(self, vl):
        dr = vl.get_drive()
        mount_point = vl.get_mount().get_root().get_parse_name()
        file_info = DiskManager.get_file_info(mount_point)

        self.dlg_lbl_name.set_label(vl.get_name())
        self.dlg_lbl_model.set_label(dr.get_name())

        self.dlg_lbl_dev.set_label(file_info["device"])
        self.dlg_lbl_mountpoint.set_label(mount_point)

        self.dlg_lbl_used_gb.set_label(f"{int(file_info['usage_kb'])/1024/1024:.2f} GB (%{file_info['usage_percent']*100:.2f})")
        self.dlg_lbl_free_gb.set_label(f"{int(file_info['free_kb'])/1024/1024:.2f} GB (%{file_info['free_percent']*100:.2f})")
        self.dlg_lbl_total_gb.set_label(f"{int(file_info['total_kb'])/1024/1024:.2f} GB")

        self.dlg_lbl_filesystem_type.set_label(DiskManager.get_filesystem_of_partition(file_info["device"])) 
    

    def showVolumeSizes(self, vl, lbl_volume_name, lbl_volume_size_info, pb_volume_size, lbl_volume_dev_directory):
        mount_point = vl.get_mount().get_root().get_parse_name()
        file_info = DiskManager.get_file_info(mount_point)

        # Show values on UI
        lbl_volume_name.set_markup(f'<b>{vl.get_name()}</b> <span size="small" alpha="75%">{ mount_point }</span>')
        lbl_volume_size_info.set_markup(f'<span size="small"><b>{int(file_info["free_kb"])/1024/1024:.2f} GB</b> is free of {int(file_info["total_kb"])/1024/1024:.2f} GB</span>')
        lbl_volume_dev_directory.set_markup(f'<span size="small" alpha="75%">{ file_info["device"] }</span>')
        pb_volume_size.set_fraction(file_info["usage_percent"])

        self.window.show_all()

    
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
        btn_volume_settings = Gtk.MenuButton.new()
        btn_volume_settings.set_relief(Gtk.ReliefStyle.NONE)
        btn_volume_settings.set_valign(Gtk.Align.START)
        btn_volume_settings._volume = vl
        btn_volume_settings.connect("released", self.on_btn_volume_settings_clicked)
        if is_removable:
            btn_volume_settings.set_popover(self.popover_removable)
        else:
            btn_volume_settings.set_popover(self.popover_volume)

        box_volume.add(img_volume)
        box_volume.pack_start(box_volume_info, True, True, 0)
        box_volume.add(btn_volume_settings)
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
        home_info = DiskManager.get_file_info(GLib.get_home_dir())
        self.lbl_home_path.set_label(GLib.get_home_dir())
        self.lbl_home_dev.set_label(home_info["device"])

        # Root:
        root_info = DiskManager.get_file_info("/")
        self.lbl_root_dev.set_label(root_info["device"])
        self.lbl_root_free.set_label(f"{int(root_info['free_kb'])/1024/1024:.2f} GB")
        self.lbl_root_total.set_label(f"{int(root_info['total_kb'])/1024/1024:.2f} GB")
        self.pb_root_usage.set_fraction( root_info["usage_percent"] )

        # VolumeMonitor
        self.vm = Gio.VolumeMonitor.get()
        self.vm.connect('mount-added', self.on_mount_added)
        self.vm.connect('mount-removed', self.on_mount_removed)
        self.vm.connect('volume-added', self.on_mount_added)
        self.vm.connect('volume-removed', self.on_mount_removed)
        self.vm.connect('drive-connected', self.on_mount_added)
        self.vm.connect('drive-disconnected', self.on_mount_removed)

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
                    self.addVolumeToGUI(vl, listbox, False)

                #self.box_drives.add(lbl_drive_name)
                self.box_drives.add(frame)
        
        # Removable Devices
        self.updateRemovableDevicesList()
        
    def updateRemovableDevicesList(self):
        self.box_removables.foreach(lambda child: self.box_removables.remove(child))
        
        drives = self.vm.get_connected_drives()
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
                    self.addVolumeToGUI(vl, listbox, True)
                
                #self.box_removables.add(lbl_drive_name)
                self.box_removables.add(frame)
        
        self.box_removables.show_all()
    
    # Window methods:
    def onDestroy(self, action):
        self.window.get_application().quit()



    # SIGNALS:
    def on_lb_home_row_activated(self, listbox, row):
        subprocess.run(["xdg-open", GLib.get_home_dir()])

    def on_lb_root_row_activated(self, listbox, row):
        subprocess.run(["xdg-open", "/"])
    
    def on_volume_row_activated(self, listbox, row):
        subprocess.run(["xdg-open", row._volume.get_mount().get_root().get_parse_name()])
    
    def on_btn_volume_settings_clicked(self, btn):
        self.selected_volume = btn._volume

        mount_point = self.selected_volume.get_mount().get_root().get_parse_name()
        self.selected_volume_info = DiskManager.get_file_info(mount_point)

        self.cb_mount_on_startup.set_active(DiskManager.is_drive_automounted(self.selected_volume_info["device"]))
    
    # Popover Menu Buttons:
    def on_cb_mount_on_startup_released(self, cb):
        DiskManager.set_automounted(self.selected_volume_info["device"], cb.get_active())
    
    def on_btn_volume_details_clicked(self, btn):
        vl = self.selected_volume

        self.showDiskDetailsDialog(vl)

        self.dialog_disk_details.run()
        self.dialog_disk_details.hide()
    
    def on_btn_format_removable_clicked(self, btn):
        vl = self.selected_volume

        mount_point = vl.get_mount().get_root().get_parse_name()
        file_info = DiskManager.get_file_info(mount_point)

        subprocess.Popen(["pardus-usb-formatter", file_info["device"]])

    def on_mount_added(self, volumemonitor, mount):
        self.updateRemovableDevicesList()

    
    def on_mount_removed(self, volumemonitor, mount):
        self.updateRemovableDevicesList()