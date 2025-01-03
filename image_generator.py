import torch
from diffusers import StableDiffusionPipeline
import logging

class ImageGenerator:
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
                "stabilityai/stable-diffusion-xl-base-1.0",
                torch_dtype=self.dtype,
                # Add safety checker to prevent NSFW content
                safety_checker=None,
                # Use local cache to prevent repeated downloads
                local_files_only=False
            )
            self.model = self.model.to(self.device)
            
            # Optional: Enable memory efficient attention if using CUDA
            if self.device == "cuda":
                self.model.enable_attention_slicing()
                
        except Exception as e:
            self.logger.error(f"Error initializing model: {str(e)}")
            raise
        
    def generate_3d_view(self, image):
        """Generate 3D 360 view from uploaded image"""
        try:
            # Your implementation here
            # For now, just returning the input image
            self.logger.info("Generate 3D view called")
            return image
        except Exception as e:
            self.logger.error(f"Error in generate_3d_view: {str(e)}")
            return None
        
    def modify_element(self, image, element_type, style):
        """Modify specific elements in the 3D view"""
        try:
            # Your implementation here
            self.logger.info(f"Modify element called with type: {element_type}")
            return image
        except Exception as e:
            self.logger.error(f"Error in modify_element: {str(e)}")
            return None

    def style_transfer(self, reference_img, style_img):
        """Generate new image based on reference and style images"""
        try:
            # Your implementation here
            self.logger.info("Style transfer called")
            return reference_img
        except Exception as e:
            self.logger.error(f"Error in style_transfer: {str(e)}")
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