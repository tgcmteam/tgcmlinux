# -*- coding: utf-8 -*-

# Bloque de imports
import sys, logging, getopt, time, os, subprocess
import socket, shutil

import smtplib
import mimetypes
from email.MIMEText import MIMEText
from email.message import Message
from email.mime.multipart import MIMEMultipart

VERSION = "1.0"
FECHA = "agosto de 2011"
DISTRIBUCIONES_SOPORTADAS = ["ubuntu","fedora","opensuse"]


ESTADO_INICIAL					= 0
ESTADO_SRC_PKGS_FAILED_BUILDING = 1
ESTADO_SVN_NO_CHANGED			= 2
ESTADO_SRC_PKGS_BUILDED			= 3
ESTADO_BASETGZS_FAILED_UPDATING	= 4
ESTADO_BASETGZS_UPDATED			= 5
ESTADO_DSC_NO_AVAILABLES		= 6
ESTADO_PKGS_FAILED_BUILDING		= 7
ESTADO_PKGS_BUILDED				= 8

dictEstado = {
    ESTADO_INICIAL					: "ESTADO INICIAL",
    ESTADO_SRC_PKGS_FAILED_BUILDING	: "Ha fallado la construccion de los paquetes fuentes",
    ESTADO_SVN_NO_CHANGED			: "El SVN no ha cambiado desde la ultima generacion",
    ESTADO_SRC_PKGS_BUILDED			: "Los paquetes fuentes han sido construidos",
    ESTADO_BASETGZS_FAILED_UPDATING	: "Ha fallado la actualizacion de los basetgzs",
    ESTADO_BASETGZS_UPDATED			: "Los basetgzs han sido actualizados",
    ESTADO_DSC_NO_AVAILABLES		: "Los ficheros .dsc no estan disponible",
    ESTADO_PKGS_FAILED_BUILDING		: "Ha fallado la construccion de los paquetes binarios",
    ESTADO_PKGS_BUILDED				: "Los paquetes binarios han sido construidos"
    }


#######################################
# CONSTANTES DE DIRECTORIOS
#
BUILDER_DIR 	= "/root/builder"
BASETGZ_DIR 	= BUILDER_DIR + "/basetgzs"
BUILDERPLACE_DIR= BUILDER_DIR + "/build-place"
RESULTS_DIR 	= BUILDER_DIR + "/results"
TMP_DIR 		= BUILDER_DIR + "/tmp"
ARCHIVE_DIR 	= BUILDER_DIR + "/archive"
LOGS_DIR 		= BUILDER_DIR + "/logs"

#######################################
# CONSTANTES PARA LA FAMILIA .DEB
#
DEB_SRC_BUILDER_DIR = BUILDER_DIR + "/chroots/deb-src-builder"
#UBUNTU_DISTROS 	= ["karmic", "jaunty", "intrepid", "hardy"]
UBUNTU_DISTROS 		= ["oneiric"]
FICHERO_DEB_SRC_BUILDER_TGZ = DEB_SRC_BUILDER_DIR + "/root/builder/builder.tgz"

#######################################
# CONSTANTES PARA LA FAMILIA .RPM
#
RPM_SRC_BUILDER_DIR = BUILDER_DIR + "/chroots/rpm-src-builder"
RPM_MACH_DIR 		= "/var/tmp/mach/"
FEDORA_DISTROS 		= "fedora-10-i386-core"
OPENSUSE11_CHROOT 	= "/root/builder/chroots/opensuse/11.2/builder"
FEDORA12_CHROOT 	= "/root/builder/chroots/fedora/12/builder"
FICHERO_RPM_SRC_BUILDER_TGZ = RPM_SRC_BUILDER_DIR + "/root/builder/builder.tgz"

#######################################
#
def inicializarSistemaLogs (fichero):
    logger = logging.getLogger("XX")
    logger.setLevel(logging.DEBUG)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('*** %(levelname)s: %(message)s')
    consoleHandler.setFormatter(formatter)

    logger.addHandler(consoleHandler)

    ficheroHandler = logging.FileHandler(fichero,'w')
    ficheroHandler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s,%(msecs)03d> %(levelname)s: %(message)s','%H:%M:%S')
    ficheroHandler.setFormatter(formatter)

    logger.addHandler(ficheroHandler)

    return logger

