import streamlit as st
import streamlit.components.v1 as components
import io

# Custom CSS for cursor and 3D viewer styling
st.markdown("""
    <style>
    .stApp {
        max-width: 100%;
    }
    .viewer-container {
        width: 100%;
        height: 500px;
        border: 1px solid #ddd;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Custom HTML/JS for 3D viewer using three.js
def create_3d_viewer(model_url="placeholder_model"):
    viewer_html = f"""
    <div class="viewer-container" id="model-viewer">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script>
            // Set up scene
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer();
            const container = document.getElementById('model-viewer');
            renderer.setSize(container.offsetWidth, container.offsetHeight);
            container.appendChild(renderer.domElement);

            // Add lights
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
            scene.add(ambientLight);
            const pointLight = new THREE.PointLight(0xffffff, 1);
            pointLight.position.set(5, 5, 5);
            scene.add(pointLight);

            // Create placeholder geometry (sphere)
            const geometry = new THREE.SphereGeometry(2, 32, 32);
            const material = new THREE.MeshPhongMaterial({{ color: 0x00ff00 }});
            const sphere = new THREE.Mesh(geometry, material);
            scene.add(sphere);

            camera.position.z = 5;

            // Animation
            let rotation = 0;
            function animate() {{
                requestAnimationFrame(animate);
                rotation += 0.01;
                sphere.rotation.y = rotation;
                renderer.render(scene, camera);
            }}
            animate();

            // Handle window resize
            window.addEventListener('resize', () => {{
                const width = container.offsetWidth;
                const height = container.offsetHeight;
                renderer.setSize(width, height);
                camera.aspect = width / height;
                camera.updateProjectionMatrix();
            }});
        </script>
    </div>
    """
    return viewer_html

def generate_3d_style_transfer():
    st.title("3D Style Transfer Generator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        reference_image = st.file_uploader("Upload reference object image (e.g., flower)", type=['PNG', 'JPG', 'JPEG'], key="ref_img")
        if reference_image:
            st.image(reference_image, caption="Reference Object", use_container_width=True)
    
    with col2:
        style_image = st.file_uploader("Upload style reference image (e.g., Victorian style)", type=['PNG', 'JPG', 'JPEG'], key="style_img")
        if style_image:
            st.image(style_image, caption="Style Reference", use_container_width=True)
    
    if st.button("Generate 3D Model"):
        if reference_image and style_image:
            st.info("Processing your request...")
            
            # Here you would integrate your 3D style transfer model
            # Placeholder for model processing
            # result_3d_model = your_3d_style_transfer_model(reference_image, style_image)
            
            st.subheader("3D Preview")
            viewer_html = create_3d_viewer()
            components.html(viewer_html, height=600)
            
            st.success("3D model generated! Use your mouse to rotate and zoom.")
            
            # Add download button (placeholder)
            st.download_button(
                label="Download 3D Model",
                data=io.BytesIO(b"placeholder").getvalue(),
                file_name="styled_3d_model.glb",
                mime="application/octet-stream"
            )
        else:
            st.warning("Please upload both reference and style images")

    # Add information about the app
    st.sidebar.markdown("""
    ### About
    This application generates 3D 360° views of objects with applied style transfer.
    
    #### How to use:
    1. Upload a reference image of the object
    2. Upload a style image
    3. Click 'Generate 3D Model'
    4. View and interact with the 3D model
    5. Download the result
    
    #### Controls:
    - Left click + drag: Rotate
    - Right click + drag: Pan
    - Scroll: Zoom
    """)

if __name__ == "__main__":
    generate_3d_style_transfer()