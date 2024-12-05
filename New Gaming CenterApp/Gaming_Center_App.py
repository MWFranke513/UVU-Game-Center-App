import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
from tkinter import messagebox
import time
from datetime import datetime
import math
from StatsCompiler import StatsWindow  # Import the StatsWindow class from StatsCompiler.py
import json
import os


## Still need to add ----------------------------------------------
# 1. Add the ability to add and remove stations
# 2. Add the ability to move stations around in the layout
# 3. Add the ability to save and load the station layout
# Finish adding the stats window
# Polish up the UI and make it look nice, modern, and user-friendly.
# Performance improvments and optimizations since this is a python application

dark_mode_styles = {
    "bg": "#2e2e2e",
    "fg": "#ffffff",
    "button_bg": "#444444",
    "button_fg": "#ffffff"
}

def toggle_dark_mode():
    if app.cget("bg") == "white":
        app.config(bg=dark_mode_styles["bg"])
        for widget in app.winfo_children():
            try:
                widget.config(bg=dark_mode_styles["button_bg"], fg=dark_mode_styles["button_fg"])
            except tk.TclError:
                pass  # Ignore widgets that do not support bg and fg options
    else:
        app.config(bg="white")
        for widget in app.winfo_children():
            try:
                widget.config(bg="SystemButtonFace", fg="black")
            except tk.TclError:
                pass  # Ignore widgets that do not support bg and fg options


class TimerRing(tk.Canvas):
    def __init__(self, parent, width=65, height=65):
        super().__init__(parent, width=width, height=height, highlightthickness=0)
        self.width = width
        self.height = height
        self.time_limit = 40 * 60  # 35 minutes in seconds
        self.warning_threshold = 0.8 * self.time_limit  # 28 minutes
        
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
        
        # Validate name entry
        if not hasattr(self, 'name_entry') or not self.name_entry.get().strip():
            missing_fields.append("Name")
        
        # Validate ID entry
        if not hasattr(self, 'id_entry') or not self.id_entry.get().strip():
            missing_fields.append("ID Number")
        
        # Validate game dropdown for console stations
        if hasattr(self, 'game_dropdown'):
            if not self.game_var.get():
                missing_fields.append("Game")
        
        # Validate controller dropdown for console stations
        if hasattr(self, 'controller_dropdown'):
            if not self.controller_var.get():
                missing_fields.append("Controller")

        if missing_fields:
            messagebox.showerror("Error", f"Please fill out the following fields:\n" + "\n".join(missing_fields))
            return False
        return True

    