#######################################
#
def show_version(log):
    log.info("buildEMLinux: Version %s, INDRA Sistemas, %s",VERSION, FECHA)


########################################
#
def usage():
    print """
buildEMLinux: Genera paquetes para las distribuciones Linux del Escritorio Movistar. Uso:
  buildEMLinux [-d <distribucion> [-v <version>]] [-h]

donde:
  -d <distribucion> -- Distribucion de Linux para la cual se generaran los paquetes.
                       Los valores pueden ser; "ubuntu", "fedora", "opensuse".
                       Por defecto se generan los paquetes para todas las distribuciones
  -v <version> -- Version de la distribucion para la que se generaran los paquetes.
                  Por defecto se generan paquetes para todas las versiones soportadas
  -h           -- Muestra la ayuda
"""

#################################################################################################################################################

import os
import sys
import glob
import xml.etree.ElementTree as ET

BUILDER_DIR="/root/builder"
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
        fedora_distros=["fedora12"]

        for d in fedora_distros :
            h3 = ET.SubElement(self.body, "h3")
            h3.text = "Fedora - %s" % d.split("fedora")[1]

            for pkg in glob.glob(os.path.join(LAGAR_DIR, d , "*src.rpm")) :
                h4 = ET.SubElement(self.body, "h4")
                h4.text = "--> " + os.path.basename(pkg)

    def find_opensuse_pkgs(self):
        opensuse_distros=["opensuse12"]

        for d in opensuse_distros :
            h3 = ET.SubElement(self.body, "h3")
            h3.text = "Opensuse - %s" % d.split("opensuse")[1]

            for pkg in glob.glob(os.path.join(LAGAR_DIR, d , "*src.rpm")) :
                h4 = ET.SubElement(self.body, "h4")
                h4.text = "--> " + os.path.basename(pkg)


########################################
#
def ejecutaComando(cmd,succes_code=0):
    global log

    p = subprocess.Popen(cmd, shell=True, bufsize=0,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=False)

    std_output ,std_err = p.communicate()
    return_code = p.returncode

    if std_output:
        log.debug(std_output)

    if return_code != succes_code:
        raise Exception("Failed command %s : %s" %(cmd,std_output))

    return (return_code,std_output)

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

########################################
#
def crearDirectorio (directorio):
    global log
    log.debug("\tCreacion de directorio: %s" % directorio)
    try:
        os.makedirs(directorio)
    except os.error as (errno, msg):
        if errno == 17:
            log.debug("\t\t%s: %s" % (msg,directorio))
        else:
            log.error("%d -- %s: %s" % (errno,msg,directorio) )
            sys.exit(-1)

########################################
#
def crearDirectoriosDeSalida ():
    global log
    log.info("Creando directorios para salida de datos...")

    crearDirectorio(BASETGZ_DIR)
    crearDirectorio(BUILDERPLACE_DIR)
    crearDirectorio(RESULTS_DIR)
    crearDirectorio(TMP_DIR)
    crearDirectorio(LOGS_DIR)

    log.debug("\tBorra los antiguos ficheros de log: %s" % (LOGS_DIR + "/*"))
    try:
        os.remove(LOGS_DIR + "/*")
    except os.error as (errno, msg):
        if errno == 2:
            log.debug("\t\t%s: %s" % (msg,LOGS_DIR + "/*"))
        else:
            log.error("%d -- %s: %s" % (errno,msg,directorio) )
            sys.exit(-1)

    log.info(".Creados directorios para salida de datos!")
    return


