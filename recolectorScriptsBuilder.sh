BASE_ZIVA=/root/builder
BASE_ZIVADEBIAN=/root/builder
BASE_SVN=./builder

echo "Copia scripts del sistema builder, en la maquina ziva, en el arbol de directorios del repositorio"
echo "NOTA: Para evitar introducir 70 veces la password aplicar receta --> http://linuxproblem.org/art_9.html"

comando="scp root@ziva:$BASE_ZIVA/bin/buildd $BASE_SVN/"
echo $comando
$comando

comando="scp root@ziva:$BASE_ZIVA/bin/daemon.py $BASE_SVN/"
echo $comando
$comando

comando="scp root@ziva:$BASE_ZIVA/bin/build.sh $BASE_SVN/"
echo $comando
$comando

comando="scp root@ziva:$BASE_ZIVA/bin/generadorPaquetesRPM.py $BASE_SVN/"
echo $comando
$comando

comando="scp root@ziva:$BASE_ZIVA/bin/genMail.py $BASE_SVN/"
echo $comando
$comando

comando="scp root@ziva:$BASE_ZIVA/bin/report.py $BASE_SVN/"
echo $comando
$comando

comando="scp root@ziva:$BASE_ZIVA/chroots/deb-src-builder/root/builder/bin/build.sh $BASE_SVN/deb-src-builder/"
echo $comando
$comando

comando="scp -P 2069 root@ziva:$BASE_ZIVADEBIAN/bin/build_rpm_src.sh $BASE_SVN/VMDebian/"
echo $comando
$comando

comando="scp -P 2069 root@ziva:$BASE_ZIVADEBIAN/bin/build_rpm_bin.sh $BASE_SVN/VMDebian/"
echo $comando
$comando

comando="scp -P 2069 root@ziva:$BASE_ZIVADEBIAN/chroots/rpm-src-builder/root/builder/bin/build.sh $BASE_SVN/VMDebian/rpm-src-builder/"
echo $comando
$comando

comando="scp -P 2069 root@ziva:$BASE_ZIVADEBIAN/chroots/fedora/16/builder/root/builder/bin/build.sh $BASE_SVN/VMDebian/fedora/"
echo $comando
$comando

comando="scp -P 2069 root@ziva:$BASE_ZIVADEBIAN/chroots/opensuse/12.1/builder/root/builder/bin/build.sh $BASE_SVN/VMDebian/opensuse/"
echo $comando
$comando
