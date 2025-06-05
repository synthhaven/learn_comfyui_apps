import gradio as gr
import json
import uuid
import base64
import time
from datetime import datetime
from PIL import Image
from io import BytesIO
from websocket_client import start_websocket_client_photomaker, message_queue
from photomaker_utils import run_photomaker_workflow
from config import get_client_id

# Simple function to handle image generation
def generate_image(identity_image, pose_image, prompt):
    """Simple function: upload images + prompt = get image back"""
    
    # Basic validation
    if not identity_image or not pose_image:
        return None, "❌ Please upload both identity and pose images"
    
    if not prompt.strip():
        return None, "❌ Please enter a prompt"
    
    try:
        # Generate unique ID for this request
        unique_id = str(uuid.uuid4())
        
        # Encode images to base64
        with open(identity_image, "rb") as file:
            identity_b64 = base64.b64encode(file.read()).decode("utf-8")
        with open(pose_image, "rb") as file:
            pose_b64 = base64.b64encode(file.read()).decode("utf-8")
        
        # Send to ComfyUI
        workflow_result = run_photomaker_workflow(
            unique_id=unique_id,
            identity_input=identity_b64,
            pose_input=pose_b64,
            image_style_positive_prompt=prompt,
            batch_size=1
        )
        
        # Check for workflow errors
        if "error" in workflow_result:
            return None, f"❌ Error: {workflow_result['error']}"
        
        # Wait for result from WebSocket (no timeout - wait indefinitely)
        status_msg = f"🔄 Generating your LinkedIn photo... (ID: {unique_id[:8]})"
        
        # Check queue for results indefinitely
        attempt = 0
        while True:
            if not message_queue.empty():
                try:
                    msg = message_queue.get_nowait()
                    if msg.get("unique_id") == unique_id and "result_image_b64" in msg:
                        # We got our image!
                        image_data = base64.b64decode(msg["result_image_b64"])
                        result_image = Image.open(BytesIO(image_data))
                        return result_image, "✅ Your LinkedIn photo is ready!"
                except Exception as e:
                    print(f"Error processing result: {e}")
                    continue
            
            time.sleep(0.5)
            attempt += 1
            
            # Update status every 10 attempts (5 seconds) for user feedback
            if attempt % 10 == 0:
                status_msg = f"🔄 Still generating... ({attempt//2} seconds)"
        
    except Exception as e:
        print(f"Error in generate_image: {e}")
        return None, f"❌ Error: {str(e)}"

# Super simple Gradio interface
with gr.Blocks(title="LinkedIn PhotoMaker") as demo:
    gr.Markdown("# LinkedIn PhotoMaker")
    gr.Markdown("Upload your photos, enter a prompt, and get a professional LinkedIn photo!")
    
    with gr.Row():
        identity_input = gr.Image(label="Your Identity Photo", type="filepath")
        pose_input = gr.Image(label="Pose Reference Photo", type="filepath")
    
    prompt_input = gr.Textbox(
        label="Style Prompt", 
        placeholder="Describe the style you want...",
        value="A professional portrait of a businessman wearing a leather jacket in napa valley, shoulders up shot, 27 years old, depth of field, dominant, mood focused, lighting soft, natural light, perspective close-up, warm color pallete, 100mm, bokeh, professional photoshoot, posted on linkedin",
        lines=3
    )
    
    generate_button = gr.Button("🎨 Generate LinkedIn Photo", variant="primary", size="lg")
    
    with gr.Row():
        result_image = gr.Image(label="Your LinkedIn Photo")
        status_text = gr.Textbox(label="Status", value="Ready to generate!", interactive=False)
    
    # Simple click handler
    generate_button.click(
        fn=generate_image,
        inputs=[identity_input, pose_input, prompt_input],
        outputs=[result_image, status_text]
    )

if __name__ == "__main__":
    print("🚀 Starting Simple LinkedIn PhotoMaker")
    print("=" * 50)
    
    # Start WebSocket client
    from threading import Thread
    ws_thread = Thread(target=start_websocket_client_photomaker, daemon=True)
    ws_thread.start()
    print("✅ WebSocket client started")
    
    # Launch simple interface
    print("🌐 Launching on http://127.0.0.1:9004")
    print("=" * 50)
    
    demo.launch(
        server_port=9002, 
        server_name="127.0.0.1",
        show_error=True
    )
