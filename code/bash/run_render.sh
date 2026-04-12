#!/bin/bash

# Location of this script
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
# Projectdir is two up
export PROJECTDIR="$( cd $SCRIPTDIR/../.. >/dev/null 2>&1 && pwd )"

export WORKDIR=$PROJECTDIR/output
mkdir -p $WORKDIR

echo "Working in $WORKDIR"

cd $WORKDIR

blender -b -P $PROJECTDIR/code/blender/simple_sphere.py

