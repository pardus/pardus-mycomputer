import os

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
        self.defineComponents()

        self.getDisks()
        
        # Set application:
        self.application = application

        # Show Screen:
        self.window.show_all()

    def defineComponents(self):
        def UI(str):
            return self.builder.get_object(str)
        
        self.box_drives = UI("box_drives")
    
    def showVolumeSizes(self, vl, lbl_volume_size_info, pb_volume_size, lbl_volume_path):
        fs_root = vl.get_mount().get_root()

        filesystem_size = fs_root.query_filesystem_info(Gio.FILE_ATTRIBUTE_FILESYSTEM_SIZE).get_attribute_uint64(Gio.FILE_ATTRIBUTE_FILESYSTEM_SIZE)
        filesystem_size_gb = filesystem_size/1000/1000/1000

        filesystem_size_free = fs_root.query_filesystem_info(Gio.FILE_ATTRIBUTE_FILESYSTEM_FREE).get_attribute_uint64(Gio.FILE_ATTRIBUTE_FILESYSTEM_FREE)
        filesystem_size_free_gb = filesystem_size_free/1000/1000/1000

        # Show values on UI
        pb_volume_size.set_fraction((filesystem_size - filesystem_size_free)/filesystem_size)
        lbl_volume_size_info.set_markup(f"<span size=\"small\"><b>{filesystem_size_free_gb:.2f}GB</b> is free of {filesystem_size_gb:.2f} GB</span>")
        lbl_volume_path.set_markup(f"<span size=\"small\">{vl.get_mount().get_root().get_parse_name()}</span>")
    
    def tryMountVolume(self, vl, lbl_volume_size_info, pb_volume_size, lbl_volume_path):
        if not vl.can_mount() and vl.get_mount() == None:
            print("can't mount!")
            return False

        if vl.get_mount() == None:
            def on_mounted(vl, task, lbl_volume_size_info, pb_volume_size, lbl_volume_path):
                try:
                    vl.mount_finish(task)
                    
                    self.showVolumeSizes(vl, lbl_volume_size_info, pb_volume_size, lbl_volume_path)
                    
                    return True
                except GLib.Error:
                    return False
            
            
            mo = Gio.MountOperation.new()
            vl.mount(Gio.MountMountFlags.NONE, mo, None, on_mounted, lbl_volume_size_info, pb_volume_size, lbl_volume_path)
        else:
            self.showVolumeSizes(vl, lbl_volume_size_info, pb_volume_size, lbl_volume_path)
            return True

    def getDisks(self):
        vm = Gio.VolumeMonitor.get()
        drives = vm.get_connected_drives()

        for dr in drives:
            if dr.has_volumes():
                print("Drives:", dr.get_name())

                frame = Gtk.Frame.new()
                frame.set_shadow_type(Gtk.ShadowType.IN)

                listbox = Gtk.ListBox.new()
                listbox.set_selection_mode(Gtk.SelectionMode.NONE)
                listbox.connect("row-activated", self.on_volume_row_activated)
                frame.add(listbox)

                lbl_drive_name = Gtk.Label.new()
                lbl_drive_name.set_markup(f"<b><span size=\"large\">{dr.get_name()}</span></b>")
                lbl_drive_name.set_halign(Gtk.Align.START)

                # Add Volumes to the Drive:
                for vl in dr.get_volumes():
                    #print(vl.get_name(), vl.can_mount(), vl.can_eject(), vl.get_drive())

                    # Prepare UI:
                    box_volume = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 7)
                    img_volume = Gtk.Image.new_from_icon_name("drive-harddisk", Gtk.IconSize.DIALOG)

                    box_volume_info = Gtk.Box.new(Gtk.Orientation.VERTICAL, 3)
                    # box_volume_info.set_homogeneous(True)

                    # Volume infos
                    lbl_volume_name = Gtk.Label.new()
                    lbl_volume_name.set_markup(f"<b>{vl.get_name()}</b> <span size=\"small\" alpha=\"70%\">({vl.get_identifier(Gio.VOLUME_IDENTIFIER_KIND_UNIX_DEVICE )})</span>")
                    lbl_volume_name.set_halign(Gtk.Align.START)

                    lbl_volume_path = Gtk.Label.new()
                    lbl_volume_path.set_markup(f"<span size=\"small\"> </span>")
                    lbl_volume_path.set_halign(Gtk.Align.START)
                    lbl_volume_path.set_opacity(0.7)

                    pb_volume_size = Gtk.ProgressBar.new()
                    pb_volume_size.set_valign(Gtk.Align.CENTER)
                    pb_volume_size.set_margin_end(7)

                    lbl_volume_size_info = Gtk.Label.new()
                    lbl_volume_size_info.set_markup(f"<span size=\"small\"> </span>")
                    lbl_volume_size_info.set_halign(Gtk.Align.START)

                    # Add widgets to box:
                    box_volume_info.add(lbl_volume_name)
                    box_volume_info.add(lbl_volume_path)
                    box_volume_info.add(pb_volume_size)
                    box_volume_info.add(lbl_volume_size_info)

                    box_volume.add(img_volume)
                    box_volume.pack_start(box_volume_info, True, True, 0)
                    box_volume.props.margin = 3

                    # Add to listbox
                    listbox.prepend(box_volume)
                    row = listbox.get_row_at_index(0)
                    row._volume = vl
                    row._lbl_volume_size_info = lbl_volume_size_info
                    row._pb_volume_size = pb_volume_size
                    row._lbl_volume_path = lbl_volume_path


                    print("Volume:", vl.get_name())
                    print("-- can mount:",vl.can_mount(), vl.can_eject(), vl.get_mount())

                    self.tryMountVolume(vl, lbl_volume_size_info, pb_volume_size, lbl_volume_path)

                
                self.box_drives.add(lbl_drive_name)
                self.box_drives.add(frame)
    
    # Window methods:
    def onDestroy(self, action):
        self.window.get_application().quit()

        

    # SIGNALS:
    def on_volume_row_activated(self, listbox, row):
        print("row._volume: ", row._volume.get_name())
        self.tryMountVolume(row._volume, row._lbl_volume_size_info, row._pb_volume_size, row._lbl_volume_path)