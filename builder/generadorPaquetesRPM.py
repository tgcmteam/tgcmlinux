# -*- coding: utf-8 -*-

# Bloque de imports
import sys, logging, getopt, time, os, subprocess
import socket, shutil

VERSION = "1.0"
FECHA = "octubre de 2011"

fInf = None
log = None


#######################################
#
def inicializarSistemaLogs (fichero, nivelDebug):

    if nivelDebug == "CRITICAL": 	nivelLogging = logging.CRITICAL
    elif nivelDebug == "ERROR": 	nivelLogging = logging.ERROR
    elif nivelDebug == "WARNING": 	nivelLogging = logging.WARNING
    elif nivelDebug == "INFO": 		nivelLogging = logging.INFO
    elif nivelDebug == "DEBUG":		nivelLogging = logging.DEBUG
    else: assert(0)

    logger = logging.getLogger("XX")
    logger.setLevel(nivelLogging)

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
    log.info("buildRPMs: Version %s, INDRA Sistemas, %s",VERSION, FECHA)


########################################
#
def usage():
    print """
buildRPMs: Genera paquetes RPM con la distribucion Linux del Escritorio Movistar. Uso:
  buildRPMs -i <nombreFicheroInforme> [-D <nivelDebug>] [-h]

donde:
  -i <nombreFicheroInforme> -- Indica el nombre del fichero que acumula informacion sobre los pasos de la generacion
  -D <nivelDebug> -- Selecciona nivel de debug deseado. Valores posibles (de menos a mas verboso):
                     CRITICAL, ERROR, WARNING, INFO, DEBUG (por defecto se aplica INFO)
  -h -- Muestra la ayuda

  NOTA: Este script no puede lanzarse desde una sesion ssh con la Xs entuneladas ("ssh -X").
Da un error de "X11 connection rejected because of wrong authentication".
No se porque lo da, simplemente no hacerlo, lanzarlo desde una sesion ssh normal.
"""

########################################
#
def getEstadoMaquinaVirtual(nameVM):
    global log

    cmd = 'su builder -c "/usr/bin/VBoxManage showvminfo \"Debian-builder\"" | grep State'

    p = subprocess.Popen(cmd, shell=True, bufsize=0,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=False)

    std_output ,std_err = p.communicate()
    return_code = p.returncode

    succes_code = 0
    if return_code != succes_code:
        raise Exception("Failed command %s : %s" %(cmd,std_output))

    estado = "estado raro"

    if std_output:
        log.debug(std_output)

        if std_output.find("running") != -1:
            estado = "running"

        elif std_output.find("powered off") != -1:
            estado = "powered off"

    return estado

########################################
#
def arrancaMaquinaVirtual(nameVM="Debian-builder"):

    log.info("Arrancando maquina virtual %s..." % nameVM)

    estadoVM = getEstadoMaquinaVirtual(nameVM)
    log.debug("\tEstado de la maquina virtual: %s" % estadoVM)

    if estadoVM == "powered off":
        cmd = 'su builder -c "/usr/bin/VBoxManage startvm \"Debian-builder\""'

        log.debug("\tSe lanza comando de arranque: %s" % cmd)
        p = subprocess.Popen(cmd, shell=True, bufsize=0,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=False)

        std_output ,std_err = p.communicate()
        return_code = p.returncode

        if std_output:
            log.debug(std_output)

        succes_code = 0
        if return_code != succes_code:
            raise Exception("Failed command %s : %s" %(cmd,std_output))

        log.debug("\tSe espera un minuto antes de consultar el estado de la maquina virtual...")
        time.sleep(60)

        estadoVM = getEstadoMaquinaVirtual(nameVM)
        log.debug("\tEstado de la maquina virtual: %s" % estadoVM)

        if estadoVM != "running":
            log.error("Maquina virtual no se ha arrancado correctamente (estado: %s)!. Salimos." % estadoVM)
            sys.exit(-1)

    elif estadoVM == "running":
        log.warning("Maquina virtual %s se encuentra ya ejecutandose!" % nameVM)

    else:
        log.error("Maquina virtual %s se encuentra en estado raro!. Salimos sin tocar nada." % nameVM)
        sys.exit(-1)


