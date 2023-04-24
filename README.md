# Pardus My Computer

Pardus My Computer is an ui for information and management of disks on your computer.

It is currently a work in progress. Maintenance is done by <a href="https://www.pardus.org.tr/">Pardus</a> team.

[![Packaging status](https://repology.org/badge/vertical-allrepos/pardus-mycomputer.svg)](https://repology.org/project/pardus-mycomputer/versions)

### **Dependencies**

This application is developed based on Python3 and GTK+ 3. Dependencies:
```bash
gir1.2-glib-2.0 gir1.2-gtk-3.0 gir1.2-notify-0.7 gir1.2-pango-1.0 gvfs-fuse python3-gi python3
```

### **Run Application from Source**

Install dependencies
```bash
sudo apt install gir1.2-glib-2.0 gir1.2-gtk-3.0 gir1.2-notify-0.7 gir1.2-pango-1.0 gvfs-fuse python3-gi python3
```

Clone the repository
```bash
git clone https://github.com/pardus/pardus-mycomputer.git ~/pardus-mycomputer
```

Run application
```bash
python3 ~/pardus-mycomputer/src/Main.py
```

### **Build deb package**

```bash
sudo apt install devscripts git-buildpackage
sudo mk-build-deps -ir
gbp buildpackage --git-export-dir=/tmp/build/pardus-mycomputer -us -uc
```

### **Screenshots**

![Pardus My Computer 1](screenshots/pardus-mycomputer-1.png)

![Pardus My Computer 2](screenshots/pardus-mycomputer-2.png)

![Pardus My Computer 3](screenshots/pardus-mycomputer-3.png)

![Pardus My Computer 4](screenshots/pardus-mycomputer-4.png)

![Pardus My Computer 5](screenshots/pardus-mycomputer-5.png)
