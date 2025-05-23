import time
import requests
import base64

# Test input data
text = "Hello, this is a test of real-time video generation."
speaker_id = "random"

with open("examples/avatar.png", "rb") as f:
    image_bytes = f.read()
image_base64 = base64.b64encode(image_bytes).decode("utf-8")

payload = {
    "text": text,
    "speaker_id": speaker_id,
    "image_bytes": image_base64
}

start = time.time()

response = requests.post("http://0.0.0.0:8091/generate", json=payload, stream=True)

total_time = time.time() - start

if response.status_code == 200:
    with open("output_video.mp4", "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:  # filter out keep-alive chunks
                f.write(chunk)
    print("Video saved to output_video.mp4")
else:
    print("Request failed:", response.status_code, response.text)

print(f"Total time: {total_time:.2f} seconds")
