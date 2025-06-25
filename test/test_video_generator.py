import json
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

response = requests.post("http://0.0.0.0:8091/generate", json=payload)

total_time = time.time() - start

if response.status_code == 200:
    print(response.text)

    reponse_data = json.loads(response.text)

    while True:
        response = requests.get(f"http://0.0.0.0:8091/video?session_id={reponse_data['session_id']}")

        print(response)

        if response.status_code==200:
            print(response.text)

            response_data = json.loads(response.text)

            if response_data is not None:
                if response_data['status'] == "SUCCESS":
                    print("Finish")
                    break

        time.sleep(2)
else:
    print("Request failed:", response.status_code, response.text)

print(f"Total time: {total_time:.2f} seconds")
