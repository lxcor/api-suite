#!/bin/sh

#version 1.0

ROOT=$PWD

VENV=$ROOT/sandbox/venv
VPIP=$VENV/bin/pip3

case "$1" in

    venv-install)

        echo 'venv-install'

        REQS=${2:-sandbox/requirements.txt}
        rm -rf $VENV
        python3 -m venv $VENV
        $VPIP install --upgrade pip setuptools wheel
        (cd sandbox && $VPIP install -r requirements.txt)
        ;;

    venv-update)

        echo 'venv-update'

        (cd sandbox && $VPIP install -r requirements.txt)
        ;;

    venv-uninstall)

        echo 'venv-uninstall'

        rm -rf $VENV
        ;;

    pip-update)

        echo 'pip-update'

        $VPIP install --upgrade pip
        ;;

    *)
        echo 'enter option'
        ;;

esac
