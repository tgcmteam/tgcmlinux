#!/usr/bin/python

import os
import sys
import glob
import xml.etree.ElementTree as ET

BUILDER_DIR="/home/builder/linuxbuilder"
LAGAR_DIR=os.path.join(BUILDER_DIR, "archive")

class report :
    def __init__(self, date):
        self.root = ET.Element("html")
        head = ET.SubElement(self.root, "head")
        title = ET.SubElement(head, "title")
        title.text = "Linux TGCM Testing"
        self.body = ET.SubElement(self.root, "body")
        h1 = ET.SubElement(self.body, "h1")
        h1.text = "GNU/Linux TGCM Testing Page"

        h2 = ET.SubElement(self.body, "h2")
        h2.text = "Last compilation : %s" % date

    def save(self):
        tree = ET.ElementTree(self.root)
        tree.write(os.path.join(LAGAR_DIR, "index.html"))

    def find_ubuntu_pkgs(self) :
        #ubuntu_distros=["lucid", "karmic"]
        ubuntu_distros=["oneiric"]
        dsc = {}

        for d in ubuntu_distros :
            h3 = ET.SubElement(self.body, "h3")
            h3.text = "Ubuntu - %s" % d

            for pkg in glob.glob(os.path.join(LAGAR_DIR, "ubuntu",
                                              "pool", "main", "*",
                                              "*", "*%s*.deb" % d)) :
                h4 = ET.SubElement(self.body, "h4")
                h4.text = "--> " + os.path.basename(pkg)

    def find_fedora_pkgs(self):
        fedora_distros=["fedora16"]

        for d in fedora_distros :
            h3 = ET.SubElement(self.body, "h3")
            h3.text = "Fedora - %s" % d.split("fedora")[1]

            #for pkg in glob.glob(os.path.join(LAGAR_DIR, d , "*src.rpm")) :
            for pkg in glob.glob(os.path.join(LAGAR_DIR, d , "*.rpm")) :
                h4 = ET.SubElement(self.body, "h4")
                h4.text = "--> " + os.path.basename(pkg)

    def find_opensuse_pkgs(self):
        opensuse_distros=["opensuse121"]

        for d in opensuse_distros :
            h3 = ET.SubElement(self.body, "h3")
            h3.text = "Opensuse - %s" % d.split("opensuse")[1]

            for pkg in glob.glob(os.path.join(LAGAR_DIR, d , "*.rpm")) :
                h4 = ET.SubElement(self.body, "h4")
                h4.text = "--> " + os.path.basename(pkg)


if __name__ == "__main__":

    if len(sys.argv) != 2 :
        exit(0)

    r = report(sys.argv[1])
    r.find_ubuntu_pkgs()
    r.find_fedora_pkgs()
    r.find_opensuse_pkgs()
    r.save()





