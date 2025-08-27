import streamlit as st
from streamlit_drawable_canvas import st_canvas
import numpy as np
import cv2
import tensorflow as tf
from tensorflow.keras.models import load_model

# ---------- Load Urdu, English, and Digit Models ----------
@st.cache_resource
def load_models():
    tf.keras.backend.clear_session()
    urdu_model = load_model('Models/urdu_model.keras')
    tf.keras.backend.clear_session()
    english_model = load_model('Models/english_model.keras')
    tf.keras.backend.clear_session()
    digit_model = load_model('Models/digit_model.keras')
    return urdu_model, english_model, digit_model

urdu_model, english_model, digit_model = load_models()

# English letter mapping
def get_word_dict():
    return {i: chr(65 + i) for i in range(26)}
word_dict = get_word_dict()

# App title
st.title("Handwritten Character Similarity Checker")

# Sidebar controls
language = st.sidebar.radio("Select Language:", ["English", "Urdu", "Digit"])
target_input = st.sidebar.text_input("Target (Letter for English, Index for Urdu, Digit for Digit):")
stroke_width = 20

# Set canvas colors
bg_color = "#000000"  # black background for all
stroke_color = "#FFFFFF"  # white strokes for all

# Draw canvas
canvas_result = st_canvas(
    fill_color="rgba(0, 0, 0, 0)",
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    width=280,
    height=280,
    drawing_mode="freedraw",
    key="canvas",
)

def predict_digit_similarity_from_array(image_array, model, target_digit):
    gray = cv2.cvtColor(image_array[:, :, :3].astype('uint8'), cv2.COLOR_RGB2GRAY)
    resized = cv2.resize(gray, (28, 28))
    norm = resized / 255.0
    img_flat = norm.reshape(1, -1)
    prediction = model.predict(img_flat)
    predicted_label = int(np.argmax(prediction))
    similarity_percentage = prediction[0][int(target_digit)] * 100
    return predicted_label, similarity_percentage, resized

# Handle prediction
def predict_letter(image_array, lang, target):
    gray = cv2.cvtColor(image_array[:, :, :3].astype('uint8'), cv2.COLOR_RGB2GRAY)
    resized = cv2.resize(gray, (28, 28))
    norm = resized.astype('float32') / 255.0
    inp = norm.reshape(1, 28, 28, 1)

    sim_val = None
    if lang == "English":
        preds = english_model.predict(inp)
        idx = int(np.argmax(preds))
        letter = word_dict[idx]
        tgt = target.strip().upper()
        inv = {v: k for k, v in word_dict.items()}
        if tgt in inv:
            sim_val = preds[0][inv[tgt]] * 100
            sim = f"{sim_val:.2f}%"
        else:
            sim = "Invalid English target letter."
        return letter, sim, resized, sim_val
    elif lang == "Urdu":
        try:
            ti = int(target)
            preds = urdu_model.predict(inp)[0]
            sim_val = preds[ti] * 100
            sim = f"{sim_val:.2f}%"
            return None, sim, resized, sim_val
        except:
            return None, "Invalid Urdu target index.", resized, None
    elif lang == "Digit":
        try:
            predicted_label, sim_val, resized_img = predict_digit_similarity_from_array(
                image_array, digit_model, int(target))
            sim = f"{sim_val:.2f}%"
            return predicted_label, sim, resized_img, sim_val
        except:
            return None, "Invalid target digit.", resized, None

# On predict button click
if st.button("Predict"):
    if canvas_result.image_data is None:
        st.warning("Please draw on the canvas first.")
    else:
        letter, similarity_text, proc_img, sim_val = predict_letter(
            canvas_result.image_data,
            language,
            target_input
        )

        # Display results
        if language == "English":
            st.write(f"**Predicted Letter:** {letter}")
            st.write(f"**Similarity to '{target_input.strip().upper()}':** {similarity_text}")
        elif language == "Urdu":
            st.write(f"**Similarity:** {similarity_text}")
        elif language == "Digit":
            st.write(f"**Predicted Digit:** {letter}")
            st.write(f"**Similarity to '{target_input.strip()}':** {similarity_text}")

        # Reward or failure message
        if sim_val is not None:
            if sim_val >= 75:
                st.success("Great job! 🎉 Your handwriting is very similar to the target.")
            else:
                st.error("Try again! ❗ The similarity is below 75%.")

        # Show processed image
        st.image(proc_img, caption="Processed 28×28 Image", use_column_width=False)