class Station(tk.Frame):
    def __init__(self, parent, app, station_type, station_num):
        super().__init__(parent, borderwidth=2, relief="groove")  # Add border
        self.parent = parent
        self.app = app  # Store reference to the app
        self.station_type = station_type
        self.station_num = station_num
        self.timer = StationTimer()
        self.setup_ui()
        self.update_timer()

    def setup_ui(self):
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        # Console type toggle
        self.console_var = tk.StringVar(value=self.station_type)
        # ttk.Radiobutton(header_frame, text="XBOX", variable=self.console_var, value="XBOX", command=self.change_console_type).pack(side="left")
        # ttk.Radiobutton(header_frame, text="Switch", variable=self.console_var, value="Switch", command=self.change_console_type).pack(side="left")
        
        ttk.Label(header_frame, text=f"Station {self.station_num}").pack(side="right")  # Move station number to the right

        if self.station_type in ["XBOX", "Switch"]:
            ttk.Radiobutton(header_frame, text="XBOX", variable=self.console_var, value="XBOX", command=self.change_console_type).pack(side="left")
            ttk.Radiobutton(header_frame, text="Switch", variable=self.console_var, value="Switch", command=self.change_console_type).pack(side="left")
            # Name and ID fields
            name_frame = ttk.Frame(self)
            name_frame.pack(fill="x", padx=5, pady=2)
            ttk.Label(name_frame, text="Name:\t").pack(side="left")
            self.name_entry = ttk.Entry(name_frame)
            self.name_entry.pack(side="left", fill="x", expand=True, padx=5)
            ttk.Label(name_frame, text="ID #").pack(side="left")
            self.id_entry = ttk.Entry(name_frame)
            self.id_entry.pack(side="left", fill="x", expand=True, padx=5)

            # Game and controller dropdowns
            game_frame = ttk.Frame(self)
            game_frame.pack(fill="x", padx=5, pady=2)
            ttk.Label(game_frame, text="Game:\t").pack(side="left")
            self.game_var = tk.StringVar()
            games = self.app.get_games_for_console(self.station_type)  # Use app to get games
            self.game_dropdown = ttk.Combobox(game_frame, textvariable=self.game_var, values=games, width=15)
            self.game_dropdown.pack(side="left", padx=5)

            controller_frame = ttk.Frame(self)
            controller_frame.pack(fill="x", padx=5, pady=2)
            ttk.Label(controller_frame, text="Ctrl:\t").pack(side="left")
            self.controller_var = tk.StringVar()
            controllers = ["1", "2", "3", "4"]
            self.controller_dropdown = ttk.Combobox(controller_frame, textvariable=self.controller_var, values=controllers, width=15)
            self.controller_dropdown.pack(side="left", padx=5)

            # Initialize timer with console-specific attributes
            self.timer.name_entry = self.name_entry
            self.timer.id_entry = self.id_entry
            self.timer.game_dropdown = self.game_dropdown
            self.timer.game_var = self.game_var
            self.timer.controller_dropdown = self.controller_dropdown
            self.timer.controller_var = self.controller_var

        else:  # For other station types
            ttk.Label(header_frame, text=self.station_type).pack(side="left")
                        # Name and ID fields
            name_frame = ttk.Frame(self)
            name_frame.pack(fill="x", padx=5, pady=2)
            ttk.Label(name_frame, text="Name:\t").pack(side="left")
            self.console_var = tk.StringVar(value=self.station_type)
            self.game_var = tk.StringVar()
            self.controller_var = tk.StringVar()
            self.name_entry = ttk.Entry(name_frame)
            self.name_entry.pack(side="left", fill="x", expand=True, padx=5)
            ttk.Label(name_frame, text="ID #").pack(side="left")
            self.id_entry = ttk.Entry(name_frame)
            self.id_entry.pack(side="left", fill="x", expand=True, padx=5)

            station_frame = ttk.Frame(self)
            station_frame.pack(fill="x", padx=5)
            ttk.Label(station_frame, text="Station\t").pack(side="left")
            self.station_num_entry = ttk.Entry(station_frame, width=5)
            self.station_num_entry.insert(0, str(self.station_num))
            self.station_num_entry.configure(state="readonly")
            self.station_num_entry.pack(side="left", padx=5)

        # Timer controls with ring
        timer_frame = ttk.Frame(self)
        timer_frame.pack(side="bottom", fill="x", padx=2, pady=2)
        # Initialize timer with basic attributes
        self.timer.name_entry = self.name_entry
        self.timer.id_entry = self.id_entry
        
        # Add timer ring
        self.timer_ring = TimerRing(timer_frame, width=75, height=75)  # Increase size of timer ring
        self.timer_ring.pack(side="right", padx=5)
        
        self.timer_label = ttk.Label(self.timer_ring, text="00:00:00", font=("Helvetica", 12))  # Increase font size of timer label
        self.timer_label.pack(side="right", padx=5, pady=25)

        # Stopwatch buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(side="bottom", fill="x", padx=2, pady=2)
        ttk.Button(button_frame, text="Start", command=self.start_timer).pack(side="left", padx=2)
        ttk.Button(button_frame, text="Stop", command=self.stop_timer).pack(side="left", padx=2)
        ttk.Button(button_frame, text="Reset", command=self.reset_timer).pack(side="left", padx=2)

    def change_console_type(self):
        self.station_type = self.console_var.get()
        games = self.app.get_games_for_console(self.station_type)
        self.game_dropdown['values'] = games
        self.game_var.set('')

    def update_timer(self):
        if self.timer.is_running:
            elapsed = self.timer.get_time()
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.timer_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Update progress ring
            progress = min(elapsed / self.timer.TIME_LIMIT, 1.0)
            self.timer_ring.draw_ring(progress)
            
            # Update timer color based on elapsed time
            if elapsed >= self.timer.TIME_LIMIT:
                self.timer_label.config(foreground="red")
                if not self.timer.alert_shown:
                    self.show_time_alert()
                    self.timer.alert_shown = True
            elif elapsed >= (self.timer.TIME_LIMIT * 0.8):
                self.timer_label.config(foreground="orange")
            else:
                self.timer_label.config(foreground="green")
        
        self.after(1000, self.update_timer)

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
        self.timer_label.config(text="00:00:00", foreground="black")
        self.timer_ring.draw_ring(0)  # Reset progress ring
        self.name_entry.delete(0, tk.END)
        
        if self.station_type in ["XBOX", "Switch"]:
            self.game_dropdown.set("")
            self.controller_dropdown.set("")

    def reset_station(self):
        self.log_usage()
        self.timer.reset()
        self.timer_label.config(text="00:00:00", foreground="black")
        self.timer_ring.draw_ring(0)  # Reset progress ring
        self.name_entry.delete(0, tk.END)
        
        if self.station_type in ["XBOX One", "Switch"]:
            self.game_dropdown.set("")
            self.controller_dropdown.set("")

    def log_usage(self):
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
        if self.station_type in ["XBOX One", "Switch"]:
            console_type = "XBOX" if self.station_type == "XBOX One" else "Switch"
            games = self.parent.get_games_for_console(console_type)
            self.game_dropdown['values'] = games
            if self.game_var.get() not in games:
                self.game_var.set('')
class GamesWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("View/Edit Games")
        self.geometry("400x300")
        self.parent = parent  # Store reference to parent
        self.games = self.load_games()  # Load games from file
        self.setup_ui()

    def load_games(self):
        try:
            with open('games_list.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default games if file doesn't exist
            default_games = {
                "Switch": ["Mario Kart 8", "Animal Crossing"],
                "XBOX": ["Halo Infinite", "Forza Horizon 5"]
            }
            self.save_games(default_games)
            return default_games

    def save_games(self, games_dict):
        with open('games_list.json', 'w') as f:
            json.dump(games_dict, f)

    def setup_ui(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.switch_tab = ttk.Frame(self.notebook)
        self.xbox_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.switch_tab, text='Switch Games')
        self.notebook.add(self.xbox_tab, text='XBOX Games')

        self.setup_games_tab(self.switch_tab, "Switch")
        self.setup_games_tab(self.xbox_tab, "XBOX")

    def setup_games_tab(self, parent, console):
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        games_listbox = tk.Listbox(frame)
        games_listbox.pack(side='left', fill='both', expand=True)

        for game in self.games[console]:
            games_listbox.insert('end', game)

        button_frame = ttk.Frame(frame)
        button_frame.pack(side='right', fill='y')

        add_button = ttk.Button(button_frame, text="Add", command=lambda: self.add_game(console, games_listbox))
        add_button.pack(pady=5)
        remove_button = ttk.Button(button_frame, text="Remove", command=lambda: self.remove_game(console, games_listbox))
        remove_button.pack(pady=5)

    def add_game(self, console, games_listbox):
        new_game = simpledialog.askstring("Add Game", f"Enter new game for {console}:")
        if new_game:
            self.games[console].append(new_game)
            self.update_games_listbox(console, games_listbox)
            self.save_games(self.games)
            self.parent.update_all_stations_games()  # Update all station dropdowns

    def remove_game(self, console, games_listbox):
        selected_game = games_listbox.get(tk.ACTIVE)
        if selected_game:
            self.games[console].remove(selected_game)
            self.update_games_listbox(console, games_listbox)
            self.save_games(self.games)
            self.parent.update_all_stations_games()  # Update all station dropdowns

    def update_games_listbox(self, console, games_listbox):
        games_listbox.delete(0, tk.END)
        for game in self.games[console]:
            games_listbox.insert('end', game)

class StationSelectionDialog(simpledialog.Dialog):
    def __init__(self, parent, title, stations):
        self.stations = stations
        self.selected_station = None
        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text="Select Station:").grid(row=0, column=0, padx=10, pady=10)
        self.station_var = tk.StringVar()
        self.station_dropdown = ttk.Combobox(master, textvariable=self.station_var, values=self.stations)
        self.station_dropdown.grid(row=0, column=1, padx=10, pady=10)
        return self.station_dropdown

    def apply(self):
        self.selected_station = self.station_var.get()

class GamingCenterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gaming Center App")
        self.geometry("1200x1000")
        self.stations = []  # Keep track of all stations
        self.waitlist = []  # List to keep track of people on the waitlist
        self.create_menu()
        self.setup_ui()

    def setup_ui(self):
        # Create main container with more padding
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        # Configure grid weights
        for i in range(6):  # 6 rows
            main_frame.grid_rowconfigure(i, weight=1)
        for i in range(3):  # 3 columns
            main_frame.grid_columnconfigure(i, weight=1)
        # Add button to view and edit games at the top right
        games_button = ttk.Button(main_frame, text="View/Edit Games", command=self.open_games_window)
        waitlist_button= ttk.Button(main_frame, text="Waitlist", command=self.show_waitlist_window)
        waitlist_button.grid(row=0, column=3, padx=10, pady=10, sticky="ne")
        games_button.grid(row=0, column=2, padx=10, pady=10, sticky="ne")
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

        # Add the "View/Edit Games List" button
        view_edit_games_button = tk.Button(self, text="View/Edit Games List")
        view_edit_games_button.pack(pady=10)

        # Add the waitlist button with notification bubble
        waitlist_frame = tk.Frame(self)
        waitlist_frame.pack(pady=10)

        self.waitlist_button = tk.Button(waitlist_frame, text="Waitlist", command=self.show_waitlist_window)
        self.waitlist_button.pack(side=tk.LEFT)

        self.notification_bubble = tk.Label(waitlist_frame, text="", bg="red", fg="white", font=("Arial", 10, "bold"))
        self.notification_bubble.pack(side=tk.LEFT, padx=5)
        self.update_notification_bubble()

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
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="View Statistics", command=self.open_stats_window)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Dark Mode", command=toggle_dark_mode)
        

    def open_stats_window(self):
        StatsWindow(self)

    def open_games_window(self):
        GamesWindow(self)

    def update_notification_bubble(self):
        if self.waitlist:
            self.notification_bubble.config(text=str(len(self.waitlist)))
            self.notification_bubble.pack(side=tk.LEFT, padx=5)
        else:
            self.notification_bubble.pack_forget()

    def show_waitlist_window(self):
        waitlist_window = tk.Toplevel(self)
        waitlist_window.title("Waitlist")
        waitlist_window.geometry("500x500")

        waitlist_listbox = tk.Listbox(waitlist_window)
        waitlist_listbox.pack(fill=tk.BOTH, expand=True)

        for i, person in enumerate(self.waitlist):
            waitlist_listbox.insert(tk.END, f"{i+1}. {person['name']} - Station: {person['station']} - Wait Time: {self.calculate_wait_time(person['station'])}")

        add_button = tk.Button(waitlist_window, text="Add to Waitlist", command=lambda: self.add_to_waitlist(waitlist_listbox))
        add_button.pack(pady=5)

        remove_button = tk.Button(waitlist_window, text="Remove from Waitlist", command=lambda: self.remove_from_waitlist(waitlist_listbox))
        remove_button.pack(pady=5)

    def add_to_waitlist(self, waitlist_listbox):
        name = simpledialog.askstring("Add to Waitlist", "Enter Name:")
        if not name:
            return

        station_names = [f"{station.station_type} {station.station_num}" for station in self.stations]
        dialog = StationSelectionDialog(self, "Select Station", station_names)
        if not dialog.selected_station:
            return

        self.waitlist.append({"name": name, "station": dialog.selected_station})
        self.update_notification_bubble()
        self.update_waitlist_listbox(waitlist_listbox)

    def remove_from_waitlist(self, waitlist_listbox):
        selected_index = waitlist_listbox.curselection()
        if not selected_index:
            return

        self.waitlist.pop(selected_index[0])
        self.update_notification_bubble()
        self.update_waitlist_listbox(waitlist_listbox)

    def update_waitlist_listbox(self, waitlist_listbox):
        waitlist_listbox.delete(0, tk.END)
        for i, person in enumerate(self.waitlist):
            waitlist_listbox.insert(tk.END, f"{i+1}. {person['name']} - Station: {person['station']} - Wait Time: {self.calculate_wait_time(person['station'])}")

    def calculate_wait_time(self, station):
        # Placeholder function to calculate wait time based on station's timer
        return "10 mins"


if __name__ == "__main__":
    app = GamingCenterApp()
    app.mainloop()
