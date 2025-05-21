# 🗣️ TalkingFace — End-to-End Talking Head Generation Pipeline

Welcome to **TalkingFace**, an end-to-end pipeline designed for generating realistic talking head videos from text or audio inputs.

This project supports using [SadTalker](https://github.com/OpenTalker/SadTalker) for high-quality video generation, combined with [Parler TTS](https://github.com/huggingface/parler-tts) for natural and expressive text-to-speech synthesis. It also features:

- ⚡ TensorRT model export for lightning-fast inference  
- 🧵 Multithreaded seamless cloning to keep the pipeline smooth and efficient  
- 🚀 API implementation with Ray Serve for easy scaling and deployment  

Whether you want to convert text into talking avatars or bring portraits to life with synced speech, **TalkingFace** makes the entire process streamlined and accessible.

---

## ⚙️ Installation

```bash
conda create -n talkinghead python=3.10 -y

conda activate talkinghead

pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu121

conda install ffmpeg

pip install -r requirements.txt
````

## Download models
Run the following script to automatically download all the models:
```bash
bash scripts/download_models.sh
```
---

## 🛠️ How to Use

### 1. Export the Generator to TensorRT

1. Export to ONNX

```bash
python tensorrt/to_onnx.py
```

2. Export to ONNX graphsurgeon
```bash
python tensorrt/to_onnx_gs.py
```

3. Compile the Grid Sample 3D
```bash
cd tensorrt/plugin
mkdir build && cd build
cmake .. -DTensorRT_ROOT=/your/local/path/to/tensorrt
make
```

4. Export to TensorRT engine
```bash
sh to_trt.sh
```

This will generate a `model.engine` file optimized for fast inference.

### 2. Run Inference

```bash
python inference_trt.py \
    --driven_audio examples/audio.wav \
    --source_image examples/avatar.png \
    --still --preprocess full \
    --batch_size 8
```

You'll see your input image come to life, it may take some time!

---

## 🤝 Acknowledgements

Big shoutout to the amazing developers of [SadTalker](https://github.com/OpenTalker/SadTalker) for their inspiring open-source work — this project is built on their solid foundation.

Thanks also to the [Parler TTS](https://github.com/huggingface/parler-tts) team at Huggingface for their excellent text-to-speech module integration.

Special thanks to the blog post on [Zhihu](https://zhuanlan.zhihu.com/p/675551997) for the detailed instructions and insights into TensorRT implementation, and to [grid-sample3d-trt-plugin](https://github.com/SeanWangJS/grid-sample3d-trt-plugin) by SeanWangJS for the 3D grid sample TensorRT plugin.
