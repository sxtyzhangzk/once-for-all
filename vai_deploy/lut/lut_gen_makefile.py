import yaml
import argparse
import os

current_directory = os.path.dirname(os.path.realpath(__file__))

def gen_makefile_from_example(filename, output):
    layer_names = []

    with open(filename, 'r') as stream:
        lutfile = yaml.safe_load(stream)
        for layer in lutfile:
            layer_names.append(layer)
    
    with open(output, 'w') as outfile:
        outfile.write(".PHONY: clean all\n")

        outfile.write("all: ")
        for i in range(len(layer_names)):
            outfile.write(f"task{i} ")  # We cannot use the xmodel filename as the target since it may contain special characters like ':'
        outfile.write("\n")

        outfile.write("clean:\n")
        outfile.write("\trm -f *.xmodel\n")
        outfile.write("\trm -rf workdir-*\n")
        outfile.write("\n")
        
        for i, layer in zip(range(len(layer_names)), layer_names):
            outfile.write(f"task{i}:\n")
            outfile.write(f"\t{current_directory}/lut_layer.sh {layer}\n")
            outfile.write("\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="The filename of the example LUT")
    parser.add_argument("output", help="The filename of the output Makefile")
    args = parser.parse_args()

    gen_makefile_from_example(args.filename, args.output)
    