########################################
#
def construirPaquetesDebSrc ():
    global log

    log.info("Construyendo paquetes fuente .deb...")

    comando = "/usr/sbin/chroot %s /root/builder/bin/build.sh" % (DEB_SRC_BUILDER_DIR)
    log.debug("\tLanza chroot y el script de descarga del SVN y generacion --> Comando: %s" % comando)

    ejecutaComando(comando)

    log.info(".Construidos paquetes fuente .deb!")

    if os.access(FICHERO_DEB_SRC_BUILDER_TGZ,os.R_OK):

        log.info("Preparando y descomprimiendo el builder.tgz generado...")
        tmpDirPkg = TMP_DIR + "/deb"

        log.debug("\tBorra el directorio de ficheros temporales: %s" % tmpDirPkg)
        try:
            shutil.rmtree(tmpDirPkg)
        except os.error as (errno, msg):
            if errno == 2:
                log.debug("\t\t%s: %s" % (msg,LOGS_DIR + "/*"))
            else:
                log.error("%d -- %s: %s" % (errno,msg,tmpDirPkg) )
                return(ESTADO_SRC_PKGS_FAILED_BUILDING)

        log.debug("\tCrea el directorio de ficheros temporales: %s" % tmpDirPkg)
        os.makedirs(tmpDirPkg)

        log.debug("\tEstablece como directorio actual el de los ficheros temporales")
        os.chdir(tmpDirPkg)

        comando = "tar xvzf %s" % (FICHERO_DEB_SRC_BUILDER_TGZ)
        log.debug("\tDescomprime el builder.tgz generado --> Comando: %s" % comando)

        ejecutaComando(comando)

        log.debug("\tBorra el builder.tgz generado")
        os.remove(FICHERO_DEB_SRC_BUILDER_TGZ)

        log.info(".Preparado y descomprimido el builder.tgz generado!")

    else:
        log.warning("No existe fichero %s. No ha habido cambios en repositorio de software." % FICHERO_DEB_SRC_BUILDER_TGZ)
        return(ESTADO_SVN_NO_CHANGED)

    return(ESTADO_SRC_PKGS_BUILDED)


########################################
# (pendiente de unificar con la funcion anterior cuando el tema este mas "rodado")
def construirPaquetesRpmSrc ():
    global log

    log.info("Construyendo paquetes fuente .rpm...")

    comando = "i386 /usr/sbin/chroot %s /root/builder/bin/build.sh" % (RPM_SRC_BUILDER_DIR)
    log.debug("\tLanza chroot y el script de descarga del SVN y generacion --> Comando: %s" % comando)

    x = """
    ejecutaComando(comando)

    log.info(".Construidos paquetes fuente .rpm!")

    if os.access(FICHERO_RPM_SRC_BUILDER_TGZ,os.R_OK):

        log.info("Preparando y descomprimiendo el builder.tgz generado...")
        tmpDirPkg = TMP_DIR + "/rpm"

        log.debug("\tBorra el directorio de ficheros temporales: %s" % tmpDirPkg)
        shutil.rmtree(tmpDirPkg)

        log.debug("\tCrea el directorio de ficheros temporales: %s" % tmpDirPkg)
        os.makedirs(tmpDirPkg)

        log.debug("\tEstablece como directorio actual el de los ficheros temporales")
        os.chdir(tmpDirPkg)

        comando = "tar xvzf %s" % (FICHERO_RPM_SRC_BUILDER_TGZ)
        log.debug("\tDescomprime el builder.tgz generado --> Comando: %s" % comando)
        ejecutaComando(comando)

        log.debug("\tBorra el builder.tgz generado")
        os.remove(FICHERO_RPM_SRC_BUILDER_TGZ)

        log.info(".Preparado y descomprimido el builder.tgz generado!")

    else:
        log.error("No existe fichero %s" % FICHERO_RPM_SRC_BUILDER_TGZ)
        sys.exit(-3)

    """
    return

