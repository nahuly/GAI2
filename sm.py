import streamlit as st
import magenta
from magenta.models.melody_rnn import melody_rnn_sequence_generator
from magenta.protobuf import music_pb2
from magenta.music import sequence_proto_to_midi_file
import random

# Streamlit 제목
st.title("AI 음악 생성기")

# 사용자 입력 받기
genre = st.selectbox("원하는 장르를 선택하세요:", ["Pop", "Rock", "Jazz", "Classical"])
tempo = st.selectbox("원하는 템포를 선택하세요:", ["Fast", "Medium", "Slow"])
mood = st.selectbox("원하는 분위기를 선택하세요:", [
                    "Energetic", "Calm", "Romantic", "Fun"])

# 생성 버튼 클릭 시 음악 생성
if st.button("AI 음악 생성"):
    st.write("AI가 음악을 생성 중입니다...")

    # Magenta Melody RNN 모델 로드 (모델 파일 경로를 적어야 합니다)
    bundle_file = '/path/to/melody_rnn_checkpoint.tar'
    generator = melody_rnn_sequence_generator.MelodyRnnSequenceGenerator()

    # 모델 초기화
    generator.initialize(bundle_file)

    # 사용자 선택을 기반으로 입력 시퀀스 설정
    input_sequence = music_pb2.NoteSequence()

    # AI 모델을 통해 음악 생성
    generated_sequence = generator.generate(input_sequence)

    # 생성된 MIDI 파일로 변환
    midi_file = '/path/to/generated_melody.mid'
    sequence_proto_to_midi_file(generated_sequence, midi_file)

    # 음악 다운로드 링크 제공
    with open(midi_file, "rb") as file:
        st.download_button("생성된 음악 다운로드", file,
                           "generated_melody.mid", "audio/midi")

    st.write(f"장르: {genre}, 템포: {tempo}, 분위기: {mood}에 맞는 음악을 생성했습니다!")
