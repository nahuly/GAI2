import streamlit as st
from PIL import Image
import cv2
import numpy as np


def main():
    st.title("Realistic Image Transformation with Streamlit")
    st.subheader("Upload an image and apply transformations")

    # Sidebar for navigation
    selected_box = st.sidebar.selectbox(
        'Choose an option',
        ('Welcome', 'Upload Image', 'Transform Image')
    )

    if selected_box == 'Welcome':
        welcome()
    elif selected_box == 'Upload Image':
        upload_image()
    elif selected_box == 'Transform Image':
        transform_image()


def welcome():
    st.write("Welcome to the Realistic Image Transformation App!")
    st.image('example.jpg', use_column_width=True)


def upload_image():
    uploaded_file = st.file_uploader(
        "Choose an image...", type=["jpg", "png", "jpeg"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Image', use_column_width=True)
        st.session_state['uploaded_image'] = image


def transform_image():
    if 'uploaded_image' not in st.session_state:
        st.write("Please upload an image first!")
        return

    image = st.session_state['uploaded_image']
    st.image(image, caption='Original Image', use_column_width=True)

    # Convert to OpenCV format
    opencv_image = np.array(image.convert('RGB'))
    opencv_image = cv2.cvtColor(opencv_image, cv2.COLOR_RGB2BGR)

    # Apply a transformation (e.g., converting to grayscale)
    gray_image = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
    st.image(gray_image, caption='Transformed Image',
             use_column_width=True, channels='GRAY')


if __name__ == "__main__":
    main()