########################################
#
def actualizarDebBasetgz ():
    global log

    log.info("Actualizacion de basetgzs")

    for versionDistro in UBUNTU_DISTROS:
        log.info("Actualizando basetgzs para paquetes .deb (i386 y amd64) y version de distro: %s..." % \
            (versionDistro))

        fechaEnSegundos = long(time.time())

        comando = "pbuilder --update --basetgz %s/%s.tgz  > %s/%s_%s_UPDATE.txt 2>&1" % \
            (BASETGZ_DIR,versionDistro,LOGS_DIR,versionDistro,fechaEnSegundos)
        log.debug("\tLanza pbuilder para actualizar basetgz de 32bits --> Comando: %s" % comando)

        p32b = subprocess.Popen(comando, shell=True, bufsize=4096,stdin=subprocess.PIPE, \
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=False)

        comando = "x86_64 pbuilder --update --basetgz %s/%s64.tgz  > %s/%s_%s_UPDATE64.txt 2>&1" % \
            (BASETGZ_DIR,versionDistro,LOGS_DIR,versionDistro,fechaEnSegundos)
        log.debug("\tLanza pbuilder para actualizar basetgz de 64bits --> Comando: %s" % comando)

        p64b = subprocess.Popen(comando, shell=True, bufsize=4096,stdin=subprocess.PIPE,\
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=False)

        time.sleep(5)

        std_output_32b ,std_err_32b = p32b.communicate()
        return_code_32b = p32b.returncode

        if std_output_32b:
            log.debug(std_output_32b)

        if return_code_32b != 0:
            log.error("Failed update basetgzs for %s distro de 32 bits" %(versionDistro))
            return(ESTADO_BASETGZS_FAILED_UPDATING)

        std_output_64b ,std_err_64b = p64b.communicate()
        return_code_64b = p64b.returncode

        if std_output_64b:
            log.debug(std_output_64b)

        if return_code_64b != 0:
            log.error("Failed update basetgzs for %s distro de 64 bits" %(versionDistro))
            return(ESTADO_BASETGZS_FAILED_UPDATING)

    log.info(".Actualizados basetgzs!")
    return(ESTADO_BASETGZS_UPDATED)


