#!/bin/bash

# Location of this script
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
# Projectdir is two up
export PROJECTDIR="$( cd $SCRIPTDIR/../.. >/dev/null 2>&1 && pwd )"

export LC_ALL=C

export PYTHONDIR=$PROJECTDIR/../common/blender
export PYTHONPATH=$PYTHONPATH:$PYTHONDIR
export BLENDER_USER_SCRIPTS=$PYTHONPATH:$PYTHONDIR

export WORKDIR=$PROJECTDIR/output

mkdir -p $WORKDIR

cd $WORKDIR

echo "Working in $WORKDIR"
rm -f $WORKDIR/blender.log
# Redirecting logs to WORKDIR/blender.log
/usr/bin/nice -20 blender --python-use-system-env -b -P $PROJECTDIR/code/blender/myscene.py 2>&1 | tee $WORKDIR/blender.log
#  -- --gpu-backend opengl

# Test if the render was successful from the log file
if grep -q "Finished" $WORKDIR/blender.log; then
    echo "✅ Render completed successfully."
    exit 0
else
    echo "❌ Render failed or was interrupted."
    exit 1
fi
