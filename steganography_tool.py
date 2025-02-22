import streamlit as st
from PIL import Image
import numpy as np
from cryptography.fernet import Fernet
import io

def get_cipher():
    key_input = st.text_input("Enter encryption key (leave empty to generate a new one):", type="password")
    if key_input:
        key = key_input.encode()
    else:
        if 'key' not in st.session_state:
            st.session_state['key'] = Fernet.generate_key()
        key = st.session_state['key']
    return Fernet(key)

cipher = get_cipher()

def encode_image(image, message):
    image = image.convert("RGB")
    img_array = np.array(image)
    message = cipher.encrypt(message.encode())
    message_bin = ''.join(format(byte, '08b') for byte in message)
    
    max_bytes = img_array.size // 8
    if len(message) > max_bytes:
        st.error(f"Message too long! Max {max_bytes} characters.")
        return None
    
    prefix = format(len(message_bin), '016b')
    message_bin = prefix + message_bin  
    
    flat_img = img_array.flatten()
    for i in range(len(message_bin)):
        flat_img[i] = (flat_img[i] & ~1) | int(message_bin[i])
    
    encoded_img = flat_img.reshape(img_array.shape)
    return Image.fromarray(encoded_img)

def decode_image(image):
    image = image.convert("RGB")
    img_array = np.array(image)
    flat_img = img_array.flatten()
    
    length_bin = ''.join(str(flat_img[i] & 1) for i in range(16))
    message_length = int(length_bin, 2)
    message_bin = ''.join(str(flat_img[i] & 1) for i in range(16, 16 + message_length))
    
    byte_list = [message_bin[i:i+8] for i in range(0, len(message_bin), 8)]
    byte_data = bytearray(int(byte, 2) for byte in byte_list if len(byte) == 8)
    
    try:
        decoded_message = cipher.decrypt(bytes(byte_data)).decode()
        return decoded_message
    except:
        return "No hidden message found or incorrect decryption key."

st.title("Steganography Tool - Hide Messages in Images")
option = st.radio("Choose an option:", ("Encode Message", "Decode Message"))
uploaded_file = st.file_uploader("Upload an Image", type=["png", "jpg", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)
    
    if option == "Encode Message":
        message = st.text_area("Enter the secret message:")
        if st.button("Encode and Download"):
            encoded_img = encode_image(image, message)
            if encoded_img:
                buf = io.BytesIO()
                encoded_img.save(buf, format="PNG")
                st.download_button(label="Download Encoded Image", data=buf.getvalue(), file_name="encoded_image.png", mime="image/png")
    
    elif option == "Decode Message":
        if st.button("Decode Message"):
            decoded_message = decode_image(image)
            st.text_area("Decoded Message:", decoded_message)

