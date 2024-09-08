from pydantic import BaseModel
import json
import requests
import uuid
import requests
import asyncio
import websocket
from PIL import Image
import io
import os
from pydantic import BaseModel

# We load our workflow here
LINKEDIN_PHOTOMAKER_PATH = "/workspace/learn_comfyui_apps/app/workflows/linkedin_photomaker_solution.json"
# Server configuration
SERVER_ADDRESS = "0.0.0.0:9000"
SERVER_URL = f"http://{SERVER_ADDRESS}"
RUN_WORKFLOW_URL = f"{SERVER_URL}/prompt"
WS_SERVER_URL = f"ws://{SERVER_ADDRESS}/ws"

# Unique client ID for tracking the session
DEFAULT_CLIENT_ID = "06a96135-59b2-4a29-b7c8-a83fc011ea63"
with open(LINKEDIN_PHOTOMAKER_PATH, "r") as f:
    PHOTOMAKER_WORKFLOW = json.load(f)

# Function to run the workflow synchronously
def run_workflow(workflow={}):
    """Run the workflow and return the response."""
    data = {"prompt": workflow, "client_id": DEFAULT_CLIENT_ID}
    headers = {'Content-Type': 'application/json'}

    try:
        print(f"Sending request to {RUN_WORKFLOW_URL}")
        # print(f"Request data: {json.dumps(data, indent=2)}")
        response = requests.post(RUN_WORKFLOW_URL, json=data, headers=headers)
        print(f"Received response with status code: {response.status_code}")
        print(f"Response content: {response.text}")
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        print(f"Error occurred while sending the request: {e}")
        return {"error": str(e)}

# <STUDENT_SECTION>
# Map the inputs to your workflow
# Find the nodes corresponding to the unique_id
# and the inputs, outputs and batch size for your workflow
PHOTOMAKER_SPEC = {
    # positive prompt will map to
    "unique_id": "31",
    # TWO IMAGES WE USED
    "identity_input" : "29",
    "pose_input": "30", 
    ## THE PROMPT WE USED 
    "image_style_positive_prompt": "6",
    ## THE BATCH SIZE WE WERE USING.
    "batch_size_node" : "5",
}


def format_input_to_photomaker(workflow, unique_id, identity_input, pose_input, image_style_positive_prompt, batch_size=1):
    """
    Formats the workflow dictionary to include the specified inputs.

    Args:
        workflow (dict): The workflow dictionary to be updated.
        unique_id (str): The unique identifier for the specific workflow instance.
        identity_input (str): The identity input value.
        pose_input (str): The pose input value.
        image_style_positive_prompt (str): The positive prompt for the image style.
        batch_size (int, optional): The batch size. Defaults to 1.

    Returns:
        dict: The updated workflow dictionary.
    """
    # Update the workflow with the provided inputs
    # We then modify our nodes with the inputs
    workflow[PHOTOMAKER_SPEC["identity_input"]]["inputs"]["image"] = identity_input
    workflow[PHOTOMAKER_SPEC["pose_input"]]["inputs"]["image"] = pose_input
    workflow[PHOTOMAKER_SPEC["image_style_positive_prompt"]]["inputs"]["text"] = image_style_positive_prompt

    # Set our batch size
    workflow[PHOTOMAKER_SPEC["batch_size_node"]]["inputs"]["batch_size"] = batch_size

    # This step is very important. The unique_id lets us track generations
    workflow[PHOTOMAKER_SPEC["unique_id"]]["inputs"]["unique_id"] = unique_id


    return workflow


def run_photomaker_workflow(unique_id, identity_input, pose_input, image_style_positive_prompt, batch_size=1, client_id=DEFAULT_CLIENT_ID):
    """
    Run the PhotoMaker workflow with the provided inputs.

    This function formats the PhotoMaker workflow with the specified inputs and executes it asynchronously.
    The unique identifier (unique_id) allows for tracking of specific workflow instances. The function
    updates the workflow dictionary with the necessary inputs, including identity, pose, and style prompts,
    and sends the formatted workflow to the workflow execution URL.

    Args:
        unique_id (str): A unique identifier for the specific workflow instance.
        identity_input (str): The identity input value, typically a description or path to an image.
        pose_input (str): The pose input value, describing the desired pose or path to a reference image.
        image_style_positive_prompt (str): The positive prompt for the image style, describing the desired style.
        batch_size (int, optional): The batch size for processing. Defaults to 1.
        client_id (str, optional): The client identifier for tracking and authentication. Defaults to DEFAULT_CLIENT_ID.

    Returns:
        dict: A dictionary containing the workflow result, including the 'prompt_id' and any encountered errors.
    """
    # Format the workflow with the provided inputs
    updated_workflow = format_input_to_photomaker(
        PHOTOMAKER_WORKFLOW, 
        unique_id, 
        identity_input, 
        pose_input, 
        image_style_positive_prompt, 
        batch_size
    )
    
    # Run the workflow
    workflow_result = run_workflow(updated_workflow)
    
    # Handle the workflow result, typically handled by a webhook
    return workflow_result


if __name__ == '__main__':
    pass
