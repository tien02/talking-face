import os
import onnx
import onnx_graphsurgeon as gs

base_dir = "./tensorrt"
onnx_path = os.path.join(base_dir, "model.onnx")
onnx_gs_path = os.path.join(base_dir, "model_gs.onnx")

model = onnx.load(onnx_path)
graph = gs.import_onnx(model)
for node in graph.nodes:
    if "GridSample" in node.name:
        node.attrs = {"name": "GridSample3D", "version": 1, "namespace": ""}
        node.op = "GridSample3D"

onnx.save(gs.export_onnx(graph), onnx_gs_path)