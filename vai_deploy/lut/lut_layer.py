import torch
import torch.nn as nn
import re
import argparse
import os
from ofa.utils.layers import set_layer_from_config, ResidualBlock
from ofa.utils import MyGlobalAvgPool2d

import pytorch_nndct as nndct

layer_name_rules = {}

def match_conv(kernel, in_h, in_w, in_c, out_h, out_w, out_c):
    kernel = 3
    stride_h = in_h // out_h
    stride_w = in_w // out_w
    assert(stride_h == stride_w)
    config = {
        "name": "ConvLayer",
        "kernel_size": kernel,
        "stride": stride_h,
        "dilation": 1,
        "groups": 1,
        "bias": False,
        "has_shuffle": False,
        "in_channels": in_c,
        "out_channels": out_c,
        "use_bn": True,
        "act_func": "relu6",
        "dropout_rate": 0,
        "ops_order": "weight_bn_act"
    }
    data = torch.randn([1, in_c, in_h, in_w])
    net = nn.Sequential(set_layer_from_config(config))
    return (data, net)

def match_first_conv(in_h, in_w, in_c, out_h, out_w, out_c):
    return match_conv(3, in_h, in_w, in_c, out_h, out_w, out_c)

layer_name_rules["Conv-input:(\d+)x(\d+)x(\d+)-output:(\d+)x(\d+)x(\d+)"] = match_first_conv

def match_feature_mix(in_h, in_w, in_c, out_h, out_w, out_c):
    data, conv = match_conv(1, in_h, in_w, in_c, out_h, out_w, out_c)
    pool = MyGlobalAvgPool2d(keep_dim=False)
    net = nn.Sequential(conv, pool)
    return (data, net)

layer_name_rules["Conv_1-input:(\d+)x(\d+)x(\d+)-output:(\d+)x(\d+)x(\d+)"] = match_feature_mix

def match_mbconv(in_h, in_w, in_c, out_h, out_w, out_c, expand, kernel, stride, idskip):
    config = {
        "name": "MobileInvertedResidualBlock",
            "mobile_inverted_conv": {
                "name": "MBInvertedConvLayer",
                "in_channels": in_c,
                "out_channels": out_c,
                "kernel_size": kernel,
                "stride": stride,
                "expand_ratio": expand,
                "mid_channels": in_c * expand,
                "act_func": "relu6",
                "use_se": False
            },
        "shortcut": None
    }
    if idskip == '1':
        config["shortcut"] = {
            "name": "IdentityLayer",
            "in_channels": [
                in_c
            ],
            "out_channels": [
                out_c
            ],
            "use_bn": False,
            "act_func": None,
            "dropout_rate": 0,
            "ops_order": "weight_bn_act"
        }
    data = torch.randn([1, in_c, in_h, in_w])
    net = nn.Sequential(ResidualBlock.build_from_config(config))
    return (data, net)

layer_name_rules["expanded_conv-input:(\d+)x(\d+)x(\d+)-output:(\d+)x(\d+)x(\d+)-expand:(\d+)-kernel:(\d+)-stride:(\d+)-idskip:(\d+)"] = match_mbconv

def match_classifier(in_h, in_w, in_c, out_c):
    config = {
        "name": "LinearLayer",
        "in_features": in_h * in_w * in_c,
        "out_features": out_c,
        "bias": True,
        "use_bn": False,
        "act_func": None,
        "dropout_rate": 0,
        "ops_order": "weight_bn_act"
    }
    data = torch.randn([1, in_c * in_h * in_w])
    net = nn.Sequential(set_layer_from_config(config))
    return (data, net)

layer_name_rules["Logits-input:(\d+)x(\d+)x(\d+)-output:(\d+)"] = match_classifier



def build_layer_from_name(name):
    for k, v in layer_name_rules.items():
        match = re.match(k, name)
        if match:
            return v(*[int(x) for x in match.groups()])
    return None

def vai_quantize(data, net):
    net.eval()
    quantizer = nndct.torch_quantizer('calib', net, data, device=torch.device("cpu"))
    quant_model = quantizer.quant_model
    quant_model.eval()
    for i in range(10):
        fake_data = torch.rand_like(data)
        quant_model(fake_data)
    quantizer.export_quant_config()

def vai_deploy(data, net):
    net.eval()
    quantizer = nndct.torch_quantizer('test', net, data, device=torch.device("cpu"))
    quant_model = quantizer.quant_model
    quant_model.eval()
    quant_model(data)
    quantizer.export_xmodel()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="The name of layer")
    args = parser.parse_args()

    data, net = build_layer_from_name(args.name)

    # The compiler may complain `Data value is out of range!' if we don't initialize the weights
    def weights_init(m):
        if isinstance(m, nn.Conv2d):
            torch.nn.init.normal_(m.weight)
    net.apply(weights_init)

    vai_quantize(data, net)
    vai_deploy(data, net)