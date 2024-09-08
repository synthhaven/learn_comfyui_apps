from . import nodes

NODE_CLASS_MAPPINGS = {
    "LoadImageFromUI": nodes.LoadImageBase64,
    "LoadMaskFromUI": nodes.LoadMaskBase64,
    "SendImageToUI": nodes.SendImageWebSocket,
    "AddUniqueIDforUIImage": nodes.AddUniqueIDforUIImage,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageFromUI": "Load Image from UI (Base 64)",
    "LoadMaskFromUI": "Load Mask from UI (Base64)",
    "SendImageToUI": "Send Image to UI (WebSocket)",
    "AddUniqueIDforUIImage": "Add UniqueID to track Generation)",


}
