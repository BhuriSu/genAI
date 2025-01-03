import torch
from diffusers import StableDiffusionPipeline
import logging

class StyleTransfer:
    def __init__(self):
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Determine device and dtype
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.dtype = torch.float16 if self.device == "cuda" else torch.float32
        
        self.logger.info(f"Using device: {self.device}")
        self.logger.info(f"Using dtype: {self.dtype}")
        
        try:
            self.model = StableDiffusionPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                torch_dtype=self.dtype
            ).to(self.device)
            
            # Enable memory efficient attention if using CUDA
            if self.device == "cuda":
                self.model.enable_attention_slicing()
                
        except Exception as e:
            self.logger.error(f"Error initializing model: {str(e)}")
            raise

    def transfer_style(self, reference_img, style_img):
        try:
            # Implement style transfer using StableDiffusion
            result = self.model(
                image=reference_img,
                style_image=style_img,
                num_inference_steps=50
            ).images[0]
            return result
        except Exception as e:
            self.logger.error(f"Error in transfer_style: {str(e)}")
            return None

    def __del__(self):
        """Cleanup method to free GPU memory"""
        if hasattr(self, 'model'):
            try:
                del self.model
                if self.device == "cuda":
                    torch.cuda.empty_cache()
            except Exception as e:
                self.logger.error(f"Error in cleanup: {str(e)}")