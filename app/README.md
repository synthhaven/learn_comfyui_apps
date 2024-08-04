# This folder contains your app!


Those are the two main interesting parts.

* **linkedin_photomaker.py**: This file contains the user interface. It sends requests to ComfyUI and updates the output based on the requests it receives back
* **photomaker_utils.py**: This file contains the code necessary to send in a request from the user interface to ComfyUI. You will in here, implement the logic to use the Exported API json from your workflow and call the ComfyAPI.



It also contains a server to interface. 


* **websocket_client.py**: A simple server to receive messages from ComfyUI. You won't have to touch this file
