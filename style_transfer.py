import torch
from diffusers import StableDiffusionPipeline

class StyleTransfer:
    def __init__(self):
        self.model = StableDiffusionPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            torch_dtype=torch.float16
        ).to("cuda")

    def transfer_style(self, reference_img, style_img):
        # Implement style transfer using StableDiffusion
        result = self.model(
            image=reference_img,
            style_image=style_img,
            num_inference_steps=50
        ).images[0]
        return result
