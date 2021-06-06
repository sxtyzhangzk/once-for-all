#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo Please specify a example LUT
    exit 1
fi

if [ ! -f arch.json ]; then
    echo Please put 'arch.json' file to current directory
    exit 1
fi

if [ -z "$PYNQNAME" ]; then
    PYNQNAME=pynq
fi


CURDIR=$(dirname "$BASH_SOURCE")

ssh $PYNQNAME "rm -rf ~/lut-workspace; mkdir ~/lut-workspace"
scp $CURDIR/lut/lut_run.py $PYNQNAME:~/lut-workspace/

python3 $CURDIR/lut_gen_makefile.py $1 lut.make
make -f lut.make clean
make -f lut.make -j$(nproc)

scp ./*.xmodel $PYNQNAME:~/lut-workspace/
ssh -t $PYNQNAME "cd ~/lut-workspace; sudo python3 lut_run.py"
scp $PYNQNAME:~/lut-workspace/lut.yaml .

echo All done.