import tensorrt as trt
import ctypes
import numpy as np
import pycuda.autoinit
import pycuda.driver as cuda

def load_engine(engine_path, logger):
    with open(engine_path, "rb") as f, trt.Runtime(logger) as runtime:
        engine = runtime.deserialize_cuda_engine(f.read())
        context = engine.create_execution_context()
        return engine, context

def inference(engine, context, inputs: dict):
    stream = cuda.Stream()
    bindings = {}
    device_buffers = {}

    # Set dynamic input shapes before accessing tensor shapes
    for name in engine:
        if engine.get_tensor_mode(name) == trt.TensorIOMode.INPUT:
            context.set_input_shape(name, tuple(inputs[name].shape))

    # Get all I/O tensor names
    tensor_names = [name for name in engine]

    for name in tensor_names:
        mode = engine.get_tensor_mode(name)
        dtype = trt.nptype(engine.get_tensor_dtype(name))
        shape = context.get_tensor_shape(name)

        if mode == trt.TensorIOMode.INPUT:
            host_input = inputs[name].cpu().numpy().astype(dtype).ravel()
            device_input = cuda.mem_alloc(host_input.nbytes)
            cuda.memcpy_htod_async(device_input, host_input, stream)
            device_buffers[name] = device_input
            bindings[name] = int(device_input)
            context.set_tensor_address(name, int(device_input))
        elif mode == trt.TensorIOMode.OUTPUT:
            size = np.prod(shape) * np.dtype(dtype).itemsize
            if size < 0:
                raise ValueError(f"Invalid shape {shape} for output tensor '{name}'")
            device_output = cuda.mem_alloc(int(size))
            device_buffers[name] = device_output
            bindings[name] = int(device_output)
            context.set_tensor_address(name, int(device_output))

    # Execute inference
    context.execute_async_v3(stream_handle=stream.handle)

    # Copy outputs back to host
    outputs = {}
    for name in tensor_names:
        if engine.get_tensor_mode(name) == trt.TensorIOMode.OUTPUT:
            dtype = trt.nptype(engine.get_tensor_dtype(name))
            shape = context.get_tensor_shape(name)
            size = np.prod(shape)
            host_output = np.empty(size, dtype=dtype)
            cuda.memcpy_dtoh_async(host_output, device_buffers[name], stream)
            outputs[name] = host_output.reshape(shape)

    stream.synchronize()
    return outputs


class OcclusionAwareSPADEGenerator:
    def __init__(self, engine_path: str, plugin_path: str):
        logger  = trt.Logger(trt.Logger.VERBOSE)
        success = ctypes.CDLL(plugin_path, mode = ctypes.RTLD_GLOBAL)
        if not success:
            print("load grid_sample_3d plugin error")
            raise Exception()

        trt.init_libnvinfer_plugins(logger, "")

        self.engine, self.context = load_engine(engine_path, logger)

    def __call__(self, source_image, kp_driving, kp_source):
        inputs = {
            "source_image": source_image,
            "kp_driving": kp_driving,
            "kp_source": kp_source,
        }

        """
        {
            "mask": mask,
            "occlusion_map": occlusion_map,
            "prediction": prediction 
        }
        """
        output = inference(self.engine, self.context, inputs)
        return output