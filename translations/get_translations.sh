#!/bin/bash
# Get
xgettext --language=Glade --output=translation.pot ../ui/MainWindow.glade;

# Merge with existing ones
msgmerge tr.po translation.pot -o tr.po;