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
REST_API_URL = "http://0.0.0.0:9000/history"  # Replace with actual view endpoint if different
SAVE_DIR = "/workspace/SynthhavenAPI/repositories/ComfyUI/custom_nodes/ComfyUI_IK_demo/ui/test_linkedin/"
os.makedirs(SAVE_DIR, exist_ok=True)


DEFAULT_CLIENT_ID = "06a96135-59b2-4a29-b7c8-a83fc011ea63"

message_queue = Queue()


# Import function here to load the graph and do all prompt shenanigans
# Load LCM workflow

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

            if message_type == "create_linkedin_photo":
                print(f"Sending request to create image")
                # Parse the data here
                # Send it to comfyAPI with the proper handler
                return
            elif message_type == "result_linkedin_message":
                print("Image ready!")
                # Parse the data here
                data = msg["data"]
                # Add it to the queue so gradio can see it.

                # Save it to the folder so people can see what they're making
               #server_response_data = {"unique_id": unique_id,"result_image_b64":img_str }
                # render_id = msg
                # os.makedirs(f"/workspace/SynthhavenAPI/repositories/ComfyUI/custom_nodes/ComfyUI_IK_demo/ui/test_json_messages/{}",exists=ok)
                print(f"We got a linkedin message with fields {msg.keys()}")
                print(f"Keys of data are { msg['data'].keys() }")
                render_id = msg["data"]["unique_id"]
                b64_image = msg["data"]["result_image_b64"]

                # dump it on the generation folder.
                path_for_this_job = f"/workspace/SynthhavenAPI/repositories/ComfyUI/custom_nodes/ComfyUI_IK_demo/ui/test_json_messages_linkedin/{render_id}"
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
                # print(msg) # This may be printing the giant strings.
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



class LCMHandler:
    def __init__(self):
        self.handler_name = "LCMHandler"

    def on_message(self, ws, message):
        try:
            print(f"Handler {self.handler_name} received message")
            msg = json.loads(message)
            message_type = msg.get('type')
            print(f"Message type: {message_type}")
            print(f"Received message!")
            print("****************LOGGING ALL********************")
            # print(f"Raw Message: {message}")
            print("***********************************************")
            if isinstance(message, bytes):
                print("Received binary message (possible image data).")
                self.handle_bytes_data(message)  # Use self.handle_bytes_data
                return
            msg = json.loads(message)

            message_type = msg.get("type")
            if message_type == "result_linkedin_message":
                #server_response_data = {"unique_id": unique_id,"result_image_b64":img_str }
                # render_id = msg
                # os.makedirs(f"/workspace/SynthhavenAPI/repositories/ComfyUI/custom_nodes/ComfyUI_IK_demo/ui/test_json_messages/{}",exists=ok)
                print(f"We got a linkedin message with fields {msg.keys()}")
                print(f"Keys of data are { msg['data'].keys() }")
                render_id = msg["data"]["unique_id"]
                b64_image = msg["data"]["result_image_b64"]

                # dump it on the generation folder.
                path_for_this_job = f"{SAVE_DIR}/{render_id}"
                os.makedirs(path_for_this_job,exist_ok=True)
                
                #### COMPLETE THIS BETTER
                # ADD TO THE QUEUE
                message_queue.put(msg["data"])


                # Image id for this job_id
                image_id = uuid.uuid4()


                # Save the image
                image_path = os.path.join(path_for_this_job, f"{render_id}--{image_id}.png")
                # Decode the base64 image data and convert it to a PIL image
                try:
                    image_data = base64.b64decode(b64_image)
                    image = Image.open(io.BytesIO(image_data))

                    # Save the image
                    image_path = os.path.join(path_for_this_job, f"{render_id}--{image_id}.png")
                    image.save(image_path, format="PNG")
                    print(f"Image saved at {image_path}")



                except Exception as e:
                    print(f"Error decoding and saving the image: {e}")


                return

            if message_type == "result_linkedin_message_complete":
                print(f"Message arrived for job completion. Updating status")
                render_id = msg["data"]["unique_id"]

                path_for_this_job = f"/workspace/SynthhavenAPI/repositories/ComfyUI/custom_nodes/ComfyUI_IK_demo/ui/test_json_messages/{render_id}"
                os.makedirs(path_for_this_job,exist_ok=True)

                with open(os.path.join(path_for_this_job, "status.json"),"w") as status_file:
                    json.dump(msg["data"], status_file)

                print(f"Successful job status saved in {path_for_this_job}")
                message_queue.put(msg["data"])
                return



            if message_type == "execution_success":
                prompt_id = msg["data"]["prompt_id"]
                print(f"Execution completed successfully for prompt_id: {prompt_id}")
            elif message_type == "status":
                status_info = msg.get("data", {}).get("status", {})
                exec_info = status_info.get('exec_info', {})
                queue_remaining = exec_info.get("queue_remaining", 'N/A')
                print(f"Status Update: Queue Remaining: {queue_remaining}")
            elif message_type == "execution_start":
                prompt_id = msg["data"]["prompt_id"]
                timestamp = msg["data"]["timestamp"]
                print(f"Execution started for prompt_id: {prompt_id} at timestamp: {timestamp}")
            elif message_type == "execution_cached":
                prompt_id = msg["data"]["prompt_id"]
                nodes = msg["data"]["nodes"]
                print(f"Execution cached for prompt_id: {prompt_id} with nodes: {nodes}")
            elif message_type == "executing":
                current_node = msg["data"]["node"]
                prompt_id = msg["data"]["prompt_id"]
                print(f"Executing node: {current_node} for prompt_id: {prompt_id}")
            elif message_type == "executed":
                print("Execution completed with the following images:")
                images = msg["data"]["output"].get("images", [])
                for idx, img_info in enumerate(images):
                    print(f"Image {idx}: {img_info}")
            else:
                print(f"Received unhandled message type: {message_type}")
        except json.JSONDecodeError:
            print("Received non-JSON message:", message)
        except Exception as e:
            print(f"Error processing message: {e}")
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

