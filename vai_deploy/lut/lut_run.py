#!/usr/bin/env python3
from pynq_dpu import DpuOverlay
import numpy as np
import time
import glob
import os

overlay = DpuOverlay("dpu.bit")

with open("lut.yaml", 'w') as lutfile:
    for modelfile in glob.glob("*.xmodel"):
        overlay.load_model(modelfile)

        modelname = os.path.splitext(modelfile)[0]

        print(f"Model {modelname} Loaded.")

        dpu = overlay.runner

        shape_in  = [tuple(t.dims) for t in dpu.get_input_tensors()]
        shape_out = [tuple(t.dims) for t in dpu.get_output_tensors()]

        print("shapeIn = ", shape_in)
        print("shapeOut = ", shape_out)

        inputs  = [np.random.randn(*shape).astype(np.float32) for shape in shape_in]
        outputs = [np.random.randn(*shape).astype(np.float32) for shape in shape_out]

        COUNT = 1000

        start = time.time()
        for i in range(COUNT):
            job_id = dpu.execute_async(inputs, outputs)
            dpu.wait(job_id)
        end = time.time()

        mean_time = (end - start) / COUNT * 1000

        print(f"Time = {mean_time} ms")

        lutfile.write(f"{modelname}:\n")
        lutfile.write(f"  count: {COUNT}\n")
        lutfile.write(f"  mean: {mean_time}\n")
        lutfile.write(f"  std: 0\n") # We don't have the stderr data