########################################
#
def adaptarPaquetesParaUbuntu ():
    global log

    log.info("Adaptacion de paquetes")

    sleepTime = 0
    for versionDistro in UBUNTU_DISTROS:
        log.info("Adaptando paquetes para ubuntu-%s..." % versionDistro)

        comando = "find %s/deb -name tgcm*.dsc | grep %s" % (TMP_DIR,versionDistro)
        log.debug("\tLanza un find para obtener lista de ficheros .dsc --> Comando: %s" % comando)

        p = subprocess.Popen(comando, shell=True, bufsize=4096,stdin=subprocess.PIPE, stdout=subprocess.PIPE,\
            stderr=subprocess.STDOUT, close_fds=False)

        tgcmDsc ,std_err = p.communicate()
        return_code = p.returncode

        if not tgcmDsc:
            log.warning("No encontrados ficheros .dsc!")
            return(ESTADO_DSC_NO_AVAILABLES)

        log.debug(tgcmDsc)

        sleepTime += 15

        #BUILDER_build_deb_dsc std_output versionDistro "tgcm" sleepTime &

        log.info("\tBuilding %s for %s in %s secs" % (tgcmDsc,versionDistro,sleepTime))
        time.sleep(sleepTime)
        fechaEnSegundos = long(time.time())
        crearDirectorio("RESULTS_DIR/%s" % fechaEnSegundos)
        crearDirectorio(LOGS_DIR)

        log.info("Building packages for %s..." % versionDistro)
        comando = "pbuilder --build --basetgz %s/%s.tgz --buildplace %s --buildresult %s/%s %s >> %s/tgcm_%s_%s.txt 2>&1" % \
            (BASETGZ_DIR,versionDistro,BUILDERPLACE_DIR,RESULTS_DIR,fechaEnSegundos,\
            tgcmDsc,LOGS_DIR,versionDistro,fechaEnSegundos)

        log.debug("\tLanza un pbuilder --build para adaptar paquetes --> Comando: %s" % comando)

        p32b = subprocess.Popen(comando, shell=True, bufsize=4096,stdin=subprocess.PIPE, \
             stdout=subprocess.PIPE,stderr=subprocess.STDOUT,close_fds=False)

        std_output_32b ,std_err_32b = p32b.communicate()
        return_code_32b = p32b.returncode

        if std_output_32b:
            log.debug(std_output_32b)

        if return_code_32b != 0:
            log.error("Failed build packages for %s distro de 32 bits" %(versionDistro))
            return(ESTADO_PKGS_FAILED_BUILDING)

        log.info("Builded packages for %s!" % versionDistro)

        log.info("Building packages for %s64..." % versionDistro)
        comando = "x86_64 pbuilder --build --basetgz %s/%s64.tgz --buildplace %s --buildresult %s/%s %s >> %s/tgcm_%s_%s.txt 2>&1" % \
            (BASETGZ_DIR,versionDistro,BUILDERPLACE_DIR,RESULTS_DIR,fechaEnSegundos,\
            tgcmDsc,LOGS_DIR,versionDistro,fechaEnSegundos)

        log.debug("\tLanza un pbuilder --build para adaptar paquetes --> Comando: %s" % comando)

        p64b = subprocess.Popen(comando, shell=True, bufsize=4096,stdin=subprocess.PIPE, \
             stdout=subprocess.PIPE,stderr=subprocess.STDOUT,close_fds=False)

        std_output_64b ,std_err_64b = p64b.communicate()
        return_code_64b = p64b.returncode

        if std_output_64b:
            log.debug(std_output_64b)

        if return_code_64b != 0:
            log.error("Failed build packages for %s distro de 64 bits" %(versionDistro))
            return(ESTADO_PKGS_FAILED_BUILDING)

        log.info("Builded packages for %s64!" % versionDistro)

        log.info(".Adaptados paquetes!")



        log.info("Instalando paquetes generados en el repositorio de ubuntu-%s..." % versionDistro)
        log.info(". Al final del presente proceso se firman los paquetes (para ellos se indica en el fichero ../conf/distributions la firma a utilizar y se debe utilizar una firma sin passphrase asociada (o bien pelearse con el gpg-agent)")

        copiaDirectorioTrabajo = os.getcwd()

        log.debug("\tEstablece como directorio actual: %s" % (ARCHIVE_DIR + "/ubuntu"))
        os.chdir(ARCHIVE_DIR + "/ubuntu")

        while os.access("./db/lockfile",os.R_OK):
            log.info("Lock repod db (%s for %s in %s secs)" % (tgcmDsc,versionDistro,sleepTime))
            time.sleep(sleepTime)

        comando = "reprepro remove %s tgcm >> %s/tgcm_%s_Deploy_%s.txt 2>&1" % \
            (versionDistro,LOGS_DIR,versionDistro,fechaEnSegundos)
        log.debug("\tComando: %s" % comando)

        p = subprocess.Popen(comando, shell=True, bufsize=4096,stdin=subprocess.PIPE, \
             stdout=subprocess.PIPE,stderr=subprocess.STDOUT,close_fds=False)

        std_output ,std_err = p.communicate()
        if p.returncode != 0:
            log.error("Error en ejecucion de comando '%s'" % comando)
            return(ESTADO_PKGS_FAILED_BUILDING)

        while os.access("./db/lockfile",os.R_OK):
            log.info("Lock repod db (%s for %s in %s secs)" % (tgcmDsc,versionDistro,sleepTime))
            time.sleep(sleepTime)

        comando = "reprepro --section Net --priority optional includedsc %s %s >> %s/tgcm_%s_Deploy_%s.txt 2>&1" % \
            (versionDistro,tgcmDsc,LOGS_DIR,versionDistro,fechaEnSegundos)
        log.debug("\tComando: %s" % comando)

        p = subprocess.Popen(comando, shell=True, bufsize=4096,stdin=subprocess.PIPE, \
             stdout=subprocess.PIPE,stderr=subprocess.STDOUT,close_fds=False)

        std_output ,std_err = p.communicate()
        if p.returncode != 0:
            log.error("Error en ejecucion de comando '%s'" % comando)
            return(ESTADO_PKGS_FAILED_BUILDING)

        comando = "find %s/%s -name *.deb -exec reprepro includedeb %s {} \; >> %s/tgcm_%s_Deploy_%s.txt 2>&1" % \
            (RESULTS_DIR,fechaEnSegundos,versionDistro,LOGS_DIR,versionDistro,fechaEnSegundos)
        log.debug("\tComando: %s" % comando)

        p = subprocess.Popen(comando, shell=True, bufsize=4096,stdin=subprocess.PIPE, \
             stdout=subprocess.PIPE,stderr=subprocess.STDOUT,close_fds=False)

        std_output ,std_err = p.communicate()

        log.debug("\tRetorna al directorio anterior: %s" % (copiaDirectorioTrabajo))
        os.chdir(copiaDirectorioTrabajo)

        dirTmpGeneracion =  "%s/%s" % (RESULTS_DIR,fechaEnSegundos)
        log.debug("\tBorra el directorio de temporal de generacion: %s" % (dirTmpGeneracion))
        try:
            shutil.rmtree(dirTmpGeneracion)
        except os.error as (errno, msg):
            if errno == 2:
                log.debug("\t\t%s: %s" % (msg,LOGS_DIR + "/*"))
            else:
                log.error("%d -- %s: %s" % (errno,msg,dirTmpGeneracion) )
                return(ESTADO_PKGS_FAILED_BUILDING)

    log.info(".Instalados paquetes generados!")
    return(ESTADO_PKGS_BUILDED)

