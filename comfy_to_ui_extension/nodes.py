from __future__ import annotations
from PIL import Image
import numpy as np
import base64
import torch
from io import BytesIO
from server import PromptServer, BinaryEventTypes


class LoadImageBase64:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"image": ("STRING", {"multiline": False})}}

    RETURN_TYPES = ("IMAGE", "MASK")
    CATEGORY = "UI_tools"
    FUNCTION = "load_image"

    def load_image(self, image):
        imgdata = base64.b64decode(image)
        img = Image.open(BytesIO(imgdata))

        if "A" in img.getbands():
            mask = np.array(img.getchannel("A")).astype(np.float32) / 255.0
            mask = 1.0 - torch.from_numpy(mask)
        else:
            mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")

        img = img.convert("RGB")
        img = np.array(img).astype(np.float32) / 255.0
        img = torch.from_numpy(img)[None,]

        return (img, mask)


class LoadMaskBase64:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"mask": ("STRING", {"multiline": False})}}

    RETURN_TYPES = ("MASK",)
    CATEGORY = "external_tooling"
    FUNCTION = "load_mask"

    def load_mask(self, mask):
        imgdata = base64.b64decode(mask)
        img = Image.open(BytesIO(imgdata))
        img = np.array(img).astype(np.float32) / 255.0
        img = torch.from_numpy(img)
        if img.dim() == 3:  # RGB(A) input, use red channel
            img = img[:, :, 0]
        return (img.unsqueeze(0),)

class AddUniqueIDforUIImage:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"unique_id": ("STRING", {"multiline": False})}}

    RETURN_TYPES = ("STRING",)
    FUNCTION = "add_unique_id"
    CATEGORY = "UI_tools"

    def add_unique_id(self, unique_id):
        return unique_id

class SendImageWebSocket:
    @classmethod
    def INPUT_TYPES(s):
        # Defines the input types required for this class, specifically expecting a list of images.
        return {"required": {"images": ("IMAGE",), "unique_id": ("STRING", {"multiline": False})}}

    RETURN_TYPES = ()  # No return types defined for this class.
    FUNCTION = "send_images"  # The function to be called when processing.
    OUTPUT_NODE = True  # Indicates that this class can output data.
    CATEGORY = "UI_tools"  # Categorizes this class for organizational purposes.

    def send_images(self, images, unique_id):
        results = []  # Initialize a list to store results for each image.
        
        # Iterate over each image tensor provided in the input.
        for tensor in images:
            # Convert the tensor to a numpy array and scale pixel values to [0, 255].
            array = 255.0 * tensor.cpu().numpy()
            # Create a PIL Image from the numpy array, ensuring pixel values are within valid range.

            # TODO: Convert this PIL image into a base64 image
            image = Image.fromarray(np.clip(array, 0, 255).astype(np.uint8))
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()


            # Get the instance of the PromptServer to send the image.
            server = PromptServer.instance

            # Create our data 
            event_type = "result_linkedin_message"
            data = {
                "unique_id": unique_id,
                "result_image_b64": img_str,
            }

            server.send_sync(event=event_type, data=data, sid=server.client_id)

            results.append(
                {"source": "websocket", "content-type": "image/png", "type": "output"}
            )

        # Return a dictionary containing the results of the sent images for UI display.
        return {"ui": {"images": results}}
