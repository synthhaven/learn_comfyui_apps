
import gradio as gr
from threading import Thread
# Start websocket client needs to be updated with the photomaker handler.
from websocket_client import start_websocket_client, message_queue
import time
import base64
from PIL import Image
from io import BytesIO
import asyncio
# This will be used from the ui
from photomaker_utils import run_photomaker_workflow

latest_message = ""
latest_image = None

# Function to process messages from the WebSocket client
# Function to process messages from the WebSocket client

# There are a few differences here.
# Namely, we will have ways to upload images. In the button press, the
# UI needs to send the request to server

import gradio as gr
from threading import Thread
import json
import uuid
import base64
from PIL import Image
import io
import time
from websocket_client import start_websocket_client_photomaker, message_queue, WS_SERVER_URL, DEFAULT_CLIENT_ID
from photomaker_utils import run_photomaker_workflow
latest_message = ""
latest_image = None

DEFAULT_CLIENT_ID = "06a96135-59b2-4a29-b7c8-a83fc011ea63"


# Function to process messages from the WebSocket client
# Function to process messages from the WebSocket client
def update_message():
    print("Starting Message update coroutine")
    global latest_message, latest_image
    while True:
        # print(message_queue)
        if not message_queue.empty():
            print(f"SOMETHING HIT THE QUQE")
            print(f"The queue has {len(list(message_queue.queue))}")
            print(f"The call to empty gives me {message_queue.empty()}")
            msg = message_queue.get()
            print(f"Message keys are: {msg.keys()}")
            # result_image_b64

            # Check if the message contains image data
            if "result_image_b64" in msg.keys():
                print(f"We got an image")
                try:
                    # Decode the base64 string to an image
                    print("Decoding image")
                    image_data = base64.b64decode(msg["result_image_b64"])
                    latest_image = Image.open(BytesIO(image_data))
                    latest_message = {"unique_id" : msg["unique_id"], "result_image_b64": "too long lol"}
                except Exception as e:
                    print(f"Error decoding image: {e}")
            else:
                # When wouldn't it have message data? Errors, progress and binary messages. 
                if "result_image_b64" in msg.keys():
                    latest_message = {"unique_id" : msg["unique_id"], "result_image_b64": "too long lol"}
                else:
                    latest_message = f"Latest message: {msg}"

        time.sleep(0.05)

# Function to fetch the latest message for Gradio interface
def fetch_latest_message():
    global latest_message
    return latest_message

# Function to fetch the latest image for Gradio interface
def fetch_latest_image():
    global latest_image
    return latest_image

# Function to handle the submission
def submit_photomaker_workflow(identity_image, pose_image, image_style_prompt, batch_size):
    unique_id = str(uuid.uuid4())
    
    try:
        with open(identity_image, "rb") as file:
            identity_b64 = base64.b64encode(file.read()).decode("utf-8")
        with open(pose_image, "rb") as file:
            pose_b64 = base64.b64encode(file.read()).decode("utf-8")
    except Exception as e:
        print(f"Error encoding images: {e}")
        return f"Error encoding images: {e}"

    # Call the run_photomaker_workflow function synchronously
    workflow_result = run_photomaker_workflow(
        unique_id=unique_id,
        identity_input=identity_b64,
        pose_input=pose_b64,
        image_style_positive_prompt=image_style_prompt,
        batch_size=batch_size
    )
    
    # Add the result to the queue
    message_queue.put(workflow_result)

    return "Request sent, unique_id: " + unique_id
# Gradio interface setup
with gr.Blocks() as demo:
    gr.Markdown("### LinkedIn Photomaker")
    with gr.Row():
        identity_input = gr.Image(label="Identity Image", type="filepath")
        pose_input = gr.Image(label="Pose Image", type="filepath")
    image_style_prompt = gr.Textbox(label="Image Style Positive Prompt", placeholder="Enter style prompt here")
    batch_size_slider = gr.Slider(label="Batch Size", minimum=1, maximum=5, step=1, value=1)

    submit_button = gr.Button("Generate LinkedIn Photo")
    submit_button.click(
        fn=submit_photomaker_workflow,
        inputs=[identity_input, pose_input, image_style_prompt, batch_size_slider],
        outputs=gr.Textbox(label="Status", placeholder="Status message will appear here")
    )

    gr.Markdown("### Generated Image")
    generated_image = gr.Image(label="Generated Image", interactive=False)

    # Set up live update for the output textbox with polling every 1 second
    demo.load(fetch_latest_message, inputs=None, outputs=gr.Textbox(label="Status", placeholder="Status message will appear here"), every=1)

    # Set up live update for the image with polling every 1 second
    demo.load(fetch_latest_image, inputs=None, outputs=generated_image, every=1)

# Start WebSocket client in a separate thread
Thread(target=start_websocket_client_photomaker, daemon=True).start()

# Start the message update thread
Thread(target=update_message, daemon=True).start()

# Launch the Gradio interface
demo.launch(server_port=9002, server_name="0.0.0.0")
