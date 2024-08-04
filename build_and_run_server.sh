#!/bin/bash

# Entrypoint at /workspace. Ensure the script is executed from the repository root

# Make a venv at root
python -m venv project_environment

# Activate virtual environment
source project_environment/bin/activate

# Install requirements
pip install -r requirements.txt

# Clone ComfyUI
git clone https://github.com/comfyanonymous/ComfyUI.git

# Cd into the comfy repo
cd ComfyUI

# Install requirements.txt
pip install -r requirements.txt

# Cd into workspace/ComfyUI/custom_nodes
cd custom_nodes

# Git clone all the extensions
# ComfyUI-Manager
git clone https://github.com/ltdrdata/ComfyUI-Manager.git
# IPAdapter_plus
git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus.git
# Inspire-Pack
git clone https://github.com/ltdrdata/ComfyUI-Inspire-Pack.git
# Impact-Pack
git clone https://github.com/ltdrdata/ComfyUI-Impact-Pack.git
# Instant ID
git clone https://github.com/cubiq/ComfyUI_InstantID.git

# Cd back to ComfyUI directory
cd ..

# Install dependencies for all extensions
for dir in ./custom_nodes/*; do
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

# Now, call the script to install all models (this step should be implemented)
# echo "Downloading all necessary models..."

# Run the ComfyUI server
echo "Starting ComfyUI server..."
python main.py --port 9000 --listen 0.0.0.0 --enable-cors-header '*'
