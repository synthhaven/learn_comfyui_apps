# Creating Your Very Own Linkedin Photo Generator
![Our UI](comfy_interface.png)
![Generated Image](american%20psycho.webp))


This repository showcases an example of how to create a comfyui app that can generate custom profile pictures for your social media. It also demonstrates how you can run comfy wokrflows behind a user interface


# Creating your runpod container:

Follow the instructions on the class document to setup runpod: 

# How to run:

If you're on runpod, run 

```
git clone https://github.com/synthhaven/learn_comfyui_apps.git
cd learn_comfyui_apps
source ./build_and_run_server.sh
```
=
Once this step is finished, we are ready to get started. 


Finally, we can run our comfyui server. Run the following command. You will then be able to access it in runpod.


```bash
comfy --workspace=/workspace/learn_comfyui_apps/ComfyUI/ launch -- --port 9000 --listen 0.0.0.0 --enable-cors-header '*'
```


# Workflows:

Refer to app/workflows/linkedin_photomaker_solution.json for a finished comfyUI app. 

In order to run the server, run the commands 

```bash
cd app
python run_photomaker.py
```

Then, go to Runpod and click on **Connect**. You will see your application on port 9002.



# How to turn the workflow I made in class into the server?

This repository already comes with the comfy_to_ui_extension. This extension is already copied when you run the `build_and_run_server.sh` 
and it gets loaded as a custom node inside of ComfyUI. This node lets you send data into your ComfyUI instance from an external application and get results back.

The only thing you need to do is the following. First examine app/photomaker_utils.py in line 50. You will see something that looks like this:

``` python

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

```

This corresponds to the inputs we want to feed from the outside to comfy. Click at the solution workflow, and see what nodes the numbers "31", "29", "30", etc map to. Do the same thing for your workflow.



# Using ComfyUI

Throughout the class, you've learned a lot about different close source model APIs. Those usually handle simple text to image requests.

However, if you want to work on building amazing image AI appplications, you will have to know how to use ComfyUI

Do not let the name fool you. Although comfy enables you to visually build AI image applications, comfy is far from a simple no-code tool.

Comfy contains code for the most advanced approaches available in image models and it gives you the power to even create you own code.

Through this class, we will learn how to do some of the things we learned about image models to get a grasp of ComfyUI. After that, we will create an application that enables us to generate professional quality shots that we can use on our social media.

