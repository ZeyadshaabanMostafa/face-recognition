import cv2
import os
import csv
import numpy as np
from tkinter import Tk, Canvas, Button, Label, filedialog, Toplevel, Text, Scrollbar, Frame, font
from PIL import Image, ImageTk, ImageDraw
import face_recognition
import time

# Function to search for CSV files
def find_csv_files(directory):
    non_criminal_file = None
    criminal_file = None
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith('.csv'):
                if 'non-criminal' in filename.lower():
                    non_criminal_file = os.path.join(root, filename)
                elif 'criminal' in filename.lower():
                    criminal_file = os.path.join(root, filename)
    return non_criminal_file, criminal_file

# Load face encodings from CSV
def load_encodings_from_csv(file_path):
    encodings = []
    names = []
    data = []
    try:
        with open(file_path, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for row in reader:
                name = row[0]
                encoding = np.array([float(val) for val in row[1].split(',')])
                encodings.append(encoding)
                names.append(name)
                data.append(row)
    except Exception as e:
        print(f"Error loading encodings: {e}")
    return encodings, names, data

# User Guide Window
def show_user_guide():
    guide_window = Toplevel()
    guide_window.title("User Guide")
    guide_window.geometry("600x400")
    guide_window.configure(bg='#2d2d2d')  # Dark background
    
    guide_text = Text(guide_window, wrap="word", height=20, width=70, 
                     font=("Arial", 11), bg='#2d2d2d', fg='white', bd=0)
    guide_text.insert("1.0", 
                     "Welcome to the Face Recognition System\n\n"
                     "1. Upload an image by clicking on 'Upload' button.\n"
                     "2. The system will detect faces and match them.\n"
                     "3. Criminal details will be displayed if matched.\n"
                     "4. Click 'Clear' to reset the interface.\n\n"
                     "Note: Ensure CSV files are available on your Desktop.")
    guide_text.config(state="disabled")
    
    scrollbar = Scrollbar(guide_window, command=guide_text.yview)
    scrollbar.pack(side="right", fill="y")
    guide_text.config(yscrollcommand=scrollbar.set)
    guide_text.pack(padx=20, pady=20)

class FaceRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition System")
        self.root.geometry("1200x700")
        
        # Dark mode color scheme
        self.bg_color = "#000206"      # Dark background
        self.panel_color = "#00040c"   # Darker panels
        self.text_color = "white"      # White text
        self.button_color = "#000819"  # Blue buttons
        self.highlight_color = "#3a5a80"  # Darker blue for hover
        self.separator_color = "#555555"  # Dark separator
        
        self.root.config(bg=self.bg_color)
        self.root.resizable(False, False)

        # Custom fonts
        self.title_font = font.Font(family="Arial", size=18, weight="bold")
        self.label_font = font.Font(family="Arial", size=12)
        self.button_font = font.Font(family="Arial", size=12, weight="bold")

        # Main container
        self.main_frame = Frame(root, bg=self.bg_color)
        self.main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Setup UI components
        self.setup_ui()
        
        # Load face data
        self.load_face_data()
    
    def setup_ui(self):
        # Left panel (image display)
        self.left_frame = Frame(self.main_frame, bg=self.panel_color, bd=2, relief='solid')
        self.left_frame.pack(side='left', fill='both', expand=True, padx=(0, 20), pady=10)

        # Canvas for image
        self.canvas = Canvas(self.left_frame, bg=self.panel_color, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True, padx=10, pady=10)

        # Right panel (information)
        self.right_frame = Frame(self.main_frame, bg=self.panel_color, bd=2, relief='solid', width=400)
        self.right_frame.pack(side='right', fill='y', padx=(0, 0), pady=10)
        self.right_frame.pack_propagate(False)  # Keep fixed width

        # Information header
        info_header = Label(self.right_frame, text="Result", font=self.title_font, 
                          bg=self.panel_color, fg=self.text_color)
        info_header.pack(pady=(20, 10), anchor='w')

        # Information labels - stored in a list to manage them easily
        self.info_labels = [
            Label(self.right_frame, text="Name :", font=self.label_font, 
                 bg=self.panel_color, fg=self.text_color, anchor='w'),
            Label(self.right_frame, text="Status :", font=self.label_font, 
                 bg=self.panel_color, fg=self.text_color, anchor='w'),
            Label(self.right_frame, text="Age :", font=self.label_font, 
                 bg=self.panel_color, fg=self.text_color, anchor='w'),
            Label(self.right_frame, text="Crime :", font=self.label_font, 
                 bg=self.panel_color, fg=self.text_color, anchor='w'),
            Label(self.right_frame, text="Last Crime Date :", font=self.label_font, 
                 bg=self.panel_color, fg=self.text_color, anchor='w'),
            Label(self.right_frame, text="Possibility Of Committing Crime :", 
                 font=self.label_font, bg=self.panel_color, fg=self.text_color, anchor='w'),
            Label(self.right_frame, text="Case Number :", font=self.label_font, 
                 bg=self.panel_color, fg=self.text_color, anchor='w')
        ]

        # Pack all labels (they will always remain visible)
        for label in self.info_labels:
            label.pack(fill='x', padx=20, pady=(5, 0), anchor='w')

        # Separator
        separator = Frame(self.right_frame, height=2, bg=self.separator_color)
        separator.pack(fill='x', pady=20, padx=20)

        # Button frame
        button_frame = Frame(self.right_frame, bg=self.panel_color)
        button_frame.pack(pady=10)

        # Buttons (Upload, Clear, User Guide)
        button_style = {
            'font': self.button_font,
            'bg': self.button_color,
            'fg': "white",
            'activebackground': self.highlight_color,
            'width': 10,
            'height': 1,
            'bd': 0,
            'highlightthickness': 0,
            'relief': 'flat'
        }

        self.upload_button = Button(button_frame, text="Upload", 
                                   command=self.upload_image, **button_style)
        self.clear_button = Button(button_frame, text="Clear", 
                                  command=self.clear_image, **button_style)
        self.user_guide_button = Button(button_frame, text="User Guide", 
                                       command=show_user_guide, **button_style)

        # Pack buttons with animations
        buttons = [self.upload_button, self.clear_button, self.user_guide_button]
        for button in buttons:
            button.pack(pady=5, fill='x')
            # Add hover effects
            button.bind("<Enter>", lambda e, b=button: b.config(bg=self.highlight_color))
            button.bind("<Leave>", lambda e, b=button: b.config(bg=self.button_color))
            # Add click animation
            button.bind("<Button-1>", lambda e, b=button: self.animate_button_click(b))

    def animate_button_click(self, button):
        # Button click animation
        orig_color = button.cget("bg")
        button.config(bg="#2a4a70")  # Darker blue when clicked
        self.root.update()
        self.root.after(100, lambda: button.config(bg=orig_color))

    def load_face_data(self):
        # Load face encodings
        non_criminal_file, criminal_file = find_csv_files(os.path.expanduser("~"))
        if non_criminal_file and criminal_file:
            self.known_face_encodings, self.known_face_names, self.known_data = load_encodings_from_csv(non_criminal_file)
            self.criminal_face_encodings, self.criminal_face_names, self.criminal_data = load_encodings_from_csv(criminal_file)
        else:
            print("CSV files not found. Please ensure both files exist.")

    def upload_image(self):
        # File dialog to select image
        image_path = filedialog.askopenfilename(title="Select an image", 
                                              filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
        if image_path:
            # Show loading animation
            self.show_loading_animation()
            # Process after a short delay to allow animation to show
            self.root.after(100, lambda: self.process_and_display_image(image_path))

    def show_loading_animation(self):
        # Create loading animation
        if hasattr(self, 'loading_id'):
            self.canvas.delete(self.loading_id)
            
        loading_img = Image.new('RGB', (500, 500), (60, 60, 60))  # Dark loading background
        self.loading_draw = ImageDraw.Draw(loading_img)
        self.loading_tk = ImageTk.PhotoImage(loading_img)
        self.loading_id = self.canvas.create_image(0, 0, anchor="nw", image=self.loading_tk)
        self.canvas.image = self.loading_tk
        self.loading_angle = 0
        self.animate_loading()

    def animate_loading(self):
        # Animate loading spinner
        if hasattr(self, 'loading_id'):
            loading_img = Image.new('RGB', (500, 500), (60, 60, 60))  # Dark loading background
            draw = ImageDraw.Draw(loading_img)
            draw.arc([(100, 100), (400, 400)], self.loading_angle, self.loading_angle+270, 
                    fill=self.button_color, width=10)
            self.loading_tk = ImageTk.PhotoImage(loading_img)
            self.canvas.itemconfig(self.loading_id, image=self.loading_tk)
            self.canvas.image = self.loading_tk
            self.loading_angle = (self.loading_angle + 20) % 360
            self.root.after(50, self.animate_loading)

    def process_and_display_image(self, image_path):
        try:
            # Process the selected image
            img = cv2.imread(image_path)
            if img is None:
                return

            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_width, img_height = img_pil.size

            # Remove loading animation if it exists
            if hasattr(self, 'loading_id'):
                self.canvas.delete(self.loading_id)
                del self.loading_id

            # Fade in the image
            self.fade_in_image(img_pil)

            # Face recognition
            face_locations = face_recognition.face_locations(img_rgb)
            face_encodings = face_recognition.face_encodings(img_rgb, face_locations)

            if not face_encodings:
                self.animate_text_change(self.info_labels[0], "Name : No faces detected")
                # Clear other fields
                for label in self.info_labels[1:]:
                    label.config(text=label.cget("text").split(':')[0] + " :")
                return

            for face_encoding in face_encodings:
                self.process_face(face_encoding)
        except Exception as e:
            print(f"Error processing image: {e}")

    def fade_in_image(self, img_pil):
        # Fade in image animation
        for alpha in np.linspace(0, 1, 10):
            blended = Image.blend(Image.new('RGB', img_pil.size, (60, 60, 60)), img_pil, alpha)  # Dark blend
            img_tk = ImageTk.PhotoImage(blended)
            self.canvas.create_image(0, 0, anchor="nw", image=img_tk)
            self.canvas.image = img_tk
            self.root.update()
            time.sleep(0.03)

        # Set final image
        img_tk = ImageTk.PhotoImage(img_pil)
        self.canvas.create_image(0, 0, anchor="nw", image=img_tk)
        self.canvas.image = img_tk
        self.canvas.config(width=img_pil.width, height=img_pil.height)

    def clear_image(self):
        # Clear the canvas and reset labels
        self.canvas.delete("all")
        for label in self.info_labels:
            label.config(text=label.cget("text").split(':')[0] + " :")

    def animate_text_change(self, label, new_text):
        try:
            # Animate text change
            current_text = label.cget("text")
            # Erase current text
            for i in range(len(current_text), -1, -1):
                if not label.winfo_exists():  # Check if label still exists
                    return
                label.config(text=current_text[:i])
                self.root.update()
                time.sleep(0.02)
            # Type new text
            for i in range(1, len(new_text)+1):
                if not label.winfo_exists():  # Check if label still exists
                    return
                label.config(text=new_text[:i])
                self.root.update()
                time.sleep(0.02)
        except Exception as e:
            print(f"Error animating text: {e}")

    def process_face(self, face_encoding):
        threshold = 0.55
        
        # First check criminal matches
        criminal_distances = face_recognition.face_distance(self.criminal_face_encodings, face_encoding)
        best_criminal_idx = np.argmin(criminal_distances)
        best_criminal_dist = criminal_distances[best_criminal_idx]

        if best_criminal_dist < threshold:
            # Criminal match found - show all details
            name = f"{self.criminal_face_names[best_criminal_idx]} (Criminal)"
            self.animate_text_change(self.info_labels[0], f"Name : {name}")
            
            data = self.criminal_data[best_criminal_idx]
            self.animate_text_change(self.info_labels[1], f"Status : {data[2]}")
            self.animate_text_change(self.info_labels[2], f"Age : {data[3]}")
            self.animate_text_change(self.info_labels[3], f"Crime : {data[4]}")
            self.animate_text_change(self.info_labels[4], f"Last Crime Date : {data[6]}")
            self.animate_text_change(self.info_labels[5], 
                                   f"Possibility Of Committing Crime : {data[7]}")
            self.animate_text_change(self.info_labels[6], f"Case Number : {data[8]}")
            return

        # If not criminal, check non-criminal matches
        known_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
        best_known_idx = np.argmin(known_distances)
        best_known_dist = known_distances[best_known_idx]

        if best_known_dist < threshold:
            name = f"{self.known_face_names[best_known_idx]} (Not Criminal)"
            self.animate_text_change(self.info_labels[0], f"Name : {name}")
            self.animate_text_change(self.info_labels[1], f"Status : {self.known_data[best_known_idx][2]}")
            
            # For non-criminals, show empty fields but keep labels visible
            self.animate_text_change(self.info_labels[2], "Age : ")
            self.animate_text_change(self.info_labels[3], "Crime : ")
            self.animate_text_change(self.info_labels[4], "Last Crime Date : ")
            self.animate_text_change(self.info_labels[5], "Possibility Of Committing Crime : ")
            self.animate_text_change(self.info_labels[6], "Case Number : ")
        else:
            self.animate_text_change(self.info_labels[0], "Name : Unknown Person")
            self.animate_text_change(self.info_labels[1], "Status : Unknown")
            
            # For unknown persons, show empty fields but keep labels visible
            self.animate_text_change(self.info_labels[2], "Age : ")
            self.animate_text_change(self.info_labels[3], "Crime : ")
            self.animate_text_change(self.info_labels[4], "Last Crime Date : ")
            self.animate_text_change(self.info_labels[5], "Possibility Of Committing Crime : ")
            self.animate_text_change(self.info_labels[6], "Case Number : ")

if __name__ == "__main__":
    root = Tk()
    app = FaceRecognitionApp(root)
    root.mainloop()