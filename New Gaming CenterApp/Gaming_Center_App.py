import tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter import ttk
import customtkinter as ctk
from customtkinter import CTkImage
from CTkListbox import *
from pathlib import Path
from PIL import Image, ImageTk
import time
import requests
from io import BytesIO
# import cairosvg
import json
import os
import re
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate
import threading
import cProfile
from datetime import datetime, timedelta
from StatsCompiler import StatsWindow  # Import the StatsWindow class from StatsCompiler.py

# Configure customtkinter
ctk.set_appearance_mode("dark")  # Default to light mode
ctk.set_default_color_theme("./uvu_green.json")  # You can change this to other themes if desired

import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk

class CustomErrorBox(tk.Toplevel):
    def __init__(self, parent, title, message):
        super().__init__(parent)
        
        # Window setup
        self.title(title)
        self.configure(bg="#fff")
        self.resizable(False, False)
        
        # Make window modal
        self.transient(parent)
        self.grab_set()
        
        # Calculate position for center of screen
        window_width = 630
        window_height = 220
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        # Set initial window size and position
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Create main frame with grid
        main_frame = ctk.CTkFrame(self, fg_color="#fff")
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Configure grid columns and rows
        main_frame.grid_columnconfigure(1, weight=1)  # Text column expands
        main_frame.grid_rowconfigure(0, weight=1)     # Content row expands
        
        # Create left frame for GIF
        left_frame = ctk.CTkFrame(main_frame, fg_color="#fff")
        left_frame.grid(row=0, column=0, padx=(0, 20), sticky="n")
        
        # Create right frame for text
        right_frame = ctk.CTkFrame(main_frame, fg_color="#fff")
        right_frame.grid(row=0, column=1, sticky="nsew")
        main_frame.grid_rowconfigure(0, weight=1)  # Allow row to expand
        main_frame.grid_columnconfigure(1, weight=1)  # Allow column to expand
        
        # Create bottom frame for button
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="#edeeed")
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky="e", pady=(20, 0))
        
        # Load and animate GIF
        try:
            self.gif_path = "./icon_cache/finger_wag.gif"
            self.frames = []
            self.current_frame = 0
            
            # Load all frames of the GIF and resize them
            gif = Image.open(self.gif_path)
            # Set fixed size for the GIF
            desired_height = 100
            aspect_ratio = gif.width / gif.height
            new_width = int(desired_height * aspect_ratio)
            
            for frame in range(gif.n_frames):

                gif.seek(frame)
                resized_frame = gif.copy().resize((new_width, desired_height), Image.Resampling.LANCZOS)
                frame_image = ImageTk.PhotoImage(resized_frame)
                self.frames.append(frame_image)
            
            # Create label for GIF
            self.gif_label = tk.Label(left_frame, image=self.frames[0], bg="#fff")
            self.gif_label.pack(padx=10)
            
            # Start animation
            self.animate_gif()
            
        except Exception as e:
            print(f"Error loading GIF: {str(e)}")
        
        # Title message
        title_label = ctk.CTkLabel(
            right_frame,
            text="Please fill out the following fields:",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#000",
            justify="left"
        )
        title_label.pack(anchor="w")
        
        # Message (missing fields)
        message_label = ctk.CTkLabel(
            right_frame,
            text=message,
            font=ctk.CTkFont(size=14),
            text_color="#000",
            wraplength=250,
            justify="left"
        )
        message_label.pack(anchor="w", pady=(10, 0))
        
        # Calculate the required height based on the message length
        lines = message.count('\n') + 1
        additional_height = lines * 20  # Adjust this value based on your font size and line spacing
        new_window_height = window_height + additional_height
        
        # Set the new window size and position
        self.geometry(f'{window_width}x{new_window_height}+{center_x}+{center_y}')
        
        # OK Button
        ok_button = ctk.CTkButton(
            bottom_frame,
            text="OK",
            command=self.destroy,
            fg_color="#FF5252",
            hover_color="#FF7070",
            width=100,
            height=32
        )
        ok_button.pack(side="right")
        
        # Bind Enter and Escape to close the window
        self.bind("<Return>", lambda event: self.destroy())
        self.bind("<Escape>", lambda event: self.destroy())
        
        # Position the window and set focus
        self.focus_set()
        
    def animate_gif(self):
        """Handles GIF animation"""
        try:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.gif_label.configure(image=self.frames[self.current_frame])
            self.after(12, self.animate_gif)
        except Exception as e:
            print(f"Error animating GIF: {str(e)}")

def show_custom_error(parent, title, message):
    message = message.replace("Please fill out the following fields:\n", "")
    return CustomErrorBox(parent, title, message)



class TimerManager:
    def __init__(self):
        self.timers = []
        self.is_running = False

    def add_timer(self, timer):
        self.timers.append(timer)
        if not self.is_running:
            self.start()

    def start(self):
        self.is_running = True
        self.update_timers()

    def stop(self):
        self.is_running = False
        for timer in self.timers:
            timer.stop()  # Stop each timer

    def update_timers(self):
        if not self.is_running:
            return

        for timer in self.timers:
            timer.update()  # Call an update method on each timer

        # Schedule the next update
        self.after(1000, self.update_timers)  # Update every 1 second


