import os
import sys
import subprocess
try:
    from importlib.metadata import distributions
    installed = {dist.metadata['Name'].lower() for dist in distributions()}
except ImportError:
    import pkg_resources
    installed = {pkg.key for pkg in pkg_resources.working_set}

# Check and install required packages
required = {'pyautogui', 'requests', 'Pillow'}
missing = required - installed

if missing:
    python = sys.executable
    subprocess.check_call([python, '-m', 'pip', 'install', 'setuptools', *missing], stdout=subprocess.DEVNULL)

# Now try to import tkinter
try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:
    print("Tkinter is not installed. Please install Python with tkinter support.")
    print("On Windows: Modify your Python installation to include tkinter")
    print("On Linux: sudo apt-get install python3-tk")
    print("On Mac: brew install python-tk")
    sys.exit(1)

import time
import pyautogui
import io
import requests
import base64

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("Astro AI")
        self.pack(expand=True, fill="both")
        self.configure(bg='black')

        # Configure the server URL
        self.SERVER_URL = "https://aron.danielv.no/process-image"

        # Create and configure the main window
        self.create_title_bar()  # Add this line
        self.create_widgets()
        self.configure_window()

        style = ttk.Style()
        style.configure("TFrame", background="black")
        style.configure("TLabel", background="black", foreground="white")
        style.configure("TButton", background="black", foreground="white")

    def create_title_bar(self):
        # Create custom title bar
        self.title_bar = tk.Frame(self, bg='black', relief='raised', bd=2)
        self.title_bar.pack(fill=tk.X)

        # Add title label
        self.title_label = tk.Label(self.title_bar, text="Astro AI", 
                                  bg='black', fg='white')
        self.title_label.pack(side=tk.LEFT, padx=10)

        # Add close button
        self.close_button = tk.Button(self.title_bar, text='X', 
                                    command=self.master.destroy, 
                                    bg='black', fg='white', relief='flat')
        self.close_button.pack(side=tk.RIGHT, padx=5)

        # Bind moving window to title bar
        self.title_bar.bind('<B1-Motion>', self.move_window)

    def move_window(self, event):
        self.master.geometry(f'+{event.x_root}+{event.y_root}')

    def create_widgets(self):
        # Create main frame using ttk
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(expand=True, fill="both")
        
        # Create output frame
        self.output_frame = ttk.Frame(self.main_frame)
        self.output_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Create output label
        self.output_label = ttk.Label(
            self.output_frame,
            wraplength=400,
            justify="left"
        )
        self.output_label.pack(expand=True, fill="both")

        # Create button frame
        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Create screenshot button
        self.screenshot_button = ttk.Button(
            self.button_frame,
            text="Take Screenshot",
            command=self.take_screenshot
        )
        self.screenshot_button.pack()

    def configure_window(self):
        self.master.attributes('-topmost', True)
        self.master.configure(bg='black')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def update_output_text(self, text):
        self.output_label.config(text=text)
        self.master.update_idletasks()
        
        # Get the required height and width for the text
        text_height = self.output_label.winfo_reqheight()
        text_width = self.output_label.winfo_reqwidth()
        
        # Add padding for the window and ensure space for the button
        window_height = min(text_height + 200, 1000)  # Maximum height of 800 pixels
        window_width = min(max(300, text_width + 40), 1000)  # Maximum width of 1000 pixels
        
        # Set the new window size
        self.master.geometry(f"{window_width}x{window_height}")

        # Ensure the button stays visible by adjusting the height
        button_height = self.button_frame.winfo_height()
        if window_height < button_height + 50:  # Add some extra space
            window_height = button_height + 50
            self.master.geometry(f"{window_width}x{window_height}")

    def take_screenshot(self):
        # Clear previous output
        self.update_output_text("")
        # Directly call capture_screenshot without hiding the window
        self.master.after(1, self.capture_screenshot)
    
    def validate_output(self, output):
        # Basic validation of AI response
        if not output or len(output) < 10:
            return False
        return True

    def capture_screenshot(self):
        try:
            # Take screenshot
            image = pyautogui.screenshot()
            
            # Convert image to base64
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()
            img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')
            
            # Make window visible again
            self.master.attributes('-alpha', 1.0)
            
            # Send to server
            try:
                response = requests.post(
                    self.SERVER_URL,
                    json={'image': img_base64},
                    timeout=30  # 30 seconds timeout
                )
                
                if response.status_code == 200:
                    result = response.json()['response']
                    if self.validate_output(result):
                        self.update_output_text(result)
                    else:
                        self.update_output_text("Error: Invalid output from AI.")
                else:
                    self.update_output_text(
                        f"Error: Server returned status {response.status_code}\n"
                        f"Message: {response.text}"
                    )
                    
            except requests.exceptions.ConnectionError:
                self.update_output_text(
                    "Error: Could not connect to server.\n"
                    "Please make sure the server is running."
                )
            except requests.exceptions.Timeout:
                self.update_output_text(
                    "Error: Request timed out.\n"
                    "Server took too long to respond."
                )
            except requests.exceptions.RequestException as e:
                self.update_output_text(
                    f"Error making request:\n{str(e)}"
                )
                
        except Exception as e:
            print(f"Error: {e}")
            self.update_output_text(
                f"Error processing screenshot:\n{str(e)}"
            )
        finally:
            # Ensure window is visible in case of any errors
            self.master.attributes('-alpha', 1.0)

    def copy_to_clipboard(self):
        # Copy output text to clipboard
        text = self.output_label.cget("text")
        self.clipboard_clear()
        self.clipboard_append(text)

def approach_2():
    root = tk.Tk()
    root.configure(bg='black')
    root.geometry("300x250")
    root.overrideredirect(True)  

    style = ttk.Style()
    style.theme_use('clam')  # Use 'clam' theme as base
    
    # Configure colors for various widget states
    style.configure('TFrame', background='black')
    style.configure('TLabel', background='black', foreground='white')
    style.configure('TButton', 
                    background='black', 
                    foreground='white', 
                    bordercolor='white',
                    lightcolor='white',
                    darkcolor='white')
    style.map('TButton',
              background=[('active', '#333333')],
              foreground=[('active', 'white')])
    
    app = Application(master=root)
    app.mainloop()

if __name__ == "__main__":
    try:
        approach_2()
    except Exception as e:
        print(f"Fatal error: {e}")
        input("Press Enter to exit...")
