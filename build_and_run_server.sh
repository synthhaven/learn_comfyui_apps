#!/bin/bash

# Entrypoint at /workspace. Ensure the script is executed from the repository root
# Install requirements
pip install -r requirements.txt

# Clone ComfyUI
# git clone https://github.com/comfyanonymous/ComfyUI.git
comfycli --workspace=/workspace/learn_comfyui_apps/ComfyUI install

# Cd into the comfy repo
cd /workspace/learn_comfyui_apps/ComfyUI

# Install requirements.txt
pip install -r requirements.txt

# Download models from civitai
civitconfig default -k 821d61ef05206470d1aed98938f562fa
civitdl https://civitai.com/models/299933/halcyon-sdxl-photorealism?modelVersionId=610541 /workspace/learn_comfyui_apps/ComfyUI/models/checkpoints/


# Cd into workspace/ComfyUI/custom_nodes
cd /workspace/learn_comfyui_apps/ComfyUI/custom_nodes

# Git clone all the extensions
# IPAdapter_plus
git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus.git
# Inspire-Pack
git clone https://github.com/ltdrdata/ComfyUI-Inspire-Pack.git
# Impact-Pack
git clone https://github.com/ltdrdata/ComfyUI-Impact-Pack.git
# Instant ID
git clone https://github.com/cubiq/ComfyUI_InstantID.git



# Cd back to ComfyUI directory
cd /workspace/learn_comfyui_apps/ComfyUI/
# Copy the custom extension
cp -R /workspace/learn_comfyui_apps/comfy_to_ui_extension  /workspace/learn_comfyui_apps/ComfyUI/custom_nodes

# Install dependencies for all extensions
for dir in /workspace/learn_comfyui_apps/ComfyUI/custom_nodes/*; do
  if [ -d "$dir" ]; then
    # Check if requirements.txt exists in the subdirectory
    if [ -f "$dir/requirements.txt" ]; then
      echo "Installing dependencies from $dir/requirements.txt"
      pip install -r "$dir/requirements.txt"
    else
      echo "No requirements.txt found in $dir"
    fi
  fi
done

# echo "Downloading all necessary models..."

# Run the ComfyUI server
echo "Starting ComfyUI server..."
comfy --workspace=/workspace/learn_comfyui_apps/ComfyUI/ launch -- --port 9000 --listen 0.0.0.0 --enable-cors-header '*'
