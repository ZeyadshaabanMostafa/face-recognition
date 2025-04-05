import cv2
import os
import csv
import numpy as np
from tkinter import Tk, Canvas, Button, Label, filedialog, Toplevel, Text, Scrollbar
from PIL import Image, ImageTk
import face_recognition

# Function to search for CSV files in any directory
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

# Load face encodings from CSV (average encoding per person)
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

# Function to create the User Guide window
def show_user_guide():
    guide_window = Toplevel()
    guide_window.title("User Guide")
    guide_window.geometry("600x400")

    # Create a Text widget to display the guide
    guide_text = Text(guide_window, wrap="word", height=20, width=70)
    guide_text.insert("1.0", 
                      "Welcome to the Face Recognition System\n\n"
                      "1. Upload an image by clicking on 'Upload Image' button.\n"
                      "2. The system will detect faces and try to match them with known persons.\n"
                      "3. If a match is found with a criminal, the details will be displayed.\n"
                      "4. If the person is not a criminal, their name will be shown without criminal details.\n"
                      "5. Click 'Clear Image' to remove the current image and labels.\n\n"
                      "Note:**** Ensure the CSV files containing known faces and criminal data are available in your Desktop.****\n")
    guide_text.config(state="disabled")  # Make the text widget read-only

    # Create a scrollbar for the text widget
    scrollbar = Scrollbar(guide_window, command=guide_text.yview)
    scrollbar.pack(side="right", fill="y")
    guide_text.config(yscrollcommand=scrollbar.set)
    guide_text.pack(padx=10, pady=10)

