import tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter import ttk
import customtkinter as ctk
from customtkinter import CTkImage
from pathlib import Path
from PIL import Image, ImageTk
import time
import requests
from io import BytesIO
import cairosvg
import json
import os
import re
from datetime import datetime
from StatsCompiler import StatsWindow  # Import the StatsWindow class from StatsCompiler.py

# Configure customtkinter
ctk.set_appearance_mode("dark")  # Default to light mode
ctk.set_default_color_theme("green")  # You can change this to other themes if desired


class TimerRing(ctk.CTkCanvas):
    def __init__(self, parent, width=65, height=65):
        super().__init__(parent, width=width, height=height, highlightthickness=0, bg="gray")
        self.width = width
        self.height = height
        self.time_limit = 2 * 60  # 35 minutes in seconds
        self.warning_threshold = 0.8 * self.time_limit  # 28 minutes
        self.warning_threshold2 = 0.9 * self.time_limit  # 31.5 minutes
        
    def draw_ring(self, progress):
        self.delete("all")  # Clear canvas
        
        # Calculate coordinates for the ring
        x0 = 6
        y0 = 6
        x1 = self.width - 6
        y1 = self.height - 6
        
        # Draw background ring
        self.create_oval(x0, y0, x1, y1, outline='#fff', width=4)
        
        if progress > 0:
            # Calculate color based on progress
            if progress * self.time_limit >= self.warning_threshold:
                color = 'orange'
            elif progress * self.time_limit >= self.warning_threshold2:
                color = 'red'
            else:
                color = '#00843d' # green
            
            # Calculate the extent of the arc
            extent = 360 * progress
            
            # Draw the progress arc
            self.create_arc(x0, y0, x1, y1, start=90, extent=-extent, outline=color, width=4, style='arc')

class StationTimer:
    def __init__(self):
        self.is_running = False
        self.start_time = 0
        self.elapsed_time = 0
        self.alert_shown = False
        self.TIME_LIMIT = 40 * 60  # 35 minutes in seconds

    def start(self):
        if not self.validate_fields():
            return
        if not self.is_running:
            self.is_running = True
            self.start_time = time.time() - self.elapsed_time

    def stop(self):
        if self.is_running:
            self.is_running = False
            self.elapsed_time = time.time() - self.start_time

    def reset(self):
        self.is_running = False
        self.elapsed_time = 0
        self.alert_shown = False

    def get_time(self):
        if self.is_running:
            return time.time() - self.start_time
        return self.elapsed_time

    def check_time_limit(self):
        return self.get_time() >= self.TIME_LIMIT
    

    def validate_fields(self):
        missing_fields = []
        
        # Debug print to check if name_entry exists
        print(f"Checking name_entry: {'name_entry' in self.__dict__}")
        if not hasattr(self, 'name_entry') or not self.name_entry.get().strip():
            missing_fields.append("Name")
        else:
            print(f"name_entry value: '{self.name_entry.get().strip()}'")
        
        # Debug print to check if id_entry exists
        print(f"Checking id_entry: {'id_entry' in self.__dict__}")
        if not hasattr(self, 'id_entry') or not self.id_entry.get().strip():
            missing_fields.append("ID Number (Enter N/A if not applicable)")
        else:
            print(f"id_entry value: '{self.id_entry.get().strip()}'")
        
        # Debug print to check if game_dropdown exists
        print(f"Checking game_dropdown: {'game_dropdown' in self.__dict__}")
        if hasattr(self, 'game_dropdown') and not self.game_var.get():
            missing_fields.append("Game")
        
        # Debug print to check if controller_dropdown exists
        print(f"Checking controller_dropdown: {'controller_dropdown' in self.__dict__}")
        if hasattr(self, 'controller_dropdown') and not self.controller_var.get():
            missing_fields.append("Controller")

        if missing_fields:
            messagebox.showerror("Error", f"Please fill out the following fields:\n" + "\n".join(missing_fields))
            return False
        return True