class CombinedTimer(ctk.CTkCanvas):
    def __init__(self, parent, width=120, height=120):


        parent_fg = parent.cget("fg_color")

        if isinstance(parent_fg, str):
            parent_bg = parent_fg
        else:
            appearance_mode = ctk.get_appearance_mode()
            parent_bg = parent_fg[1] if appearance_mode == "Dark" else parent_fg[0]




        super().__init__(parent, width=width, height=height, highlightthickness=0, bg=parent_bg)
        self.width = width
        self.height = height
        self.time_limit = 30 * 60
        self.warning_threshold = 0.8 * self.time_limit
        self.warning_threshold2 = 0.9 * self.time_limit
        
        self.is_running = False
        self.start_time = 0
        self.elapsed_time = 0
        self.alert_shown = False
        self.last_progress = 0
        self._update_loop_id = None  # Store the ID of the update loop
        
        # Initialize fields as None
        self.name_entry = None
        self.id_entry = None
        self.game_dropdown = None
        self.controller_dropdown = None
        self.game_var = None
        self.controller_var = None
        self.station_type = None
        self.station_num = None
        
        # Create a frame to hold the timer label for better centering
        self.label_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.label_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        self.timer_label = ctk.CTkLabel(
            self.label_frame, 
            text="00:00:00", 
            font=ctk.CTkFont(family="Helvetica", size=16)
        )
        self.timer_label.pack(expand=True)
        
    def start(self):
        print("start method called")
        if not self.validate_fields():
            return
        if not self.is_running:
            self.is_running = True
            self.start_time = time.time() - self.elapsed_time
            self.update_timer()

    def stop(self):

        if self.is_running:

            self.is_running = False

            if self._update_loop_id:

                self.after_cancel(self._update_loop_id)  # Cancel the update loop

                self._update_loop_id = None  # Reset the loop ID

    def reset(self):
        if self.is_running or self.elapsed_time > 0:  # Only log if timer was actually used
            self.parent_station.log_usage()  # Log before resetting
        
        self.is_running = False
        self.elapsed_time = 0
        self.alert_shown = False
        self.timer_label.configure(text="00:00:00", text_color="white")
        self.draw_ring(0)
        
        # Clear fields after logging
        if self.name_entry:
            self.name_entry.delete(0, tk.END)
        if self.id_entry:
            self.id_entry.delete(0, tk.END)
        if self.game_var:
            self.game_var.set("")
        if self.controller_var:
            self.controller_var.set("")


    def get_time(self):
        if self.is_running:
            return time.time() - self.start_time
        return self.elapsed_time

    def check_time_limit(self):
        return self.get_time() >= self.time_limit

    def validate_fields(self):
        print("validate_fields called")
        missing_fields = []
        
        # Always check name and ID for all station types
        if not self.name_entry or not self.name_entry.get().strip():
            missing_fields.append("Name")
        # if not self.id_entry or not self.id_entry.get().strip():
        #     missing_fields.append("ID Number (Enter N/A if not applicable)")
        
        # Only check game and controller fields for console stations
        if self.station_type in ["XBOX", "Switch"]:
            if not self.game_var or not self.game_var.get():
                missing_fields.append("Game")
            if not self.controller_var or not self.controller_var.get():
                missing_fields.append("Controller")

        if missing_fields:
            error_message = f"Please fill out the following fields:\n" + "\n".join(missing_fields)
            show_custom_error(self.winfo_toplevel(), "Error", error_message)
            return False
        
        return True

    def draw_ring(self, progress):
        # Only update if progress has changed significantly
        if abs(progress - self.last_progress) <= 0.01:
            return  # Skip drawing if change is minimal

        self.delete("all")  # Clear the canvas

        # Calculate coordinates for the ring
        x0, y0, x1, y1 = 6, 6, self.width - 6, self.height - 6

        # Draw background ring
        self.create_oval(x0, y0, x1, y1, outline='gray20', width=8)

        if progress > 0:
            # Calculate color based on progress
            color = 'green' if progress * self.time_limit < self.warning_threshold else 'orange' if progress * self.time_limit < self.warning_threshold2 else 'red'

            # Calculate the extent of the arc
            extent = 360 * progress

            # Draw the progress arc
            self.create_arc(x0, y0, x1, y1, start=-90, extent=-extent, outline=color, width=9, style='arc')

        self.last_progress = progress  # Update last progress to current

    def update_timer(self):
        if self.is_running:
            elapsed = self.get_time()
            
            # Update timer display
            hours, minutes, seconds = map(int, (elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60))
            self.timer_label.configure(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

            # Calculate progress
            progress = min(elapsed / self.time_limit, 1.0)

            # Update progress ring only if progress has changed significantly
            if abs(progress - self.last_progress) > 0.01:  # Only update if progress changes by 1%
                self.draw_ring(progress)
                self.last_progress = progress  # Update last progress to current

            # Update timer color based on elapsed time
            if elapsed >= self.time_limit:
                self.timer_label.configure(text_color="red")
                if not self.alert_shown:
                    self.show_time_alert()
                    self.alert_shown = True
            elif elapsed >= (self.time_limit * 0.8):
                self.timer_label.configure(text_color="orange")
            else:
                self.timer_label.configure(text_color="green")

            # Schedule the next update
            self.after(1000, self.update)  # Update every 1 second instead of 500ms

    def show_time_alert(self):
        if not hasattr(self, 'last_alert_time'):
            self.last_alert_time = 0

        current_time = time.time()
        if current_time - self.last_alert_time < 300:  # 300 seconds = 5 minutes
            return

        self.last_alert_time = current_time

        station_info = f"Station {self.station_num} ({self.station_type})"
        user_name = self.name_entry.get()
        if user_name:
            station_info += f" - {user_name}"
        messagebox.showwarning("Time Limit Exceeded", 
                             f"{station_info}\nhas exceeded the 30-minute time limit.\nPlease ask the user to wrap up their session.")

class Station(ctk.CTkFrame):
    def __init__(self, parent, app, station_type, station_num):
        super().__init__(parent, border_width=2, corner_radius=10)  # Add border and rounded corners
        self.parent = parent
        self.app = app  # Store reference to the app
        self.station_type = station_type
        self.station_num = station_num
        self.timer = CombinedTimer(self, width=120, height=120)

        self.timer.station_type = station_type
        self.timer.station_num = station_num
        self.timer.parent_station = self

        self.setup_ui()
        self.update_timer()

    def setup_ui(self):
        # Header frame
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=5)

        # Station number label
        ctk.CTkLabel(header_frame, text=f"Station {self.station_num}", anchor="e").pack(side="right")

        # icon_errors = set()

        # def download_icon(icon_name, size=(20, 20), retries=3):
        #     """Download an SVG icon, cache it locally, and return a CTkImage."""
        #     cache_dir = Path("./icon_cache")
        #     cache_dir.mkdir(exist_ok=True)

        #     cached_file = cache_dir / f"{icon_name}.png"
        #     if cached_file.exists():
        #         return ctk.CTkImage(Image.open(cached_file), size=size)

        #     def download():
        #         url = f"https://cdn.jsdelivr.net/npm/lucide-static@0.298.0/icons/{icon_name}.svg"
        #         for attempt in range(retries):
        #             try:
        #                 response = requests.get(url, timeout=5)
        #                 if response.status_code == 200:
        #                     svg_content = response.content.decode("utf-8")
        #                     svg_content = re.sub(r'stroke="[^"]*"', 'stroke="white"', svg_content)
        #                     svg_content = re.sub(r'fill="[^"]*"', 'fill="none"', svg_content)
        #                     png_data = cairosvg.svg2png(bytestring=svg_content.encode("utf-8"))
        #                     img = Image.open(BytesIO(png_data))
        #                     img.save(cached_file)
        #                     return ctk.CTkImage(img, size=size)
        #             except Exception as e:
        #                 print(f"Failed to fetch icon {icon_name} on attempt {attempt + 1}: {e}")
        #                 time.sleep(1)

        #         print(f"Failed to fetch icon {icon_name} after {retries} attempts. Using fallback.")
        #         fallback_path = "./icon_cache/fallback.png"
        #         fallback_img = Image.new("RGB", size, color="gray")
        #         if Path(fallback_path).exists():
        #             fallback_img = Image.open(fallback_path)
        #         return ctk.CTkImage(fallback_img, size=size)

        #     # Run the download in a separate thread
        #     thread = threading.Thread(target=download)
        #     thread.start()
        #     return None  # Return None initially, and handle the result later


        if self.station_type in ["XBOX", "Switch"]:
            # Console type toggle frame with icons
            console_toggle_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
            console_toggle_frame.pack(side="left", fill="x")

            # Load icon images
            xbox_image = Image.open("./icon_cache/xbox-logo.png")
            switch_image = Image.open("./icon_cache/switch-logo.png")
            
            # Create CTkImages with consistent size
            icon_size = (20, 20)
            xbox_icon = ctk.CTkImage(xbox_image, size=icon_size)
            switch_icon = ctk.CTkImage(switch_image, size=icon_size)

            # Initialize the console variable
            self.console_var = ctk.StringVar(value=self.station_type)

            # Function to handle button state updates
            def update_button_states():
                xbox_button.configure(
                    fg_color=("gray75", "gray25") if self.console_var.get() == "XBOX" else "transparent",
                    hover_color=("gray65", "gray35")
                )
                switch_button.configure(
                    fg_color=("gray75", "gray25") if self.console_var.get() == "Switch" else "transparent",
                    hover_color=("gray65", "gray35")
                )

            # Function to handle console selection
            def select_console(console_type):
                self.console_var.set(console_type)
                update_button_states()
                self.change_console_type()

            # Create toggle buttons with icons
            xbox_button = ctk.CTkButton(
                console_toggle_frame,
                image=xbox_icon,
                text="",
                width=40,
                height=40,
                corner_radius=8,
                fg_color="transparent",
                hover_color=("gray65", "gray35"),
                command=lambda: select_console("XBOX")
            )
            xbox_button.pack(side="left", padx=2)

            switch_button = ctk.CTkButton(
                console_toggle_frame,
                image=switch_icon,
                text="",
                width=40,
                height=40,
                corner_radius=8,
                fg_color="transparent",
                hover_color=("gray65", "gray35"),
                command=lambda: select_console("Switch")
            )
            switch_button.pack(side="left", padx=2)

            # Set initial button states
            update_button_states()

            # Create a container frame for all input fields
            fields_frame = ctk.CTkFrame(self, fg_color="transparent")
            fields_frame.pack(fill="x", padx=5, pady=2)
            
            # Configure grid columns
            fields_frame.grid_columnconfigure(1, weight=1)
            fields_frame.grid_columnconfigure(3, weight=1)
            
            # Name and ID fields (first row)
            ctk.CTkLabel(fields_frame, text="Name:").grid(row=0, column=0, padx=(0,5), sticky="w")
            self.name_entry = ctk.CTkEntry(fields_frame)
            self.name_entry.grid(row=0, column=1, padx=5, sticky="ew")
            
            ctk.CTkLabel(fields_frame, text="ID #").grid(row=0, column=2, padx=(15,5), sticky="w")
            self.id_entry = ctk.CTkEntry(fields_frame)
            self.id_entry.grid(row=0, column=3, padx=5, sticky="ew")

            # Game and Controller fields (second row)
            ctk.CTkLabel(fields_frame, text="Game:").grid(row=1, column=0, padx=(0,5), sticky="w")
            self.game_var = ctk.StringVar()
            games = self.app.get_games_for_console(self.station_type)
            self.game_dropdown = ctk.CTkComboBox(fields_frame, variable=self.game_var, values=games)
            self.game_dropdown.grid(row=1, column=1, padx=5, sticky="ew")

            ctk.CTkLabel(fields_frame, text="Ctrl:").grid(row=1, column=2, padx=(15,5), sticky="w")
            self.controller_var = ctk.StringVar()
            controllers = ["1", "2", "3", "4"]
            self.controller_dropdown = ctk.CTkComboBox(fields_frame, variable=self.controller_var, values=controllers)
            self.controller_dropdown.grid(row=1, column=3, padx=5, sticky="ew")

            # Initialize timer with console-specific attributes
            self.timer.name_entry = self.name_entry
            self.timer.id_entry = self.id_entry
            self.timer.game_dropdown = self.game_dropdown
            self.timer.game_var = self.game_var
            self.timer.controller_dropdown = self.controller_dropdown
            self.timer.controller_var = self.controller_var

        else:  # For other station types
            ctk.CTkLabel(header_frame, text=self.station_type).pack(side="left")
            
            # Name and ID fields
            fields_frame = ctk.CTkFrame(self, fg_color="transparent")
            fields_frame.pack(fill="x", padx=5, pady=2)
            
            # Configure grid columns to be uniform
            fields_frame.grid_columnconfigure(1, weight=1)  # Name entry column
            fields_frame.grid_columnconfigure(3, weight=1)  # ID entry column
            
            ctk.CTkLabel(fields_frame, text="Name:").grid(row=0, column=0, padx=(0,5), sticky="w")
            self.name_entry = ctk.CTkEntry(fields_frame)
            self.name_entry.grid(row=0, column=1, padx=5, sticky="ew")
            
            ctk.CTkLabel(fields_frame, text="ID #").grid(row=0, column=2, padx=(15,5), sticky="w")
            self.id_entry = ctk.CTkEntry(fields_frame)
            self.id_entry.grid(row=0, column=3, padx=5, sticky="ew")

            self.timer.name_entry = self.name_entry
            self.timer.id_entry = self.id_entry

        # Timer frame
        timer_frame = ctk.CTkFrame(self, fg_color="transparent")
        timer_frame.pack(fill="x", padx=2, pady=0)
        
        # Timer ring
        self.timer.pack(side="left", padx=5, pady=0)

        # Timer label
        self.timer_label = ctk.CTkLabel(
            timer_frame, 
            text="", 
            font=ctk.CTkFont(family="Helvetica", size=14)
        )
        self.timer_label.pack(side="left", padx=0)

        # Load control icons

        self.start_icon = ctk.CTkImage(Image.open("./icon_cache/play.png"), size=(15, 15))
        self.stop_icon = ctk.CTkImage(Image.open("./icon_cache/square.png"), size=(15, 15))
        self.reset_icon = ctk.CTkImage(Image.open("./icon_cache/refresh-ccw.png"), size=(15, 15))

        # Control buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(side="bottom", fill="x", padx=2, pady=2)
        ctk.CTkButton(button_frame, image=self.start_icon, text="Start", command=self.timer.start, width=30, height=30, corner_radius=20).pack(side="left", padx=2)
        ctk.CTkButton(button_frame, image=self.stop_icon, text="Stop", command=self.timer.stop, width=30, height=30, corner_radius=20).pack(side="left", padx=2)
        ctk.CTkButton(button_frame, image=self.reset_icon, text="Reset", command=self.timer.reset, width=30, height=30, corner_radius=20).pack(side="left", padx=2)

    def change_console_type(self):
        self.station_type = self.console_var.get()
        games = self.app.get_games_for_console(self.station_type)
        self.game_dropdown.configure(values=games)
        self.game_var.set('')

    def update_timer(self):
        self.timer.update_timer()
        self.after(1000, self.update_timer)

    def show_time_alert(self):
        station_info = f"Station {self.station_num} ({self.station_type})"
        user_name = self.name_entry.get()
        if user_name:
            station_info += f" - {user_name}"
        messagebox.showwarning("Time Limit Exceeded", 
                             f"{station_info}\nhas exceeded the 2-minute time limit.\nPlease ask the user to wrap up their session.")

    def start_timer(self):
        self.timer.start()

    def stop_timer(self):
        self.timer.stop()

    def reset_timer(self):
        self.timer.reset()
        self.log_usage()
        self.timer_label.configure(text="00:00:00", text_color="black")
        self.timer.draw_ring(0)  # Reset progress ring
        self.name_entry.delete(0, tk.END)
        
        if self.station_type in ["XBOX", "Switch"]:
            self.game_dropdown.set("")
            self.controller_dropdown.set("")

    def log_usage(self):
            try:
                # Get values safely using getattr to avoid attribute errors
                user_name = self.timer.name_entry.get() if self.timer.name_entry else "Unknown"
                id_number = self.timer.id_entry.get() if self.timer.id_entry else "Unknown"
                game = self.timer.game_var.get() if self.timer.game_var else "N/A"
                controller = self.timer.controller_var.get() if self.timer.controller_var else "N/A"
                duration = self.timer.get_time()
                formatted_duration = time.strftime("%H:%M:%S", time.gmtime(duration))
                
                # Prepare log entry
                log_entry = [
                    f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]}",
                    f"Station Type: {self.station_type}",
                    f"Station Number: {self.station_num}",
                    f"User Name: {user_name}",
                    f"ID Number: {id_number}",
                    f"Duration: {formatted_duration}",
                    f"Game: {game}",
                    f"Controllers: {controller}",
                    "--------------------------------------------------"
                ]
                
                # Write to log file
                with open("usage_log.txt", "a") as log_file:
                    log_file.write("\n".join(log_entry) + "\n")
                
                print(f"Successfully logged usage for Station {self.station_num}")
                
            except Exception as e:
                print(f"Error logging usage: {str(e)}")
                # Optionally show error message to user
                messagebox.showerror("Logging Error", 
                                f"Failed to log station usage. Please notify administrator.\nError: {str(e)}")

    def update_games_list(self):
        if self.station_type in ["XBOX", "Switch"]:
            console_type = "XBOX" if self.station_type == "XBOX" else "Switch"
            games = self.parent.get_games_for_console(console_type)
            self.game_dropdown.configure(values=games)
            if self.game_var.get() not in games:
                self.game_var.set(games[0] if games else '')
class GamesWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Games List")
        self.geometry("600x400")
        self.configure(bg="#333333")  # Set background color to match the dark theme
        self.games = self.load_games()
        self.setup_ui()
        
        self.lift()
        self.focus_force()
        self.grab_set()

    def load_games(self):
        if os.path.exists('games_list.json'):
            with open('games_list.json', 'r') as f:
                games = json.load(f)
                for console in games:
                    games[console].sort()  # Sort the games list alphabetically
                return games
        return {"Switch": [], "XBOX": []}

    def save_games(self, games_dict):
        with open('games_list.json', 'w') as f:
            json.dump(games_dict, f)

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure notebook without creating custom elements
        style.configure("TNotebook", 
            background="#333333",  # Match the dark theme
            borderwidth=0,          # Remove border
            padding=0               # Remove padding
        )
        
        # Configure the tab style with larger padding and font
        style.configure("TNotebook.Tab", 
            background="#444444",  # Dark background for the tabs
            foreground="white",    # Light text for the tabs
            padding=[12, 10],      # Increase padding to make the tabs larger
            borderwidth=0,         # Remove border
            font=("Helvetica", 14) # Increase font size
        )
            
        style.map("TNotebook.Tab", 
            background=[("selected", "#00843d")],  # Green for selected tab background
            foreground=[("selected", "white")]    # White text for selected tab
        )

        style.configure("TFrame", background="#333333")  # Match the dark theme

        # Create a container frame to hold the notebook and scrollbar
        container = ttk.Frame(self)
        container.pack(fill='both', expand=True, padx=0, pady=0)

        self.notebook = ttk.Notebook(container)
        self.notebook.pack(side="left", fill='both', expand=True, padx=0, pady=0)

        self.scrollbar = ctk.CTkScrollbar(container, orientation="vertical")
        self.scrollbar.pack(side="right", fill="y")

        self.switch_tab = ttk.Frame(self.notebook, style="TFrame")
        self.xbox_tab = ttk.Frame(self.notebook, style="TFrame")
        
        self.notebook.add(self.switch_tab, text='Switch Games')
        self.notebook.add(self.xbox_tab, text='XBOX Games')

        self.setup_games_tab(self.switch_tab, "Switch")
        self.setup_games_tab(self.xbox_tab, "XBOX")

    def setup_games_tab(self, parent, console):
        frame = ctk.CTkFrame(parent, border_width=0, corner_radius=0)
        frame.pack(fill='both', expand=True, padx=0, pady=0)

        # Define a custom font with a larger size
        custom_font = ("Helvetica", 16)  # Change the size as needed

        # Use tk.Listbox wrapped in a CTkFrame
        games_listbox = tk.Listbox(
            frame,
            bg="#333333",
            fg="white",
            selectbackground="#00843d",
            selectforeground="white",
            font=custom_font  # Set the custom font here
        )
        games_listbox.pack(side='left', fill='both', expand=True)

        for game in self.games[console]:
            games_listbox.insert('end', game)

        button_frame = ctk.CTkFrame(frame, border_width=0, corner_radius=20)
        button_frame.pack(side='right', fill='y', padx=5)  # Added padx for spacing

        add_button = ctk.CTkButton(
            button_frame, 
            text="Add",
            fg_color="#00843d",  # Match the tab color
            hover_color="#006e33",
            command=lambda: self.add_game(console, games_listbox),
            corner_radius=20
        )
        add_button.pack(pady=5)

        remove_button = ctk.CTkButton(
            button_frame, 
            text="Remove",
            fg_color="#00843d",
            hover_color="#006e33",
            command=lambda: self.remove_game(console, games_listbox),
            corner_radius=20
        )
        remove_button.pack(pady=5)

    def add_game(self, console, games_listbox):
        dialog = CustomDialog(self, title="Add Game", prompt=f"Enter new game for {console}:")
        new_game = dialog.show()
        if new_game:
            self.games[console].append(new_game)
            self.update_games_listbox(console, games_listbox)
            self.save_games(self.games)

    def remove_game(self, console, games_listbox):
        selected_game = games_listbox.get(tk.ACTIVE)
        if selected_game:
            self.games[console].remove(selected_game)
            self.update_games_listbox(console, games_listbox)
            self.save_games(self.games)

    def update_games_listbox(self, console, games_listbox):
        games_listbox.delete(0, tk.END)
        for game in self.games[console]:
            games_listbox.insert('end', game)
class CustomDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="Add Game", prompt="Enter new game:"):
        super().__init__(parent)
        self.title(title)
        self.geometry("300x150")
        self.resizable(False, False)

        self.result = None

        self.label = ctk.CTkLabel(self, text=prompt)
        self.label.pack(pady=10)

        self.entry = ctk.CTkEntry(self)
        self.entry.pack(pady=10, padx=10, fill="x")

        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(pady=10)

        self.ok_button = ctk.CTkButton(self.button_frame, text="OK", command=self.on_ok)
        self.ok_button.pack(side="left", padx=5)

        self.cancel_button = ctk.CTkButton(self.button_frame, text="Cancel", command=self.on_cancel)
        self.cancel_button.pack(side="left", padx=5)

        self.entry.bind("<Return>", lambda event: self.on_ok())
        self.entry.bind("<Escape>", lambda event: self.on_cancel())

    def on_ok(self):
        self.result = self.entry.get()
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()

    def show(self):
        self.grab_set()
        self.wait_window()
        return self.result

class StationSelectionDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, stations):
        super().__init__(parent)
        self.title(title)
        self.stations = stations
        self.selected_station = None
        self.setup_ui()

    def setup_ui(self):
        ctk.CTkLabel(self, text="Select Station:").grid(row=0, column=0, padx=10, pady=10)
        self.station_var = ctk.StringVar()
        self.station_dropdown = ctk.CTkComboBox(self, values=self.stations, variable=self.station_var)
        self.station_dropdown.grid(row=0, column=1, padx=10, pady=10)

        ctk.CTkButton(self, text="OK", command=self.on_ok).grid(row=1, column=0, columnspan=2, pady=10)

    def on_ok(self):
        self.selected_station = self.station_var.get()
        self.destroy()