# GUI App
class FaceRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition GUI")
        self.root.geometry("1000x600")
        self.root.config(bg='blue')
        self.root.resizable(True, True)

        # Layout
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Canvas for image
        self.canvas = Canvas(root, bg='gray')
        self.canvas.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        # Info labels
        self.info_frame = Canvas(root, bg='blue', width=400)
        self.info_frame.grid(row=0, column=1, padx=10, pady=10, sticky='n')

        self.name_label = Label(self.info_frame, text="Name: ", font=("Arial", 14), bg='blue', fg='white', anchor='w')
        self.status_label = Label(self.info_frame, text="Status: ", font=("Arial", 14), bg='blue', fg='white', anchor='w')
        self.age_label = Label(self.info_frame, text="Age: ", font=("Arial", 14), bg='blue', fg='white', anchor='w')
        self.crime_label = Label(self.info_frame, text="Crime: ", font=("Arial", 14), bg='blue', fg='white', anchor='w')
        self.crime_date_label = Label(self.info_frame, text="Last Crime Date: ", font=("Arial", 14), bg='blue', fg='white', anchor='w')
        self.possibility_label = Label(self.info_frame, text="Possibility of Committing Crime: ", font=("Arial", 14), bg='blue', fg='white', anchor='w')
        self.case_number_label = Label(self.info_frame, text="Case Number: ", font=("Arial", 14), bg='blue', fg='white', anchor='w')

        for label in [self.name_label, self.status_label, self.age_label, self.crime_label,
                      self.crime_date_label, self.possibility_label, self.case_number_label]:
            label.pack(fill="x", pady=(5, 0))

        # Buttons
        self.upload_button = Button(root, text="Upload Image", font=("Arial", 14), command=self.upload_image, bg='white', fg='blue')
        self.clear_button = Button(root, text="Clear Image", font=("Arial", 14), command=self.clear_image, bg='white', fg='blue')
        self.user_guide_button = Button(root, text="User Guide", font=("Arial", 14), command=show_user_guide, bg='white', fg='blue')

        self.upload_button.grid(row=1, column=0, pady=5, sticky='ew')
        self.clear_button.grid(row=2, column=0, pady=5, sticky='ew')
        self.user_guide_button.grid(row=3, column=0, pady=5, sticky='ew')

        # Find and load Encodings from CSV files
        non_criminal_file, criminal_file = find_csv_files(os.path.expanduser("~"))
        if non_criminal_file and criminal_file:
            self.known_face_encodings, self.known_face_names, self.known_data = load_encodings_from_csv(non_criminal_file)
            self.criminal_face_encodings, self.criminal_face_names, self.criminal_data = load_encodings_from_csv(criminal_file)
        else:
            print("CSV files not found. Please ensure that both 'non-criminal' and 'criminal' CSV files exist.")

    def upload_image(self):
        image_path = filedialog.askopenfilename(title="Select an image", filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
        if image_path:
            self.process_and_display_image(image_path)

    def clear_image(self):
        self.canvas.delete("all")
        for label in [self.name_label, self.status_label, self.age_label, self.crime_label,
                      self.crime_date_label, self.possibility_label, self.case_number_label]:
            label.config(text=label.cget("text").split(':')[0] + ":")

    def hide_non_critical_labels(self):
        # Hide labels except Name and Status when person is not a criminal
        for label in [self.age_label, self.crime_label, self.crime_date_label, self.possibility_label, self.case_number_label]:
            label.pack_forget()

    def show_all_labels(self):
        # Show all labels when person is a criminal
        for label in [self.age_label, self.crime_label, self.crime_date_label, self.possibility_label, self.case_number_label]:
            label.pack(fill="x", pady=(5, 0))

    def process_and_display_image(self, image_path):
        img = cv2.imread(image_path)
        if img is None:
            return

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_width, img_height = img_pil.size
        self.canvas.config(width=img_width, height=img_height)
        img_tk = ImageTk.PhotoImage(img_pil)
        self.canvas.create_image(0, 0, anchor="nw", image=img_tk)
        self.canvas.image = img_tk

        face_locations = face_recognition.face_locations(img_rgb)
        face_encodings = face_recognition.face_encodings(img_rgb, face_locations)

        if not face_encodings:
            self.name_label.config(text="No faces detected.")
            return

        for face_encoding in face_encodings:
            name, status = "Unknown Person", "Unknown Status"
            threshold = 0.55

            # Check criminal matches
            criminal_distances = face_recognition.face_distance(self.criminal_face_encodings, face_encoding)
            best_criminal_idx = np.argmin(criminal_distances)
            best_criminal_dist = criminal_distances[best_criminal_idx]

            if best_criminal_dist < threshold:
                name = f"{self.criminal_face_names[best_criminal_idx]} (Criminal)"
                status = self.criminal_data[best_criminal_idx][2]  # Column C (index 2)

                data = self.criminal_data[best_criminal_idx]
                self.age_label.config(text="Age: " + data[3])  # Column D (index 3)
                self.crime_label.config(text="Crime: " + data[4])  # Column E (index 4)
                self.crime_date_label.config(text="Last Crime Date: " + data[6])  # Column G (index 6)
                self.possibility_label.config(text="Possibility of Committing Crime: " + data[7])  # Column H (index 7)
                self.case_number_label.config(text="Case Number: " + data[8])  # Column I (index 8)

                # Show all labels
                self.show_all_labels()

            else:
                known_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                best_known_idx = np.argmin(known_distances)
                best_known_dist = known_distances[best_known_idx]

                if best_known_dist < threshold:
                    name = f"{self.known_face_names[best_known_idx]} (Not Criminal)"
                    status = self.known_data[best_known_idx][2]  # Column C (index 2)

                    # Hide non-critical labels when the person is not a criminal
                    self.hide_non_critical_labels()

                else:
                    name = "Unknown Person"
                    status = "Unknown"
                    self.hide_non_critical_labels()

            self.name_label.config(text="Name: " + name)
            self.status_label.config(text="Status: " + status)

# Run GUI
if __name__ == "__main__":
    root = Tk()
    app = FaceRecognitionApp(root)
    show_user_guide()  # Show user guide window on start
    root.mainloop()
