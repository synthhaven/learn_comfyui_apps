# websocket_client.py

import websocket
import json
import os
import requests
import base64
from PIL import Image
import io
import uuid
from queue import Queue

# WebSocket server URL and REST API URL
WS_SERVER_URL = "ws://0.0.0.0:9000/ws"
REST_API_URL = "http://0.0.0.0:9000/history"
SAVE_DIR = "/workspace/learn_comfyui_apps/app/outputs/save_linkedin"
os.makedirs(SAVE_DIR, exist_ok=True)


DEFAULT_CLIENT_ID = "06a96135-59b2-4a29-b7c8-a83fc011ea63"

message_queue = Queue()

# Handlers
class LinkedinPhotomakerHandler:
    def __init__(self):
        self.handler_name = "LinkedinPhotomakerHandler"

    def on_message(self, ws, message):
        try:
            print(f"Handler {self.handler_name} received message")
            msg = json.loads(message)
            message_type = msg.get('type')
            print(f"Message type: {message_type}")

            if message_type == "result_linkedin_message":
                print("Image ready!")
                # Parse the data here
                data = msg["data"]
                # Add it to the queue so gradio can see it.

                # Save it to the folder so people can see what they're making
                print(f"We got a linkedin message with fields {msg.keys()}")
                print(f"Keys of data are { msg['data'].keys() }")
                render_id = msg["data"]["unique_id"]
                b64_image = msg["data"]["result_image_b64"]

                # dump it on the generation folder.
                path_for_this_job = f"{SAVE_DIR}/{render_id}"
                os.makedirs(path_for_this_job,exist_ok=True)
                
                #### COMPLETE THIS BETTER
                # ADD TO THE QUEUE
                print("Message succesfully added to the queue. ")
                message_queue.put(msg["data"])


                # Image id for this job_id
                image_id = uuid.uuid4()


                # Save the image
                image_path = os.path.join(path_for_this_job, f"{render_id}--{image_id}.png")
                return
            elif message_type == "job_complete":
                print("Job is complete!")
                return
            else:
                print(f"Received another type of message {message_type}")

        except Exception as e:
            print(f"Error processing message: {e}")

    def on_error(self, ws, error):
        """Handle errors in the WebSocket connection."""
        print(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        """Handle the closing of the WebSocket connection."""
        print(f"WebSocket closed with status: {close_status_code}, message: {close_msg}")

    def on_open(self, ws):
        """Handle the opening of the WebSocket connection."""
        print("WebSocket connection opened")


# Queue to store received images.
class ComfyWebsocketListener:
    def __init__(self, client_id, save_dir, handler):
        print("rebooted")
        self.image_queue = Queue()
        self.client_id = client_id
        self.save_dir = save_dir
        self.handler = handler

    def handle_bytes_data(self, binary_message):
        """Handles binary data received over WebSocket, expected to contain image data."""
        try:
            with io.BytesIO(binary_message) as bio:
                first_bytes = bio.read(8)
                print(f"First few bytes: {first_bytes.hex()}")
                bio.seek(8)
                image_data = bio.read()
                image = Image.open(io.BytesIO(image_data))
                print("Successfully decoded binary image")
                image_name = f"image_{uuid.uuid4()}.png"
                image_path = os.path.join(self.save_dir, image_name)
                image.save(image_path)
                print(f"Saved image from binary data {image_path}")
                # self.image_queue.put(image)  # Use put instead of add Let's not put this on the Q for now
                print("added image to queue")
                return image
        except Exception as e:
            print(f"Error processing binary message as image: {e}")
            return None

    def on_message(self, ws, message):
        """Delegate the message to the handler's on_message method."""
        if isinstance(message, bytes):
            print("Received binary message (possible image data).")
            self.handle_bytes_data(message)
        else:
            self.handler.on_message(ws, message)

    def on_error(self, ws, error):
        """Delegate the error to the handler's on_error method."""
        self.handler.on_error(ws, error)

    def on_close(self, ws, close_status_code, close_msg):
        """Delegate the close event to the handler's on_close method."""
        self.handler.on_close(ws, close_status_code, close_msg)

    def on_open(self, ws):
        """Delegate the open event to the handler's on_open method."""
        self.handler.on_open(ws)

    def run_websocket(self):
        """Start the WebSocket client."""
        ws = websocket.WebSocketApp(
            f"{WS_SERVER_URL}?clientId={self.client_id}",
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        ws.run_forever()


def start_websocket_client_photomaker():
    listener = ComfyWebsocketListener(DEFAULT_CLIENT_ID, SAVE_DIR,LinkedinPhotomakerHandler())
    listener.run_websocket()

if __name__ == "__main__":
    listener = ComfyWebsocketListener(DEFAULT_CLIENT_ID, SAVE_DIR)
    listener.run_websocket()
