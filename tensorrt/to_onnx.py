import torch
from src.utils.init_path import init_path
from src.facerender.animate import AnimateFromCoeff

source_image_path = 'tensorrt/source_image.pt'
kp_driving_path = 'tensorrt/kp_driving.pt'
kp_source_path = 'tensorrt/kp_source.pt'

source_image = torch.load(source_image_path)
kp_driving = torch.load(kp_driving_path)
kp_source = torch.load(kp_source_path)

checkpoint_dir = './checkpoints'
size = 256
old_version = False
preprocess = 'crop'
device = "cuda:0"

sadtalker_paths = init_path(checkpoint_dir, 'src/config', size, old_version, preprocess)

animate_from_coeff = AnimateFromCoeff(sadtalker_paths, device)
model = animate_from_coeff.generator

symbolic_names = {0: "batch_size"}
torch.onnx.export(model=model,
    args = (source_image, kp_driving['value'], kp_source['value']),
    f = "tensorrt/generator/model.onnx",
    opset_version=16,
    do_constant_folding=True, 
    input_names=["source_image", "kp_driving", "kp_source"],
    output_names=["prediction"],
    dynamic_axes={
        "source_image": symbolic_names,
        "kp_driving": symbolic_names,
        "kp_source": symbolic_names
    }
)