########################################
#
def generaPaquetesRPMsrc():
    global fInf

    fInf.write("\n[RPM] Fase de construccion de paquetes fuente...\n")
    log.info("Lanzando generacion de RPM fuente dentro de la maquina virtual...")

    cmd = 'ssh root@localhost -p 2069 "./builder/bin/build_rpm_src.sh"'

    log.debug("\tSe lanza comando de generacion: %s" % cmd)
    p = subprocess.Popen(cmd, shell=True, bufsize=0,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=False)

    std_output ,std_err = p.communicate()
    return_code = p.returncode
    log.debug("\tCodigo de retorno: %d" % return_code)

    if std_output:
        log.debug(std_output)

    anexaInformeGeneracionRemoto()

    if return_code == 0:
        fInf.write("  Construidos paquetes fuente .RPM\n")

    else:
        fInf.write("  NO construidos paquetes fuente .RPM\n")

    return return_code

########################################
#
def generaPaquetesRPMbin(distro):
    global fInf

    fInf.write("\n[RPM-%s] Fase de construccion de paquetes binarios...\n" % distro)
    log.info("Lanzando generacion de RPM binarios dentro de la maquina virtual...")

    cmd = 'ssh root@localhost -p 2069 "./builder/bin/build_rpm_bin.sh %s"' % distro

    log.debug("\tSe lanza comando de generacion: %s" % cmd)
    p = subprocess.Popen(cmd, shell=True, bufsize=0,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=False)

    std_output ,std_err = p.communicate()
    return_code = p.returncode
    log.debug("\tCodigo de retorno: %d" % return_code)

    if std_output:
        log.debug(std_output)

    anexaInformeGeneracionRemoto()

    if return_code == 0:
        fInf.write("  Construidos paquetes binarios .RPM para %s\n" % distro)

    else:
        fInf.write("  NO construidos paquetes binarios .RPM para %s\n" % distro)

    return return_code


########################################
#
def copiaFicheroLatestRevisionALocal():

    log.info("Copio fichero latest-revision con el numero de generacion SVN...")

    cmd = 'scp -P 2069 root@localhost:/root/builder/chroots/rpm-src-builder/root/builder/svn/tgcm/snapshot/latest-revision /root/builder/latest-revision-rpm'

    log.debug("\tSe lanza comando de copia: %s" % cmd)
    p = subprocess.Popen(cmd, shell=True, bufsize=0,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=False)

    std_output ,std_err = p.communicate()
    return_code = p.returncode
    log.debug("\tCodigo de retorno: %d" % return_code)

    if std_output:
        log.debug(std_output)

    return return_code


########################################
#
def anexaInformeGeneracionRemoto():
    global fInf

    log.info("Se anexa el informe de generacion remoto al informe global...")

    log.debug("\tSe copia el fichero con el informe de generacion a local")

    cmd = 'scp -P 2069 root@localhost:/root/builder/InformeGeneracion.log /root/builder/InformeGeneracionRpm-parcial.log'

    log.debug("\tSe lanza comando de copia: %s" % cmd)
    p = subprocess.Popen(cmd, shell=True, bufsize=0,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=False)

    std_output ,std_err = p.communicate()
    return_code = p.returncode
    log.debug("\tCodigo de retorno: %d" % return_code)

    if std_output:
        log.debug(std_output)

    log.debug("\tSe lee el contenido del informe de generacion copiado y lo vuelco en el informe general")

    fInfParcial = open("/root/builder/InformeGeneracionRpm-parcial.log","r")
    for linea in fInfParcial:
        fInf.write(linea)
    fInfParcial.close()

    return return_code


########################################
#
def borraRPMsDelArchivo(strDistribucion):

    log.info("Borrando RPMs de %s del archivo local..." % strDistribucion)

    cmd = 'rm -fr /root/builder/archive/%s' % strDistribucion

    log.debug("\tSe lanza comando de borrado: %s" % cmd)
    p = subprocess.Popen(cmd, shell=True, bufsize=0,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=False)

    std_output ,std_err = p.communicate()
    return_code = p.returncode
    log.debug("\tCodigo de retorno: %d" % return_code)

    if std_output:
        log.debug(std_output)

    return return_code


########################################
#
def copiaRPMsAlArchivo(strDistribucion):

    log.info("Copiando RPMs de %s generados en la maquina virtual al archivo..." % strDistribucion)

    cmd = 'scp -r -P 2069 root@localhost:/root/builder/archive/%s/ /root/builder/archive/' % strDistribucion

    log.debug("\tSe lanza comando de copia: %s" % cmd)
    p = subprocess.Popen(cmd, shell=True, bufsize=0,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=False)

    std_output ,std_err = p.communicate()
    return_code = p.returncode
    log.debug("\tCodigo de retorno: %d" % return_code)

    if std_output:
        log.debug(std_output)

    return return_code


