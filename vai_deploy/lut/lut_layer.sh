#!/bin/bash
set -e
CURDIR=$(dirname "$BASH_SOURCE")
WORKDIR=workdir-$1

mkdir -p $WORKDIR

cd $WORKDIR
python3 "$CURDIR/lut_layer.py" $1

# Ignore the error of vai_c_xir since some of the layers in the LUT may not be flexible on some devices
#    it will complain `There is not enough bank space for the tensor' in this case
vai_c_xir -x quantize_result/Sequential_int.xmodel -a ../arch.json -o . -n $1 || true
cp $1.xmodel .. || true