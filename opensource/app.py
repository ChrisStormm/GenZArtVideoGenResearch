import gradio as gr
import torch
from diffusers import StableVideoDiffusionPipeline
from diffusers.utils import export_to_video
from PIL import Image
import tempfile

# Load pipeline (slow the first time)
pipe = StableVideoDiffusionPipeline.from_pretrained(
    "stabilityai/stable-video-diffusion-img2vid",
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    variant="fp16" if torch.cuda.is_available() else None
)
pipe.to("cuda" if torch.cuda.is_available() else "cpu")

# Function to generate video from image
def generate_video(image: Image.Image):
    image = image.resize((1024, 576))
    generator = torch.manual_seed(42)
    result = pipe(image, decode_chunk_size=8, generator=generator).frames[0]

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
        export_to_video(result, temp_video.name, fps=7)
        return temp_video.name

# Gradio UI
demo = gr.Interface(
    fn=generate_video,
    inputs=gr.Image(type="pil"),
    outputs=gr.Video(),
    title="Stable Video Diffusion",
    description="Upload an image and generate a 2-4 second video using Stable Video Diffusion."
)

demo.launch()

