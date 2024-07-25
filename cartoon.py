import streamlit as st
import os
import cv2
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from PIL import Image
import io

# Load image function


def li(img):
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    img = img.astype(np.float32)/127.5 - 1
    img = np.expand_dims(img, 0)
    img = tf.convert_to_tensor(img)
    return img

# Preprocess image function


def pi(img, td=224):
    shp = tf.cast(tf.shape(img)[1:-1], tf.float32)
    sd = min(shp)
    scl = td/sd
    nhp = tf.cast(shp*scl, tf.int32)
    img = tf.image.resize(img, nhp)
    img = tf.image.resize_with_crop_or_pad(img, td, td)
    return img

# Cartoon function


def cartoon(img):
    si = li(img)
    psi = pi(si, td=512)

    # Model dataflow
    m = 'cartoon_model.tflite'
    i = tf.lite.Interpreter(model_path=m)
    ind = i.get_input_details()
    i.allocate_tensors()
    i.set_tensor(ind[0]['index'], psi)
    i.invoke()

    r = i.tensor(i.get_output_details()[0]['index'])()

    # Post process the model output
    o = (np.squeeze(r)+1.0)*127.5
    o = np.clip(o, 0, 255).astype(np.uint8)
    o = cv2.cvtColor(o, cv2.COLOR_BGR2RGB)

    return o


# Streamlit app
st.title('사진을 만화체로 변환하기')

uploaded_file = st.file_uploader("사진을 선택하세요", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption='업로드된 이미지', use_column_width=True)

    if st.button('만화체로 변환'):
        cartoon_image = cartoon(image)
        st.image(cartoon_image, caption='만화체로 변환된 이미지', use_column_width=True)