########################################
#
def paraMaquinaVirtual(nameVM="Debian-builder"):

    log.info("Parando maquina virtual %s..." % nameVM)

    estadoVM = getEstadoMaquinaVirtual(nameVM)
    log.debug("\tEstado de la maquina virtual: %s" % estadoVM)

    if estadoVM == "running":
        cmd = 'su builder -c "/usr/bin/VBoxManage controlvm \"Debian-builder\" poweroff"'

        log.debug("\tSe lanza comando de parada: %s" % cmd)
        p = subprocess.Popen(cmd, shell=True, bufsize=0,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=False)

        std_output ,std_err = p.communicate()
        return_code = p.returncode

        if std_output:
            log.debug(std_output)

        succes_code = 0
        if return_code != succes_code:
            raise Exception("Failed command %s : %s" %(cmd,std_output))

        log.debug("\tSe espera unos segundos antes de consultar el estado de la maquina virtual")
        time.sleep(10)

        estadoVM = getEstadoMaquinaVirtual(nameVM)
        log.debug("\tEstado de la maquina virtual: %s" % estadoVM)

        if estadoVM != "powered off":
            log.error("Maquina virtual no se ha parado correctamente (estado: %s)!. Salimos." % estadoVM)
            sys.exit(-1)

    elif estadoVM == "powered off":
        log.warning("Maquina virtual %s se encuentra ya parada!" % nameVM)

    else:
        log.error("Maquina virtual %s se encuentra en estado raro!. Salimos sin tocar nada." % nameVM)
        sys.exit(-1)



#######################################################
###################### INICIO ##########################
########################################################
if __name__ == "__main__":
    global log

    nivelDebug = "INFO"
    nombreFicheroInforme = ""

    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:D:h")

    except getopt.GetoptError, valor:
        # print help information and exit:
        log.error("Opcion incorrecta: %s",valor)
        usage()
        sys.exit(2)

    for o, a in opts:

        if o == "-i":
            nombreFicheroInforme = a

        elif o == "-D":
            nivelDebug = a

        elif o == "-h":
            usage()
            sys.exit()

        else:
            print "Opcion ERRONEA: %s" % o
            usage()
            sys.exit()

    if nivelDebug not in ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]:
        print "Indicado un nivel de debug no reconocido"
        usage()
        sys.exit(-1)

    if nombreFicheroInforme == "" or not os.access(nombreFicheroInforme,os.W_OK):
        print "No indicado nombre del fichero de informe, o no se puede acceder a dicho fichero"
        usage()
        sys.exit(-1)

    # Prepara el sistema de logs, formatos, salidas, etc
    nombreFicheroLog = "generadorPaquetesRPM.log"
    log = inicializarSistemaLogs(nombreFicheroLog, nivelDebug)

    log.info("*** INICIO DE PROGRAMA **********")
    show_version(log)

    log.info("Lectura de parametros. Parametros leidos:")
    log.info("\tNivel de debug: [%s]" % (nivelDebug))
    log.info("\tFichero de informe: [%s]" % (nombreFicheroInforme))

    fInf = open(nombreFicheroInforme,"a")

    resultadoOK = True
    try:
        arrancaMaquinaVirtual()

        resultadoGeneracionRPMsrc = generaPaquetesRPMsrc()

        if resultadoGeneracionRPMsrc == 0:

            resultado = generaPaquetesRPMbin("FEDORA")
            if resultado == 0:
                log.debug("Solo se recupera el fichero con el numero de revisiones si la generacion ha sido correcta")
                copiaFicheroLatestRevisionALocal()

                log.debug("Solo se borra los repositorios RPM-FEDORA y se realiza la copia si la generacion ha sido correcta")
                borraRPMsDelArchivo("fedora16")
                copiaRPMsAlArchivo("fedora16")

            resultado = generaPaquetesRPMbin("OPENSUSE")
            if resultado == 0:
                log.debug("Solo se recupera el fichero con el numero de revisiones si la generacion ha sido correcta")
                copiaFicheroLatestRevisionALocal()

                log.debug("Solo se borra los repositorios RPM-OPENSUSE y se realiza la copia si la generacion ha sido correcta")
                borraRPMsDelArchivo("opensuse121")
                copiaRPMsAlArchivo("opensuse121")

        #actualizaRepositorioRPM() -- Parece que no es necesario
        paraMaquinaVirtual()

    #except os.error as (errno, msg):
    except Exception:
        resultadoOK = False

    fInf.close()


