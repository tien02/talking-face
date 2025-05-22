import time
import requests
import base64

# Test input data
text = "Hello, this is a test of real-time video generation."
speaker_id = "random"

# Load an image file to send (as bytes)
with open("examples/avatar.png", "rb") as f:
    image_bytes = f.read()

# Encode the image in base64 for transport over HTTP
image_base64 = base64.b64encode(image_bytes).decode("utf-8")

# Payload for the POST request
payload = {
    "text": text,
    "speaker_id": speaker_id,
    "image_bytes": image_base64
}

start = time.time()
# Make POST request to Ray Serve API
response = requests.post("http://0.0.0.0:8091/generate", json=payload)

total_time = time.time() - start
# Handle response
if response.status_code == 200:
    result = response.json()
    print(result)
    video_base64 = result["video_base64"]

    # Optionally save the video to file
    video_bytes = base64.b64decode(video_base64)
    with open("output_video.mp4", "wb") as f:
        f.write(video_bytes)

    print("Video saved to output_video.mp4")
else:
    print("Request failed:", response.status_code, response.text)

print(f"Total time: {total_time}")