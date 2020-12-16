#!/bin/bash

PACKAGE_NAME="$(./setup.py --name)"
VERSION="$(./setup.py --version)"

BASEDIR=$(dirname "$0")
FULLNAME="${PACKAGE_NAME}_${VERSION}focal"
DIST_DIR=${BASEDIR}/deb

if [ $UID != 0 ]
then
    echo "Please run this script with sudo:"
    echo "sudo $0 $*"
    exit 1
fi

echo "Prepare file structure"

if [ -d $DIST_DIR ]; then rm -Rf $DIST_DIR; fi

mkdir -p ${DIST_DIR}/${FULLNAME}/DEBIAN
mkdir -p ${DIST_DIR}/${FULLNAME}/usr/bin
mkdir -p ${DIST_DIR}/${FULLNAME}/usr/lib/python3/dist-packages/${PACKAGE_NAME}
mkdir -p ${DIST_DIR}/${FULLNAME}/usr/share/icons/hicolor/scalable/apps
mkdir -p ${DIST_DIR}/${FULLNAME}/usr/share/applications

./setup.py sdist
rsync -a --no-i-r --human-readable --info=progress2 ${BASEDIR}/${PACKAGE_NAME} ${DIST_DIR}/${FULLNAME}/usr/lib/python3/dist-packages
rsync -a --no-i-r --human-readable --info=progress2 ${BASEDIR}/${PACKAGE_NAME}.egg-info ${DIST_DIR}/${FULLNAME}/usr/lib/python3/dist-packages
cp ${BASEDIR}/bin/* ${DIST_DIR}/${FULLNAME}/usr/bin/
cp ${BASEDIR}/data/icons/* ${DIST_DIR}/${FULLNAME}/usr/share/icons/hicolor/scalable/apps/
cp ${BASEDIR}/data/desktop/* ${DIST_DIR}/${FULLNAME}/usr/share/applications

rm -rf ${BASEDIR}/${PACKAGE_NAME}.egg-info
rm -rf ${BASEDIR}/build
rm -rf ${BASEDIR}/dist

/bin/cat <<EOF > ${DIST_DIR}/${FULLNAME}/DEBIAN/control
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: base
Priority: optional
Architecture: all
Maintainer: Valentin Osipenko <valtron.forever@gmail.com>
Depends: python3-gi-cairo, python3-pydantic
Description: Docker-compose gui
EOF

/bin/cat <<EOF > ${DIST_DIR}/${FULLNAME}/DEBIAN/postinst
#!/bin/sh

set -e

if which py3compile >/dev/null 2>&1; then
	py3compile -p ${PACKAGE_NAME} -V 3.6-
fi
if which pypy3compile >/dev/null 2>&1; then
	pypy3compile -p ${PACKAGE_NAME} -V 3.6- || true
fi

exit 0
EOF
chmod +x ${DIST_DIR}/${FULLNAME}/DEBIAN/postinst

/bin/cat <<EOF > ${DIST_DIR}/${FULLNAME}/DEBIAN/prerm
#!/bin/sh
set -e

# Automatically added by dh_python3:
if which py3clean >/dev/null 2>&1; then
	py3clean -p ${PACKAGE_NAME} 
else
	dpkg -L ${PACKAGE_NAME} | perl -ne 's,/([^/]*)\.py$,/__pycache__/\1.*, or next; unlink $_ or die $! foreach glob($_)'
	find /usr/lib/python3/dist-packages/ -type d -name __pycache__ -empty -print0 | xargs --null --no-run-if-empty rmdir
fi

exit 0
EOF
chmod +x ${DIST_DIR}/${FULLNAME}/DEBIAN/prerm

chown -R root.root ${DIST_DIR}/${FULLNAME}/usr
find ${DIST_DIR}/${FULLNAME}/usr/lib/python3/dist-packages/${PACKAGE_NAME} | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

cd $DIST_DIR
dpkg-deb --build $FULLNAME

cd ..
chown -R $SUDO_USER.$SUDO_USER ${DIST_DIR}
rm -rf ${DIST_DIR}/${FULLNAME}