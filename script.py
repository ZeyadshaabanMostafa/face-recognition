import os
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, Label, Button, StringVar, OptionMenu, Toplevel, Text, Canvas, Frame, Scrollbar, DISABLED, NORMAL, font
from PIL import Image, ImageTk, ImageOps
from itertools import count
import time

# Initialize dataset path
dataset_base_path = ""

# Color scheme matching your reference image
bg_color = "#000206"  # Light gray background
panel_color = "#00040c"  # White panels
text_color = "white"  # Dark gray text
button_color = "#4a6fa5"  # Blue buttons (as in reference)
highlight_color = "#3a5a80"  # Darker blue for hover
separator_color = "#e0e0e0"  # Light gray separator

# Track running animations
running_animations = []

# Animation functions
def fade_widget(widget, fade_in=True, duration=300):
    """Alternative fade effect using color manipulation for regular widgets"""
    def _fade(step):
        if not widget.winfo_exists():
            return
        alpha = step/100
        if isinstance(widget, (Label, Frame)):
            # For frames and labels, we'll change the background color
            r = int(panel_color[1:3], 16)
            g = int(panel_color[3:5], 16)
            b = int(panel_color[5:7], 16)
            new_color = f"#{int(r*alpha):02x}{int(g*alpha):02x}{int(b*alpha):02x}"
            widget.config(bg=new_color)
        widget.update()
        if (fade_in and step < 100) or (not fade_in and step > 0):
            widget.after(duration//20, lambda: _fade(step + (5 if fade_in else -5)))
    
    _fade(0 if fade_in else 100)

def pulse_button(button, original_color, pulse_color, duration=1000):
    def pulse(step=0):
        if not button.winfo_exists():
            return
        progress = (step % 100) / 100
        intensity = 0.5 + 0.5 * np.sin(progress * 2 * np.pi)
        r = int(original_color[1:3], 16) * (1-intensity) + int(pulse_color[1:3], 16) * intensity
        g = int(original_color[3:5], 16) * (1-intensity) + int(pulse_color[3:5], 16) * intensity
        b = int(original_color[5:7], 16) * (1-intensity) + int(pulse_color[5:7], 16) * intensity
        color = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
        button.config(bg=color)
        button.update()
        button.after(30, lambda: pulse(step + 1))
    
    pulse()

def animate_image_appearance(panel, image_path, duration=500):
    """Animate the appearance of an image with scaling and fading"""
    # Create a temporary canvas for animation
    canvas = Canvas(panel, bg=panel_color, highlightthickness=0)
    canvas.place(relx=0.5, rely=0.5, anchor='center', width=1, height=1)
    
    # Load the image
    img = Image.open(image_path)
    img.thumbnail((400, 400))
    photo_img = ImageTk.PhotoImage(img)
    
    # Create image item on canvas
    img_item = canvas.create_image(0, 0, anchor='nw', image=photo_img)
    canvas.image = photo_img  # Keep reference
    
    def scale_step(step):
        if not canvas.winfo_exists():
            return
            
        if step <= 20:
            # Calculate current dimensions
            w = int(400 * (step/20))
            h = int(400 * (step/20))
            
            # Resize canvas and image
            canvas.config(width=w, height=h)
            canvas.coords(img_item, w//2, h//2)
            
            # Calculate opacity (0-255)
            alpha = int(255 * (step/20))
            
            # Apply alpha to image
            if alpha < 255:
                img.putalpha(alpha)
                photo_img = ImageTk.PhotoImage(img)
                canvas.itemconfig(img_item, image=photo_img)
                canvas.image = photo_img  # Keep reference
            
            panel.update()
            canvas.after(duration//20, lambda: scale_step(step+1))
        else:
            # Animation complete, replace with permanent label
            if canvas.winfo_exists():
                canvas.destroy()
                display_image(image_path, panel)
    
    # Start animation
    scale_step(1)

def animate_success(panel):
    """Add a success animation to the image panel"""
    canvas = Canvas(panel, bg=panel_color, highlightthickness=0)
    canvas.place(relx=0.5, rely=0.5, anchor='center', width=400, height=400)
    
    # Create a border that will animate
    border = canvas.create_rectangle(0, 0, 0, 0, outline='', width=5)
    
    def animate_border(step):
        if not canvas.winfo_exists():
            return
            
        colors = ['#00ff00', '#00cc00', '#009900', '#006600']
        if step < 30:
            # Calculate current dimensions
            size = 10 + (step * 13)
            x1 = (400 - size) // 2
            y1 = (400 - size) // 2
            x2 = x1 + size
            y2 = y1 + size
            
            # Update border
            canvas.coords(border, x1, y1, x2, y2)
            canvas.itemconfig(border, outline=colors[step % len(colors)])
            
            panel.update()
            canvas.after(30, lambda: animate_border(step+1))
        else:
            if canvas.winfo_exists():
                canvas.destroy()
    
    animate_border(0)

def animate_failure(panel):
    """Add a failure animation to the image panel"""
    canvas = Canvas(panel, bg=panel_color, highlightthickness=0)
    canvas.place(relx=0.5, rely=0.5, anchor='center', width=400, height=400)
    
    # Create an X that will animate
    x_line1 = canvas.create_line(0, 0, 0, 0, fill='red', width=5)
    x_line2 = canvas.create_line(0, 0, 0, 0, fill='red', width=5)
    
    def animate_x(step):
        if not canvas.winfo_exists():
            return
            
        if step < 20:
            # Calculate current dimensions
            size = step * 20
            x1 = (400 - size) // 2
            y1 = (400 - size) // 2
            x2 = x1 + size
            y2 = y1 + size
            
            # Update X lines
            canvas.coords(x_line1, x1, y1, x2, y2)
            canvas.coords(x_line2, x2, y1, x1, y2)
            
            panel.update()
            canvas.after(30, lambda: animate_x(step+1))
        else:
            if canvas.winfo_exists():
                canvas.destroy()
    
    animate_x(0)

# Function to select dataset folder
def select_dataset_folder():
    global dataset_base_path
    dataset_base_path = filedialog.askdirectory(title="Select Currency Data Folder")
    if dataset_base_path:
        folder_label.config(text=f"Selected: {os.path.basename(dataset_base_path)}")
        # Animate the label change
        def animate_label(i=10):
            if i > 0 and folder_label.winfo_exists():
                folder_label.config(font=("Arial", 12 + i))
                folder_label.update()
                folder_label.after(30, lambda: animate_label(i-1))
            else:
                folder_label.config(font=("Arial", 12))
        animate_label()

# Currency types and numbers
currency_types = ["EGP", "USD"]
currency_numbers = ["1", "5", "10", "20", "50", "100", "200"]

# Feature matching function
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

        # Use BFMatcher with knnMatch
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(des1, des2, k=2)

        # Lowe's Ratio Test
        good_matches = [m for m, n in matches if m.distance < 0.7 * n.distance]

        if len(good_matches) > 5:  # Threshold: At least 5 matching keypoints
            matched_features += 1

    return matched_features, total_features

# Currency feature search
def search_for_currency_features(front_image_path, back_image_path, selected_currency, selected_number):
    front_folder = os.path.join(dataset_base_path, selected_currency, selected_number, "front")
    back_folder = os.path.join(dataset_base_path, selected_currency, selected_number, "back")

    if not os.path.exists(front_folder) or not os.path.exists(back_folder):
        return f"❌ FAKE Currency ({selected_currency} {selected_number}) - Feature folders missing!"

    front_img = cv2.imread(front_image_path, cv2.IMREAD_GRAYSCALE)
    back_img = cv2.imread(back_image_path, cv2.IMREAD_GRAYSCALE)

    if front_img is None or back_img is None:
        return "❌ Error: Unable to read images."

    front_features = os.listdir(front_folder)
    back_features = os.listdir(back_folder)

    if not front_features or not back_features:
        return f"❌ FAKE Currency ({selected_currency} {selected_number}) - Features missing!"

    front_matched, total_front = match_features(front_img, front_folder, front_features)
    back_matched, total_back = match_features(back_img, back_folder, back_features)

    if front_matched < total_front or back_matched < total_back:
        return f"❌ FAKE Currency ({selected_currency} {selected_number}) - {front_matched}/{total_front} front, {back_matched}/{total_back} back."

    return f"✅ REAL Currency ({selected_currency} {selected_number}) - All features detected."

# GUI Functions
def upload_front_image():
    global front_image_path
    front_image_path = filedialog.askopenfilename()
    if front_image_path:
        # Clear previous image
        front_panel.config(image='')
        front_panel.image = None
        
        # Animate the button
        original_color = front_btn.cget("bg")
        def button_animation(i=0):
            if i < 5 and front_btn.winfo_exists():
                front_btn.config(bg=highlight_color if i % 2 == 0 else original_color)
                front_btn.update()
                front_btn.after(50, lambda: button_animation(i+1))
        
        button_animation()
        
        # Show loading animation
        loading_label = Label(front_panel, text="Loading...", font=("Arial", 16), bg=panel_color, fg=text_color)
        loading_label.place(relx=0.5, rely=0.5, anchor='center')
        front_panel.update()
        
        # Animate image appearance
        animate_image_appearance(front_panel, front_image_path)
        
        # Remove loading label
        loading_label.destroy()
        
        check_ready()

def upload_back_image():
    global back_image_path
    back_image_path = filedialog.askopenfilename()
    if back_image_path:
        # Clear previous image
        back_panel.config(image='')
        back_panel.image = None
        
        # Animate the button
        original_color = back_btn.cget("bg")
        def button_animation(i=0):
            if i < 5 and back_btn.winfo_exists():
                back_btn.config(bg=highlight_color if i % 2 == 0 else original_color)
                back_btn.update()
                back_btn.after(50, lambda: button_animation(i+1))
        
        button_animation()
        
        # Show loading animation
        loading_label = Label(back_panel, text="Loading...", font=("Arial", 16), bg=panel_color, fg=text_color)
        loading_label.place(relx=0.5, rely=0.5, anchor='center')
        back_panel.update()
        
        # Animate image appearance
        animate_image_appearance(back_panel, back_image_path)
        
        # Remove loading label
        loading_label.destroy()
        
        check_ready()

def display_image(image_path, panel):
    img = Image.open(image_path)
    img.thumbnail((400, 400))
    img = ImageTk.PhotoImage(img)
    panel.config(image=img)
    panel.image = img

def check_ready():
    if front_image_path and back_image_path and classify_button.winfo_exists():
        classify_button.config(state="normal")
        pulse_button(classify_button, button_color, "#5a8fc5")

def classify_image():
    selected_currency = currency_var.get()
    selected_number = currency_number_var.get()

    if not selected_currency:
        result_label.config(text="Error: Please select currency type!")
        return

    if not selected_number:
        result_label.config(text="Error: Please select currency number!")
        return

    # Animate the button press
    original_color = classify_button.cget("bg")
    def button_animation(i=0):
        if i < 5 and classify_button.winfo_exists():
            classify_button.config(bg=highlight_color if i % 2 == 0 else original_color)
            classify_button.update()
            classify_button.after(50, lambda: button_animation(i+1))
    
    button_animation()
    
    # Show processing animation
    processing_label = Label(result_label.master, text="Processing...", font=("Arial", 12), bg=panel_color, fg=text_color)
    processing_label.pack(pady=10)
    result_label.config(text="")
    
    # Simulate processing delay
    def update_processing(i=1):
        if i < 4 and processing_label.winfo_exists():
            processing_label.config(text=f"Processing{' .' * i}")
            processing_label.update()
            processing_label.after(300, lambda: update_processing(i+1))
        else:
            if processing_label.winfo_exists():
                processing_label.destroy()
            show_result()
    
    def show_result():
        result = search_for_currency_features(front_image_path, back_image_path, selected_currency, selected_number)
        
        # Animate result appearance
        result_label.config(text="")
        result_label.update()
        
        # Typewriter effect for result
        full_text = f"Result: {result}"
        def typewriter(i=0):
            if i <= len(full_text) and result_label.winfo_exists():
                result_label.config(text=full_text[:i])
                result_label.update()
                result_label.after(30, lambda: typewriter(i+1))
            else:
                # Add appropriate animation to image panels based on result
                if "REAL" in result:
                    animate_success(front_panel)
                    animate_success(back_panel)
                else:
                    animate_failure(front_panel)
                    animate_failure(back_panel)
        
        typewriter()
    
    update_processing()

def show_user_guide():
    guide_window = Toplevel(root)
    guide_window.title("User Guide")
    guide_window.geometry("450x300")
    guide_window.configure(bg=panel_color)
    guide_window.attributes('-alpha', 0)
    
    guide_text = """Welcome to the Currency Feature Recognition System!
    
    1- Click "Select Currency Data Folder" to choose the dataset.
    2- Click "Upload Front Image" to select an image of the front side.
    3- Click "Upload Back Image" to select an image of the back side.
    4- Select the currency type from the dropdown list.
    5- Select the currency number from the dropdown list.
    6- Click "Check Real/Fake" to analyze the currency.
    
    ✅ If all security features match, the currency is REAL.
    ❌ If any security feature is missing, the currency is FAKE.
    """

    text_box = Text(guide_window, wrap="word", font=("Arial", 12), height=12, width=55, 
                   bg=panel_color, fg=text_color, bd=0)
    text_box.insert("1.0", guide_text)
    text_box.config(state=DISABLED)
    text_box.pack(pady=10)

    close_btn = Button(guide_window, text="Close", command=guide_window.destroy, 
           font=button_font, bg=button_color, fg="white", activebackground=highlight_color)
    close_btn.pack()
    
    # Animate window appearance
    def fade_in(i=0):
        if i <= 100 and guide_window.winfo_exists():
            alpha = i/100
            guide_window.attributes('-alpha', alpha)
            guide_window.update()
            guide_window.after(15, lambda: fade_in(i+5))
    
    fade_in()

# Create Main GUI
root = tk.Tk()
root.title("Currency Feature Search")
root.geometry("1200x700")
root.configure(bg=bg_color)

# Set window to fade in on startup
root.attributes('-alpha', 0)

# Custom fonts
title_font = font.Font(family="Arial", size=18, weight="bold")
label_font = font.Font(family="Arial", size=12)
button_font = font.Font(family="Arial", size=12, weight="bold")

# Main container
main_frame = Frame(root, bg=bg_color)
main_frame.pack(fill='both', expand=True, padx=20, pady=20)

# Left panel (image display)
left_frame = Frame(main_frame, bg=panel_color, bd=2, relief='solid')
left_frame.pack(side='left', fill='both', expand=True, padx=(0, 20), pady=10)

# Front image panel
front_frame = Frame(left_frame, bg=panel_color)
front_frame.pack(fill='both', expand=True, pady=(0, 10))
Label(front_frame, text="Front Image", font=label_font, bg=panel_color, fg=text_color).pack()
front_panel = Label(front_frame, bg=panel_color)
front_panel.pack()

# Back image panel
back_frame = Frame(left_frame, bg=panel_color)
back_frame.pack(fill='both', expand=True, pady=(10, 0))
Label(back_frame, text="Back Image", font=label_font, bg=panel_color, fg=text_color).pack()
back_panel = Label(back_frame, bg=panel_color)
back_panel.pack()

# Right panel (controls)
right_frame = Frame(main_frame, bg=panel_color, bd=2, relief='solid', width=400)
right_frame.pack(side='right', fill='y', padx=(0, 0), pady=10)
right_frame.pack_propagate(False)

# Title
Label(right_frame, text="Currency Recognition", font=title_font, 
      bg=panel_color, fg=text_color).pack(pady=(20, 10))

# Folder selection
folder_btn = Button(right_frame, text="Select Dataset Folder", command=select_dataset_folder,
       font=button_font, bg=button_color, fg="white", activebackground=highlight_color)
folder_btn.pack(fill='x', pady=5)
folder_label = Label(right_frame, text="No folder selected", font=label_font, 
                     bg=panel_color, fg=text_color)
folder_label.pack()

# Upload buttons
front_btn = Button(right_frame, text="Upload Front Image", command=upload_front_image,
       font=button_font, bg=button_color, fg="white", activebackground=highlight_color)
front_btn.pack(fill='x', pady=5)
back_btn = Button(right_frame, text="Upload Back Image", command=upload_back_image,
       font=button_font, bg=button_color, fg="white", activebackground=highlight_color)
back_btn.pack(fill='x', pady=5)

# Currency selection
Label(right_frame, text="Currency Type:", font=label_font, 
      bg=panel_color, fg=text_color).pack(pady=(10, 0))
currency_var = StringVar(root)
currency_var.set(currency_types[0])
OptionMenu(right_frame, currency_var, *currency_types).pack(fill='x')

Label(right_frame, text="Currency Number:", font=label_font, 
      bg=panel_color, fg=text_color).pack(pady=(10, 0))
currency_number_var = StringVar(root)
currency_number_var.set(currency_numbers[0])
OptionMenu(right_frame, currency_number_var, *currency_numbers).pack(fill='x')

# Separator
separator = Frame(right_frame, height=2, bg=separator_color)
separator.pack(fill='x', pady=20)

# Classify button
classify_button = Button(right_frame, text="Check Real/Fake", command=classify_image, 
                         state="disabled", font=button_font, bg=button_color, 
                         fg="white", activebackground=highlight_color)
classify_button.pack(fill='x', pady=5)

# Result label
result_label = Label(right_frame, text="", font=label_font, 
                     bg=panel_color, fg=text_color, wraplength=380)
result_label.pack(pady=10)

# User Guide button
guide_btn = Button(right_frame, text="User Guide", command=show_user_guide,
       font=button_font, bg=button_color, fg="white", activebackground=highlight_color)
guide_btn.pack(fill='x', pady=5)

# Initialize global variables
front_image_path = ""
back_image_path = ""

# Add subtle pulsing animation to buttons
pulse_button(folder_btn, button_color, "#000819")
pulse_button(front_btn, button_color, "#000819")
pulse_button(back_btn, button_color, "#000819")
pulse_button(guide_btn, button_color, "#000819")

# Fade in the main window
def fade_in_main(i=0):
    if i <= 100 and root.winfo_exists():
        alpha = i/100
        root.attributes('-alpha', alpha)
        root.update()
        root.after(15, lambda: fade_in_main(i+5))

fade_in_main()

# Clean up animations when window closes
def on_closing():
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()