class WaitlistDialog(ctk.CTkToplevel):
    def __init__(self, parent, stations, title="Add to Waitlist", prompt="Enter details:"):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x550")  # Increased height for email field
        self.resizable(False, False)

        self.result = None
        
        # Party Information
        self.name_frame = ctk.CTkFrame(self)
        self.name_frame.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(self.name_frame, text="Party Information").pack(anchor="w")
        self.name_entry = ctk.CTkEntry(self.name_frame, placeholder_text="Party Name")
        self.name_entry.pack(fill="x", pady=5)
        
        # Phone number entry with validation
        self.phone_entry = ctk.CTkEntry(self.name_frame, placeholder_text="Phone Number")
        self.phone_entry.pack(fill="x", pady=5)
        
        # Add validation to the phone number entry
        self.phone_entry.configure(
            validate="key",  # Validate on each keystroke
            validatecommand=(self.register(self.validate_phone), "%P")  # Pass the new input to the validation function
        )
        
        # Email address field (new)
        self.email_entry = ctk.CTkEntry(self.name_frame, placeholder_text="Email Address (Optional)")
        self.email_entry.pack(fill="x", pady=5)
        
        self.size_entry = ctk.CTkEntry(self.name_frame, placeholder_text="Party Size")
        self.size_entry.pack(fill="x", pady=5)

        # Notes
        self.notes_frame = ctk.CTkFrame(self)
        self.notes_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(self.notes_frame, text="Additional Notes").pack(anchor="w")
        self.notes_entry = ctk.CTkEntry(self.notes_frame, placeholder_text="Notes")
        self.notes_entry.pack(fill="x", pady=5)

        # Station Selection
        self.station_frame = ctk.CTkFrame(self)
        self.station_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(self.station_frame, text="Station").pack(anchor="w")
        self.station_var = ctk.StringVar()
        self.station_dropdown = ctk.CTkComboBox(
            self.station_frame,
            variable=self.station_var,
            values=stations
        )
        self.station_dropdown.pack(fill="x", pady=5)

        # Buttons
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(pady=20)
        
        self.ok_button = ctk.CTkButton(self.button_frame, text="Add to Waitlist", command=self.on_ok)
        self.ok_button.pack(side="left", padx=5)
        
        self.cancel_button = ctk.CTkButton(self.button_frame, text="Cancel", command=self.on_cancel)
        self.cancel_button.pack(side="left", padx=5)

    def validate_phone(self, new_input):
        """Validate the phone number input."""
        # Allow empty input (for backspace/deletion)
        if not new_input:
            return True
        
        # Check if the input is numeric and no more than 10 digits
        return new_input.isdigit() and len(new_input) <= 10

    def on_ok(self):
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        size = self.size_entry.get().strip()
        notes = self.notes_entry.get().strip()
        station = self.station_var.get()
        email = self.email_entry.get().strip()  # Get email value
        
        # Validate the phone number
        if not (phone.isdigit() and len(phone) == 10):
            messagebox.showerror("Invalid Phone Number", "Please enter a valid 10-digit phone number.")
            return
        
        if name and phone and size and station:
            current_time = datetime.now()
            self.result = {
                "party": name,
                "phone": phone,
                "size": int(size),
                "notes": notes,
                "station": station,
                "arrival": current_time.strftime("%I:%M %p"),
                "quotedTime": (current_time + timedelta(minutes=15)).strftime("%I:%M %p")
            }
            
            # Only add email if provided
            if email:
                self.result["email"] = email
                
            self.grab_release()
            self.destroy()
        else:
            messagebox.showerror("Error", "Please fill out all required fields.")

    def on_cancel(self):
        """Cancel the dialog without saving changes"""
        self.result = None
        self.grab_release()
        self.destroy()
    
    def show(self):
        """Display the dialog and wait for user input"""
        self.grab_set()  # Make the dialog modal
        self.wait_window()  # Wait for the window to be destroyed
        return self.result  # Return the result after the window is closed

class BowlingWaitlistDialog(ctk.CTkToplevel):
    def __init__(self, parent, lanes, title="Add to Bowling Waitlist", prompt="Enter details:"):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x700")  # Increased height for email field
        self.resizable(False, False)

        self.result = None
        self.lanes = lanes
        
        # Party Information
        self.name_frame = ctk.CTkFrame(self)
        self.name_frame.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(self.name_frame, text="Party Information").pack(anchor="w")
        self.name_entry = ctk.CTkEntry(self.name_frame, placeholder_text="Party Name")
        self.name_entry.pack(fill="x", pady=5)
        
        # Phone number entry with validation
        self.phone_entry = ctk.CTkEntry(self.name_frame, placeholder_text="Phone Number")
        self.phone_entry.pack(fill="x", pady=5)
        
        # Add validation to the phone number entry
        self.phone_entry.configure(
            validate="key",  # Validate on each keystroke
            validatecommand=(self.register(self.validate_phone), "%P")  # Pass the new input to the validation function
        )
        
        # Email address field (new)
        self.email_entry = ctk.CTkEntry(self.name_frame, placeholder_text="Email Address (Optional)")
        self.email_entry.pack(fill="x", pady=5)
        
        self.size_entry = ctk.CTkEntry(self.name_frame, placeholder_text="Party Size")
        self.size_entry.pack(fill="x", pady=5)

        # Number of Lanes Needed
        self.lanes_frame = ctk.CTkFrame(self)
        self.lanes_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(self.lanes_frame, text="Number of Lanes Needed").pack(anchor="w")
        
        # Create a frame for the lane count dropdown
        lanes_count_frame = ctk.CTkFrame(self.lanes_frame, fg_color="transparent")
        lanes_count_frame.pack(fill="x", pady=5)
        
        # Lane count dropdown with values 1-6
        self.lanes_needed_var = ctk.StringVar(value="1")
        self.lanes_needed_dropdown = ctk.CTkComboBox(
            lanes_count_frame,
            variable=self.lanes_needed_var,
            values=["1", "2", "3", "4", "5", "6"],
            command=self.update_lane_selector
        )
        self.lanes_needed_dropdown.pack(fill="x")

        # Notes
        self.notes_frame = ctk.CTkFrame(self)
        self.notes_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(self.notes_frame, text="Additional Notes").pack(anchor="w")
        self.notes_entry = ctk.CTkEntry(self.notes_frame, placeholder_text="Notes")
        self.notes_entry.pack(fill="x", pady=5)

        # Lane Preferences Frame
        self.preferences_frame = ctk.CTkFrame(self)
        self.preferences_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(self.preferences_frame, text="Lane Preferences (Optional)").pack(anchor="w")

        # Add checkbox for specifying lane preferences
        self.specify_lanes_var = ctk.BooleanVar(value=False)
        self.specify_lanes_checkbox = ctk.CTkCheckBox(
            self.preferences_frame, 
            text="Specify preferred lanes",
            variable=self.specify_lanes_var,
            command=self.toggle_lane_preferences
        )
        self.specify_lanes_checkbox.pack(pady=5, anchor="w")
        
        # Container for lane selection dropdowns
        self.lane_selectors_frame = ctk.CTkFrame(self.preferences_frame, fg_color="transparent")
        # Initially hidden, will be shown when checkbox is checked
        
        # Create initial lane selector for one lane
        self.lane_selectors = []
        self.update_lane_selector(self.lanes_needed_var.get())

        # Buttons
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(pady=20)
        
        self.ok_button = ctk.CTkButton(self.button_frame, text="Add to Bowling Waitlist", command=self.on_ok)
        self.ok_button.pack(side="left", padx=5)
        
        self.cancel_button = ctk.CTkButton(self.button_frame, text="Cancel", command=self.on_cancel)
        self.cancel_button.pack(side="left", padx=5)

    def toggle_lane_preferences(self):
        """Show or hide lane preference selectors based on checkbox state"""
        if self.specify_lanes_var.get():
            self.lane_selectors_frame.pack(fill="x", pady=5)
        else:
            self.lane_selectors_frame.pack_forget()

    def update_lane_selector(self, value=None):
        """Update lane selector dropdowns based on number of lanes needed"""
        # Clear existing lane selectors
        for selector in self.lane_selectors:
            for widget in selector.winfo_children():
                widget.destroy()
            selector.destroy()
        self.lane_selectors = []
        
        # Get number of lanes needed
        num_lanes = int(self.lanes_needed_var.get())
        
        # Recreate the frame
        self.lane_selectors_frame.destroy()
        self.lane_selectors_frame = ctk.CTkFrame(self.preferences_frame, fg_color="transparent")
        if self.specify_lanes_var.get():
            self.lane_selectors_frame.pack(fill="x", pady=5)
        
        # Create new lane selectors based on the number of lanes needed
        for i in range(num_lanes):
            lane_frame = ctk.CTkFrame(self.lane_selectors_frame, fg_color="transparent")
            lane_frame.pack(fill="x", pady=2)
            
            label = ctk.CTkLabel(lane_frame, text=f"Lane {i+1} Preference:")
            label.pack(side="left", padx=(0, 5))
            
            lane_var = ctk.StringVar()
            lane_dropdown = ctk.CTkComboBox(
                lane_frame,
                variable=lane_var,
                values=self.lanes,
                width=100
            )
            lane_dropdown.pack(side="left", fill="x", expand=True)
            
            self.lane_selectors.append(lane_frame)

    def validate_phone(self, new_input):
        """Validate the phone number input."""
        # Allow empty input (for backspace/deletion)
        if not new_input:
            return True
        
        # Check if the input is numeric and no more than 10 digits
        return new_input.isdigit() and len(new_input) <= 10

    def on_ok(self):
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        size = self.size_entry.get().strip()
        notes = self.notes_entry.get().strip()
        lanes_needed = int(self.lanes_needed_var.get())
        email = self.email_entry.get().strip()  # Get email value
        
        # Validate the phone number
        if not (phone.isdigit() and len(phone) == 10):
            messagebox.showerror("Invalid Phone Number", "Please enter a valid 10-digit phone number.")
            return
        
        # Get preferred lanes if specified
        preferred_lanes = []
        if self.specify_lanes_var.get() and self.lane_selectors:
            for i, frame in enumerate(self.lane_selectors):
                dropdown = [w for w in frame.winfo_children() if isinstance(w, ctk.CTkComboBox)]
                if dropdown:
                    lane = dropdown[0].get()
                    if lane:
                        preferred_lanes.append(lane)
        
        if name and phone and size:
            current_time = datetime.now()
            
            # Format notes to include lanes needed
            formatted_notes = f"Lanes needed: {lanes_needed}"
            if notes:  # Add user notes if provided
                formatted_notes += f" - {notes}"
                
            # Format preferred lanes for display in the station column
            if preferred_lanes:
                station_display = ", ".join(preferred_lanes)
            else:
                station_display = "Any Lanes"
                
            self.result = {
                "party": name,
                "phone": phone,
                "size": int(size),
                "notes": formatted_notes,
                "station": station_display,  # Display preferred lanes or "Any Lanes"
                "arrival": current_time.strftime("%I:%M %p"),
                "quotedTime": (current_time + timedelta(minutes=30)).strftime("%I:%M %p"),
                "lanes_needed": lanes_needed,  # Store the number of lanes needed
                "preferred_lanes": preferred_lanes  # Store the list of preferred lanes
            }
            
            # Only add email if provided
            if email:
                self.result["email"] = email
                
            self.grab_release()
            self.destroy()
        else:
            messagebox.showerror("Error", "Please fill out all required fields.")


    def on_cancel(self):
        """Cancel the dialog without saving changes"""
        self.result = None
        self.grab_release()
        self.destroy()
    
    def show(self):
        """Display the dialog and wait for user input"""
        self.grab_set()  # Make the dialog modal
        self.wait_window()  # Wait for the window to be destroyed
        return self.result  # Return the result after the window is closed
class GamingCenterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gaming Center App")
        self.geometry("1500x950")
        self.stations = []  # Keep track of all stations
        self.waitlist = []  # List to keep track of people on the waitlist
        self.timers = []
        self.waitlist_tree = None  # Initialize waitlist_tree as None

        # Create the main content frame that will contain everything else
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True)

        # Create and setup the sidebar
        self.setup_sidebar()

                # Create the content area
        self.content_area = ctk.CTkFrame(self.main_container)
        self.content_area.pack(side="left", fill="both", expand=True)

        #         # Create main container with more padding
        # main_frame = ctk.CTkFrame(self.content_area)
        # main_frame.pack(fill="both", expand=True, padx=20, pady=20)


        # self.create_menu()
        self.setup_ui()

        # Bind the close event to the stop_timers method
        self.protocol("WM_DELETE_WINDOW", self.on_close)


    def setup_sidebar(self):
        # Create the sidebar frame with dark background
        self.sidebar = ctk.CTkFrame(self.main_container, fg_color="gray16", width=85, corner_radius=20)
        self.sidebar.pack(side="left", fill="y", padx=(0, 20))
        self.sidebar.pack_propagate(False)  # Prevent the sidebar from shrinking

        # Add the main logo at the top
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=60)
        logo_frame.pack(fill="x", pady=(10, 20))
        logo_frame.pack_propagate(False)

        # Load logo image
        logo_image_path = "./icon_cache/GamingCenterApp.png"
        try:
            logo_image = Image.open(logo_image_path)
            logo_ctk_image = ctk.CTkImage(logo_image, size=(60, 60))
        except Exception as e:
            print(f"Error loading logo image: {e}")
            # Use a placeholder image or skip the logo if the image fails to load
            logo_ctk_image = None

        # Create logo label with image
        logo_label = ctk.CTkLabel(
            logo_frame,
            image=logo_ctk_image,
            text="",  # Ensure no default text is displayed
            width=85,
            height=85
        )
        logo_label.place(relx=0.5, rely=0.5, anchor="center")

        home = ctk.CTkImage(Image.open("./icon_cache/house.png"), size=(24, 24))
        games = ctk.CTkImage(Image.open("./icon_cache/gamepad-2.png"), size=(24, 24))
        waitlist = ctk.CTkImage(Image.open("./icon_cache/list-plus.png"), size=(24, 24))
        stats = ctk.CTkImage(Image.open("./icon_cache/chart-pie.png"), size=(24, 24))

        # Create sidebar buttons with hover effects
        self.create_sidebar_button(home, "Home", command=self.show_home)
        self.create_sidebar_button(games, "Games", command=self.open_games_window)
        self.waitlist_button = self.create_sidebar_button(waitlist, "Waitlist", command=self.show_waitlist_window)
        self.create_sidebar_button(stats, "Stats", command=self.open_stats_window)

        # Add a count label to the Waitlist button
        self.waitlist_count_label = ctk.CTkLabel(
            self.waitlist_button,
            text="0",
            fg_color="red",
            text_color="white",
            corner_radius=10,
            width=20,
            height=20,
            font=("Helvetica", 10, "bold")
        )
        self.waitlist_count_label.place(relx=0.8, rely=0.2, anchor="center")  # Position in the top-right corner
        self.update_waitlist_count()  # Initialize the counter

        # Initialize the notification bubble in the sidebar
        self.notification_bubble = ctk.CTkLabel(
            self.sidebar,
            text="",
            fg_color="red",
            text_color="white",
            corner_radius=10
        )
        self.notification_bubble.place(relx=0.9, rely=0.1, anchor="ne")  # Position in the top-right corner of the sidebar
        self.notification_bubble.place_forget()  # Hide the notification bubble initially

    def create_sidebar_button(self, icon, tooltip, command=None):
        # Create button frame
        btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        btn_frame.pack(fill="x", pady=5)

        # Create the actual button
        btn = ctk.CTkButton(
            btn_frame,
            image=icon,
            text="",
            width=52,
            height=52,
            corner_radius=8,
            fg_color="transparent",
            hover_color="#333333",
            command=command
        )
        btn.place(relx=0.5, rely=0.5, anchor="center")

        # Create tooltip
        self.create_tooltip(btn, tooltip)

        return btn  # Return the button widget for further customization

    def create_tooltip(self, widget, text):
        def enter(event):
            # Create tooltip window
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+40}+{event.y_root}")
            
            # Create tooltip label
            label = tk.Label(tooltip, text=text, justify='left', padx=12, pady=12,
                           background="#333333", foreground="white",
                           relief='solid', borderwidth=1,
                           font=("Helvetica", "16", "normal"))
            label.pack()
            
            # Store tooltip reference
            widget.tooltip = tooltip
            
        def leave(event):
            # Destroy tooltip if it exists
            if hasattr(widget, "tooltip"):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def show_home(self):
        # Implement home view functionality
        pass

    def stop_timers(self):

        for timer in self.timers:  # Assuming self.timers is a list of your timer instances

            timer.stop()  # Call the stop method for each timer

        self.is_running = False  # Set running flag to False


    def on_close(self):

        self.stop_timers()  # Stop all timers

        self.destroy()      # Close the application

    def setup_ui(self):
        # Create main container with more padding
        main_frame = ctk.CTkFrame(self.content_area)
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        # Configure grid weights
        for i in range(6):  # 6 rows
            main_frame.grid_rowconfigure(i, weight=1)
        for i in range(3):  # 3 columns
            main_frame.grid_columnconfigure(i, weight=1)
        # # Add button to view and edit games at the top right
        # games_button = ctk.CTkButton(main_frame, text="View/Edit Games", command=self.open_games_window, corner_radius=20)
        # waitlist_button = ctk.CTkButton(main_frame, text="Waitlist", command=self.show_waitlist_window, corner_radius=20)
        # waitlist_button.grid(row=0, column=3, padx=10, pady=10, sticky="ne")
        # games_button.grid(row=0, column=2, padx=10, pady=10, sticky="ne")

        # # Notification bubble for waitlist
        # self.notification_bubble = ctk.CTkLabel(main_frame, text="", fg_color="red", text_color="white", corner_radius=10)
        # self.notification_bubble.grid(row=0, column=1, padx=10, pady=10, sticky="ne")
        # Create first 4 console stations (left column) in reverse order
        for i in range(4):
            station = Station(main_frame, self, "XBOX", 4 - i)  # Pass self to Station
            station.grid(row=i, column=0, padx=10, pady=10, sticky="nsew")
            self.stations.append(station)
        # Create 5th console station (top center)
        station = Station(main_frame, self, "XBOX", 5)  # Pass self to Station
        station.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.stations.append(station)
        # Create other activity stations (under 5th console)
        activities = [
            ("Ping-Pong", 1),
            ("Ping-Pong", 2),
            ("Foosball", 1),
            ("Air Hockey", 1),
            ("PoolTable", 1),
            ("PoolTable", 2),
        ]
        row, col = 1, 1  # Start position (under 5th console)
        for activity, num in activities:
            station = Station(main_frame, self, activity, num)  # Pass self to Station
            station.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.stations.append(station)
            col += 1
            if col > 2:  # Move to next row after 2 columns
                col = 1
                row += 1

    def get_games_for_console(self, console_type):
        try:
            with open('games_list.json', 'r') as f:
                games_dict = json.load(f)
                games_list = games_dict.get(console_type, [])
                # Sort the games list alphabetically
                games_list.sort()
                return games_list
                return games_list
        except FileNotFoundError:
            return []

    def update_all_stations_games(self):
        for station in self.stations:
            if hasattr(station, 'update_games_list'):
                station.update_games_list()

    def open_stats_window(self):
        StatsWindow(self)

    def open_games_window(self):
        GamesWindow(self)

    def update_notification_bubble(self):
        """Update the notification bubble to reflect the current number of parties in the waitlist."""
        # Count both regular waitlist and bowling waitlist entries
        regular_count = len(self.waitlist)
        bowling_count = len(self.bowling_waitlist) if hasattr(self, 'bowling_waitlist') else 0
        total_count = regular_count + bowling_count
        
        if total_count > 0:
            self.waitlist_count_label.configure(text=str(total_count))  # Update the Waitlist button counter
            self.waitlist_count_label.place(relx=0.8, rely=0.2, anchor="center")  # Ensure the label is visible
        else:
            self.waitlist_count_label.place_forget()  # Hide the label when there are no parties

    def update_count_label(self):
        """Update the count label to reflect the current number of parties in the waitlist."""
        if hasattr(self, 'count_label'):  # Check if the count label exists
            self.count_label.configure(text=str(len(self.waitlist)))

    def update_waitlist_count(self):
        """Update the count label on the Waitlist button."""
        # Count both regular waitlist and bowling waitlist entries if bowling waitlist exists
        regular_count = len(self.waitlist)
        bowling_count = len(self.bowling_waitlist) if hasattr(self, 'bowling_waitlist') else 0
        total_count = regular_count + bowling_count
        
        if total_count > 0:
            self.waitlist_count_label.configure(text=str(total_count), fg_color="red")  # Show and highlight if there are parties
            self.waitlist_count_label.place(relx=0.8, rely=0.2, anchor="center")  # Ensure the label is visible
        else:
            self.waitlist_count_label.place_forget()  # Hide the label when there are no parties     

    def show_waitlist_window(self):
        """Method for GamingCenterApp class"""
        # Initialize bowling waitlist if it doesn't exist
        if not hasattr(self, 'bowling_waitlist'):
            self.bowling_waitlist = []  # Create a separate list for bowling waitlist
        
        waitlist_window = ctk.CTkToplevel(self)
        waitlist_window.title("Waitlist")
        waitlist_window.geometry("1200x800")
        self.waitlist_window = waitlist_window  # Store reference to the window

        waitlist_window.lift()
        waitlist_window.focus_force()
        waitlist_window.grab_set()
        
        # Create main container
        main_frame = ctk.CTkFrame(waitlist_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header frame with title, toggle and count
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Create toggle for waitlist type
        self.waitlist_type_var = ctk.StringVar(value="Game Center")
        waitlist_toggle = ctk.CTkSegmentedButton(
            header_frame,
            values=["Game Center", "Bowling Lanes"],
            variable=self.waitlist_type_var,
            command=self.switch_waitlist_type
        )
        waitlist_toggle.pack(side="left", padx=(0, 20))
        
        title_frame = ctk.CTkFrame(header_frame)
        title_frame.pack(side="left")
        
        # Title label that will update based on selected waitlist type
        self.title_label = ctk.CTkLabel(
            title_frame, 
            text="Gaming Center Waitlist", 
            font=("Helvetica", 20, "bold")
        )
        self.title_label.pack(side="left", padx=5)
        
        # Count label that will update based on selected waitlist
        self.count_label = ctk.CTkLabel(
            title_frame, 
            text=str(len(self.waitlist)), 
            fg_color="blue", 
            text_color="white",
            corner_radius=10, 
            width=30
        )
        self.count_label.pack(side="left", padx=5)

        # Search frame
        search_frame = ctk.CTkFrame(header_frame)
        search_frame.pack(side="right")
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search parties", width=200)
        self.search_entry.pack(side="right", padx=5)

        # Create a frame to hold both the treeview and buttons side by side
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True)

        # Create custom style for Treeview
        style = ttk.Style()
        style.theme_use("default")

        style.configure(
            "Waitlist.Treeview",
            background="#2b2b2b",
            foreground="white",
            fieldbackground="#2b2b2b",
            rowheight=50,
            font=("Helvetica", 12)
        )
        style.configure(
            "Waitlist.Treeview.Heading",
            background="#333333",
            foreground="white",
            font=("Helvetica", 12, "bold"),
            relief="flat"
        )
        style.map(
            "Waitlist.Treeview",
            background=[("selected", "#1f538d")],
            foreground=[("selected", "white")]
        )

        # Create columns - same structure for both waitlist types
        columns = ("party", "size", "notes", "station", "quotedTime", "arrival")
        self.waitlist_tree = ttk.Treeview(
            content_frame,
            columns=columns,
            show="headings",
            style="Waitlist.Treeview"
        )
        
        # Configure column headings and widths
        self.headings = {
            "party": "PARTY",
            "size": "SIZE",
            "notes": "NOTES",
            "station": "STATION",  # Will be changed to "LANE" for bowling
            "quotedTime": "QUOTED TIME",
            "arrival": "ARRIVAL"
        }
        
        for col, heading in self.headings.items():
            self.waitlist_tree.heading(col, text=heading)
            if col == "size":
                self.waitlist_tree.column(col, width=50, anchor="center")  # Narrow size column
            else:
                self.waitlist_tree.column(col, width=150, anchor="w")  # Adjust width of other columns

        # Create a frame for the buttons column
        buttons_frame = ctk.CTkFrame(content_frame, width=200)  # Set a fixed width for the actions column
        buttons_frame.pack(side="right", fill="y", padx=(10, 0))
        
        # Add a header for the actions column
        ctk.CTkLabel(buttons_frame, text="ACTIONS", font=("Helvetica", 11, "bold")).pack(pady=(0, 0))

        # Load icons
        check_icon = ctk.CTkImage(Image.open("./icon_cache/check.png"), size=(16, 16))
        x_icon = ctk.CTkImage(Image.open("./icon_cache/x.png"), size=(16, 16))
        pencil_icon = ctk.CTkImage(Image.open("./icon_cache/pencil.png"), size=(16, 16))
        message_icon = ctk.CTkImage(Image.open("./icon_cache/message-circle-more.png"), size=(16, 16))

        # Add a single row of placeholder buttons (grayed-out and un-clickable)
        self.placeholder_buttons_frame = ctk.CTkFrame(buttons_frame)
        self.placeholder_buttons_frame.pack(pady=10, padx=5)

        ctk.CTkButton(
            self.placeholder_buttons_frame,
            image=check_icon,
            text="",
            width=30,
            height=30,
            fg_color="gray",
            hover_color="gray",
            state="disabled"  # Disable the button
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            self.placeholder_buttons_frame,
            image=x_icon,
            text="",
            width=30,
            height=30,
            fg_color="gray",
            hover_color="gray",
            state="disabled"  # Disable the button
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            self.placeholder_buttons_frame,
            image=pencil_icon,
            text="",
            width=30,
            height=30,
            fg_color="gray",
            hover_color="gray",
            state="disabled"  # Disable the button
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            self.placeholder_buttons_frame,
            image=message_icon,
            text="",
            width=30,
            height=30,
            fg_color="gray",
            hover_color="gray",
            state="disabled"  # Disable the button
        ).pack(side="left", padx=2)

        # Pack the treeview with scrollbar
        tree_scroll = ctk.CTkScrollbar(content_frame, orientation="vertical", command=self.waitlist_tree.yview)
        self.waitlist_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.waitlist_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        # Store reference to buttons_frame for updating
        self.buttons_frame = buttons_frame

        # Add floating action button - will be updated based on waitlist type
        station_names = [f"{station.station_type} {station.station_num}" for station in self.stations]
        self.add_button = ctk.CTkButton(
            waitlist_window,
            text="+",
            width=60,
            height=60,
            corner_radius=60,
            font=("Helvetica", 24, "bold"),
            command=lambda: self.add_to_waitlist(station_names)
        )
        self.add_button.place(relx=0.95, rely=0.95, anchor="se")

        def update_tree(event=None):
            search_text = self.search_entry.get().lower()
            self.update_waitlist_tree(search_text)

        self.search_entry.bind('<KeyRelease>', update_tree)
        
        # Update the waitlist display
        self.update_waitlist_tree()

    def switch_waitlist_type(self, value=None):
        """Switch between Game Center and Bowling Lanes waitlists"""
        waitlist_type = self.waitlist_type_var.get()
        
        # Update the title and column headers
        if waitlist_type == "Game Center":
            self.title_label.configure(text="Gaming Center Waitlist")
            self.count_label.configure(text=str(len(self.waitlist)))
            self.waitlist_tree.heading("station", text="STATION")
            
            # Update add button command for gaming center
            station_names = [f"{station.station_type} {station.station_num}" for station in self.stations]
            self.add_button.configure(
                command=lambda: self.add_to_waitlist(station_names)
            )
        else:  # Bowling Lanes
            self.title_label.configure(text="Bowling Lanes Waitlist")
            self.count_label.configure(text=str(len(self.bowling_waitlist)))
            self.waitlist_tree.heading("station", text="LANE")
            
            # Update add button command for bowling lanes
            lane_names = [f"Lane {i}" for i in range(1, 7)]  # Lanes 1-6
            self.add_button.configure(
                command=lambda: self.add_to_bowling_waitlist(lane_names)
            )
        
        # Update the displayed waitlist
        self.update_waitlist_tree()

    def add_to_waitlist(self, station_names):
        """Modified to accept station_names parameter and not show email dialog"""
        dialog = WaitlistDialog(self, station_names, title="Add to Waitlist", prompt="Enter details:")
        result = dialog.show()
        if result:
            self.waitlist.append(result)
            self.update_waitlist_tree()
            self.update_waitlist_count()  # Update the sidebar count label

    def add_to_bowling_waitlist(self, lane_names):
        """Add a new entry to the bowling waitlist without showing email dialog"""
        dialog = BowlingWaitlistDialog(self, lane_names, title="Add to Bowling Waitlist", prompt="Enter details:")
        result = dialog.show()
        if result:
            self.bowling_waitlist.append(result)
            self.update_waitlist_tree()
            self.update_waitlist_count()  # Update the sidebar count label

    def send_sms_notification(self, entry):
        """Send notification to the party with option to add email if not already present."""
        phone_number = entry['phone']
        party_name = entry['party']
        station_name = entry['station']
        
        # Check if the entry already has an email, if not, prompt for one
        if 'email' not in entry or not entry['email']:
            email_dialog = ctk.CTkInputDialog(
                title="Add Email Address", 
                text=f"No email found for {party_name}. Enter email address for notifications:"
            )
            email = email_dialog.get_input()
            if email:
                # Update the entry with the new email
                entry['email'] = email
                # Update the waitlist entry
                waitlist_type = self.waitlist_type_var.get() if hasattr(self, 'waitlist_type_var') else "Game Center"
                current_waitlist = self.bowling_waitlist if waitlist_type == "Bowling Lanes" else self.waitlist
                if entry in current_waitlist:
                    idx = current_waitlist.index(entry)
                    current_waitlist[idx] = entry
                self.update_waitlist_tree()
        
        # Now proceed with sending the notification
        if 'email' in entry and entry['email']:
            # Use the stored email
            recipient_email = entry['email']
            
            # Similar logic to send_sms but directly using the stored email
            email = "uvuslwcgamecenter@gmail.com"
            password = "jfuq wefo nxzk kkde"  # App password
            
            subject = f"UVU Gaming Center - Station Ready for {party_name}"
            message_body = (
                f"Hello {party_name},\n\n"
                f"Your station {station_name} at the UVU Gaming Center is ready for you!\n\n"
                "Please arrive within the next 10 minutes so your position isn't forfeited.\n\n"
                "Thank you,\n"
                "UVU Gaming Center Staff"
            )
            
            try:
                # Create the email message
                msg = MIMEText(message_body)
                msg['From'] = email
                msg['To'] = recipient_email
                msg['Subject'] = subject
                msg['Date'] = formatdate(localtime=True)
                
                # Send the email
                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(email, password)
                    server.sendmail(email, recipient_email, msg.as_string())
                    
                print(f"Email notification sent to: {recipient_email}")
                messagebox.showinfo("Success", f"Notification email sent to {recipient_email}")
                status = "Notification sent successfully!"
            except Exception as e:
                error_msg = str(e)
                print(f"Failed to send email notification: {error_msg}")
                messagebox.showerror("Error", f"Failed to send notification email.\n\nError: {error_msg}")
                status = f"Failed to send notification: {error_msg}"
        else:
            # If no email is stored, proceed with the standard notification function
            status = self.send_sms(phone_number, party_name, station_name)
        
        print(status)  # Print the status for debugging
        
        # Determine success based on status
        if "successfully" in status.lower():
            return "Notification sent successfully!"
        else:
            return "Failed to send notification."

    def edit_waitlist_entry(self, entry):
        """
        Open a dialog to edit an existing waitlist entry.
        """
        waitlist_type = self.waitlist_type_var.get()
        
        if waitlist_type == "Game Center":
            # Get the list of station names for the dropdown
            station_names = [f"{station.station_type} {station.station_num}" for station in self.stations]
            dialog_class = WaitlistDialog
            current_waitlist = self.waitlist
        else:  # Bowling Lanes
            station_names = [f"Lane {i}" for i in range(1, 7)]
            dialog_class = BowlingWaitlistDialog
            current_waitlist = self.bowling_waitlist

        # Create the edit dialog with the current entry's data
        dialog = dialog_class(
            self,
            station_names,
            title=f"Edit {'Bowling' if waitlist_type == 'Bowling Lanes' else 'Game Center'} Waitlist Entry",
            prompt="Edit details:"
        )

        # Pre-populate the dialog fields with the current entry's data
        dialog.name_entry.insert(0, entry["party"])
        dialog.phone_entry.insert(0, entry["phone"])
        dialog.size_entry.insert(0, str(entry["size"]))
        dialog.notes_entry.insert(0, entry["notes"])
        
        # Handle station differently for each dialog type
        if waitlist_type == "Game Center":
            dialog.station_var.set(entry["station"])
        
        # Pre-populate email if it exists
        if 'email' in entry and entry['email']:
            dialog.email_entry.insert(0, entry["email"])
        
        # If it's a bowling entry, pre-populate the lanes needed field
        if waitlist_type == "Bowling Lanes" and 'lanes_needed' in entry:
            dialog.lanes_needed_var.set(str(entry["lanes_needed"]))
            dialog.update_lane_selector()
            
            # Set preferred lanes if they exist
            if 'preferred_lanes' in entry and entry['preferred_lanes']:
                dialog.specify_lanes_var.set(True)
                dialog.toggle_lane_preferences()
                for i, lane in enumerate(entry['preferred_lanes']):
                    if i < len(dialog.lane_selectors):
                        lane_dropdown = [w for w in dialog.lane_selectors[i].winfo_children() if isinstance(w, ctk.CTkComboBox)]
                        if lane_dropdown:
                            lane_dropdown[0].set(lane)

        # Show the dialog and get the result
        result = dialog.show()
        if result:
            # Update the entry in the waitlist
            if entry in current_waitlist:
                index = current_waitlist.index(entry)
                current_waitlist[index] = result
                self.update_waitlist_tree()
                self.update_count_label()
            self.update_waitlist_tree()
            self.update_waitlist_count()  # Update the sidebar count label

    def add_to_bowling_waitlist(self, lane_names):
        """Add a new entry to the bowling waitlist"""
        dialog = BowlingWaitlistDialog(self, lane_names, title="Add to Bowling Waitlist", prompt="Enter details:")
        result = dialog.show()
        if result:
            # Optionally capture email at time of registration
            email_dialog = ctk.CTkInputDialog(
                title="Optional Email Address", 
                text=f"Enter email address for {result['party']} (optional, for notifications):"
            )
            email = email_dialog.get_input()
            if email:
                result['email'] = email
                
            self.bowling_waitlist.append(result)
            self.update_waitlist_tree()
            self.update_waitlist_count()  # Update the sidebar count label
            
    def send_sms(self, phone_number, party_name, station_name):
        """Send SMS via email-to-SMS gateways for all major carriers simultaneously."""
        email = "uvuslwcgamecenter@gmail.com"
        password = "jfuq wefo nxzk kkde"  # App password
        
        # Format the message (keep it short for SMS)
        message_body = (
            f"Hello {party_name}, your station {station_name} at UVU Gaming Center is ready! "
            "Please arrive within 10 minutes to keep your spot."
        )
        
        # Common carrier email-to-SMS gateways
        carriers = {
            "at&t": "@txt.att.net",
            "tmobile": "@tmomail.net",
            "verizon": "@vtext.com",
            "sprint": "@messaging.sprintpcs.com",
            "boost": "@sms.myboostmobile.com",
            "cricket": "@sms.cricketwireless.net",
            "uscellular": "@email.uscc.net",
            "metro": "@mymetropcs.com"
        }
        
        # Show a loading indicator
        loading_window = ctk.CTkToplevel(self)
        loading_window.title("Sending Notification")
        loading_window.geometry("300x100")
        loading_window.lift()
        loading_window.grab_set()
        
        ctk.CTkLabel(loading_window, text=f"Sending notification to {party_name}...").pack(pady=10)
        progress_bar = ctk.CTkProgressBar(loading_window)
        progress_bar.pack(pady=10, padx=20, fill="x")
        progress_bar.set(0)
        
        def send_notifications():
            success_count = 0
            error_messages = []
            
            # Try sending to all carriers
            for i, (carrier_name, suffix) in enumerate(carriers.items()):
                try:
                    # Update progress
                    progress = (i + 1) / len(carriers)
                    progress_bar.set(progress)
                    loading_window.update_idletasks()
                    
                    # Construct SMS gateway address
                    recipient = f"{phone_number}{suffix}"
                    
                    # Create the email message
                    msg = MIMEText(message_body)
                    msg['From'] = email
                    msg['To'] = recipient
                    msg['Subject'] = ""  # Keep empty for SMS
                    msg['Date'] = formatdate(localtime=True)
                    
                    # Connect to server and send
                    with smtplib.SMTP("smtp.gmail.com", 587) as server:
                        server.starttls()
                        server.login(email, password)
                        server.sendmail(email, recipient, msg.as_string())
                    
                    success_count += 1
                    
                except Exception as e:
                    error_messages.append(f"{carrier_name}: {str(e)}")
            
            # Close loading window
            loading_window.grab_release()
            loading_window.destroy()
            
            # Show results
            if success_count > 0:
                messagebox.showinfo(
                    "Notification Sent", 
                    f"Notification sent to {party_name} through {success_count} carriers."
                )
                return "Notification sent successfully!"
            else:
                error_details = "\n".join(error_messages[:3]) + "\n..."
                messagebox.showerror(
                    "Notification Failed", 
                    f"Failed to send notification to {party_name}.\n\nErrors encountered with all carriers."
                )
                return f"Failed to send notification: {error_messages[0]}"
        
        # Run the sending function in a separate thread
        threading.Thread(target=send_notifications).start()
        
        return "Sending notification..."

    def send_sms_notification(self, entry):
        """Send notification to the party."""
        phone_number = entry['phone']
        party_name = entry['party']
        station_name = entry['station']
        
        # Check if we have a stored email from registration
        if 'email' in entry and entry['email']:
            # Use the stored email
            recipient_email = entry['email']
            
            # Similar logic to send_sms but directly using the stored email
            email = "uvuslwcgamecenter@gmail.com"
            password = "jfuq wefo nxzk kkde"  # App password
            
            subject = f"UVU Gaming Center - Station Ready for {party_name}"
            message_body = (
                f"Hello {party_name},\n\n"
                f"Your station {station_name} at the UVU Gaming Center is ready for you!\n\n"
                "Please arrive within the next 10 minutes so your position isn't forfeited.\n\n"
                "Thank you,\n"
                "UVU Gaming Center Staff"
            )
            
            try:
                # Create the email message
                msg = MIMEText(message_body)
                msg['From'] = email
                msg['To'] = recipient_email
                msg['Subject'] = subject
                msg['Date'] = formatdate(localtime=True)
                
                # Send the email
                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(email, password)
                    server.sendmail(email, recipient_email, msg.as_string())
                    
                print(f"Email notification sent to: {recipient_email}")
                messagebox.showinfo("Success", f"Notification email sent to {recipient_email}")
                status = "Notification sent successfully!"
            except Exception as e:
                error_msg = str(e)
                print(f"Failed to send email notification: {error_msg}")
                messagebox.showerror("Error", f"Failed to send notification email.\n\nError: {error_msg}")
                status = f"Failed to send notification: {error_msg}"
        else:
            # If no email is stored, proceed with the standard notification function
            status = self.send_sms(phone_number, party_name, station_name)
        
        print(status)  # Print the status for debugging
        
        # Determine success based on status
        if "successfully" in status.lower():
            return "Notification sent successfully!"
        else:
            return "Failed to send notification."
    def send_sms_notification_old(self, entry):
        """Send an SMS notification to the party through all carriers."""
        phone_number = entry['phone']
        party_name = entry['party']
        station_name = entry['station']

        # Send the SMS through all carriers
        status = self.send_sms(phone_number, party_name, station_name)
        print(status)  # Print the status for debugging
        return status
        print(status)  # Print the status for debugging

    def handle_click(self, event):
        """Handle clicks on the treeview to show action buttons"""
        region = self.waitlist_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.waitlist_tree.identify_column(event.x)
            if column == "#7":  # Actions column
                item = self.waitlist_tree.identify_row(event.y)
                if item:
                    # Get the item's bbox
                    bbox = self.waitlist_tree.bbox(item, column)
                    if bbox:
                        self.show_action_buttons(item, bbox)

    def show_action_buttons(self, item, bbox):
        """Show action buttons in a popup window"""
        # Get the corresponding entry from waitlist
        idx = self.waitlist_tree.index(item)
        waitlist_type = self.waitlist_type_var.get()
        current_waitlist = self.bowling_waitlist if waitlist_type == "Bowling Lanes" else self.waitlist
        
        if idx >= len(current_waitlist):
            return
        entry = current_waitlist[idx]
        
        # Create popup window for buttons
        popup = tk.Toplevel(self.waitlist_window)
        popup.overrideredirect(True)
        
        # Position popup at the cell location
        tree_x = self.waitlist_tree.winfo_rootx()
        tree_y = self.waitlist_tree.winfo_rooty()
        popup.geometry(f"+{tree_x + bbox[0]}+{tree_y + bbox[1]}")
        
        # Create frame for buttons
        button_frame = ctk.CTkFrame(popup)
        button_frame.pack(padx=2, pady=2)
        
        # Create buttons
        complete_btn = ctk.CTkButton(
            button_frame, 
            text="✓", 
            width=30, 
            height=30,
            fg_color="green",
            hover_color="darkgreen",
            command=lambda: [self.complete_waitlist_entry(entry), popup.destroy()]
        )
        
        remove_btn = ctk.CTkButton(
            button_frame,
            text="✕",
            width=30,
            height=30,
            fg_color="red",
            hover_color="darkred",
            command=lambda: [self.remove_waitlist_entry(entry), popup.destroy()]
        )
        
        edit_btn = ctk.CTkButton(
            button_frame,
            text="✎",
            width=30,
            height=30,
            fg_color="blue",
            hover_color="darkblue",
            command=lambda: [self.edit_waitlist_entry(entry), popup.destroy()]
        )
        
        complete_btn.pack(side="left", padx=2)
        remove_btn.pack(side="left", padx=2)
        edit_btn.pack(side="left", padx=2)
        
        # Auto-close popup when mouse leaves
        def on_leave(e):
            popup.destroy()
        
        popup.bind('<Leave>', on_leave)

    def update_waitlist_tree(self, search_text=""):
        """Updated method to handle placeholder buttons and support both waitlist types"""
        # Clear existing entries and buttons
        for item in self.waitlist_tree.get_children():
            self.waitlist_tree.delete(item)
        
        # Clear existing buttons (except placeholders)
        for widget in self.buttons_frame.winfo_children()[1:]:  # Skip the header label
            if widget != self.placeholder_buttons_frame:  # Don't remove the placeholder buttons frame
                widget.destroy()
        
        # Determine which waitlist to display
        waitlist_type = self.waitlist_type_var.get() if hasattr(self, 'waitlist_type_var') else "Game Center"
        current_waitlist = self.bowling_waitlist if waitlist_type == "Bowling Lanes" else self.waitlist
        
        # If there are entries in the waitlist, hide placeholder buttons
        if current_waitlist:
            self.placeholder_buttons_frame.pack_forget()  # Hide placeholder buttons
        else:
            self.placeholder_buttons_frame.pack(pady=10, padx=5)  # Show placeholder buttons
        
        # Add entries and their corresponding buttons
        for entry in current_waitlist:
            if search_text and search_text not in entry['party'].lower():
                continue
            
            # Calculate wait time - handle differently for bowling lanes
            if waitlist_type == "Bowling Lanes":
                wait_time = "30 mins" # Default wait time for bowling
                quoted_time = f"{entry['quotedTime']} ({wait_time})"
            else:
                wait_time = self.calculate_wait_time(entry['station'])
                quoted_time = f"{entry['quotedTime']} ({wait_time})"
            
            # Insert row
            self.waitlist_tree.insert("", "end", values=(
                f"{entry['party']}\n{entry['phone']}",
                entry['size'],
                entry['notes'],
                entry['station'],
                quoted_time,
                entry['arrival']
            ))
            
            # Load icons
            check_icon = ctk.CTkImage(Image.open("./icon_cache/check.png"), size=(16, 16))
            x_icon = ctk.CTkImage(Image.open("./icon_cache/x.png"), size=(16, 16))
            pencil_icon = ctk.CTkImage(Image.open("./icon_cache/pencil.png"), size=(16, 16))
            message_icon = ctk.CTkImage(Image.open("./icon_cache/message-circle-more.png"), size=(16, 16))
            
            # Create a frame for this entry's buttons
            entry_buttons = ctk.CTkFrame(self.buttons_frame)
            entry_buttons.pack(pady=10, padx=5)
            
            # Create buttons for this entry
            ctk.CTkButton(
                entry_buttons,
                image=check_icon,
                text="",
                width=30,
                height=30,
                fg_color="green",
                hover_color="darkgreen",
                command=lambda e=entry: self.complete_waitlist_entry(e)
            ).pack(side="left", padx=2)
            
            ctk.CTkButton(
                entry_buttons,
                image=x_icon,
                text="",
                width=30,
                height=30,
                fg_color="red",
                hover_color="darkred",
                command=lambda e=entry: self.remove_waitlist_entry(e)
            ).pack(side="left", padx=2)
            
            ctk.CTkButton(
                entry_buttons,
                image=pencil_icon,
                text="",
                width=30,
                height=30,
                fg_color="blue",
                hover_color="darkblue",
                command=lambda e=entry: self.edit_waitlist_entry(e)
            ).pack(side="left", padx=2)
            
            # Add Send SMS button
            ctk.CTkButton(
                entry_buttons,
                image=message_icon,
                text="",
                width=30,
                height=30,
                fg_color="purple",
                hover_color="#800080",
                command=lambda e=entry: self.send_sms_notification(e)
            ).pack(side="left", padx=2)
        
        # Update count label with current waitlist count
        if hasattr(self, 'count_label'):
            self.count_label.configure(text=str(len(current_waitlist)))

    def edit_waitlist_entry(self, entry):
        """
        Open a dialog to edit an existing waitlist entry.
        """
        waitlist_type = self.waitlist_type_var.get()
        
        if waitlist_type == "Game Center":
            # Get the list of station names for the dropdown
            station_names = [f"{station.station_type} {station.station_num}" for station in self.stations]
            dialog_class = WaitlistDialog
            current_waitlist = self.waitlist
        else:  # Bowling Lanes
            station_names = [f"Lane {i}" for i in range(1, 7)]
            dialog_class = BowlingWaitlistDialog
            current_waitlist = self.bowling_waitlist

        # Create the edit dialog with the current entry's data
        dialog = dialog_class(
            self,
            station_names,
            title=f"Edit {'Bowling' if waitlist_type == 'Bowling Lanes' else 'Game Center'} Waitlist Entry",
            prompt="Edit details:"
        )

        # Pre-populate the dialog fields with the current entry's data
        dialog.name_entry.insert(0, entry["party"])
        dialog.phone_entry.insert(0, entry["phone"])
        dialog.size_entry.insert(0, str(entry["size"]))
        dialog.notes_entry.insert(0, entry["notes"])
        
        # Handle station differently for each dialog type
        if waitlist_type == "Game Center":
            dialog.station_var.set(entry["station"])
        
        # Pre-populate email if it exists
        if 'email' in entry and entry['email']:
            dialog.email_entry.insert(0, entry["email"])
        
        # If it's a bowling entry, pre-populate the lanes needed field
        if waitlist_type == "Bowling Lanes" and 'lanes_needed' in entry:
            dialog.lanes_needed_var.set(str(entry["lanes_needed"]))
            dialog.update_lane_selector()
            
            # Set preferred lanes if they exist
            if 'preferred_lanes' in entry and entry['preferred_lanes']:
                dialog.specify_lanes_var.set(True)
                dialog.toggle_lane_preferences()
                for i, lane in enumerate(entry['preferred_lanes']):
                    if i < len(dialog.lane_selectors):
                        lane_dropdown = [w for w in dialog.lane_selectors[i].winfo_children() if isinstance(w, ctk.CTkComboBox)]
                        if lane_dropdown:
                            lane_dropdown[0].set(lane)

        # Show the dialog and get the result
        result = dialog.show()
        if result:
            # Update the entry in the waitlist
            if entry in current_waitlist:
                index = current_waitlist.index(entry)
                current_waitlist[index] = result
                self.update_waitlist_tree()
                self.update_count_label()
            self.update_waitlist_tree()
            self.update_waitlist_count()  # Update the sidebar count label
    def remove_waitlist_entry(self, entry):
        """Remove an entry from the waitlist."""
        waitlist_type = self.waitlist_type_var.get()
        current_waitlist = self.bowling_waitlist if waitlist_type == "Bowling Lanes" else self.waitlist
        
        if entry in current_waitlist:
            current_waitlist.remove(entry)
            self.update_waitlist_tree()
            self.update_count_label()
            self.update_waitlist_count()  # This will now correctly count both lists
            self.update_notification_bubble()  # Update notification for all changes
            self.update_waitlist_count()
            
            # Only update notification bubble for game center waitlist
            if waitlist_type == "Game Center":
                self.update_notification_bubble()

    def complete_waitlist_entry(self, entry):
        """Mark an entry as complete."""
        waitlist_type = self.waitlist_type_var.get()
        current_waitlist = self.bowling_waitlist if waitlist_type == "Bowling Lanes" else self.waitlist
        
        if entry in current_waitlist:
            current_waitlist.remove(entry)
            self.update_waitlist_tree()
            self.update_count_label()
            self.update_waitlist_count()  # This will now correctly count both lists
            self.update_notification_bubble()  # Update notification for all changes

    def calculate_wait_time(self, station_name):
        try:
            for station in self.stations:
                if f"{station.station_type} {station.station_num}" == station_name:
                    elapsed_time = station.timer.get_time()
                    remaining_time = max(station.timer.time_limit - elapsed_time, 0)
                    minutes, seconds = divmod(remaining_time, 60)
                    return f"{int(minutes)} mins {int(seconds)} secs"
            return "N/A"
        except Exception as e:
            print(f"Error calculating wait time: {str(e)}")
            return "N/A"

if __name__ == "__main__":
    app = GamingCenterApp()
    app.iconbitmap("icon_cache/GamingCenterApp.ico")
    app.mainloop()
cProfile.run('app.mainloop()', 'restats')