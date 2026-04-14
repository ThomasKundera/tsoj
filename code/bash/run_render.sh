#!/bin/bash

# Location of this script
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
# Projectdir is two up
export PROJECTDIR="$( cd $SCRIPTDIR/../.. >/dev/null 2>&1 && pwd )"

export PYTHONDIR=$PROJECTDIR/code/blender

export PYTHONPATH=$PYTHONPATH:$PYTHONDIR
export BLENDER_USER_SCRIPTS=$PYTHONPATH:$PYTHONDIR

export WORKDIR=$PROJECTDIR/output
mkdir -p $WORKDIR

echo "Working in $WORKDIR"

cd $WORKDIR

blender --python-use-system-env -b -P $PROJECTDIR/code/blender/myscene.py

echo "Done"