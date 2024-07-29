import streamlit as st
from PIL import Image
import io
from rembg import remove
import torch
from torchvision import transforms
from stylegan2_pytorch import ModelLoader


def load_stylegan_model():
    model = ModelLoader(
        name='stylegan2-ffhq-config-f',
        latent_dim=512,
        truncation=0.7
    )
    return model


def generate_realistic_image(model, input_image):
    # 이미지를 StyleGAN2의 입력 형식으로 변환
    transform = transforms.Compose([
        transforms.Resize((1024, 1024)),
        transforms.ToTensor(),
        transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
    ])
    input_tensor = transform(input_image).unsqueeze(0)

    # StyleGAN2를 사용하여 실사화된 이미지 생성
    with torch.no_grad():
        output = model.model(input_tensor)

    # 출력을 PIL 이미지로 변환
    output_image = transforms.ToPILImage()(
        output[0].cpu().clamp(-1, 1) * 0.5 + 0.5)
    return output_image


def main():
    st.title("실사화 이미지 변환 앱")

    uploaded_file = st.file_uploader(
        "이미지를 선택하세요...", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='업로드된 이미지', use_column_width=True)

        # 배경 제거
        if st.button('배경 제거'):
            output = remove(image)
            st.image(output, caption='배경이 제거된 이미지', use_column_width=True)

            # 실사화 변환
            if st.button('실사화 변환'):
                model = load_stylegan_model()
                realistic_image = generate_realistic_image(model, output)
                st.image(realistic_image, caption='실사화된 이미지',
                         use_column_width=True)


if __name__ == "__main__":
    main()
