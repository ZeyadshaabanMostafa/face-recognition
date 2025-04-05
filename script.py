import os
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, Label, Button, StringVar, OptionMenu, Toplevel, Text, Canvas, Frame, Scrollbar, DISABLED, NORMAL
from PIL import Image, ImageTk

# ✅ Initialize dataset path
dataset_base_path = ""

# ✅ Function to let the user select the dataset folder
def select_dataset_folder():
    global dataset_base_path
    dataset_base_path = filedialog.askdirectory(title="Select Currency Data Folder")
    if dataset_base_path:
        folder_label.config(text=f"Selected Folder: {os.path.basename(dataset_base_path)}")

# ✅ Currency types and numbers
currency_types = ["EGP", "USD"]
currency_numbers = ["1", "5", "10", "20", "50", "100", "200"]

# ✅ Improved Feature Matching (SIFT/ORB)
def match_features(image, feature_folder, feature_list):
    """Use SIFT (if available) or ORB for feature matching."""
    try:
        sift = cv2.SIFT_create()  # Use SIFT (better than ORB)
    except:
        sift = cv2.ORB_create(nfeatures=1500)  # ORB as backup

    kp1, des1 = sift.detectAndCompute(image, None)
    if des1 is None:
        return 0, len(feature_list)  # No features detected in input image

    matched_features = 0
    total_features = len(feature_list)

    for feature_img_name in feature_list:
        feature_img_path = os.path.join(feature_folder, feature_img_name)
        feature_img = cv2.imread(feature_img_path, cv2.IMREAD_GRAYSCALE)

        if feature_img is None:
            continue

        kp2, des2 = sift.detectAndCompute(feature_img, None)
        if des2 is None:
            continue

        # ✅ Use BFMatcher with knnMatch
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(des1, des2, k=2)

        # ✅ Lowe's Ratio Test
        good_matches = [m for m, n in matches if m.distance < 0.7 * n.distance]

        if len(good_matches) > 5:  # Threshold: At least 5 matching keypoints
            matched_features += 1

    return matched_features, total_features  # Return matched and total features

# ✅ Function to Check Currency Features
def search_for_currency_features(front_image_path, back_image_path, selected_currency, selected_number):
    front_folder = os.path.join(dataset_base_path, selected_currency, selected_number, "front")
    back_folder = os.path.join(dataset_base_path, selected_currency, selected_number, "back")

    if not os.path.exists(front_folder) or not os.path.exists(back_folder):
        return f"❌ FAKE Currency ({selected_currency} {selected_number}) - Security feature folders are missing!"

    front_img = cv2.imread(front_image_path, cv2.IMREAD_GRAYSCALE)
    back_img = cv2.imread(back_image_path, cv2.IMREAD_GRAYSCALE)

    if front_img is None or back_img is None:
        return "❌ Error: Unable to read one or both uploaded images."

    front_features = os.listdir(front_folder)
    back_features = os.listdir(back_folder)

    if not front_features or not back_features:
        return f"❌ FAKE Currency ({selected_currency} {selected_number}) - Security feature images are missing!"

    # ✅ Feature matching
    front_matched, total_front = match_features(front_img, front_folder, front_features)
    back_matched, total_back = match_features(back_img, back_folder, back_features)

    # ✅ If any expected feature is missing, classify as FAKE
    if front_matched < total_front or back_matched < total_back:
        return f"❌ FAKE Currency ({selected_currency} {selected_number}) - {front_matched}/{total_front} matched in Front, {back_matched}/{total_back} matched in Back."

    return f"✅ REAL Currency ({selected_currency} {selected_number}) - All security features detected."

# ✅ GUI Functions
def upload_front_image():
    global front_image_path
    front_image_path = filedialog.askopenfilename()
    if front_image_path:
        display_image(front_image_path, front_panel)
        check_ready()

def upload_back_image():
    global back_image_path
    back_image_path = filedialog.askopenfilename()
    if back_image_path:
        display_image(back_image_path, back_panel)
        check_ready()

def display_image(image_path, panel):
    img = Image.open(image_path)
    img.thumbnail((400, 400))
    img = ImageTk.PhotoImage(img)
    panel.config(image=img)
    panel.image = img

def check_ready():
    if front_image_path and back_image_path:
        classify_button.config(state="normal")

def classify_image():
    selected_currency = currency_var.get()
    selected_number = currency_number_var.get()

    if not selected_currency:
        result_label.config(text="Error: Please select a currency type!")
        return

    if not selected_number:
        result_label.config(text="Error: Please select a currency number!")
        return

    result = search_for_currency_features(front_image_path, back_image_path, selected_currency, selected_number)
    result_label.config(text=f"Result: {result}")

# ✅ Function to show user guide window
def show_user_guide():
    guide_window = Toplevel(root)
    guide_window.title("User Guide")
    guide_window.geometry("450x300")

    guide_text = """Welcome to the Currency Feature Recognition System!
    
    1- Click "Select Currency Data Folder" to choose the dataset.
    2- Click "Upload Front Image" to select an image of the front side (the side that has the date).
    3- Click "Upload Back Image" to select an image of the back side.
    4- Select the currency type from the dropdown list.
    5- Select the currency number from the dropdown list.
    6- Click "Check Real/Fake" to analyze the currency.
    
    ✅ If all security features match, the currency is REAL.
    ❌ If any security feature is missing, the currency is FAKE.

    Close this window to continue.
    """

    text_box = Text(guide_window, wrap="word", font=("Arial", 12), height=12, width=55)
    text_box.insert("1.0", guide_text)
    text_box.config(state=DISABLED)
    text_box.pack(pady=10)

    Button(guide_window, text="Close", command=guide_window.destroy).pack()

# ✅ Create Main GUI
root = tk.Tk()
root.title("Currency Feature Search")
root.geometry("500x600")

canvas = Canvas(root)
scrollbar = Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = Frame(canvas)

scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

Label(scrollable_frame, text="Currency Feature Recognition System", font=("Arial", 16)).pack()

# ✅ User Guide Button
Button(scrollable_frame, text="User Guide", command=show_user_guide).pack()

# ✅ Select Folder Button
Button(scrollable_frame, text="Select Currency Data Folder", command=select_dataset_folder).pack()
folder_label = Label(scrollable_frame, text="No folder selected", font=("Arial", 10))
folder_label.pack()

Button(scrollable_frame, text="Upload Front Image", command=upload_front_image).pack()
front_panel = Label(scrollable_frame)
front_panel.pack()

Button(scrollable_frame, text="Upload Back Image", command=upload_back_image).pack()
back_panel = Label(scrollable_frame)
back_panel.pack()

currency_var = StringVar(root)
currency_var.set(currency_types[0])
OptionMenu(scrollable_frame, currency_var, *currency_types).pack()

currency_number_var = StringVar(root)
currency_number_var.set(currency_numbers[0])
OptionMenu(scrollable_frame, currency_number_var, *currency_numbers).pack()

classify_button = Button(scrollable_frame, text="Check Real/Fake", command=classify_image, state="disabled")
classify_button.pack()

result_label = Label(scrollable_frame, text="", font=("Arial", 14))
result_label.pack()

root.after(100, show_user_guide)
root.mainloop()
