import gradio as gr
import requests
import base64
import uuid

def generate_video(text):
    # Load avatar image and encode
    with open("examples/avatar.png", "rb") as f:
        image_bytes = f.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    # Payload
    payload = {
        "text": text,
        "speaker_id": "random",
        "image_bytes": image_base64
    }

    # Unique filename to avoid conflicts
    output_path = f"output_{uuid.uuid4().hex}.mp4"

    # Send request
    response = requests.post("http://0.0.0.0:8091/generate", json=payload, stream=True)

    if response.status_code == 200:
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return output_path
    else:
        return f"Error: {response.status_code} - {response.text}"

# Gradio interface
demo = gr.Interface(
    fn=generate_video,
    inputs=gr.Textbox(lines=2, placeholder="Enter text for video generation..."),
    outputs=gr.Video(label="Generated Video"),
    title="Real-Time Text-to-Video Demo",
    description="Enter some text and watch the avatar generate a video in real time.",
)

if __name__ == "__main__":
    demo.launch()
