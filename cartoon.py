import os
import numpy as np
import tensorflow as tf
from PIL import Image
import streamlit as st

# Ensure the temp directory exists
os.makedirs("temp", exist_ok=True)

# Load image


def li(p):
    img = Image.open(p).convert('RGB')
    img = np.array(img).astype(np.float32) / 127.5 - 1
    img = np.expand_dims(img, 0)
    return tf.convert_to_tensor(img)

# Preprocess image


def pi(img, td=224):
    shp = tf.cast(tf.shape(img)[1:-1], tf.float32)
    sd = tf.reduce_min(shp)
    scl = td / sd
    nhp = tf.cast(shp * scl, tf.int32)
    img = tf.image.resize(img, nhp)
    img = tf.image.resize_with_crop_or_pad(img, td, td)
    return img


def cartoon(img_p):
    # Loading image
    si = li(img_p)

    psi = pi(si, td=512)
    psi.shape

    # Model dataflow
    m = 'cartoon_model.tflite'
    i = tf.lite.Interpreter(model_path=m)
    ind = i.get_input_details()
    i.allocate_tensors()
    i.set_tensor(ind[0]['index'], psi)
    i.invoke()

    r = i.tensor(i.get_output_details()[0]['index'])()

    # Post process the model output
    o = (np.squeeze(r) + 1.0) * 127.5
    o = np.clip(o, 0, 255).astype(np.uint8)
    o = Image.fromarray(o)
    o = o.convert('RGB')

    return o


# Streamlit app
st.title('Cartoonify Your Image')

uploaded_file = st.file_uploader(
    "Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Save the uploaded file to a temporary location
    temp_file_path = os.path.join("temp", uploaded_file.name)
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Display the input image
    st.image(temp_file_path, caption='Input Image', use_column_width=True)

    # Process the image
    output_image = cartoon(temp_file_path)

    # Display the output image
    st.image(output_image, caption='Cartoonified Image', use_column_width=True)
