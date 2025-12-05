#!/usr/bin/env bash

poetry run black -l 72 src
find /home/szhumatiy/Work/cluster-live-verify -name \*.py -print0 | xargs -0 sed -i -e 's/^[[:space:]]\+$//' -e 's/[[:space:]]\+$//'

