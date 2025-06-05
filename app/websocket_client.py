# websocket_client.py

import websocket
import json
import os
import requests
import base64
from PIL import Image
import io
import uuid
import time
import threading
from queue import Queue, Empty
from config import (
    get_comfyui_ws_url,
    get_save_directory,
    get_client_id,
    config
)

# WebSocket server URL and REST API URL from configuration
WS_SERVER_URL = get_comfyui_ws_url()
REST_API_URL = config.get("comfyui.history_url")
SAVE_DIR = get_save_directory()

# Ensure save directory exists
SAVE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_CLIENT_ID = get_client_id()

# Configuration for reconnection and queue management
MAX_RECONNECT_ATTEMPTS = config.get("app.reconnect_attempts", 5)
RECONNECT_DELAY = config.get("app.reconnect_delay", 2)
MAX_QUEUE_SIZE = config.get("app.max_queue_size", 100)

# Thread-safe message queue with size limit
message_queue = Queue(maxsize=MAX_QUEUE_SIZE)

class ConnectionState:
    """Thread-safe connection state management."""
    def __init__(self):
        self._lock = threading.Lock()
        self._connected = False
        self._reconnect_attempts = 0
        
    def set_connected(self, state: bool):
        with self._lock:
            self._connected = state
            if state:
                self._reconnect_attempts = 0
    
    def is_connected(self) -> bool:
        with self._lock:
            return self._connected
    
    def increment_reconnect_attempts(self) -> int:
        with self._lock:
            self._reconnect_attempts += 1
            return self._reconnect_attempts
    
    def get_reconnect_attempts(self) -> int:
        with self._lock:
            return self._reconnect_attempts

# Global connection state
connection_state = ConnectionState()

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
                
                # Add to queue with proper error handling
                try:
                    # Try to put message in queue, remove oldest if full
                    if message_queue.full():
                        try:
                            message_queue.get_nowait()  # Remove oldest message
                            print("Queue full, removed oldest message")
                        except Empty:
                            pass
                    
                    message_queue.put_nowait(data)
                    print("Message successfully added to the queue.")
                except Exception as queue_error:
                    print(f"Error adding message to queue: {queue_error}")

                # Save it to the folder so people can see what they're making
                print(f"We got a linkedin message with fields {msg.keys()}")
                print(f"Keys of data are { msg['data'].keys() }")
                render_id = msg["data"]["unique_id"]
                b64_image = msg["data"]["result_image_b64"]

                # dump it on the generation folder.
                try:
                    path_for_this_job = SAVE_DIR / render_id
                    path_for_this_job.mkdir(parents=True, exist_ok=True)
                    
                    # Image id for this job_id
                    image_id = uuid.uuid4()
                    
                    # Save the image
                    image_path = path_for_this_job / f"{render_id}--{image_id}.png"
                    # Note: Image saving could be implemented here if needed
                    
                except Exception as save_error:
                    print(f"Error saving image: {save_error}")
                
                return
            elif message_type == "job_complete":
                print("Job is complete!")
                return
            else:
                print(f"Received another type of message {message_type}")

        except json.JSONDecodeError as json_error:
            print(f"Error parsing JSON message: {json_error}")
        except Exception as e:
            print(f"Error processing message: {e}")

    def on_error(self, ws, error):
        """Handle errors in the WebSocket connection."""
        print(f"WebSocket error: {error}")
        connection_state.set_connected(False)

    def on_close(self, ws, close_status_code, close_msg):
        """Handle the closing of the WebSocket connection."""
        print(f"WebSocket closed with status: {close_status_code}, message: {close_msg}")
        connection_state.set_connected(False)

    def on_open(self, ws):
        """Handle the opening of the WebSocket connection."""
        print("WebSocket connection opened")
        connection_state.set_connected(True)


# Queue to store received images.
class ComfyWebsocketListener:
    def __init__(self, client_id, save_dir, handler):
        print(f"Initializing WebSocket listener for client: {client_id}")
        self.image_queue = Queue()
        self.client_id = client_id
        self.save_dir = save_dir
        self.handler = handler
        self.ws = None
        self.should_reconnect = True
        self.reconnect_thread = None

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
                image_path = self.save_dir / image_name
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
        # Schedule reconnection if needed
        if self.should_reconnect:
            self._schedule_reconnect()

    def on_close(self, ws, close_status_code, close_msg):
        """Delegate the close event to the handler's on_close method."""
        self.handler.on_close(ws, close_status_code, close_msg)
        # Schedule reconnection if needed
        if self.should_reconnect:
            self._schedule_reconnect()

    def on_open(self, ws):
        """Delegate the open event to the handler's on_open method."""
        self.handler.on_open(ws)

    def _schedule_reconnect(self):
        """Schedule a reconnection attempt."""
        attempts = connection_state.get_reconnect_attempts()
        if attempts >= MAX_RECONNECT_ATTEMPTS:
            print(f"Max reconnection attempts ({MAX_RECONNECT_ATTEMPTS}) reached. Stopping reconnection.")
            return
        
        # Only start one reconnection thread at a time
        if self.reconnect_thread is None or not self.reconnect_thread.is_alive():
            self.reconnect_thread = threading.Thread(target=self._reconnect_after_delay)
            self.reconnect_thread.daemon = True
            self.reconnect_thread.start()

    def _reconnect_after_delay(self):
        """Reconnect after a delay."""
        attempt = connection_state.increment_reconnect_attempts()
        delay = RECONNECT_DELAY * attempt  # Exponential backoff
        
        print(f"Scheduling reconnection attempt {attempt} in {delay} seconds...")
        time.sleep(delay)
        
        if not connection_state.is_connected() and self.should_reconnect:
            print(f"Attempting to reconnect (attempt {attempt})...")
            self._create_websocket()

    def _create_websocket(self):
        """Create and start the WebSocket connection."""
        try:
            self.ws = websocket.WebSocketApp(
                f"{WS_SERVER_URL}?clientId={self.client_id}",
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            # Run in a non-blocking way to allow for reconnection
            self.ws.run_forever()
        except Exception as e:
            print(f"Error creating WebSocket connection: {e}")
            connection_state.set_connected(False)

    def run_websocket(self):
        """Start the WebSocket client with reconnection capability."""
        print(f"Starting WebSocket connection to: {WS_SERVER_URL}")
        self.should_reconnect = True
        self._create_websocket()

    def stop_websocket(self):
        """Stop the WebSocket client and disable reconnection."""
        print("Stopping WebSocket connection...")
        self.should_reconnect = False
        connection_state.set_connected(False)
        if self.ws:
            self.ws.close()

def get_message_queue_status():
    """Get current message queue status for debugging."""
    return {
        "size": message_queue.qsize(),
        "max_size": MAX_QUEUE_SIZE,
        "connected": connection_state.is_connected(),
        "reconnect_attempts": connection_state.get_reconnect_attempts()
    }

def start_websocket_client_photomaker():
    """Start the WebSocket client for the photomaker application."""
    listener = ComfyWebsocketListener(DEFAULT_CLIENT_ID, SAVE_DIR, LinkedinPhotomakerHandler())
    listener.run_websocket()

if __name__ == "__main__":
    listener = ComfyWebsocketListener(DEFAULT_CLIENT_ID, SAVE_DIR, LinkedinPhotomakerHandler())
    listener.run_websocket()