class Station(ctk.CTkFrame):
    def __init__(self, parent, app, station_type, station_num):
        super().__init__(parent, border_width=2, corner_radius=10)  # Add border and rounded corners
        self.parent = parent
        self.app = app  # Store reference to the app
        self.station_type = station_type
        self.station_num = station_num
        self.timer = StationTimer()
        self.setup_ui()
        self.update_timer()

    def setup_ui(self):
        # Header frame
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=5)

        # Station number label
        ctk.CTkLabel(header_frame, text=f"Station {self.station_num}", anchor="e").pack(side="right")

        icon_errors = set()

        def download_icon(icon_name, size=(20, 20), retries=3):
            """Download an SVG icon, cache it locally, and return a CTkImage."""
            cache_dir = Path("./icon_cache")
            cache_dir.mkdir(exist_ok=True)

            cached_file = cache_dir / f"{icon_name}.png"
            if cached_file.exists():
                return CTkImage(Image.open(cached_file), size=size)

            url = f"https://cdn.jsdelivr.net/npm/lucide-static@0.298.0/icons/{icon_name}.svg"

            for attempt in range(retries):
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        svg_content = response.content.decode("utf-8")
                        svg_content = re.sub(r'stroke="[^"]*"', 'stroke="white"', svg_content)
                        svg_content = re.sub(r'fill="[^"]*"', 'fill="none"', svg_content)
                        png_data = cairosvg.svg2png(bytestring=svg_content.encode("utf-8"))
                        img = Image.open(BytesIO(png_data))
                        img.save(cached_file)
                        return CTkImage(img, size=size)
                except Exception as e:
                    if icon_name not in icon_errors:
                        icon_errors.add(icon_name)
                        print(f"Failed to fetch icon {icon_name} on attempt {attempt + 1}: {e}")
                    time.sleep(1)

            print(f"Failed to fetch icon {icon_name} after {retries} attempts. Using fallback.")
            fallback_path = "./icon_cache/fallback.png"
            fallback_img = Image.new("RGB", size, color="gray")
            if Path(fallback_path).exists():
                fallback_img = Image.open(fallback_path)
            return CTkImage(fallback_img, size=size)

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

            # Name and ID fields
            name_frame = ctk.CTkFrame(self, fg_color="transparent", width=200)
            name_frame.pack(fill="x", padx=5, pady=2)
            ctk.CTkLabel(name_frame, text="Name:").grid(row=0, column=0, padx=(0,5), sticky="w")
            self.name_entry = ctk.CTkEntry(name_frame)
            self.name_entry.grid(row=0, column=1, padx=5, sticky="ew")
            ctk.CTkLabel(name_frame, text="ID #").grid(row=0, column=2, padx=(5,0), sticky="w")
            self.id_entry = ctk.CTkEntry(name_frame)
            self.id_entry.grid(row=0, column=3, padx=5, sticky="ew")

            # Game dropdown
            game_frame = ctk.CTkFrame(self, fg_color="transparent", width=20)
            game_frame.pack(fill="x", padx=5, pady=2)
            ctk.CTkLabel(game_frame, text="Game:").grid(row=0, column=0, padx=(0,5), sticky="w")
            self.game_var = ctk.StringVar()
            games = self.app.get_games_for_console(self.station_type)
            self.game_dropdown = ctk.CTkComboBox(
                game_frame, 
                variable=self.game_var, 
                values=games, 
                width=200
            )
            self.game_dropdown.grid(row=0, column=1, padx=5, sticky="ew")

            # Controller dropdown
            controller_frame = ctk.CTkFrame(self, fg_color="transparent")
            controller_frame.pack(fill="x", padx=5, pady=2)
            ctk.CTkLabel(controller_frame, text="Ctrl:").grid(row=0, column=0, padx=(0,20), sticky="ew")
            self.controller_var = ctk.StringVar()
            controllers = ["1", "2", "3", "4"]
            self.controller_dropdown = ctk.CTkComboBox(
                controller_frame, 
                variable=self.controller_var, 
                values=controllers, 
                width=200
            )
            self.controller_dropdown.grid(row=0, column=1, padx=5, sticky="ew")

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
            name_frame = ctk.CTkFrame(self, fg_color="transparent")
            name_frame.pack(fill="x", padx=5, pady=2)
            ctk.CTkLabel(name_frame, text="Name:").grid(row=0, column=0, padx=(0,5), sticky="w")
            self.console_var = ctk.StringVar(value=self.station_type)
            self.game_var = ctk.StringVar()
            self.controller_var = ctk.StringVar()
            self.name_entry = ctk.CTkEntry(name_frame)
            self.name_entry.grid(row=0, column=1, padx=5, sticky="ew")
            ctk.CTkLabel(name_frame, text="ID #").grid(row=0, column=2, padx=(5,0), sticky="w")
            self.id_entry = ctk.CTkEntry(name_frame)
            self.id_entry.grid(row=0, column=3, padx=5, sticky="ew")

        # Timer frame
        timer_frame = ctk.CTkFrame(self, fg_color="transparent")
        timer_frame.pack(fill="x", padx=2, pady=2)
        
        # Timer ring
        self.timer_ring = TimerRing(timer_frame, width=75, height=75)
        self.timer_ring.pack(side="left", padx=5)
        
        self.timer_label = ctk.CTkLabel(
            timer_frame, 
            text="00:00:00", 
            font=ctk.CTkFont(family="Helvetica", size=14)
        )
        self.timer_label.pack(side="left", padx=5)

        # Load control icons
        self.start_icon = download_icon('play', size=(15, 15))
        self.stop_icon = download_icon('square', size=(15, 15))
        self.reset_icon = download_icon('refresh-ccw', size=(15, 15))

        # Control buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(side="bottom", fill="x", padx=2, pady=2)
        ctk.CTkButton(button_frame, image=self.start_icon, text="Start", command=self.timer.start, width=30, height=30, corner_radius=20).pack(side="left", padx=2)
        ctk.CTkButton(button_frame, image=self.stop_icon, text="Stop", command=self.timer.stop, width=30, height=30, corner_radius=20).pack(side="left", padx=2)
        ctk.CTkButton(button_frame, image=self.reset_icon, text="Reset", command=self.timer.reset, width=30, height=30, corner_radius=20).pack(side="left", padx=2)
    def change_console_type(self):
        # Rest of the method remains the same as in original script
        self.station_type = self.console_var.get()
        games = self.app.get_games_for_console(self.station_type)
        self.game_dropdown.configure(values=games)
        self.game_var.set('')

    def update_timer(self):
        # Most of this method remains the same as in original script
        if self.timer.is_running:
            elapsed = self.timer.get_time()
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.timer_label.configure(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Update progress ring
            progress = min(elapsed / self.timer.TIME_LIMIT, 1.0)
            self.timer_ring.draw_ring(progress)
            
            # Update timer color based on elapsed time
            if elapsed >= self.timer.TIME_LIMIT:
                self.timer_label.configure(text_color="red")
                if not self.timer.alert_shown:
                    self.show_time_alert()
                    self.timer.alert_shown = True
            elif elapsed >= (self.timer.TIME_LIMIT * 0.8):
                self.timer_label.configure(text_color="orange")
            else:
                self.timer_label.configure(text_color="green")
        
        self.after(1000, self.update_timer)

    # Rest of the methods remain the same as in the original script
    def show_time_alert(self):
        station_info = f"Station {self.station_num} ({self.station_type})"
        user_name = self.name_entry.get()
        if user_name:
            station_info += f" - {user_name}"
        messagebox.showwarning("Time Limit Exceeded", 
                             f"{station_info}\nhas exceeded the 35-minute time limit.\nPlease ask the user to wrap up their session.")

    def start_timer(self):
        self.timer.start()

    def stop_timer(self):
        self.timer.stop()

    def reset_timer(self):
        self.log_usage()
        self.timer.reset()
        self.timer_label.configure(text="00:00:00", text_color="black")
        self.timer_ring.draw_ring(0)  # Reset progress ring
        self.name_entry.delete(0, tk.END)
        
        if self.station_type in ["XBOX", "Switch"]:
            self.game_dropdown.set("")
            self.controller_dropdown.set("")

    def log_usage(self):
        # Remains the same as in original script
        user_name = self.name_entry.get()
        game = self.game_var.get()
        controller = self.controller_var.get()
        duration = self.timer.get_time()
        formatted_duration = time.strftime("%H:%M:%S", time.gmtime(duration))
        with open("usage_log.txt", "a") as log_file:
            log_file.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]}\n")
            log_file.write(f"Station Type: {self.station_type}\n")
            log_file.write(f"Station Number: {self.station_num}\n")
            log_file.write(f"User Name: {user_name}\n")
            log_file.write(f"ID Number: {self.id_entry.get()}\n")
            log_file.write(f"Duration: {formatted_duration}\n")
            log_file.write(f"Game: {game}\n")
            log_file.write(f"Controllers: {controller}\n")
            log_file.write("--------------------------------------------------\n")

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
        self.games = self.load_games()
        self.setup_ui()
        
        self.lift()
        self.focus_force()
        self.grab_set()

    def load_games(self):
        if os.path.exists('games_list.json'):
            with open('games_list.json', 'r') as f:
                return json.load(f)
        return {"Switch": [], "XBOX": []}

    def save_games(self, games_dict):
        with open('games_list.json', 'w') as f:
            json.dump(games_dict, f)

    def setup_ui(self):
        # Customize the ttk.Notebook style to match the dark theme
        style = ttk.Style()
        style.theme_use("clam")  # Use a theme that supports custom colors
        style.configure("TNotebook", background="#333333", borderwidth=0)  # Dark background for the notebook, remove border
        style.configure("TNotebook.Tab", 
                        background="#444444",  # Dark background for the tabs
                        foreground="white",    # Light text for the tabs
                        padding=[10, 5])       # Padding for the tabs
        style.map("TNotebook.Tab", 
                  background=[("selected", "#00843d")],  # Green for selected tab background
                  foreground=[("selected", "white")])   # White text for selected tab

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.switch_tab = ttk.Frame(self.notebook)
        self.xbox_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.switch_tab, text='Switch Games')
        self.notebook.add(self.xbox_tab, text='XBOX Games')

        self.setup_games_tab(self.switch_tab, "Switch")
        self.setup_games_tab(self.xbox_tab, "XBOX")

    def setup_games_tab(self, parent, console):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill='both', expand=True, padx=0, pady=0)

        # Use CTkTextbox with state="disabled" to make it read-only
        games_textbox = ctk.CTkTextbox(frame, state="disabled")
        games_textbox.pack(side='left', fill='both', expand=True)

        # Enable the textbox temporarily to insert games
        games_textbox.configure(state="normal")
        for game in self.games[console]:
            games_textbox.insert('end', game + "\n")
        games_textbox.configure(state="disabled")

        button_frame = ctk.CTkFrame(frame)
        button_frame.pack(side='right', fill='y')

        add_button = ctk.CTkButton(button_frame, text="Add", command=lambda: self.add_game(console, games_textbox))
        add_button.pack(pady=5)
        remove_button = ctk.CTkButton(button_frame, text="Remove", command=lambda: self.remove_game(console, games_textbox))
        remove_button.pack(pady=5)

    def add_game(self, console, games_textbox):
        dialog = CustomDialog(self, title="Add Game", prompt=f"Enter new game for {console}:")
        new_game = dialog.show()
        if new_game:
            self.games[console].append(new_game)
            self.update_games_textbox(console, games_textbox)
            self.save_games(self.games)

    def remove_game(self, console, games_textbox):
        selected_game = games_textbox.get("1.0", "end-1c").splitlines()[-1]
        if selected_game:
            self.games[console].remove(selected_game)
            self.update_games_textbox(console, games_textbox)
            self.save_games(self.games)

    def update_games_textbox(self, console, games_textbox):
        # Enable the textbox temporarily to update its content
        games_textbox.configure(state="normal")
        games_textbox.delete("1.0", "end")
        for game in self.games[console]:
            games_textbox.insert('end', game + "\n")
        games_textbox.configure(state="disabled")
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
        self.geometry("300x200")
        self.resizable(False, False)

        self.result = None

        self.label = ctk.CTkLabel(self, text=prompt)
        self.label.pack(pady=10)

        self.name_entry = ctk.CTkEntry(self, placeholder_text="Name")
        self.name_entry.pack(pady=10, padx=10, fill="x")

        self.station_var = tk.StringVar()
        self.station_dropdown = ctk.CTkComboBox(self, variable=self.station_var, values=stations)
        self.station_dropdown.pack(pady=10, padx=10, fill="x")

        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(pady=10)

        self.ok_button = ctk.CTkButton(self.button_frame, text="OK", command=self.on_ok)
        self.ok_button.pack(side="left", padx=5)

        self.cancel_button = ctk.CTkButton(self.button_frame, text="Cancel", command=self.on_cancel)
        self.cancel_button.pack(side="left", padx=5)

        self.name_entry.bind("<Return>", lambda event: self.on_ok())
        self.name_entry.bind("<Escape>", lambda event: self.on_cancel())

    def on_ok(self):
        name = self.name_entry.get().strip()
        station = self.station_var.get()
        if name and station:
            self.result = {"name": name, "station": station}
            self.grab_release()  # Release the grab before destroying
            self.destroy()
        else:
            messagebox.showerror("Error", "Please fill out all fields.")

    def on_cancel(self):
        self.result = None
        self.grab_release()  # Release the grab before destroying
        self.destroy()

    def show(self):
        self.grab_set()
        self.wait_window(self)  # Wait for the dialog to close
        return self.result
class GamingCenterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gaming Center App")
        self.geometry("1500x950")
        self.stations = []  # Keep track of all stations
        self.waitlist = []  # List to keep track of people on the waitlist
        self.create_menu()
        self.setup_ui()

    def setup_ui(self):
        # Create main container with more padding
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        # Configure grid weights
        for i in range(6):  # 6 rows
            main_frame.grid_rowconfigure(i, weight=1)
        for i in range(3):  # 3 columns
            main_frame.grid_columnconfigure(i, weight=1)
        # Add button to view and edit games at the top right
        games_button = ctk.CTkButton(main_frame, text="View/Edit Games", command=self.open_games_window, corner_radius=20)
        waitlist_button= ctk.CTkButton(main_frame, text="Waitlist", command=self.show_waitlist_window, corner_radius=20)
        waitlist_button.grid(row=0, column=3, padx=10, pady=10, sticky="ne")
        games_button.grid(row=0, column=2, padx=10, pady=10, sticky="ne")

        # Notification bubble for waitlist
        self.notification_bubble = ctk.CTkLabel(main_frame, text="", fg_color="red", text_color="white", corner_radius=10)
        self.notification_bubble.grid(row=0, column=1, padx=10, pady=10, sticky="ne")
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
                return games_dict.get(console_type, [])
        except FileNotFoundError:
            return []

    def update_all_stations_games(self):
        for station in self.stations:
            if hasattr(station, 'update_games_list'):
                station.update_games_list()

    def create_menu(self):
        menubar = ctk.CTkFrame(self, fg_color="gray20")
        menubar.pack(side="top", fill="x")

        file_button = ctk.CTkButton(menubar, text="File", command=self.show_file_menu, fg_color="gray20", corner_radius=0)
        file_button.pack(side="left", padx=0, pady=0)

        view_button = ctk.CTkButton(menubar, text="View", command=self.show_view_menu, fg_color="gray20", corner_radius=0)
        view_button.pack(side="left", padx=0, pady=0)

    def show_file_menu(self):
        menu = tk.Menu(self, tearoff=0)
        menu.config(bg="gray20", fg="white", activebackground="gray30", activeforeground="white", font=("Helvetica", 12))
        menu.add_command(label="View Statistics", command=self.open_stats_window)
        menu.add_separator()
        menu.add_command(label="Exit", command=self.quit)
        menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())

    def show_view_menu(self):
        menu = tk.Menu(self, tearoff=0)
        menu.config(bg="gray20", fg="white", activebackground="gray30", activeforeground="white", font=("Helvetica", 12))
        # Add view menu items here
        menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        

    def open_stats_window(self):
        StatsWindow(self)

    def open_games_window(self):
        GamesWindow(self)

    def update_notification_bubble(self):
        if self.waitlist:
            self.notification_bubble.configure(text=str(len(self.waitlist)))
            self.notification_bubble.pack(side=tk.LEFT, padx=5)
        else:
            self.notification_bubble.pack_forget()

    def show_waitlist_window(self):
        waitlist_window = ctk.CTkToplevel(self)
        waitlist_window.title("Waitlist")
        waitlist_window.geometry("500x500")

        waitlist_window.lift()
        waitlist_window.focus_force()
        waitlist_window.grab_set()

        # Create Treeview with custom style
        style = ttk.Style()
        style.theme_use("clam")  # Use a theme that supports custom colors
        style.configure("Custom.Treeview", 
                        background="#333333",  # Dark background
                        foreground="white",    # Light text
                        fieldbackground="#333333",  # Background for cells
                        rowheight=25)
        style.configure("Custom.Treeview.Heading", 
                        background="#444444",  # Darker background for headings
                        foreground="white",    # Light text for headings
                        relief="flat")         # Flat relief for headings
        style.map("Custom.Treeview", 
                background=[("selected", "#00843d")],  # Green for selected background
                foreground=[("selected", "white")])   # White text for selected items

        columns = ("Name", "Station", "Wait Time")
        waitlist_tree = ttk.Treeview(waitlist_window, columns=columns, show="headings", style="Custom.Treeview")
        waitlist_tree.heading("Name", text="Name", command=lambda: self.sort_treeview_column(waitlist_tree, "Name", False))
        waitlist_tree.heading("Station", text="Station", command=lambda: self.sort_treeview_column(waitlist_tree, "Station", False))
        waitlist_tree.heading("Wait Time", text="Wait Time", command=lambda: self.sort_treeview_column(waitlist_tree, "Wait Time", False))
        waitlist_tree.pack(fill=tk.BOTH, expand=True)

        # Insert waitlist data
        self.update_waitlist_tree(waitlist_tree)

        add_button = ctk.CTkButton(waitlist_window, text="Add to Waitlist", command=lambda: self.add_to_waitlist(waitlist_tree))
        add_button.pack(pady=5)

        remove_button = ctk.CTkButton(waitlist_window, text="Remove from Waitlist", command=lambda: self.remove_from_waitlist(waitlist_tree))
        remove_button.pack(pady=5)

    def update_waitlist_tree(self, waitlist_tree):
        # Clear existing items
        for item in waitlist_tree.get_children():
            waitlist_tree.delete(item)
        
        # Insert new items
        for person in self.waitlist:
            wait_time = self.calculate_wait_time(person['station'])
            waitlist_tree.insert("", "end", values=(person['name'], person['station'], wait_time))

    def add_to_waitlist(self, waitlist_tree):
        station_names = [f"{station.station_type} {station.station_num}" for station in self.stations]
        dialog = WaitlistDialog(self, station_names, title="Add to Waitlist", prompt="Enter details:")
        result = dialog.show()
        if result:
            self.waitlist.append(result)
            self.update_waitlist_tree(waitlist_tree)  # Update the tree immediately

    def remove_from_waitlist(self, waitlist_tree):
        selected_item = waitlist_tree.selection()
        if not selected_item:
            return

        item_index = waitlist_tree.index(selected_item[0])
        self.waitlist.pop(item_index)
        self.update_waitlist_tree(waitlist_tree)  # Update the tree immediately

    def calculate_wait_time(self, station_name):
        for station in self.stations:
            if f"{station.station_type} {station.station_num}" == station_name:
                elapsed_time = station.timer.get_time()
                remaining_time = max(station.timer.TIME_LIMIT - elapsed_time, 0)
                minutes, seconds = divmod(remaining_time, 60)
                return f"{int(minutes)} mins {int(seconds)} secs"
        return "N/A"
if __name__ == "__main__":
    app = GamingCenterApp()
    app.mainloop()