# # Queue to store received images.
# class ComfyWebsocketListener:
#     def __init__(self, client_id,save_dir):
#         print("rebooted")
#         self.image_queue = Queue()
#         self.client_id = client_id
#         self.save_dir = save_dir

#     def handle_bytes_data(self, binary_message):
#         """Handles binary data received over WebSocket, expected to contain image data."""
#         try:
#             with io.BytesIO(binary_message) as bio:
#                 first_bytes = bio.read(8)
#                 print(f"First few bytes: {first_bytes.hex()}")
#                 bio.seek(8)
#                 image_data = bio.read()
#                 image = Image.open(io.BytesIO(image_data))
#                 print("Successfully decoded binary image")
#                 image_name = f"image_{uuid.uuid4()}.png"
#                 image_path = os.path.join(self.save_dir, image_name)
#                 image.save(image_path)
#                 print(f"Saved image from binary data {image_path}")
#                 self.image_queue.put(image)  # Use put instead of add
#                 print("added image to queue")
#                 return image
#         except Exception as e:
#             print(f"Error processing binary message as image: {e}")
#             return None

#     def on_message(self, ws, message):
#         """Handle incoming messages from the WebSocket."""
#         try:

#             print(f"Received message!")
#             print("****************LOGGING ALL********************")
#             # print(f"Raw Message: {message}")
#             print("***********************************************")
#             if isinstance(message, bytes):
#                 print("Received binary message (possible image data).")
#                 self.handle_bytes_data(message)  # Use self.handle_bytes_data
#                 return
#             msg = json.loads(message)

#             message_type = msg.get("type")
#             if message_type == "result_linkedin_message":
#                 #server_response_data = {"unique_id": unique_id,"result_image_b64":img_str }
#                 # render_id = msg
#                 # os.makedirs(f"/workspace/SynthhavenAPI/repositories/ComfyUI/custom_nodes/ComfyUI_IK_demo/ui/test_json_messages/{}",exists=ok)
#                 print(f"We got a linkedin message with fields {msg.keys()}")
#                 print(f"Keys of data are { msg['data'].keys() }")
#                 render_id = msg["data"]["unique_id"]
#                 b64_image = msg["data"]["result_image_b64"]

#                 # dump it on the generation folder.
#                 path_for_this_job = f"/workspace/SynthhavenAPI/repositories/ComfyUI/custom_nodes/ComfyUI_IK_demo/ui/test_json_messages/{render_id}"
#                 os.makedirs(path_for_this_job,exist_ok=True)
                
#                 #### COMPLETE THIS BETTER
#                 # ADD TO THE QUEUE
#                 message_queue.put(msg["data"])



