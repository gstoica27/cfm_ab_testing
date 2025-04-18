import os
import random
import streamlit as st
import pandas as pd
from PIL import Image

# === CONFIGURATION ===
FOLDER_A = "images_a"
FOLDER_B = "images_b"
RESULTS_FILE = "ab_test_results.csv"

# === LOAD & SHUFFLE IMAGE NAMES ===
image_names = sorted(os.listdir(FOLDER_A))
random.shuffle(image_names)

# === SESSION STATE ===
if "index" not in st.session_state:
    st.session_state.index = 0
if "responses" not in st.session_state:
    st.session_state.responses = []
if "assignments" not in st.session_state:
    st.session_state.assignments = {}
if "run_next" not in st.session_state:
    st.session_state.run_next = False

# === SAFE RERUN HANDLER ===
if st.session_state.run_next:
    st.session_state.run_next = False
    st.experimental_rerun()
    st.stop()  # Just in case

# === IDENTIFY TESTER ===
st.title("Image Comparison Study")
tester = st.text_input("Enter your name or ID:", key="tester_id")
if not tester:
    st.warning("Please enter your ID to begin.")
    st.stop()

# === FINISH LOGIC ===
if st.session_state.index >= len(image_names):
    st.success("✅ You’ve completed the test. Thank you!")

    df = pd.DataFrame(st.session_state.responses)

    # Save to global file
    if os.path.exists(RESULTS_FILE):
        old_df = pd.read_csv(RESULTS_FILE)
        df = pd.concat([old_df, df], ignore_index=True)
    df.to_csv(RESULTS_FILE, index=False)

    # Save individual results
    user_file = f"results_{tester}.csv"
    df[df["tester"] == tester].to_csv(user_file, index=False)

    # === SUMMARY ===
    st.markdown("### 🔍 Your Summary")
    user_df = df[df["tester"] == tester]
    st.write("**Total Comparisons:**", len(user_df))
    st.write("**Preferences:**", user_df["preferred_model"].value_counts().to_dict())
    st.write("**Average Confidence:**", round(user_df["confidence"].mean(), 2))
    st.write("**Comments (if any):**")
    st.write(user_df[user_df["comment"] != ""][["image", "comment"]])

    st.stop()

# === CURRENT IMAGE ===
img_name = image_names[st.session_state.index]
img_path_a = os.path.join(FOLDER_A, img_name)
img_path_b = os.path.join(FOLDER_B, img_name)

# Randomize left/right
if img_name not in st.session_state.assignments:
    if random.random() < 0.5:
        st.session_state.assignments[img_name] = {"left": "A", "right": "B"}
    else:
        st.session_state.assignments[img_name] = {"left": "B", "right": "A"}

assignment = st.session_state.assignments[img_name]
img_left = Image.open(img_path_a if assignment["left"] == "A" else img_path_b)
img_right = Image.open(img_path_a if assignment["right"] == "A" else img_path_b)

# === UI ===
st.markdown(f"### Image {st.session_state.index + 1} of {len(image_names)}")

col1, col2 = st.columns(2)
with col1:
    st.image(img_left, caption="Left", use_column_width=True)
with col2:
    st.image(img_right, caption="Right", use_column_width=True)

# === INPUTS ===
preference = st.radio(
    "Which image do you prefer?",
    ["Left", "Right", "No preference"],
    horizontal=True
)

confidence = st.slider("How confident are you?", 1, 5, 3)
comment = st.text_input("Any comments? (optional)", "")

# === SUBMIT ===
if st.button("Submit and continue"):
    preferred_model = (
        assignment["left"] if preference == "Left"
        else assignment["right"] if preference == "Right"
        else "None"
    )

    st.session_state.responses.append({
        "tester": tester,
        "image": img_name,
        "left_model": assignment["left"],
        "right_model": assignment["right"],
        "preferred_side": preference,
        "preferred_model": preferred_model,
        "confidence": confidence,
        "comment": comment
    })

    st.session_state.index += 1
    st.session_state.run_next = True
    st.stop()
