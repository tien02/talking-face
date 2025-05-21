trtexec \
  --onnx=./tensorrt/model_gs.onnx \
  --saveEngine=./tensorrt/model.engine \
  --plugins=./plugin/build/libgrid_sample_3d_plugin.so \
  --minShapes=source_image:1x3x256x256,kp_driving:1x15x3,kp_source:1x15x3 \
  --optShapes=source_image:8x3x256x256,kp_driving:8x15x3,kp_source:8x15x3 \
  --maxShapes=source_image:16x3x256x256,kp_driving:16x15x3,kp_source:16x15x3
