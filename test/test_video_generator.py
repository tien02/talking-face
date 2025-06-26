import json
import time
import requests
import base64

# Test input data
text = "What is the difference between SQL and NoSQL databases? When would you use each?"
speaker_id = "male"

payload = {
    "text": text,
    "speaker_id": speaker_id,
    "alpha": 0.5,
    "threshold": 0.9,
}

start = time.time()

response = requests.post("http://0.0.0.0:8091/generate", json=payload)

total_time = time.time() - start

if response.status_code == 200:
    print(response.text)

    reponse_data = json.loads(response.text)

    while True:
        response = requests.get(f"http://0.0.0.0:8091/video?session_id={reponse_data['session_id']}")

        print(response.text)

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
