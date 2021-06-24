# Deploy OFA on Xilinx Vitis AI

A latency lookup table is necessary for OFA to predict the latency for a specific device. Here we provided scripts to generate the lookup table on Vitis AI platform. These scripts are based on the PyTorch flow of Vitis AI 1.3.

To get started, set up the Docker image of Vitis AI on the host (following the guide on https://github.com/Xilinx/Vitis-AI) and the PYNQ-DPU environment on the FPGA board (following the guide on https://github.com/Xilinx/DPU-PYNQ). In the docker image, switch to the pytorch flow and clone the once-for-all repo:

```
conda activate vitis-ai-pytorch 
git clone https://github.com/mit-han-lab/once-for-all
cd once-for-all
```

Then set up the ssh connection between the host and the FPGA board, you may want to edit `~/.ssh/config` and add an entry for the board:

```
Host pynq
	HostName *.*.*.* # The IP address of FPGA board
	User xilinx
```

It’s a good idea to copy the public key to the FPGA board:

```
ssh-keygen
ssh-copy-id pynq
```

Create a workspace for the LUT generator:

```
mkdir workspace
cd workspace
```

And copy the arch.json of your DPU configuration to the workspace. It should be generated when building the DPU hardware design.

```
cp <path to arch.json> arch.json
```

Now you could run the script to generate the lookup table. The script requires a previous lookup table to get all possible configurations of layers. We provided some examples in `vai_deploy/lut-examples`, pass the filename as the argument of the script to use them:

```
PYNQNAME=pynq ../vai_deploy/generate_lut.sh ../vai_deploy/lut-examples/128_lookup_table.yaml
```

The script will generate a xmodel file for each possible layer, copy them to the FPGA board (specified in environment variable `PYNQNAME`), run them on DPU and generate the new lookup table. You could check the generated table, which named `lut.yaml`

Note that some layers may fail to run on specific devices when the required on-chip RAM exceeds the hardware limit, you may encounter some red lines saying `There is not enough bank space for the tensor` and it is usually safe to ignore them as long as there is at least one feasible configuration for a layer.

When OFA finds a specialized network for FPGA, you could quantize it using the quantization tools of Vitis AI. We also have a script:

```
cd vai_deploy
python3 ./quantize.py
```

The quantization could be done without the docker environment, but later you need to use it to export the model to a xmodel file. Copy the scripts into docker and run:

```
python3 ./quantize.py --deploy
vai_c_xir -x quantize_result/ProxylessNASNets_int.xmodel -a arch.json -o . -n ProxylessNASNets
```