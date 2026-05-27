import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import speech_recognition as sr
from deep_translator import GoogleTranslator
lingua = input("Digite a língua para tradução (ex: 'en' para inglês, 'fr' para francês): ")
duration = 5  # seconds
sample_rate = 44100  # Hz


print("Fale agora...")
recording = sd.rec(
  int(duration * sample_rate), # o número de amostras a serem registradas
  samplerate=sample_rate,      # taxa de amostras
  channels=1,                  # 1 significa gravação mono
  dtype="int16")
sd.wait()  # aguardando o término da gravação

wav.write("output.wav", sample_rate, recording)
print("Gravação concluída, estou reconhecendo...")

recognizer = sr.Recognizer()
with sr.AudioFile("output.wav") as source:
    audio = recognizer.record(source)


try:
    result = recognizer.recognize_google(audio, language="pt-BR", show_all=True)
    print("Resultado bruto:", result)

    if not result:
        print("A fala não pôde ser reconhecida.")
    else:
        text = result["alternative"][0].get("transcript", "")
        print("Você disse:", text)

        translator = GoogleTranslator(source='pt', target=lingua)
        translated = translator.translate(text)
        print(f"🌍 Tradução para {lingua}:", translated)
except sr.UnknownValueError:
    print("A fala não pôde ser reconhecida.")
except sr.RequestError as e:
    print(f"Service error: {e}")