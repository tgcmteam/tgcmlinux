import sys
import smtplib
import mimetypes
from email.MIMEText import MIMEText
from email.message import Message
from email.mime.multipart import MIMEMultipart

listaCorreoTodos = ["mpcrecio@eservicios.indra.es","fbgonzalez@indra.es","jmgonzalezc@indra.es", "dcastellanos@indra.es","imorillo@indra.es","jrandrino@indra.es","rgserranos@eservicios.indra.es"]
listaCorreoDiscreta = ["jmgonzalezc@indra.es","aescamilla@indra.es"]

#listaCorreoTodos = ["gallina17@indra.es","aescamilla@indra.es"]
#listaCorreoDiscreta = ["aescamilla@indra.es"]

########################################
#
def enviarMailConResultadoGeneracion(toAddr, subject, message, adjuntos=[]):

    """Sends mail"""
    server = smtplib.SMTP("smtp.indra.es", 25)
    server.starttls()
##    server.set_debuglevel(1)
    server.login("tgcmteam", "tgcm2012")

    outer = MIMEMultipart()

    outer['To']= ', '.join(toAddr)
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

    distribucionesGeneradas = "ubuntu, fedora16 y openSUSE 12.1"
    plantillaResumenDistribucionesGeneradas = "ubuntu (%s), fedora16 (%s) y openSUSE 12.1 (%s)"

    resultadoOK = True
    fechaHora = sys.argv[1]
    versionSVNdeb = sys.argv[2]
    versionSVNrpm = sys.argv[3]
    ficInformeGeneracion = sys.argv[4]

    resumenDistribucionesGeneradas = plantillaResumenDistribucionesGeneradas % (versionSVNdeb,versionSVNrpm,versionSVNrpm)

    if resultadoOK:
        #log.info("Envio de mail de aviso con el resultado de la generacion (salida de log?)")
        mailPositivoDestino = listaCorreoTodos
        mailPositivoAsunto 	= "EMLinux: Disponibles paquetes para %s..."
        mailPositivoMensaje = """Hola,

Generacion de paquetes %s iniciada el %s.

Version SVN y URL para recoger paquetes:
  UBUNTU ==> #SVN: %s -- http://ziva.tid.indra.es/archive/ubuntu/pool/main/t/tgcm/
  FEDORA ==> #SVN: %s -- http://ziva.tid.indra.es/archive/fedora16/
  OpSUSE ==> #SVN: %s -- http://ziva.tid.indra.es/archive/opensuse121/

Detalle del proceso de generacion:
%s
Gracias por su colaboracion
    """
        #log.debug("\tEnvio mail de aviso de paquetes disponible")
        asunto = mailPositivoAsunto % (resumenDistribucionesGeneradas)

        strInforme = ""
        fInf = open(ficInformeGeneracion,"r")
        for linea in fInf:
            strInforme += linea
        fInf.close()

        mensaje = mailPositivoMensaje % (distribucionesGeneradas,fechaHora,versionSVNdeb,versionSVNrpm,versionSVNrpm,strInforme)
        try:
            enviarMailConResultadoGeneracion(mailPositivoDestino,asunto,mensaje)
        except smtplib.SMTPAuthenticationError(code, resp):
            #log.error("ERROR de autenticacion ante servidor de correo!!")
            print "ERROR de autenticacion ante servidor de correo!!"
