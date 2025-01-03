import gradio as gr
from image_generator import ImageGenerator
from rag_system import RAGSystem
from style_transfer import StyleTransfer
from PIL import Image
import numpy as np

class App:
    def __init__(self):
        self.img_gen = ImageGenerator()
        self.rag = RAGSystem()
        self.style = StyleTransfer()

    def generate_3d_view(self, image):
        if image is not None:
            # Convert numpy array to PIL Image if necessary
            if isinstance(image, np.ndarray):
                image = Image.fromarray(image)
            return self.img_gen.generate_3d_view(image)
        return None

    def modify_element(self, image, element, style_desc):
        if image is not None and element and style_desc:
            if isinstance(image, np.ndarray):
                image = Image.fromarray(image)
            return self.img_gen.modify_element(image, element, style_desc)
        return None

    def process_rag(self, url, question):
        if url:
            content = self.rag.scrape_content(url)
            self.rag.process_content(content)
            if question:
                return self.rag.query(question)
        return "Please provide a URL first"

    def transfer_style(self, ref_img, style_img):
        if ref_img is not None and style_img is not None:
            if isinstance(ref_img, np.ndarray):
                ref_img = Image.fromarray(ref_img)
            if isinstance(style_img, np.ndarray):
                style_img = Image.fromarray(style_img)
            return self.style.transfer_style(ref_img, style_img)
        return None

def main():
    app = App()

    with gr.Blocks() as interface:
        gr.Markdown("# 3D Image Generation & RAG System")

        with gr.Tab("3D Generation"):
            with gr.Row():
                with gr.Column():
                    input_image = gr.Image(label="Upload Image")
                    generate_btn = gr.Button("Generate 3D View")
                with gr.Column():
                    output_image = gr.Image(label="Generated 3D View")
            
            with gr.Row():
                element_dropdown = gr.Dropdown(
                    choices=["clothing", "background"],
                    label="Modify Element"
                )
                style_input = gr.Textbox(label="Enter style description")
                modify_btn = gr.Button("Apply Modification")
            
            modified_output = gr.Image(label="Modified Result")

        with gr.Tab("RAG System"):
            url_input = gr.Textbox(label="Enter URL")
            question_input = gr.Textbox(label="Ask a question")
            query_btn = gr.Button("Process and Query")
            rag_output = gr.Textbox(label="Results")

        with gr.Tab("Style Transfer"):
            with gr.Row():
                ref_input = gr.Image(label="Reference Image")
                style_input_img = gr.Image(label="Style Image")
            
            style_btn = gr.Button("Generate")
            style_output = gr.Image(label="Style Transfer Result")

        # Set up event handlers
        generate_btn.click(
            app.generate_3d_view,
            inputs=[input_image],
            outputs=[output_image]
        )

        modify_btn.click(
            app.modify_element,
            inputs=[output_image, element_dropdown, style_input],
            outputs=[modified_output]
        )

        query_btn.click(
            app.process_rag,
            inputs=[url_input, question_input],
            outputs=[rag_output]
        )

        style_btn.click(
            app.transfer_style,
            inputs=[ref_input, style_input_img],
            outputs=[style_output]
        )

    # Launch with local-only settings
    interface.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        inbrowser=True
    )

if __name__ == "__main__":
    main()