########################################
#
def enviarMailConResultadoGeneracion(toAddr, subject, message, adjuntos=[]):
    global log

    """Sends mail"""
    server = smtplib.SMTP("smtp.indra.es", 25)
    server.starttls()
##    server.set_debuglevel(1)
    server.login("tgcmteam", "tgcm1234")

    outer = MIMEMultipart()

    outer['To']= toAddr
    outer['Subject']= subject
    mensaje = MIMEText(message)
    outer.attach(mensaje)
    for path in adjuntos:
        if os.path.exists(path):
            fp = open(path)
            adj = MIMEText (fp.read(), 'html')
            fp.close()
            adj.add_header('Content-Disposition', 'attachment', filename=path)
            outer.attach(adj)

    server.sendmail("tgcmteam@indra.es", toAddr, outer.as_string())

    server.close()
    return



#######################################################
###################### INICIO ##########################
########################################################
if __name__ == "__main__":

    # Prepara el sistema de logs, formatos, salidas, etc
    nombreFicheroLog = "buildEMLinux.log"
    log = inicializarSistemaLogs(nombreFicheroLog)

    log.info("*** INICIO DE PROGRAMA **********")
    show_version(log)

    fechaHoraInicial = time.strftime("%a %b %d %H:%M:%S %Z %Y",time.localtime())
    log.info("Se anota la fecha y hora de inicio: %s" % fechaHoraInicial)

    log.info("Lectura de parametros...")
    distribucion = "ALL"
    version = "ALL"

    try:
        opts, args = getopt.getopt(sys.argv[1:], "d:v:h")

    except getopt.GetoptError, valor:
        # print help information and exit:
        log.error("Opcion incorrecta: %s",valor)
        usage()
        sys.exit(2)

    for o, a in opts:

        if o == "-d":
            distribucion = a

        elif o == "-v":
            version = a

        elif o == "-h":
            usage()
            sys.exit()

        else:
            log.error("Opcion ERRONEA: %s",o)
            usage()
            sys.exit()

    log.info("Lectura de parametros:")
    if distribucion == "ALL" and version != "ALL":
        log.error("Definida version, pero no definida la distribucion a la cual pertenece")
        usage()
        sys.exit(-1)

    if distribucion not in ["ubuntu","fedora","opensuse","ALL"]:
        log.error("Indicada una distribucion no soportada")
        usage()
        sys.exit(-1)

    log.info("Parametros leidos:")
    log.info("\tDistribucion: [%s]" % (distribucion))
    log.info("\tVersion: [%s]" % (version))

    if distribucion == "ALL":
        distros = DISTRIBUCIONES_SOPORTADAS
    else:
        distros = distribucion

    estadoPaquetesUbuntu = estadoPaquetesFedora = estadoPaquetesOpensuse = ESTADO_INICIAL

    crearDirectoriosDeSalida()

    if "ubuntu" in distros:
        estadoPaquetesUbuntu = construirPaquetesDebSrc()

    #if ("fedora" in distros) or ("opensuse" in distros):
    #	estadoPaquetesFedora, estadoPaquetesOpensuse = construirPaquetesRpmSrc()

    for distro in distros:

        log.info("Procesando distribucion %s" % distro)
        #if distro == "ubuntu" and estadoPaquetesUbuntu == ESTADO_SRC_PKGS_BUILDED:
        if distro == "ubuntu":
            estadoPaquetesUbuntu = actualizarDebBasetgz()
            estadoPaquetesUbuntu = adaptarPaquetesParaUbuntu()

        #elif distro == "fedora" and estadoPaquetesFedora == ESTADO_SRC_PKGS_BUILDED:
        #	estadoPaquetesFedora = adaptarPaquetesParaFedora()

        #elif distro == "opensuse" and estadoPaquetesOpensuse == ESTADO_SRC_PKGS_BUILDED:
        #	estadoPaquetesOpensuse = adaptarPaquetesParaOpensuse()


    log.info("Publicacion de paquetes (pagina web tipo tabla con enlaces a los paquetes generados)");
    r = report(fechaHoraInicial)
    r.find_ubuntu_pkgs()
    r.find_fedora_pkgs()
    r.find_opensuse_pkgs()
    r.save()

    log.info("Envio de mail de aviso con el resultado de la generacion (salida de log?)")

    mailPositivoDestino = "aescamilla@indra.es"
    mailPositivoAsunto 	= "EMLinux: Disponibles paquetes para %s..."
    mailPositivoMensaje = """
Hola,

    Tras una dura pelea se ha conseguido triunfalmente generar los paquetes para %s.

Gracias por su colaboracion
    """

    mailNegativoDestino = "aescamilla@indra.es"
    mailNegativoAsunto 	= "EMLinux: Problemas en la generacion de paquetes para %s..."
    mailNegativoMensaje = """
Hola,

    Problemones a la hora de generar paquetes para %s.
    Lista de problemones:
%s
Gracias por su colaboracion
    """

    listaDistribucionesConstruidas = ""
    listaDistribucionesProblematicas = ""
    listaProblemones = ""

    if estadoPaquetesUbuntu == ESTADO_PKGS_BUILDED:
        listaDistribucionesConstruidas += "Ubuntu "
    else:
        listaDistribucionesProblematicas += "Ubuntu "
        listaProblemones += "\t\t* Ubuntu   -- %s\n" % (dictEstado[estadoPaquetesUbuntu])

    if estadoPaquetesFedora == ESTADO_PKGS_BUILDED:
        listaDistribucionesConstruidas += "Fedora "
    else:
        listaDistribucionesProblematicas += "Fedora "
        listaProblemones += "\t\t* Fedora   -- %s\n" % (dictEstado[estadoPaquetesFedora])

    if estadoPaquetesOpensuse == ESTADO_PKGS_BUILDED:
        listaDistribucionesConstruidas += "Opensuse"
    else:
        listaDistribucionesProblematicas += "Opensuse"
        listaProblemones += "\t\t* Opensuse -- %s\n" % (dictEstado[estadoPaquetesOpensuse])

    if listaDistribucionesConstruidas != "":
        log.debug("\tEnvio mail de aviso de paquetes disponible")
        asunto = mailPositivoAsunto % (listaDistribucionesConstruidas)
        mensaje = mailPositivoMensaje % (listaDistribucionesConstruidas)
        enviarMailConResultadoGeneracion(mailPositivoDestino,asunto,mensaje)

    if listaDistribucionesProblematicas != "":
        log.debug("\tEnvio mail de error de paquetes con problemas")
        asunto = mailNegativoAsunto % (listaDistribucionesProblematicas)
        mensaje = mailNegativoMensaje % (listaDistribucionesProblematicas,listaProblemones)
        enviarMailConResultadoGeneracion(mailNegativoDestino,asunto,mensaje)