#                 # Image id for this job_id
#                 image_id = uuid.uuid4()


#                 # Save the image
#                 image_path = os.path.join(path_for_this_job, f"{render_id}--{image_id}.png")
#                 # Decode the base64 image data and convert it to a PIL image
#                 try:
#                     image_data = base64.b64decode(b64_image)
#                     image = Image.open(io.BytesIO(image_data))

#                     # Save the image
#                     image_path = os.path.join(path_for_this_job, f"{render_id}--{image_id}.png")
#                     image.save(image_path, format="PNG")
#                     print(f"Image saved at {image_path}")



#                 except Exception as e:
#                     print(f"Error decoding and saving the image: {e}")


#                 return

#             if message_type == "result_linkedin_message_complete":
#                 print(f"Message arrived for job completion. Updating status")
#                 render_id = msg["data"]["unique_id"]

#                 path_for_this_job = f"/workspace/SynthhavenAPI/repositories/ComfyUI/custom_nodes/ComfyUI_IK_demo/ui/test_json_messages/{render_id}"
#                 os.makedirs(path_for_this_job,exist_ok=True)

#                 with open(os.path.join(path_for_this_job, "status.json"),"w") as status_file:
#                     json.dump(msg["data"], status_file)

#                 print(f"Successful job status saved in {path_for_this_job}")
#                 message_queue.put(msg["data"])
#                 return



#             if message_type == "execution_success":
#                 prompt_id = msg["data"]["prompt_id"]
#                 print(f"Execution completed successfully for prompt_id: {prompt_id}")
#             elif message_type == "status":
#                 status_info = msg.get("data", {}).get("status", {})
#                 exec_info = status_info.get('exec_info', {})
#                 queue_remaining = exec_info.get("queue_remaining", 'N/A')
#                 print(f"Status Update: Queue Remaining: {queue_remaining}")
#             elif message_type == "execution_start":
#                 prompt_id = msg["data"]["prompt_id"]
#                 timestamp = msg["data"]["timestamp"]
#                 print(f"Execution started for prompt_id: {prompt_id} at timestamp: {timestamp}")
#             elif message_type == "execution_cached":
#                 prompt_id = msg["data"]["prompt_id"]
#                 nodes = msg["data"]["nodes"]
#                 print(f"Execution cached for prompt_id: {prompt_id} with nodes: {nodes}")
#             elif message_type == "executing":
#                 current_node = msg["data"]["node"]
#                 prompt_id = msg["data"]["prompt_id"]
#                 print(f"Executing node: {current_node} for prompt_id: {prompt_id}")
#             elif message_type == "executed":
#                 print("Execution completed with the following images:")
#                 images = msg["data"]["output"].get("images", [])
#                 for idx, img_info in enumerate(images):
#                     print(f"Image {idx}: {img_info}")
#             else:
#                 print(f"Received unhandled message type: {message_type}")
#         except json.JSONDecodeError:
#             print("Received non-JSON message:", message)
#         except Exception as e:
#             print(f"Error processing message: {e}")

#     def on_error(self, ws, error):
#         """Handle errors in the WebSocket connection."""
#         print(f"WebSocket error: {error}")

#     def on_close(self, ws, close_status_code, close_msg):
#         """Handle the closing of the WebSocket connection."""
#         print(f"WebSocket closed with status: {close_status_code}, message: {close_msg}")

#     def on_open(self, ws):
#         """Handle the opening of the WebSocket connection."""
#         print("WebSocket connection opened")

#     def run_websocket(self):
#         """Start the WebSocket client."""
#         ws = websocket.WebSocketApp(
#             f"{WS_SERVER_URL}?clientId={self.client_id}",
#             on_open=self.on_open,
#             on_message=self.on_message,
#             on_error=self.on_error,
#             on_close=self.on_close
#         )
#         ws.run_forever()



def start_websocket_client():
    listener = ComfyWebsocketListener(DEFAULT_CLIENT_ID, SAVE_DIR,LCMHandler())
    listener.run_websocket()


def start_websocket_client_photomaker():
    listener = ComfyWebsocketListener(DEFAULT_CLIENT_ID, SAVE_DIR,LinkedinPhotomakerHandler())
    listener.run_websocket()

if __name__ == "__main__":
    listener = ComfyWebsocketListener(DEFAULT_CLIENT_ID, SAVE_DIR)
    listener.run_websocket()
