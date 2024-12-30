import streamlit as st
from image_generator import ImageGenerator
from rag_system import RAGSystem
from style_transfer import StyleTransfer
from PIL import Image

def main():
    st.title("3D Image Generation & RAG System")
    
    tab1, tab2, tab3 = st.tabs(["3D Generation", "RAG System", "Style Transfer"])
    
    img_gen = ImageGenerator()
    rag = RAGSystem()
    style = StyleTransfer()

    with tab1:
        st.header("3D View Generator")
        uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg'])
        if uploaded_file:
            image = Image.open(uploaded_file)
            result = img_gen.generate_3d_view(image)
            st.image(result)
            
            element = st.selectbox("Modify Element", ["clothing", "background"])
            if element:
                style = st.text_input("Enter style description")
                if st.button("Apply"):
                    modified = img_gen.modify_element(result, element, style)
                    st.image(modified)

    with tab2:
        st.header("RAG System")
        url = st.text_input("Enter URL:")
        if st.button("Process"):
            content = rag.scrape_content(url)
            rag.process_content(content)
            st.success("Content processed")
            
        question = st.text_input("Ask a question:")
        if question:
            results = rag.query(question)
            st.write(results)

    with tab3:
        st.header("Style Transfer")
        ref_img = st.file_uploader("Reference Image", type=['png', 'jpg'])
        style_img = st.file_uploader("Style Image", type=['png', 'jpg'])
        if ref_img and style_img and st.button("Generate"):
            result = style.transfer_style(ref_img, style_img)
            st.image(result)

if __name__ == "__main__":
    main()