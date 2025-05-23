import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import tkinter as tk
from tkinter import simpledialog, messagebox, ttk, font as tkFont
import customtkinter as ctk
from customtkinter import CTkImage
from CTkScrollableDropdown import CTkScrollableDropdown
import pandas
from CTkListbox import *
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw
import PIL.Image, PIL.ImageDraw, PIL.ImageTk
import time
import requests
from io import BytesIO
import math
import json
import re
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate
import threading
import cProfile
from datetime import datetime, timedelta
from StatsCompiler import StatsManager
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import textwrap  # <-- Add this import
from functools import partial

# Configure customtkinter
ctk.set_appearance_mode("dark")  # Default to light mode
ctk.set_default_color_theme("./uvu_green.json")  # You can change this to other themes if desired


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
    def __init__(self, parent, width=160, height=160):
        # Get parent background color
        parent_fg = parent.cget("fg_color")
        if isinstance(parent_fg, str) and parent_fg != "transparent":
            parent_bg = parent_fg
        else:
            appearance_mode = ctk.get_appearance_mode()
            parent_bg = "#171717" if appearance_mode == "Dark" else "#e6f2ec"  # fallback color

        super().__init__(parent, width=width, height=height, 
                         highlightthickness=0, bg=parent_bg)
        
        # Configure rendering quality
        self._configure_antialiasing()
        
        self.width = width
        self.height = height
        self.time_limit = 1 * 60
        self.warning_threshold = 0.8 * self.time_limit
        self.warning_threshold2 = 0.9 * self.time_limit
        
        self.is_running = False
        self.start_time = 0
        self.elapsed_time = 0
        self.alert_shown = False
        self.last_progress = 0
        self._update_loop_id = None
        self._blink_loop_id = None
        self.is_blinking = False
        self.blink_state = True
        self.blink_count = 0
        
        # Initialize fields
        self.name_entry = None
        self.id_entry = None
        self.game_dropdown = None
        self.controller_dropdown = None
        self.game_var = None
        self.controller_var = None
        self.station_type = None
        self.station_num = None
        
        # Timer display
        self.label_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.label_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        font_family = self.parent_station.app.get_font_family() if hasattr(self, 'parent_station') else "Helvetica"
        self.timer_label = ctk.CTkLabel(
            self.label_frame, 
            text="00:00:00", 
            font=ctk.CTkFont(family=font_family, size=12, weight="normal"),
            fg_color="transparent"
        )
        self.timer_label.pack(expand=True)
        
        # Draw the initial gray ring at startup
        self.draw_ring(0)

    def _configure_antialiasing(self):
        """Configure rendering quality settings"""
        try:
            self.tk.call("tk", "scaling", 2.0)
            self.tk.call("::tk::unsupported::MacWindowStyle", "style", self._w, "textured", "dark")
            self.tk.call('::tk::unsupported::ExposeCommandOptions', 'arc', '-smooth', '1')
        except Exception:
            pass

    def start(self):
        if not self.validate_fields():
            return
        if not self.is_running:
            self.is_running = True
            self.start_time = time.time() - self.elapsed_time
            self.update_timer()

        if hasattr(self, 'parent_station'):
            self.parent_station.update_button_states(is_active=True)

    def stop(self):
        if self.is_running:
            self.elapsed_time = time.time() - self.start_time
            self.is_running = False
        if self._update_loop_id:
            self.after_cancel(self._update_loop_id)
            self._update_loop_id = None
        if self._blink_loop_id:
            self.after_cancel(self._blink_loop_id)
            self._blink_loop_id = None
        self.is_blinking = False


        if hasattr(self, 'parent_station'):
            self.parent_station.update_button_states(is_active=False)

    def reset(self):
        self.is_running = False
        self.elapsed_time = 0
        self.alert_shown = False
        self.is_blinking = False
        self.timer_label.configure(text="00:00:00", text_color="white")
        self.draw_ring(0)
        
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
        missing_fields = []
        
        if not hasattr(self, 'name_entry') or self.name_entry is None or not self.name_entry.get().strip():
            missing_fields.append("Name")
        
        if self.station_type in ["XBOX", "Switch"]:
            if not hasattr(self, 'game_var') or self.game_var is None or not self.game_var.get():
                missing_fields.append("Game")
            if not hasattr(self, 'controller_var') or self.controller_var is None or not self.controller_var.get():
                missing_fields.append("Controller")

        if missing_fields:
            error_message = f"Please fill out the following fields:\n" + "\n".join(missing_fields)
            show_custom_error(self.winfo_toplevel(), "Error", error_message)
            return False
        return True

    def draw_ring(self, progress, color_override=None):
        import PIL.Image, PIL.ImageDraw, PIL.ImageTk
        
        scale = 8
        width, height = int(self.width * scale), int(self.height * scale)
        ring_width = int(min(width, height) * 0.07)
        center = (width // 2, height // 2)
        radius = int(min(center) * 0.97)
        
        img = PIL.Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = PIL.ImageDraw.Draw(img)

        # Background ring
        draw.ellipse(
            [center[0]-radius, center[1]-radius, center[0]+radius, center[1]+radius],
            outline="#333333" if ctk.get_appearance_mode() == "Dark" else "#CCCCCC",
            width=ring_width
        )

        # Progress arc
        if progress > 0:
            color = color_override or ('#2AAA2A' if ctk.get_appearance_mode() == "Dark" else '#228B22')
            start_angle = -90
            end_angle = start_angle + (progress * 360)
            
            for i in range(ring_width):
                draw.arc(
                    [
                        center[0]-radius + i, center[1]-radius + i,
                        center[0]+radius - i, center[1]+radius - i
                    ],
                    start=start_angle,
                    end=end_angle,
                    fill=color,
                    width=1
                )

        img = img.resize((self.width, self.height), PIL.Image.LANCZOS)
        self._ring_img = PIL.ImageTk.PhotoImage(img)
        self.delete("all")
        self.create_image(self.width//2, self.height//2, image=self._ring_img)

    def update_timer(self):
        if self.is_running:
            elapsed = self.get_time()
            hours, minutes, seconds = map(int, (elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60))
            self.timer_label.configure(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

            progress = min(elapsed / self.time_limit, 1.0)

            # Determine the appropriate color based on time elapsed
            if elapsed >= self.time_limit:
                color = "red"
                if not self.is_blinking:
                    self.is_blinking = True
                    self.start_blinking()
                    if hasattr(self, 'parent_station'):
                        self.parent_station.highlight_time_exceeded()
                self.timer_label.configure(text_color="red")
            elif elapsed >= (self.time_limit * 0.9):
                color = "orange"
                self.timer_label.configure(text_color="orange")
                # Update parent station border
                if hasattr(self, 'parent_station'):
                    self.parent_station.configure(border_color="orange", border_width=2)
            elif elapsed >= (self.time_limit * 0.8):
                color = "yellow"
                self.timer_label.configure(text_color="yellow")
                # Update parent station border
                if hasattr(self, 'parent_station'):
                    self.parent_station.configure(border_color="yellow", border_width=2)
            else:
                color = "green"
                self.timer_label.configure(text_color="green")
                # Update parent station border
                if hasattr(self, 'parent_station'):
                    self.parent_station.configure(border_color="green", border_width=2)
                    
            if not self.is_blinking and abs(progress - self.last_progress) > 0.01:
                self.draw_ring(progress)
                self.last_progress = progress

        self._update_loop_id = self.after(1000, self.update_timer)

    def start_blinking(self):
        if not self.is_blinking:
            return
        self.blink_state = not self.blink_state
        if self.blink_state:
            self.draw_ring(1.0, "red")
        else:
            self.draw_ring(1.0, "#8B0000")
        self._blink_loop_id = self.after(500, self.start_blinking)

    def show_time_alert(self):
        if not hasattr(self, 'last_alert_time'):
            self.last_alert_time = 0

        current_time = time.time()
        if current_time - self.last_alert_time < 300:
            return

        self.last_alert_time = current_time
        if hasattr(self, 'parent_station'):
            self.parent_station.highlight_time_exceeded()

    def update_font(self):
        """Update the timer font after parent_station is set"""
        if hasattr(self, 'parent_station') and hasattr(self.parent_station, 'app'):
            font_family = self.parent_station.app.get_font_family()
            self.timer_label.configure(
                font=ctk.CTkFont(family=font_family, size=12, weight="normal")
            )


class ShadowFrame(ctk.CTkFrame):
    """A frame with a drop shadow effect"""
    def __init__(self, master, **kwargs):
        # Extract shadow-specific properties
        shadow_color = kwargs.pop("shadow_color", "#0D0D0D")
        shadow_offset = kwargs.pop("shadow_offset", 4)
        
        # Create container frame
        self.container = ctk.CTkFrame(master, fg_color="transparent")
        
        # Create shadow frame
        self.shadow = ctk.CTkFrame(
            self.container, 
            fg_color=shadow_color,
            corner_radius=kwargs.get("corner_radius", 15),
            border_width=0
        )
        self.shadow.place(
            x=shadow_offset, 
            y=shadow_offset, 
            relwidth=1, 
            relheight=1
        )
        
        # Create main frame on top
        super().__init__(self.container, **kwargs)
        self.place(x=0, y=0, relwidth=1, relheight=1)
    
    def pack(self, **kwargs):
        self.container.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.container.grid(**kwargs)
    
    def place(self, **kwargs):
        self.container.place(**kwargs)


class Station(ctk.CTkFrame):
    def __init__(self, parent, app, station_type, station_num):
        # Match the main app background color for better contrast
        super().__init__(
            parent, 
            border_width=0,
            border_color="#333333", 
            corner_radius=15,
            fg_color="#171717"  # Keep only standard CTkFrame parameters
        )
        self.parent = parent
        self.app = app
        self.station_type = station_type
        self.station_num = station_num
        
        # Configure 3-column layout
        self.grid_columnconfigure(0, weight=1)  # Left inputs
        self.grid_columnconfigure(1, weight=0)  # Timer (fixed width)
        self.grid_columnconfigure(2, weight=1)  # Right inputs
        self.grid_rowconfigure(1, weight=1)     # Middle row
        
        self.setup_ui()
        # self.update_timer()
        
        # Ensure placeholders are shown after UI setup
        self.after(100, self.ensure_placeholders)
        
    def update_game_combobox_color(self, *args):
        if self.game_var.get() == "Select Game":
            self.game_combobox.configure(text_color="#565B5E")
        else:
            self.game_combobox.configure(text_color="#fff")

    def update_controller_combobox_color(self, *args):
        if self.controller_var.get() == "Number of Controllers":
            self.controller_combobox.configure(text_color="#565B5E")
        else:
            self.controller_combobox.configure(text_color="#fff")


    def setup_ui(self):
        # Standard styling
        field_font = ctk.CTkFont(size=12)
        field_height = 34
        field_pady = 5
        field_width = 140
        
        # Custom placeholder colors - make sure they're visible
        placeholder_color = "#333333"
        
        # Header Frame
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        
        # Station number label (always on the right)
        font_family = self.app.get_font_family()
        station_label = ctk.CTkLabel(
            header_frame, 
            text=f"Station {self.station_num}",
            font=ctk.CTkFont(family=font_family, size=14, weight="bold")
        )
        station_label.pack(side="right", padx=5)
        # Create a container frame for station type controls (left side)
        station_type_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        station_type_frame.pack(side="left")
        
        # Handle different station types
        if self.station_type in ["XBOX", "Switch"]:
            # Console toggle buttons
            xbox_image = Image.open("./icon_cache/xbox-logo.png")
            switch_image = Image.open("./icon_cache/switch-logo.png")
            xbox_icon = ctk.CTkImage(xbox_image, size=(20, 20))
            switch_icon = ctk.CTkImage(switch_image, size=(20, 20))
            
            self.console_var = ctk.StringVar(value=self.station_type)
            
            def update_button_states():
                xbox_button.configure(
                    fg_color=("gray75", "gray25") if self.console_var.get() == "XBOX" else "transparent",
                    hover_color=("gray65", "gray35")
                )
                switch_button.configure(
                    fg_color=("gray75", "gray25") if self.console_var.get() == "Switch" else "transparent",
                    hover_color=("gray65", "gray35")
                )
            
            def select_console(console_type):
                self.console_var.set(console_type)
                update_button_states()
                self.change_console_type()
            
            xbox_button = ctk.CTkButton(
                station_type_frame,
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
            self.app.create_tooltip(xbox_button, "Xbox Console")

            switch_button = ctk.CTkButton(
                station_type_frame,
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
            self.app.create_tooltip(switch_button, "Nintendo Switch")
            
            update_button_states()
        else:
            # Static icons for non-console stations
            try:
                # Choose the icon based on station type
                if self.station_type == "PoolTable":
                    icon_path = "./icon_cache/pool.png"
                    tooltip_text = "Pool Table"
                elif self.station_type == "Foosball":
                    icon_path = "./icon_cache/foosball.png"
                    tooltip_text = "Foosball Table"
                elif self.station_type == "Air Hockey":
                    icon_path = "./icon_cache/air-hockey.png"
                    tooltip_text = "Air Hockey Table"
                elif self.station_type == "Ping-Pong":
                    icon_path = "./icon_cache/ping-pong.png"
                    tooltip_text = "Ping-Pong Table"
                else:
                    icon_path = "./icon_cache/gamepad-2.png"  # Default icon
                    tooltip_text = self.station_type
                
                # Load and display the icon
                icon_image = Image.open(icon_path)
                station_icon = ctk.CTkImage(icon_image, size=(30, 30))
                
                icon_label = ctk.CTkLabel(
                    station_type_frame,
                    image=station_icon,
                    text="",
                    width=40,
                    height=40,
                    fg_color="gray25",
                    corner_radius=8
                )
                icon_label.pack(side="left", padx=2)
                
                # Add enhanced tooltip for the icon
                self.app.create_tooltip(icon_label, tooltip_text)
                
            except Exception as e:
                print(f"Error loading icon for {self.station_type}: {e}")
        
        # Left Input Column
        left_fields = ctk.CTkFrame(self, fg_color="transparent")
        left_fields.grid(row=1, column=0, sticky="nsew", padx=(10,5), pady=field_pady)
        
        # Name Field with working placeholder
        self.name_entry = ctk.CTkEntry(
            left_fields,
            width=field_width,
            height=32,
            border_width=1,
            border_color="#333333",
            corner_radius=9,
            fg_color="transparent",
            placeholder_text="Name",
            font=field_font,
            placeholder_text_color="#565B5E"  # Set explicit placeholder color
        )
        self.name_entry.pack(fill="x", pady=field_pady)
        self.add_active_glow(self.name_entry, "#00843d", "#333333")  # Add glow effect
        
        # Game Dropdown (use CTkComboBox as anchor)
        if self.station_type in ["XBOX", "Switch"]:
            self.game_var = ctk.StringVar()
            games = self.app.get_games_for_console(self.station_type)


            self.game_var = ctk.StringVar(value="Select Game")
            self.game_combobox = ctk.CTkComboBox(
                left_fields,
                variable=self.game_var,
                values=games,  # Do NOT include "Select Game" in this list!
                width=field_width,
                height=field_height,
                border_width=1,
                border_color="#333333",
                fg_color="#171717",
                corner_radius=9,
                font=field_font,
                justify="left",
                state="readonly"
            )
            self.game_combobox.pack(fill="x", pady=field_pady)
            self.add_active_glow(self.game_combobox, "#00843d", "#333333")
            self.game_var.trace_add("write", self.update_game_combobox_color)
            self.update_game_combobox_color()

            # Attach the scrollable dropdown
            self.game_dropdown = CTkScrollableDropdown(
                self.game_combobox,
                values=games,
                command=lambda v: self.game_var.set(v),
                width=240,
                height=220,
                font=field_font,
                justify="left",
                resize=False,
                button_height=32  # Makes each option taller
            )
 

        # Right Input Column
        right_fields = ctk.CTkFrame(self, fg_color="transparent")
        right_fields.grid(row=1, column=2, sticky="nsew", padx=(5,10), pady=field_pady)
        
        # ID Field with working placeholder
        self.id_entry = ctk.CTkEntry(
            right_fields,
            width=field_width,
            height=32,
            border_width=1,
            border_color="#333333",
            fg_color="transparent",
            corner_radius=9,
            placeholder_text="UVID (If Applicable)",
            placeholder_text_color="#565B5E",  # Set explicit placeholder color
            font=field_font
        )
        # Force focus and then remove focus to trigger the placeholder
        self.id_entry.pack(fill="x", pady=field_pady)
        self.add_active_glow(self.id_entry, "#00843d", "#333333")  # Add glow effect
        
        # Controller Dropdown (use CTkComboBox as anchor)
        if self.station_type in ["XBOX", "Switch"]:
            self.controller_var = ctk.StringVar(value="Number of Controllers")
            controllers = ["1", "2", "3", "4"]
            self.controller_combobox = ctk.CTkComboBox(
            right_fields,
            variable=self.controller_var,
            values=controllers,
            width=field_width,
            height=field_height,
            border_width=1,
            border_color="#333333",
            fg_color="#171717",
            button_color="#333333",
            button_hover_color="#888888",
            corner_radius=9,
            font=field_font,
            justify="left",
            state="readonly"
            )
            self.controller_combobox.pack(fill="x", pady=field_pady)
            self.add_active_glow(self.controller_combobox, "#00843d", "#333333")
            self.controller_var.trace_add("write", self.update_controller_combobox_color)
            self.update_controller_combobox_color()
            self.controller_combobox.configure(cursor="hand2")
            self.controller_combobox.bind("<Enter>", lambda e: self.controller_combobox.configure(cursor="hand2"))

            self.controller_dropdown = CTkScrollableDropdown(
            self.controller_combobox,
            values=controllers,
            command=lambda v: self.controller_var.set(v),
            width=field_width,
            height=120,
            font=field_font,
            justify="left"
            )

            # --- Apply same styling to the Game Dropdown ---
            self.game_combobox.configure(
            fg_color="#171717",
            button_color="#333333",
            button_hover_color="#888888",
            border_width=1,
            border_color="#333333",
            corner_radius=9,
            font=field_font,
            justify="left",
            state="readonly"
            )
            self.game_combobox.configure(cursor="hand2")
            self.game_combobox.bind("<Enter>", lambda e: self.game_combobox.configure(cursor="hand2"))

        # Center Timer Column
        timer_container = ctk.CTkFrame(self, fg_color="transparent")
        timer_container.grid(row=1, column=1, sticky="ns", padx=10)
        
        self.timer = CombinedTimer(timer_container, width=160, height=160)
        self.timer.pack(pady=10)
        
        # Connect fields to timer
        self.timer.name_entry = self.name_entry
        self.timer.id_entry = self.id_entry
        self.timer.parent_station = self
        self.timer.station_type = self.station_type
        self.timer.station_num = self.station_num
        self.timer.update_font() 
        
        if hasattr(self, 'game_var'):
            self.timer.game_var = self.game_var
            self.timer.game_dropdown = self.game_dropdown
            
        if hasattr(self, 'controller_var'):
            self.timer.controller_var = self.controller_var
            self.timer.controller_dropdown = self.controller_dropdown

        # Control Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=3, sticky="sew", padx=10, pady=(0, 5))
        
        btn_container = ctk.CTkFrame(button_frame, fg_color="transparent")
        btn_container.pack()
        
        # Load button icons with white color for inactive state
        self.start_icon_inactive = self.colorize_icon("./icon_cache/play.png", "#FFFFFF")
        self.stop_icon_inactive = self.colorize_icon("./icon_cache/square.png", "#FFFFFF")
        self.reset_icon_inactive = self.colorize_icon("./icon_cache/refresh-ccw.png", "#FFFFFF")
        
        # Load button icons with color for active state
        self.start_icon_active = self.colorize_icon("./icon_cache/play.png", "#4DA977")
        self.stop_icon_active = self.colorize_icon("./icon_cache/square.png", "#A3483F")
        self.reset_icon_active = self.colorize_icon("./icon_cache/refresh-ccw.png", "#00BFB3")
        
        # Green Start button (initially inactive)
        start_button = ctk.CTkButton(
            btn_container, 
            image=self.start_icon_inactive, 
            text="Start", 
            command=self.timer.start,
            width=80,
            height=30,
            corner_radius=20,
            fg_color="transparent",
            border_width=1,
            border_color="#00843d",
            text_color="#FFFFFF",
            hover_color="#1a2e28"
        )
        start_button.pack(side="left", padx=5)
        
        # Red Stop button (initially inactive)
        stop_button = ctk.CTkButton(
            btn_container,
            image=self.stop_icon_inactive,
            text="Stop",
            command=self.timer.stop,
            width=80,
            height=30,
            corner_radius=20,
            fg_color="transparent",
            border_width=1,
            border_color="#00843d",
            text_color="#FFFFFF",
            hover_color="#1a2e28"
        )
        stop_button.pack(side="left", padx=5)
        
        # Blue Reset button (initially inactive)
        reset_button = ctk.CTkButton(
            btn_container,
            image=self.reset_icon_inactive,
            text="Reset",
            command=self.reset_timer,
            width=80,
            height=30,
            corner_radius=20,
            fg_color="transparent",
            border_width=1,
            border_color="#00843d",
            text_color="#FFFFFF",
            hover_color="#1a2e28"
        )
        reset_button.pack(side="left", padx=5)
        
        # Store buttons for later state management
        self.start_button = start_button
        self.stop_button = stop_button
        self.reset_button = reset_button
        
        # Initialize button states
        self.update_button_states(is_active=False)



    def add_active_glow(self, widget, glow_color="#00FFD0", normal_color="#333333", steps=8, duration=120):
        widget._original_border_color = normal_color

        def color_to_str(color):
            if isinstance(color, (list, tuple)):
                return color[0]
            return color

        def hex_to_rgb(hex_color):
            hex_color = color_to_str(hex_color).lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(*rgb)

        def interpolate_color(c1, c2, t):
            return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

        def fade_to(target_color, start_color, step=0):
            if step > steps:
                widget.configure(border_color=target_color)
                return
            t = step / steps
            rgb = interpolate_color(hex_to_rgb(start_color), hex_to_rgb(target_color), t)
            widget.configure(border_color=rgb_to_hex(rgb))
            widget.after(duration // steps, lambda: fade_to(target_color, start_color, step + 1))

        def on_focus_in(event):
            fade_to(glow_color, widget._original_border_color)

        def on_focus_out(event):
            fade_to(widget._original_border_color, glow_color)

        # Only bind focus events if not a ComboBox (prevents dropdown from closing)
        if not isinstance(widget, ctk.CTkComboBox):
            widget.bind("<FocusIn>", on_focus_in)
            widget.bind("<FocusOut>", on_focus_out)

    def colorize_icon(self, icon_path, color_hex):
        """Recolor an icon to match the button text color"""
        # Open the icon
        img = Image.open(icon_path).convert("RGBA")
        
        # Create a solid color image of the same size
        colored = Image.new("RGBA", img.size, color_hex)
        
        # Use the original image as a mask
        result = Image.new("RGBA", img.size, (0, 0, 0, 0))
        result.paste(colored, (0, 0), img)
        
        return ctk.CTkImage(result, size=(15, 15))
    

    def update_button_states(self, is_active):
        """Update button appearance based on timer active state"""
        if is_active:
            # Timer is active - Apply active state styling
            
            # Start button
            self.start_button.configure(
                image=self.start_icon_active,
                border_color="#4DA977",
                text_color="#4DA977",
                hover=False,  # Disable hover effect
                fg_color="transparent"
            )
            
            # Stop button - active stop styling
            self.stop_button.configure(
                image=self.stop_icon_active,
                border_color="#A3483F",
                text_color="#A3483F",
                hover_color="#2d1a1a",  # Appropriate hover effect
                fg_color="transparent"
            )
            
            # Reset button - active reset styling
            self.reset_button.configure(
                image=self.reset_icon_active,
                border_color="#00BFB3",
                text_color="#00BFB3",
                hover_color="#1a202d",  # Appropriate hover effect 
                fg_color="transparent"
            )
        else:
            # Timer is inactive - Apply default styling
            
            # All buttons use the UVU green with white text
            for button, icon in [
                (self.start_button, self.start_icon_inactive),
                (self.stop_button, self.stop_icon_inactive),
                (self.reset_button, self.reset_icon_inactive)
            ]:
                button.configure(
                    image=icon,
                    border_color="#00843d",
                    text_color="#FFFFFF",
                    hover_color="#1a2e28",
                    fg_color="transparent"
                )

    def change_console_type(self):
        self.station_type = self.console_var.get()
        games = self.app.get_games_for_console(self.station_type)
        self.game_dropdown.configure(values=games)
        self.game_var.set("Select Game")

    # def update_timer(self):
    #     self.timer.update_timer()
    #     self.after(1000, self.update_timer)

    def highlight_time_exceeded(self):
        self.configure(border_color="red", border_width=3)
        if not hasattr(self, 'alert_label'):
            self.alert_label = ctk.CTkLabel(
                self,
                text="TIME EXCEEDED",
                fg_color="red",
                text_color="white",
                corner_radius=6,
                font=("Helvetica", 12, "bold")
            )
            self.alert_label.place(relx=0.5, rely=0.09, anchor="center")
        else:
            self.alert_label.place(relx=0.5, rely=0.09, anchor="center")

    def show_time_alert(self):
        self.highlight_time_exceeded()

    def start_timer(self):
        self.timer.start()

    def stop_timer(self):
        self.timer.stop()

    def ensure_placeholders(self):
        """Force the placeholders to be shown by accessing and manipulating the entry widgets"""
        # Force refresh of the placeholder texts
        if hasattr(self, 'name_entry') and not self.name_entry.get():
            self.name_entry._entry.config(validate='none')  # Disable validation temporarily
            self.name_entry._entry.delete(0, tk.END)        # Clear any content
            self.name_entry._activate_placeholder()         # Changed from _check_placeholder
            
        if hasattr(self, 'id_entry') and not self.id_entry.get():
            self.id_entry._entry.config(validate='none')
            self.id_entry._entry.delete(0, tk.END)
            self.id_entry._activate_placeholder()           # Changed from _check_placeholder
            
    def reset_timer(self):
        should_log = self.timer.is_running or self.timer.elapsed_time > 0
        
        if self.timer.is_running:
            self.timer.stop()
        
        if should_log:
            self.log_usage()
        
        self.timer.reset()
        self.configure(border_width=0)
        
        # Reset fields and force placeholders to show
        self.name_entry.delete(0, tk.END)
        self.id_entry.delete(0, tk.END)
        
        # Force placeholder refresh
        self.name_entry._activate_placeholder()    # Changed from _check_placeholder
        self.id_entry._activate_placeholder()      # Changed from _check_placeholder
        
        if hasattr(self, 'game_var'):
            self.game_var.set("Select Game")
        if hasattr(self, 'controller_var'):
            self.controller_var.set("Number of Controllers")
        
        if hasattr(self, 'alert_label'):
            self.alert_label.place_forget()

        self.update_button_states(is_active=False)

    def log_usage(self):
        try:
            log_file_path = os.path.join("usage_log.txt")

            user_name = self.name_entry.get().strip() if hasattr(self, 'name_entry') and self.name_entry else "Unknown"
            id_number = self.id_entry.get().strip() if hasattr(self, 'id_entry') and self.id_entry else "Unknown"
            game = "N/A"
            controller = "N/A"
            if self.station_type in ["XBOX", "Switch"]:
                if hasattr(self, 'game_var') and self.game_var:
                    game = self.game_var.get()
                if hasattr(self, 'controller_var') and self.controller_var:
                    controller = self.controller_var.get()
            duration = self.timer.get_time() if hasattr(self.timer, 'get_time') else 0
            formatted_duration = time.strftime("%H:%M:%S", time.gmtime(duration))

            log_entry = [
                f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]}",
                f"Station Type: {self.station_type}",
                f"Station Number: {self.station_num}",
                f"User Name: {user_name}",
                f"ID Number: {id_number}" if id_number else "ID Number: N/A",
                f"Duration: {formatted_duration}",
                f"Game: {game}",
                f"Controllers: {controller}",
                "--------------------------------------------------"
            ]

            with open(log_file_path, "a", encoding="utf-8") as log_file:
                log_file.write("\n".join(log_entry) + "\n")
                log_file.flush()

        except Exception as e:
            import traceback
            print(f"Error logging usage: {str(e)}")
            print(traceback.format_exc())
            messagebox.showerror(
                "Logging Error",
                f"Failed to log station usage. Please notify administrator.\nError: {str(e)}"
            )

    def update_games_list(self):
        if self.station_type in ["XBOX", "Switch"]:
            console_type = "XBOX" if self.station_type == "XBOX" else "Switch"
            games = self.app.get_games_for_console(console_type)
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
        station = self.station_var.get()
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
        self.geometry("1500x1100")
        self.load_orbitron_font()
        self.stations = []
        self.waitlist = []
        self.timers = []
        self.waitlist_tree = None
        self.pages = {}  # Add this to hold your pages
        self.active_sidebar_btn = None  # Track active sidebar button

        # Set the base application background color
        self.configure(fg_color="#090A09")
        
        # Create the main container
        self.main_container = ctk.CTkFrame(self, fg_color="#090A09", corner_radius=0)
        self.main_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Create top bar
        top_bar = ctk.CTkFrame(self.main_container, fg_color="#171717", height=40, corner_radius=0)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)
        self.top_bar = top_bar
        
        # Create sidebar
        sidebar = ctk.CTkFrame(self.main_container, fg_color="#171717", width=85, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self.sidebar = sidebar
        
        # Create content area
        content_container = ctk.CTkFrame(self.main_container, fg_color="#090A09", corner_radius=0)
        content_container.pack(side="right", fill="both", expand=True)
        
        content_area = ctk.CTkFrame(
            content_container, 
            fg_color="#090A09",
            corner_radius=30
        )
        content_area.pack(fill="both", expand=True, padx=(0, 10), pady=(10, 10))
        
        inner_content = ctk.CTkFrame(
            content_area,
            fg_color="#090A09",
            corner_radius=25
        )
        inner_content.pack(fill="both", expand=True, padx=15, pady=15)
        self.content_area = inner_content
        
        # Setup UI components
        self.setup_top_bar(top_bar)
        self.setup_sidebar(sidebar)
        self.setup_pages()  # New method to create all pages
        self.show_page("home")  # Show home by default
        self.create_arch_overlay()

    def setup_pages(self):
        # Create all pages as frames, but only pack/grid the active one
        self.pages["home"] = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.pages["waitlist"] = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.pages["stats"] = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.pages["reservations"] = ctk.CTkFrame(self.content_area, fg_color="transparent")
        # ...add more as needed...

        # Build the home page (station cards)
        self.setup_home_page(self.pages["home"])
        # Build waitlist and stats pages
        self.setup_waitlist_page(self.pages["waitlist"])
        self.setup_stats_page(self.pages["stats"])
        self.setup_reservations_page(self.pages["reservations"])

    def show_page(self, page_name):
        # Hide all pages
        for page in self.pages.values():
            page.pack_forget()
        # Show the selected page
        self.pages[page_name].pack(fill="both", expand=True)
        # Update sidebar active state
        self.set_active_sidebar(page_name)

        self.pages[page_name].pack(fill="both", expand=True)
        self.set_active_sidebar(page_name)
        if hasattr(self, "arch_overlay"):
            self.arch_overlay.lift()

    def set_active_sidebar(self, page_name):
        # Reset all sidebar buttons to default
        for name, btn in self.sidebar_buttons.items():
            btn.configure(fg_color="transparent")
        # Highlight the active one
        if page_name in self.sidebar_buttons:
            self.sidebar_buttons[page_name].configure(fg_color="#00843d")  # Example active color


    def setup_home_page(self, frame):
        main_frame = ctk.CTkFrame(frame, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        frames_to_focus = [main_frame, frame]

        for f in frames_to_focus:
            f.bind("<Button-1>", lambda event, f=f: f.focus_set())

        for i in range(6):  # 6 rows
            main_frame.grid_rowconfigure(i, weight=1)
        for i in range(3):  # 3 columns
            main_frame.grid_columnconfigure(i, weight=1)

        # Create first 4 console stations (left column) in reverse order
        for i in range(4):
            shadow = ctk.CTkFrame(
                main_frame,
                corner_radius=15,
                fg_color="#282828",
                border_width=0
            )
            shadow.grid(row=i, column=0, padx=(10, 14), pady=(10, 14), sticky="nsew")
            station = Station(main_frame, self, "XBOX", 4 - i)
            station.grid(row=i, column=0, padx=10, pady=10, sticky="nsew")
            self.stations.append(station)
            self.timers.append(station.timer)

        # 5th console station (top center)
        shadow = ctk.CTkFrame(
            main_frame,
            corner_radius=15,
            fg_color="#282828",
            border_width=0
        )
        shadow.grid(row=0, column=1, columnspan=2, padx=(10, 14), pady=(10, 14), sticky="nsew")
        station = Station(main_frame, self, "XBOX", 5)
        station.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.stations.append(station)
        self.timers.append(station.timer)

        # Other activity stations
        activities = [
            ("Ping-Pong", 1),
            ("Ping-Pong", 2),
            ("Foosball", 1),
            ("Air Hockey", 1),
            ("PoolTable", 1),
            ("PoolTable", 2),
        ]
        row, col = 1, 1
        for activity, num in activities:
            shadow = ctk.CTkFrame(
                main_frame,
                corner_radius=15,
                fg_color="#282828",
                border_width=0
            )
            shadow.grid(row=row, column=col, padx=(10, 14), pady=(10, 14), sticky="nsew")
            station = Station(main_frame, self, activity, num)
            station.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.stations.append(station)
            self.timers.append(station.timer)
            col += 1
            if col > 2:
                col = 1
                row += 1


    def setup_reservations_page(self, frame):
        import pandas as pd

        url = "https://uvu365-my.sharepoint.com/:x:/g/personal/10699677_uvu_edu/EfDDWIdsIgpEsoV6krvPkIgBJPVtMi1Kbqz0F0-lbURXDw?e=zaL1aK&nav=MTVfezEzQTdENUIwLThGNjMtNDI4Ni1CMjg2LTE2Q0NGQTNDOEU5M30"
        loading_label = ctk.CTkLabel(frame, text="Loading reservations...", font=("Helvetica", 16))
        loading_label.pack(pady=20)

        def load_data():
            try:
                df = pd.read_excel(url)
                loading_label.destroy()
                # Display the first 10 rows as a simple table
                text = df.head(10).to_string(index=False)
                reservations_text = ctk.CTkTextbox(frame, width=900, height=400, font=("Consolas", 12))
                reservations_text.insert("1.0", text)
                reservations_text.configure(state="disabled")
                reservations_text.pack(padx=20, pady=20)
            except Exception as e:
                loading_label.configure(text=f"Failed to load reservations:\n{e}")

        import threading
        threading.Thread(target=load_data, daemon=True).start()

    def setup_waitlist_page(self, frame):
        # Initialize bowling waitlist if it doesn't exist
        if not hasattr(self, 'bowling_waitlist'):
            self.bowling_waitlist = []

        main_frame = ctk.CTkFrame(frame, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header frame with title, toggle and count
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        self.waitlist_type_var = ctk.StringVar(value="Game Center")
        waitlist_toggle = ctk.CTkSegmentedButton(
            header_frame,
            values=["Game Center", "Bowling Lanes"],
            variable=self.waitlist_type_var,
            command=self.switch_waitlist_type
        )
        waitlist_toggle.pack(side="left", padx=(0, 20))

        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left")

        self.title_label = ctk.CTkLabel(
            title_frame,
            text="Gaming Center Waitlist",
            font=("Helvetica", 20, "bold")
        )
        self.title_label.pack(side="left", padx=5)

        self.count_label = ctk.CTkLabel(
            title_frame,
            text=str(len(self.waitlist)),
            fg_color="blue",
            text_color="white",
            corner_radius=10,
            width=30
        )
        self.count_label.pack(side="left", padx=5)

        search_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        search_frame.pack(side="right")
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search parties", width=200)
        self.search_entry.pack(side="right", padx=5)

        # Content frame for treeview and buttons
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)

        # Treeview styling
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

        # Treeview columns
        columns = ("party", "size", "notes", "station", "quotedTime", "arrival")
        self.waitlist_tree = ttk.Treeview(
            content_frame,
            columns=columns,
            show="headings",
            style="Waitlist.Treeview"
        )

        # Configure column headings
        self.headings = {
            "party": "PARTY",
            "size": "SIZE",
            "notes": "NOTES",
            "station": "STATION",
  # Will be changed to "LANE" for bowling
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

        # Placeholder buttons (shown when no entries exist)
        self.placeholder_buttons_frame = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        self.placeholder_buttons_frame.pack(pady=10, padx=5)

        ctk.CTkButton(
            self.placeholder_buttons_frame,
            text="✓",
            width=30,
            height=30,
            fg_color="gray",
            hover_color="gray",
            state="disabled"
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            self.placeholder_buttons_frame,
            text="✕",
            width=30,
            height=30,
            fg_color="gray",
            hover_color="gray",
            state="disabled"
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            self.placeholder_buttons_frame,
            text="✎",
            width=30,
            height=30,
            fg_color="gray",
            hover_color="gray",
            state="disabled"
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            self.placeholder_buttons_frame,
            text="✉",
            width=30,
            height=30,
            fg_color="gray",
            hover_color="gray",
            state="disabled"
        ).pack(side="left", padx=2)

        # Treeview scrollbar
        tree_scroll = ctk.CTkScrollbar(content_frame, orientation="vertical", command=self.waitlist_tree.yview)
        self.waitlist_tree.configure(yscrollcommand=tree_scroll.set)
        self.waitlist_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        # Store references for later updates
        self.buttons_frame = buttons_frame

        # Add floating action button
        station_names = [f"{station.station_type} {station.station_num}" for station in self.stations]
        self.add_button = ctk.CTkButton(
            main_frame,
            text="+",
            width=60,
            height=60,
            corner_radius=60,
            font=("Helvetica", 24, "bold"),
            command=lambda: self.add_to_waitlist(station_names)
        )
        self.add_button.place(relx=0.95, rely=0.95, anchor="se")

        # Bind search functionality
        def update_tree(event=None):
            search_text = self.search_entry.get().lower()
            self.update_waitlist_tree(search_text)

        self.search_entry.bind('<KeyRelease>', update_tree)
        self.update_waitlist_tree()

    def setup_stats_page(self, frame):
        """Set up the complete statistics page in the main app window"""
        # Create main container frame
        self.stats_main_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self.stats_main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Initialize stats manager
        self.stats_manager = StatsManager()
        
        # Configure theme colors and appearance
        self.stats_colors = {
            "primary": "#00843d",      # UVU Green
            "secondary": "#4c7553",    # Muted green
            "accent": "#add557",       # Light green accent
            "text_light": "#FFFFFF",   # Light text
            "text_dark": "#1a1a1a",    # Dark text
            "success": "#28a745",      # Success green
            "warning": "#ffc107",      # Warning yellow
            "danger": "#dc3545",       # Error red
            "card_bg": "#2a2a2a",      # Card background
            "hover": "#3a3a3a",        # Hover state
        }
        
        self.stats_fonts = {
            "heading": ("Roboto", 18, "bold"),
            "subheading": ("Roboto", 16, "normal"),
            "body": ("Roboto", 12, "normal"),
            "small": ("Roboto", 10, "normal"),
            "label": ("Roboto", 12, "bold"),
        }

        # Configure grid layout
        self.stats_main_frame.grid_columnconfigure(0, weight=1)
        self.stats_main_frame.grid_rowconfigure(0, weight=0)  # Header
        self.stats_main_frame.grid_rowconfigure(1, weight=1)  # Content
        
        # Create header with filters and title
        header_frame = ctk.CTkFrame(self.stats_main_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)
        
        # Title 
        title_label = ctk.CTkLabel(
            header_frame, 
            text="Gaming Center Statistics", 
            font=("Roboto", 24, "bold"),
            text_color=self.stats_colors["text_light"]
        )
        title_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # Filter container
        filter_frame = ctk.CTkFrame(
            header_frame, 
            fg_color=self.stats_colors["card_bg"],
            corner_radius=10
        )
        filter_frame.grid(row=0, column=1, sticky="e", padx=10, pady=10)
        
        # Time period selector
        ctk.CTkLabel(
            filter_frame, 
            text="Time Period:", 
            font=self.stats_fonts["label"]
        ).pack(side="left", padx=(15, 5), pady=10)
        
        period_choices = [
            'Today', 'Yesterday', 'Last 7 Days', 'Last 30 Days', 
            'This Month', 'Last Month', 'This Semester', 'Last Semester', 
            'This Year', 'Last Year', 'All Time'
        ]
        self.stats_period_var = tk.StringVar(value='Today')
        self.period_dropdown = ctk.CTkComboBox(
            filter_frame, 
            variable=self.stats_period_var, 
            values=period_choices,
            state='readonly',
            width=180, 
            height=32,
            corner_radius=6,
            dropdown_hover_color=self.stats_colors["hover"],
            button_color=self.stats_colors["primary"],
            button_hover_color=self.stats_colors["secondary"],
            dropdown_fg_color=self.stats_colors["card_bg"],
        )
        self.period_dropdown.pack(side="left", padx=(5, 15), pady=10)
        self.period_dropdown.configure(command=self.update_stats)
        
        # Create notebook for tabbed interface
        self.stats_notebook = ctk.CTkTabview(
            self.stats_main_frame, 
            corner_radius=10,
            segmented_button_selected_color=self.stats_colors["primary"],
            segmented_button_selected_hover_color=self.stats_colors["secondary"],
            segmented_button_unselected_color="#3a3a3a",
            segmented_button_unselected_hover_color="#4a4a4a",
            command=self.on_stats_tab_change
        )
        self.stats_notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Create tabs
        summary_tab = self.stats_notebook.add("Summary")
        station_tab = self.stats_notebook.add("Station Details")
        games_tab = self.stats_notebook.add("Game Rankings")
        
        # Set up content for each tab
        self.setup_stats_summary_tab(summary_tab)
        self.setup_stats_station_tab(station_tab)
        self.setup_stats_games_tab(games_tab)
        
        # Add export button container at bottom
        footer_frame = ctk.CTkFrame(self.stats_main_frame, fg_color="transparent", height=50)
        footer_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        footer_frame.grid_columnconfigure(0, weight=1)
        
        # Export button
        export_button = ctk.CTkButton(
            footer_frame, 
            text="Export Data", 
            command=self.export_stats_to_excel,
            height=36,
            corner_radius=8,
            font=self.stats_fonts["label"],
            hover_color=self.stats_colors["secondary"],
        )
        export_button.pack(side="right", padx=10, pady=5)
        
        # Status indicator
        self.stats_status_label = ctk.CTkLabel(
            footer_frame,
            text="",
            font=self.stats_fonts["small"],
            text_color="gray70"
        )
        self.stats_status_label.pack(side="left", padx=10, pady=5)
        
        # Initialize tooltip manager
        self.stats_tooltip_texts = {
            "export_button": "Export current statistics to CSV files",
            "period_dropdown": "Select the time period for statistics",
            "station_dropdown": "Select a specific station to view detailed statistics",
            "total_time": "Total usage time across all stations",
            "total_sessions": "Total number of user sessions",
            "avg_session": "Average duration of all sessions",
            "station_usage": "Breakdown of usage by station type",
            "game_rankings": "Most popular games based on play time"
        }
        
        # Update statistics
        self.update_stats()

    def setup_stats_summary_tab(self, parent):
        """Set up the summary tab with key statistics"""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=1)
        
        # Top Row - Key Metrics cards
        usage_content, _ = self.create_stats_card(
            parent, "Usage Statistics", row=0, column=0, padx=(0, 5), pady=(0, 10)
        )

        usage_content.grid_columnconfigure(0, weight=2)
        usage_content.grid_columnconfigure(1, weight=3)
        
        self.total_time_label = self.create_stats_metric_display(
            usage_content, "Total Usage Time:", 0)
        self.total_sessions_label = self.create_stats_metric_display(
            usage_content, "Total Sessions:", 1)
        self.avg_session_label = self.create_stats_metric_display(
            usage_content, "Average Session:", 2)
        
        # Right card - Usage Chart
        chart_content, _ = self.create_stats_card(
            parent, "Usage Trends", row=0, column=1, padx=(5, 0), pady=(0, 10))
        
        self.summary_chart_frame = chart_content
        self.summary_chart_canvas = self.create_stats_matplotlib_graph(chart_content)
        self.summary_chart_canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        # Bottom row - Station Type Breakdown
        station_type_content, _ = self.create_stats_card(
            parent, "Station Type Breakdown", row=1, column=0, colspan=2)
        
        station_type_content.grid_columnconfigure(0, weight=3)
        station_type_content.grid_columnconfigure(1, weight=2)
        station_type_content.grid_rowconfigure(0, weight=1)
        
        # Table frame
        tree_frame = ctk.CTkFrame(station_type_content, fg_color="transparent")
        tree_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)
        
        self.type_tree = ttk.Treeview(
            tree_frame, 
            columns=('Station Type', 'Sessions', 'Total Time', 'Avg Time'), 
            show='headings', 
            height=6, 
            style="Custom.Treeview"
        )
        self.type_tree.heading('Station Type', text='Station Type')
        self.type_tree.heading('Sessions', text='Sessions')
        self.type_tree.heading('Total Time', text='Total Time')
        self.type_tree.heading('Avg Time', text='Avg Time')
        
        self.type_tree.column('Station Type', width=150, anchor='w')
        self.type_tree.column('Sessions', width=80, anchor='center')
        self.type_tree.column('Total Time', width=100, anchor='center')
        self.type_tree.column('Avg Time', width=100, anchor='center')
        
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.type_tree.yview)
        self.type_tree.configure(yscrollcommand=tree_scrollbar.set)
        tree_scrollbar.pack(side="right", fill="y")
        self.type_tree.pack(fill="both", expand=True)
        
        # Chart frame
        chart_frame = ctk.CTkFrame(station_type_content, fg_color="transparent")
        chart_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=5)
        
        self.station_type_graph = self.create_stats_matplotlib_graph(chart_frame)
        self.station_type_graph.get_tk_widget().pack(fill="both", expand=True)

    def setup_stats_station_tab(self, parent):
        """Set up the station details tab"""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=1)
        
        # Station selector card
        selector_content, _ = self.create_stats_card(
            parent, "Station Selection", row=0, column=0, pady=(0, 10))
        
        ctk.CTkLabel(
            selector_content,
            text="Select Station:",
            font=self.stats_fonts["body"]
        ).pack(side="left", padx=(5, 10), pady=10)
        
        self.station_var = tk.StringVar()
        self.station_dropdown = ctk.CTkComboBox(
            selector_content,
            variable=self.station_var,
            state='readonly',
            width=250,
            height=32,
            corner_radius=6,
            dropdown_hover_color=self.stats_colors["hover"],
            button_color=self.stats_colors["primary"],
            button_hover_color=self.stats_colors["secondary"],
            dropdown_fg_color=self.stats_colors["card_bg"]
        )
        self.station_dropdown.pack(side="left", padx=10, pady=10)
        self.station_dropdown.configure(command=self.update_stats_station_stats)
        
        # Populate the dropdown
        stations = self.stats_manager.get_all_stations()
        self.station_dropdown.configure(values=stations)
        
        # Station details area
        details_content, _ = self.create_stats_card(parent, "Station Statistics", row=1, column=0)
        details_content.grid_columnconfigure(0, weight=1)
        details_content.grid_columnconfigure(1, weight=1)
        details_content.grid_rowconfigure(0, weight=1)
        
        # Left side - Station metrics
        left_frame = ctk.CTkFrame(details_content, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)
        
        self.station_tree = ttk.Treeview(
            left_frame,
            columns=('Metric', 'Value'),
            show='headings',
            height=10,
            style="Custom.Treeview"
        )
        self.station_tree.heading('Metric', text='Metric')
        self.station_tree.heading('Value', text='Value')
        self.station_tree.column('Metric', width=150, anchor='w')
        self.station_tree.column('Value', width=200, anchor='e')
        
        tree_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.station_tree.yview)
        self.station_tree.configure(yscrollcommand=tree_scrollbar.set)
        tree_scrollbar.pack(side="right", fill="y")
        self.station_tree.pack(fill="both", expand=True)
        
        # Right side - Station usage chart
        right_frame = ctk.CTkFrame(details_content, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=5)
        
        self.station_chart_frame = right_frame
        self.station_type_usage_graph = self.create_stats_matplotlib_graph(right_frame)
        self.station_type_usage_graph.get_tk_widget().pack(fill="both", expand=True)

    def setup_stats_games_tab(self, parent):
        """Set up the game rankings tab"""
        parent.grid_columnconfigure(0, weight=4)
        parent.grid_columnconfigure(1, weight=3)
        parent.grid_rowconfigure(0, weight=1)
        
        # Game rankings card - left side
        games_content, _ = self.create_stats_card(
            parent, "Game Rankings", row=0, column=0, padx=(0, 5))
        
        self.games_tree = ttk.Treeview(
            games_content,
            columns=('Rank', 'Game', 'Sessions', 'Total Time'),
            show='headings',
            height=15,
            style="Custom.Treeview"
        )
        self.games_tree.heading('Rank', text='Rank')
        self.games_tree.heading('Game', text='Game')
        self.games_tree.heading('Sessions', text='Sessions')
        self.games_tree.heading('Total Time', text='Total Time')
        
        self.games_tree.column('Rank', width=50, anchor='center')
        self.games_tree.column('Game', width=220, anchor='w')
        self.games_tree.column('Sessions', width=80, anchor='center')
        self.games_tree.column('Total Time', width=120, anchor='center')
        
        game_scrollbar = ttk.Scrollbar(games_content, orient="vertical", command=self.games_tree.yview)
        self.games_tree.configure(yscrollcommand=game_scrollbar.set)
        game_scrollbar.pack(side="right", fill="y")
        self.games_tree.pack(fill="both", expand=True)
        
        # Game chart card - right side
        chart_content, _ = self.create_stats_card(
            parent, "Game Popularity", row=0, column=1, padx=(5, 0))
        
        self.game_rankings_frame = chart_content
        self.game_rankings_graph = self.create_stats_matplotlib_graph(chart_content)
        self.game_rankings_graph.get_tk_widget().pack(fill="both", expand=True)

    def create_stats_card(self, parent, title, row=0, column=0, rowspan=1, colspan=1, padx=10, pady=10):
        """Create a consistent card-style container for statistics"""
        card = ctk.CTkFrame(
            parent, 
            fg_color=self.stats_colors["card_bg"],
            corner_radius=10, 
            border_width=0
        )
        card.grid(row=row, column=column, rowspan=rowspan, columnspan=colspan, 
                sticky="nsew", padx=padx, pady=pady)
        
        # Add shadow effect
        shadow = ctk.CTkFrame(
            parent,
            fg_color="gray20",
            corner_radius=10,
            border_width=0
        )
        
        shadow_padx = self._stats_add_padding_offset(padx, 2)
        shadow_pady = self._stats_add_padding_offset(pady, 2)
        
        shadow.grid(row=row, column=column, rowspan=rowspan, columnspan=colspan, 
                sticky="nsew", padx=shadow_padx, pady=shadow_pady)
        card.lift()
        
        # Card title
        title_label = ctk.CTkLabel(
            card, 
            text=title, 
            font=self.stats_fonts["subheading"],
            anchor="w", 
            text_color=self.stats_colors["text_light"]
        )
        title_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        # Separator
        separator = ctk.CTkFrame(card, height=1, fg_color="gray40")
        separator.pack(fill="x", padx=15, pady=(5, 10))
        
        # Container for content
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        return content_frame, card

    def _stats_add_padding_offset(self, padding, offset):
        """Helper method for card shadows"""
        if isinstance(padding, tuple):
            return (padding[0] + offset, padding[1] + offset)
        else:
            return padding + offset

    def create_stats_metric_display(self, parent, label_text, row, icon_name=None):
        """Create a metric display with label and value"""
        if icon_name:
            icon_label = ctk.CTkLabel(
                parent, 
                text="●",
                font=("Roboto", 16),
                width=20,
                text_color=self.stats_colors["accent"]
            )
            icon_label.grid(row=row, column=0, sticky="w", padx=(0, 5), pady=(10, 10))
        
        ctk.CTkLabel(
            parent,
            text=label_text,
            font=self.stats_fonts["body"],
            anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=(30, 10), pady=(10, 10))
        
        value_label = ctk.CTkLabel(
            parent,
            text="Loading...",
            font=self.stats_fonts["heading"],
            anchor="e",
            text_color=self.stats_colors["accent"]
        )
        value_label.grid(row=row, column=1, sticky="e", padx=(10, 0), pady=(10, 10))
        
        return value_label

    def create_stats_matplotlib_graph(self, parent):
        """Create a Matplotlib graph with dark theme"""
        plt.style.use('dark_background')
        fig, ax = plt.subplots()
        
        fig.patch.set_facecolor(self.stats_colors["card_bg"])
        ax.set_facecolor(self.stats_colors["card_bg"])
        
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        
        fig.tight_layout(pad=3.0)
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        return canvas

    def update_stats(self, event=None):
        """Update all statistics based on selected time period"""
        period = self.stats_period_var.get()
        self.stats_status_label.configure(text=f"Loading {period} statistics...")
        self.update_idletasks()
        
        stats = self.stats_manager.get_summary_stats(period)
        
        self.animate_stats_label_update(self.total_time_label, stats['total_time'])
        self.animate_stats_label_update(self.total_sessions_label, str(stats['total_sessions']))
        self.animate_stats_label_update(self.avg_session_label, stats['avg_session'])

        self.type_tree.delete(*self.type_tree.get_children())
        for station_type, type_stats in stats['station_types'].items():
            self.type_tree.insert('', 'end', values=(
                station_type,
                type_stats['sessions'],
                type_stats['total_time'],
                type_stats['avg_time']
            ))

        if self.stats_notebook.get() == "Game Rankings":
            self.update_stats_game_rankings()

        self.update_stats_summary_graph(stats)
        self.update_stats_station_type_graph(stats['station_types'])
        
        self.stats_status_label.configure(text=f"Showing statistics for: {period}")

    def animate_stats_label_update(self, label, new_value):
        """Animate label updates"""
        label.configure(text=new_value)
        self.update_idletasks()

    def update_stats_station_stats(self, event=None):
        """Update station statistics display"""
        station = self.station_var.get()
        if not station:
            return
            
        self.stats_status_label.configure(text=f"Loading statistics for {station}...")
        self.update_idletasks()
        
        stats = self.stats_manager.get_station_stats(station)
        self.station_tree.delete(*self.station_tree.get_children())
        
        highlight_keys = ['Total Sessions', 'Total Time', 'Average Session']
        for metric, value in stats.items():
            tag = "highlight" if metric in highlight_keys else ""
            item_id = self.station_tree.insert('', 'end', values=(metric, value), tags=(tag,))
            if tag:
                self.station_tree.tag_configure("highlight", background=self.stats_colors["primary"])
        
        self.update_stats_station_usage_graph(station)
        self.stats_status_label.configure(text=f"Showing statistics for: {station}")

    def update_stats_game_rankings(self):
        """Update the game rankings display"""
        rankings = self.stats_manager.get_game_rankings(self.stats_period_var.get())
        self.games_tree.delete(*self.games_tree.get_children())
        
        for rank, (game, stats) in enumerate(rankings.items(), 1):
            tag = f"rank{rank}" if rank <= 3 else ""
            self.games_tree.insert('', 'end', values=(
                rank,
                game,
                stats['sessions'],
                stats['total_time']
            ), tags=(tag,))
        
        self.games_tree.tag_configure("rank1", background="#ffd700", foreground="#1a1a1a")
        self.games_tree.tag_configure("rank2", background="#c0c0c0", foreground="#1a1a1a")
        self.games_tree.tag_configure("rank3", background="#cd7f32", foreground="#1a1a1a")
        
        self.update_stats_game_rankings_graph(rankings)

    def update_stats_summary_graph(self, stats):
        """Update the summary graph"""
        fig = self.summary_chart_canvas.figure
        fig.clear()
        
        total_time = self._stats_convert_time_to_minutes(stats['total_time'])
        total_sessions = stats['total_sessions']
        avg_session = self._stats_convert_time_to_minutes(stats['avg_session'])
        
        ax = fig.add_subplot(111)
        x_pos = [0, 1, 2]
        categories = ['Total Time\n(hours)', 'Total\nSessions', 'Avg Session\n(minutes)']
        total_time_hours = total_time / 60
        values = [total_time_hours, total_sessions, avg_session]
        colors = [self.stats_colors["primary"], self.stats_colors["secondary"], self.stats_colors["accent"]]
        
        bars = ax.bar(x_pos, values, color=colors, width=0.6)
        for bar in bars:
            if values[bars.index(bar)] > 0:
                label = f"{values[bars.index(bar)]:.1f}" if isinstance(values[bars.index(bar)], float) else f"{values[bars.index(bar)]}"
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (max(values) * 0.02), 
                    label, ha='center', va='bottom', color='white', fontweight='bold')
        
        ax.set_xticks(x_pos)
        ax.set_xticklabels(categories)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('gray')
        ax.spines['bottom'].set_color('gray')
        
        ax.set_title(f"Usage Summary: {self.stats_period_var.get()}", color='white', fontsize=12, pad=10)
        fig.tight_layout()
        self.summary_chart_canvas.draw()

    def update_stats_station_type_graph(self, station_types):
        """Update station type breakdown pie chart"""
        fig = self.station_type_graph.figure
        fig.clear()
        
        labels = list(station_types.keys())
        sessions = [type_stats['sessions'] for type_stats in station_types.values()]
        
        if sum(sessions) == 0:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "No data available", 
                    ha='center', va='center', fontsize=12, color='white')
            fig.tight_layout()
            self.station_type_graph.draw()
            return
        
        ax = fig.add_subplot(111)
        colors = [self.get_stats_station_color(label) for label in labels]
        max_index = sessions.index(max(sessions))
        explode = [0.05 if i == max_index else 0 for i in range(len(sessions))]
        
        wedges, texts, autotexts = ax.pie(
            sessions, 
            labels=labels, 
            autopct='%1.1f%%', 
            startangle=90, 
            colors=colors,
            explode=explode,
            shadow=True,
            wedgeprops={'edgecolor': 'white', 'linewidth': 1, 'antialiased': True},
            textprops={'color': 'white', 'fontsize': 9}
        )
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title("Station Usage Distribution", color='white', fontsize=12)
        fig.tight_layout()
        self.station_type_graph.draw()

    def update_stats_station_usage_graph(self, station):
        """Update station usage pattern graph"""
        fig = self.station_type_usage_graph.figure
        fig.clear()
        
        if not station:
            return
            
        ax = fig.add_subplot(111)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        # Generate usage patterns (placeholder - would use real data)
        import hashlib
        seed = int(hashlib.md5(station.encode()).hexdigest(), 16) % 1000
        np.random.seed(seed)
        morning = np.random.randint(0, 5, 7)
        afternoon = np.random.randint(1, 8, 7)
        evening = np.random.randint(2, 10, 7)
        
        width = 0.6
        ax.bar(days, morning, width, label='Morning', color=self.stats_colors["primary"])
        ax.bar(days, afternoon, width, bottom=morning, label='Afternoon', color=self.stats_colors["secondary"])
        ax.bar(days, evening, width, bottom=morning+afternoon, label='Evening', color=self.stats_colors["accent"])
        
        ax.set_title(f"Weekly Usage Pattern: {station}", color='white', fontsize=12)
        ax.set_ylabel("Hours Used", color='white')
        ax.legend(loc='upper right', facecolor=self.stats_colors["card_bg"], edgecolor='gray')
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('gray')
        ax.spines['bottom'].set_color('gray')
        
        fig.tight_layout()
        self.station_type_usage_graph.draw()

    def update_stats_game_rankings_graph(self, rankings):
        """Update game rankings graph"""
        fig = self.game_rankings_graph.figure
        fig.clear()
        
        if not rankings:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "No game data available", 
                    ha='center', va='center', fontsize=12, color='white')
            fig.tight_layout()
            self.game_rankings_graph.draw()
            return
        
        games = list(rankings.keys())[:8]
        sessions = [stats['sessions'] for game, stats in rankings.items()][:8]
        
        ax = fig.add_subplot(111)
        colors = self._stats_generate_color_gradient(
            self.stats_colors["primary"], 
            self.stats_colors["accent"], 
            len(games)
        )
        
        bars = ax.barh(
            games, 
            sessions, 
            color=colors,
            height=0.5, 
            edgecolor='white',
            linewidth=0.5
        )
        
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(
                width - (max(sessions) * 0.05),
                bar.get_y() + bar.get_height()/2,
                f"{sessions[i]}",
                va='center',
                color='white',
                fontweight='bold'
            )
        
        ax.set_title("Most Popular Games", color='white', fontsize=12)
        ax.set_xlabel("Number of Sessions", color='white')
        labels = [textwrap.fill(game, 20) for game in games]
        ax.set_yticks(range(len(games)))
        ax.set_yticklabels(labels)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('gray')
        ax.spines['bottom'].set_color('gray')
        
        fig.tight_layout()
        self.game_rankings_graph.draw()

    def _stats_convert_time_to_minutes(self, time_str):
        """Convert time string to minutes"""
        try:
            if 'day' in time_str:
                days_part, time_part = time_str.split(', ')
                days = int(days_part.split()[0])
                hours, minutes, seconds = map(int, time_part.split(':'))
                return days * 24 * 60 + hours * 60 + minutes
            else:
                parts = time_str.split(':')
                if len(parts) == 3:
                    hours, minutes, seconds = map(int, parts)
                    return hours * 60 + minutes
                elif len(parts) == 2:
                    minutes, seconds = map(int, parts)
                    return minutes
        except Exception as e:
            print(f"Error parsing time: {time_str}")
            print(f"Error details: {e}")
        return 0

    def _stats_generate_color_gradient(self, start_color, end_color, steps):
        """Generate color gradient"""
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
        
        start_rgb = hex_to_rgb(start_color)
        end_rgb = hex_to_rgb(end_color)
        
        colors = []
        for i in range(steps):
            r = start_rgb[0] + (end_rgb[0] - start_rgb[0]) * i / (steps-1)
            g = start_rgb[1] + (end_rgb[1] - start_rgb[1]) * i / (steps-1)
            b = start_rgb[2] + (end_rgb[2] - start_rgb[2]) * i / (steps-1)
            colors.append(rgb_to_hex((r, g, b)))
        
        return colors

    def get_stats_station_color(self, station_type):
        """Return color for station type"""
        color_map = {
            'XBOX': '#107C10',         # Xbox green
            'Playstation': '#006FCD',  # PlayStation blue
            'Switch': '#E60012',       # Nintendo red
            'PC': '#00ADEF',           # Windows blue
            'Ping-Pong': '#FF69B4',    # Hot pink
            'PoolTable': '#008080',    # Teal
            'Air Hockey': '#1E90FF',   # Dodger blue
            'Foosball': '#FF8C00',     # Dark orange
            'VR': '#9370DB',           # Medium purple
            'Board Games': '#2E8B57'   # Sea green
        }
        return color_map.get(station_type, self.stats_colors["primary"])

    def export_stats_to_excel(self):
        """Export statistics to Excel/CSV files"""
        try:
            self.stats_status_label.configure(text="Exporting data...")
            self.update_idletasks()
            
            result = self.stats_manager.export_daily_stats()
            self.stats_status_label.configure(text="✓ Export complete!")
            
            messagebox.showinfo("Export Complete", 
                            f"Statistics have been exported to the 'statistics' folder.")
            
            self.after(3000, lambda: self.stats_status_label.configure(text=""))
        except Exception as e:
            self.stats_status_label.configure(text="❌ Export failed")
            messagebox.showerror("Export Error", f"Failed to export data: {str(e)}")

    def on_stats_tab_change(self):
        """Handle tab change events"""
        active_tab = self.stats_notebook.get()
        if active_tab == "Summary":
            self.update_stats()
        elif active_tab == "Station Details":
            self.update_stats_station_stats(None)
        elif active_tab == "Game Rankings":  
            self.update_stats_game_rankings()

    def load_orbitron_font(self):
        """Load Orbitron font after window initialization"""
        try:
            # Check if font is already available in system
            available_fonts = tkFont.families()
            if "Orbitron" in available_fonts:
                print("Orbitron font found in system fonts")
                return True
            
            # If not, try to load from the font file in your project directory
            font_path = "./fonts/Orbitron-VariableFont_wght.ttf"
            if os.path.exists(font_path):
                print(f"Found font file at: {font_path}")
                
                # For Windows, add the font to the system temporarily
                if os.name == 'nt':  # Windows
                    from ctypes import windll
                    if windll.gdi32.AddFontResourceW(os.path.abspath(font_path)):
                        print("Font added to Windows resources")
                
                # Register with Tkinter
                temp_font = tkFont.Font(family="Orbitron")
                print(f"Registered font: {temp_font.actual()}")
                return True
                
            print("Orbitron font file not found")
            return False
        except Exception as e:
            print(f"Error loading font: {e}")
            return False
            
    def get_font_family(self):
        """Get the appropriate font family with fallback"""
        try:
            available_fonts = tkFont.families()
            if "Orbitron" in available_fonts:
                print("Using Orbitron font")
                return "Orbitron"
            else:
                print("Orbitron font not found, using Helvetica")
                return "Helvetica"
        except Exception as e:
            print(f"Error in get_font_family: {e}")
            return "Helvetica"


    def load_station_states(self):
        save_path = os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"), "UVU-Game-Center-App", "station_state.json")
        if not os.path.exists(save_path):
            return

        try:
            with open(save_path, "r") as f:
                state = json.load(f)

            now = time.time()

            for i, s in enumerate(state):
                if i >= len(self.stations):
                    break  # Skip if there are more saved states than stations
                    
                station = self.stations[i]
                
                # Restore fields - IMPORTANT FIX: Check if fields exist and have values
                if s.get("name") and hasattr(station, "name_entry") and station.name_entry:
                    station.name_entry.delete(0, tk.END)
                    station.name_entry.insert(0, s.get("name", ""))
                
                # Restore fields - ID entry
                if s.get("id") and hasattr(station, "id_entry") and station.id_entry:
                    station.id_entry.delete(0, tk.END)
                    station.id_entry.insert(0, s.get("id", ""))
                    
                if s.get("game") and hasattr(station, "game_var") and station.game_var:
                    station.game_var.set(s.get("game", ""))
                    
                if s.get("controller") and hasattr(station, "controller_var") and station.controller_var:
                    station.controller_var.set(s.get("controller", ""))

               

                # Restore timer state
                timer_state = s.get("timer", {})
                timer = station.timer
                timer.time_limit = timer_state.get("time_limit", timer.time_limit)
                saved_elapsed = timer_state.get("elapsed_time", 0)
                was_running = timer_state.get("is_running", False)

                if was_running:
                    timer.elapsed_time = saved_elapsed
                    timer.start_time = now - saved_elapsed
                    timer.is_running = True
                    timer.timer_label.configure(text=time.strftime("%H:%M:%S", time.gmtime(timer.elapsed_time)))
                    timer.update_timer()
                    
                    # Apply appropriate border colors based on time elapsed
                    progress = saved_elapsed / timer.time_limit
                    if progress >= 1.0:
                        station.configure(border_color="red", border_width=2)
                    elif progress >= 0.9:
                        station.configure(border_color="orange", border_width=2)
                    elif progress >= 0.8:
                        station.configure(border_color="yellow", border_width=2)
                    else:
                        station.configure(border_color="green", border_width=2)
                else:
                    timer.elapsed_time = saved_elapsed
                    timer.is_running = False
                    timer.timer_label.configure(text=time.strftime("%H:%M:%S", time.gmtime(timer.elapsed_time)))
                    timer.draw_ring(min(saved_elapsed / timer.time_limit, 1.0))

                # Restore button state
                station.update_button_states(is_active=was_running)
        except Exception as e:
            import traceback
            print(f"Error loading station states: {e}")
            print(traceback.format_exc())

    def save_station_states(self):
        state = []
        for station in self.stations:
            timer = station.timer
            is_running = timer.is_running
            elapsed_time = timer.get_time()
            
            state.append({
                "station_type": station.station_type,
                "station_num": station.station_num,
                "name": station.name_entry.get() if hasattr(station, "name_entry") and station.name_entry else "",
                "id": station.id_entry.get() if hasattr(station, "id_entry") and station.id_entry else "",
                "game": station.game_var.get() if hasattr(station, "game_var") and station.game_var else "",
                "controller": station.controller_var.get() if hasattr(station, "controller_var") and station.controller_var else "",
                "timer": {
                    "is_running": is_running,
                    "start_time": timer.start_time,
                    "elapsed_time": elapsed_time,
                    "time_limit": timer.time_limit
                }
            })
    
        save_path = os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"), "UVU-Game-Center-App", "station_state.json")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w") as f:
            json.dump(state, f)



    def create_arch_overlay(self):
        """Create an arch effect using a canvas directly"""
        arch_radius = 30
        
        try:
            # Create a transparent canvas
            self.arch_overlay = ctk.CTkCanvas(
                self.main_container,
                width=arch_radius,
                height=arch_radius,
                bg="#171717",  # Match the main background
                highlightthickness=0
            )
            
            # Draw a circle in the content area color
            self.arch_overlay.create_arc(
                0, 0,  # Top-left of bounding box
                arch_radius*2, arch_radius*2,  # Bottom-right of bounding box
                start=90, extent=90,  # Draw from 90° to 180° (top-left quadrant)
                fill="#090A09",  # Content area color
                outline=""  # No outline
            )
            
            # Position at the inner corner where sidebar and topbar meet
            self.arch_overlay.place(x=158-arch_radius, y=90-arch_radius)
            
            # Force the arch overlay to the top of the stacking order
            # This is the key fix - using tkraise() with an explicit aboveThis parameter
            self.after(100, lambda: self.main_container.tk.call('raise', self.arch_overlay._w))
        except Exception as e:
            print(f"Error creating arch overlay: {e}")

    def create_visible_arch_test(self):
        """Test version with a bright color to see positioning"""
        arch_radius = 30
        
        # Create the image
        arch_image = Image.new('RGBA', (arch_radius, arch_radius), (0, 0, 0, 0))
        
        # Use a bright test color to see if it's positioned correctly
        test_color = (255, 0, 255, 255)  # Bright magenta for testing
        
        # Draw quarter circle
        for x in range(arch_radius):
            for y in range(arch_radius):
                distance = (x**2 + y**2)**0.5
                if distance <= arch_radius:
                    arch_image.putpixel((x, y), test_color)
        
        # Convert to CTkImage
        arch_ctk_image = ctk.CTkImage(arch_image, size=(arch_radius, arch_radius))
        
        # Create and position overlay
        self.arch_overlay = ctk.CTkLabel(
            self.main_container,
            image=arch_ctk_image,
            text="",
            fg_color="transparent"
        )
        
        # Test different positions - try this first to see where it appears
        self.arch_overlay.place(x=85, y=40, anchor="nw")
        self.arch_overlay.lift()

    def create_proper_arch_overlay(self):
        """Final version with correct color matching your content area"""
        arch_radius = 25  # Slightly smaller for better proportion
        
        # Create image with scale factor for anti-aliasing
        scale_factor = 3
        scaled_radius = arch_radius * scale_factor
        arch_image = Image.new('RGBA', (scaled_radius, scaled_radius), (0, 0, 0, 0))
        draw = ImageDraw.Draw(arch_image)
        
        # This should match your inner content frame color exactly
        # Look at your code: inner_content has fg_color="#1E1E1E"
        content_bg_color = (30, 30, 30, 255)  # #1E1E1E converted to RGBA
        
        # Draw a perfect circle and take only the top-left quarter
        # Position circle so we get the curved corner effect
        draw.ellipse([0, 0, scaled_radius * 2, scaled_radius * 2], fill=content_bg_color)
        
        
        # This should match your inner content frame color exactly
        # Look at your code: inner_content has fg_color="#1E1E1E"
        content_bg_color = (30, 30, 30, 255)   # #1E1E1E converted to RGBA
        
        # Draw a perfect circle and take only the top-left quarter
        # Position circle so we get the curved corner effect
        draw.ellipse([0, 0, scaled_radius * 2, scaled_radius * 2], fill=content_bg_color)
        
        # Crop to get only the top-left quarter
        self.arch_overlay.lift()


    def setup_top_bar(self, top_bar):
        """Create a top bar with help and menu icons"""
       
        # Add triple dot menu icon on the left
        menu_icon_path = "./icon_cache/ellipsis.png"  # Assuming you have this icon
        try:
            menu_image = Image.open(menu_icon_path)
            menu_icon = ctk.CTkImage(menu_image, size=(18, 18))
            menu_button = ctk.CTkButton(
                top_bar,
                image=menu_icon,
                text="",
                width=32,
                height=32,
                corner_radius=8,
                fg_color="transparent",
               
                hover_color="#3A3A3A",
                command=self.show_menu
            )
            menu_button.pack(side="left", padx=10)
        except Exception as e:
            print(f"Error loading menu icon: {e}")
            # Fallback text button
            menu_button = ctk.CTkButton(
                top_bar,
                text="≡",
                width=32,
                height=32,
                corner_radius=8,
                fg_color="transparent",
                hover_color="#3A3A3A",
                command=self.show_menu
            )
            menu_button.pack(side="left", padx=10)
        
        # Add help icon on the right

        help_icon_path = "./icon_cache/circle-help.png"  # Assuming you have this icon
        try:
            help_image = Image.open(help_icon_path)
            help_icon = ctk.CTkImage(help_image, size=(18, 18))
            help_button = ctk.CTkButton(
                top_bar,
                image=help_icon,
                text="",
                width=32,
                height=32,
                corner_radius=8,
                fg_color="transparent",
                hover_color="#3A3A3A",
                command=self.show_help
            )
            help_button.pack(side="right", padx=10)
        except Exception as e:
            print(f"Error loading help icon: {e}")
            # Fallback text button
            help_button = ctk.CTkButton(
                top_bar,
                text="?",
                width=32,
                height=32,
                corner_radius=8,
                fg_color="transparent", 
                hover_color="#3A3A3A",
                command=self.show_help
            )
            help_button.pack(side="right", padx=10)        

    def setup_sidebar(self, sidebar):
        # Add the main logo at the top
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent", height=60)
        logo_frame.pack(fill="x", pady=(10, 20))
        logo_frame.pack_propagate(False)

        # Load logo image
        logo_image_path = "./icon_cache/GamingCenterApp.png"
        try:
            logo_image = Image.open(logo_image_path)
            logo_ctk_image = ctk.CTkImage(logo_image, size=(60, 60))
        except Exception as e:
            print(f"Error loading logo image: {e}")
            logo_ctk_image = None

        logo_label = ctk.CTkLabel(
            logo_frame,
            image=logo_ctk_image,
            text="",
            width=85,
            height=85
        )
        logo_label.place(relx=0.5, rely=0.5, anchor="center")

        # Load sidebar icons
        home = ctk.CTkImage(Image.open("./icon_cache/house.png"), size=(24, 24))
        games = ctk.CTkImage(Image.open("./icon_cache/gamepad-2.png"), size=(24, 24))
        reservations_icon = ctk.CTkImage(Image.open("./icon_cache/calendar-clock.png"), size=(24, 24))
        waitlist = ctk.CTkImage(Image.open("./icon_cache/list-plus.png"), size=(24, 24))
        stats = ctk.CTkImage(Image.open("./icon_cache/chart-pie.png"), size=(24, 24))

        # Create sidebar buttons with hover effects
        self.sidebar_buttons = {}
        self.sidebar_buttons["home"] = self.create_sidebar_button(home, "Home", command=lambda: self.show_page("home"))
        self.sidebar_buttons["games"] = self.create_sidebar_button(games, "Games", command=self.open_games_window)
        self.sidebar_buttons["reservations"] = self.create_sidebar_button(
            reservations_icon, "Reservations", command=lambda: self.show_page("reservations")
        )
        self.sidebar_buttons["waitlist"] = self.create_sidebar_button(waitlist, "Waitlist", command=lambda: self.show_page("waitlist"))
        self.sidebar_buttons["stats"] = self.create_sidebar_button(stats, "Stats", command=lambda: self.show_page("stats"))


        # Add a count label to the Waitlist button
        self.waitlist_count_label = ctk.CTkLabel(
            self.sidebar_buttons["waitlist"],
            text="0",
            fg_color="red",
            text_color="white",
            corner_radius=10,
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
        btn_frame.pack(fill="x", pady=1)

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
        """Create an enhanced tooltip with arrow pointer"""
        return EnhancedTooltip(widget, text)

    def show_home(self):
        # Implement home view functionality
        pass

    def stop_timers(self):
        for timer in self.timers:  # Assuming self.timers is a list of your timer instances
            timer.stop()  # Call the stop method for each timer
        self.is_running = False  # Set running flag to False

    def on_close(self):
        # Stop all timers and cancel after jobs
        for timer in self.timers:
            if hasattr(timer, '_update_loop_id') and timer._update_loop_id:
                timer.after_cancel(timer._update_loop_id)
                timer._update_loop_id = None
            if hasattr(timer, '_blink_loop_id') and timer._blink_loop_id:
                timer.after_cancel(timer._blink_loop_id)
                timer._blink_loop_id = None
            timer.is_blinking = False
        self.save_station_states()
        self.destroy()

    # Add placeholder methods for the new buttons
    def show_menu(self):
        """Show the application menu"""
        print("Menu clicked - functionality to be implemented")
        # Placeholder for menu functionality

    def show_help(self):
        """Show help information"""
        print("Help clicked - functionality to be implemented")
        # Placeholder for help functionality

    def setup_ui(self):
        # Create main container with proper padding to prevent overflow
        main_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        frames_to_focus = [main_frame, self.content_area]

        for frame in frames_to_focus:
            frame.bind("<Button-1>", lambda event, f=frame: f.focus_set())
        
        # Configure grid weights to ensure proper scaling
        for i in range(6):  # 6 rows
            main_frame.grid_rowconfigure(i, weight=1)
        for i in range(3):  # 3 columns
            main_frame.grid_columnconfigure(i, weight=1)
        
        # Create first 4 console stations (left column) in reverse order
        for i in range(4):
            shadow = ctk.CTkFrame(
                main_frame,
                corner_radius=15,
                fg_color="#282828",
                border_width=0
            )
            # Grid the shadow with offset padding to create the drop shadow effect
            shadow.grid(row=i, column=0, padx=(10, 14), pady=(10, 14), sticky="nsew")
            
            # Then create actual station on top of shadow
            station = Station(main_frame, self, "XBOX", 4 - i)
            station.grid(row=i, column=0, padx=10, pady=10, sticky="nsew")
            self.stations.append(station)
            self.timers.append(station.timer)
        
        # Create 5th console station (top center) with shadow
        shadow = ctk.CTkFrame(
            main_frame,
            corner_radius=15,
            fg_color="#282828",
            border_width=0
        )
        # Grid with offset padding
        shadow.grid(row=0, column=1, columnspan=2, padx=(10, 14), pady=(10, 14), sticky="nsew")
        
        station = Station(main_frame, self, "XBOX", 5)
        station.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.stations.append(station)
        self.timers.append(station.timer)
        
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
            # Create shadow
            shadow = ctk.CTkFrame(
                main_frame,
                corner_radius=15,
                fg_color="#282828",
                border_width=0
            )
            # Grid with offset padding
            shadow.grid(row=row, column=col, padx=(10, 14), pady=(10, 14), sticky="nsew")
            
            # Create station
            station = Station(main_frame, self, activity, num)
            station.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.stations.append(station)
            self.timers.append(station.timer)
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

    # def show_waitlist_window(self):
    #     """Method for GamingCenterApp class"""
    #     # Initialize bowling waitlist if it doesn't exist
    #     if not hasattr(self, 'bowling_waitlist'):
    #         self.bowling_waitlist = []  # Create a separate list for bowling waitlist
        
    #     waitlist_window = ctk.CTkToplevel(self)
    #     waitlist_window.title("Waitlist")
    #     waitlist_window.geometry("1200x800")
    #     self.waitlist_window = waitlist_window  # Store reference to the window

    #     waitlist_window.lift()
    #     waitlist_window.focus_force()
    #     waitlist_window.grab_set()
        
    #     # Create main container
    #     main_frame = ctk.CTkFrame(waitlist_window)
    #     main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    #     # Header frame with title, toggle and count
    #     header_frame = ctk.CTkFrame(main_frame)
    #     header_frame.pack(fill="x", pady=(0, 20))
        
    #     # Create toggle for waitlist type
    #     self.waitlist_type_var = ctk.StringVar(value="Game Center")
    #     waitlist_toggle = ctk.CTkSegmentedButton(
    #         header_frame,
    #         values=["Game Center", "Bowling Lanes"],
    #         variable=self.waitlist_type_var,
    #         command=self.switch_waitlist_type
    #     )
    #     waitlist_toggle.pack(side="left", padx=(0, 20))
        
    #     title_frame = ctk.CTkFrame(header_frame)
    #     title_frame.pack(side="left")
        
    #     # Title label that will update based on selected waitlist type
    #     self.title_label = ctk.CTkLabel(
    #         title_frame, 
    #         text="Gaming Center Waitlist", 
    #         font=("Helvetica", 20, "bold")
    #     )
    #     self.title_label.pack(side="left", padx=5)
        
    #     # Count label that will update based on selected waitlist
    #     self.count_label = ctk.CTkLabel(
    #         title_frame, 
    #         text=str(len(self.waitlist)), 
    #         fg_color="blue", 
    #         text_color="white",
    #         corner_radius=10, 
    #         width=30
    #     )
    #     self.count_label.pack(side="left", padx=5)

    #     # Search frame
    #     search_frame = ctk.CTkFrame(header_frame)
    #     search_frame.pack(side="right")
    #     self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search parties", width=200)
    #     self.search_entry.pack(side="right", padx=5)

    #     # Create a frame to hold both the treeview and buttons side by side
    #     content_frame = ctk.CTkFrame(main_frame)
    #     content_frame.pack(fill="both", expand=True)

    #     # Create custom style for Treeview
    #     style = ttk.Style()
    #     style.theme_use("default")

    #     style.configure(
    #         "Waitlist.Treeview",
    #         background="#2b2b2b",
    #         foreground="white",
    #         fieldbackground="#2b2b2b",
    #         rowheight=50,
    #         font=("Helvetica", 12)
    #     )
    #     style.configure(
    #         "Waitlist.Treeview.Heading",
    #         background="#333333",
    #         foreground="white",
    #         font=("Helvetica", 12, "bold"),
    #         relief="flat"
    #     )
    #     style.map(
    #         "Waitlist.Treeview",
    #         background=[("selected", "#1f538d")],
    #         foreground=[("selected", "white")]
    #     )

    #     # Create columns - same structure for both waitlist types
    #     columns = ("party", "size", "notes", "station", "quotedTime", "arrival")
    #     self.waitlist_tree = ttk.Treeview(
    #         content_frame,
    #         columns=columns,
    #         show="headings",
    #         style="Waitlist.Treeview"
    #     )
        
    #     # Configure column headings and widths
    #     self.headings = {
    #         "party": "PARTY",
    #         "size": "SIZE",
    #         "notes": "NOTES",
    #         "station": "STATION",  # Will be changed to "LANE" for bowling
    #         "quotedTime": "QUOTED TIME",
    #         "arrival": "ARRIVAL"
    #     }
        
    #     for col, heading in self.headings.items():
    #         self.waitlist_tree.heading(col, text=heading)
    #         if col == "size":
    #             self.waitlist_tree.column(col, width=50, anchor="center")  # Narrow size column
    #         else:
    #             self.waitlist_tree.column(col, width=150, anchor="w")  # Adjust width of other columns

    #     # Create a frame for the buttons column
    #     buttons_frame = ctk.CTkFrame(content_frame, width=200)  # Set a fixed width for the actions column
    #     buttons_frame.pack(side="right", fill="y", padx=(10, 0))
        
    #     # Add a header for the actions column
    #     ctk.CTkLabel(buttons_frame, text="ACTIONS", font=("Helvetica", 11, "bold")).pack(pady=(0, 0))

    #     # Load icons
    #     check_icon = ctk.CTkImage(Image.open("./icon_cache/check.png"), size=(16, 16))
    #     x_icon = ctk.CTkImage(Image.open("./icon_cache/x.png"), size=(16, 16))
    #     pencil_icon = ctk.CTkImage(Image.open("./icon_cache/pencil.png"), size=(16, 16))
    #     message_icon = ctk.CTkImage(Image.open("./icon_cache/message-circle-more.png"), size=(16, 16))

    #     # Add a single row of placeholder buttons (grayed-out and un-clickable)
    #     self.placeholder_buttons_frame = ctk.CTkFrame(buttons_frame)
    #     self.placeholder_buttons_frame.pack(pady=10, padx=5)

    #     ctk.CTkButton(
    #         self.placeholder_buttons_frame,
    #         text="✓",
    #         width=30,
    #         height=30,
    #         fg_color="gray",
    #         hover_color="gray",
    #         state="disabled"
    #     ).pack(side="left", padx=2)
    #     ctk.CTkButton(
    #         self.placeholder_buttons_frame,
    #         text="✕",
    #         width=30,
    #         height=30,
    #         fg_color="gray",
    #         hover_color="gray",
    #         state="disabled"
    #     ).pack(side="left", padx=2)
    #     ctk.CTkButton(
    #         self.placeholder_buttons_frame,
    #         text="✎",
    #         width=30,
    #         height=30,
    #         fg_color="gray",
    #         hover_color="gray",
    #         state="disabled"
    #     ).pack(side="left", padx=2)
    #     ctk.CTkButton(
    #         self.placeholder_buttons_frame,
    #         text="✉",
    #         width=30,
    #         height=30,
    #         fg_color="gray",
    #         hover_color="gray",
    #         state="disabled"
    #     ).pack(side="left", padx=2)

    #     # Now it's safe to call:
    #     self.update_waitlist_tree()

    #     # Pack the treeview with scrollbar
    #     tree_scroll = ctk.CTkScrollbar(content_frame, orientation="vertical", command=self.waitlist_tree.yview)
    #     self.waitlist_tree.configure(yscrollcommand=tree_scroll.set)
        
    #     self.waitlist_tree.pack(side="left", fill="both", expand=True)
    #     tree_scroll.pack(side="right", fill="y")

    #     # Store reference to buttons_frame for updating
    #     self.buttons_frame = buttons_frame

    #     # Add floating action button - will be updated based on waitlist type
    #     station_names = [f"{station.station_type} {station.station_num}" for station in self.stations]
    #     self.add_button = ctk.CTkButton(
    #         waitlist_window,
    #         text="+",
    #         width=60,
    #         height=60,
    #         corner_radius=60,

    #         font=("Helvetica", 24, "bold"),
    #         command=lambda: self.add_to_waitlist(station_names)
    #     )
    #     self.add_button.place(relx=0.95, rely=0.95, anchor="se")

    #     def update_tree(event=None):
    #         search_text = self.search_entry.get().lower()
    #         self.update_waitlist_tree(search_text)

    #     self.search_entry.bind('<KeyRelease>', update_tree)
        
    #     # Update the waitlist display
    #     self.update_waitlist_tree()

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
        elif waitlist_type == "Bowling Lanes":
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

    def complete_waitlist_entry(self, entry):
        """Mark a waitlist entry as complete and remove it from the list."""
        waitlist_type = self.waitlist_type_var.get() if hasattr(self, 'waitlist_type_var') else "Game Center"
        current_waitlist = self.bowling_waitlist if waitlist_type == "Bowling Lanes" else self.waitlist
        if entry in current_waitlist:
            current_waitlist.remove(entry)
            self.update_waitlist_tree()
            self.update_waitlist_count()

    def remove_waitlist_entry(self, entry):
        """Remove a waitlist entry from the appropriate list."""
        waitlist_type = self.waitlist_type_var.get() if hasattr(self, 'waitlist_type_var') else "Game Center"
        current_waitlist = self.bowling_waitlist if waitlist_type == "Bowling Lanes" else self.waitlist
        if entry in current_waitlist:
            current_waitlist.remove(entry)
            self.update_waitlist_tree()
            self.update_waitlist_count()

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
            command=partial(self.complete_waitlist_entry, entry)
        ).pack(side="left", padx=2)
        
        remove_btn = ctk.CTkButton(
            button_frame,
            text="✕",
            width=30,
            height=30,
            fg_color="red",
            hover_color="darkred",
            command=partial(self.remove_waitlist_entry, entry)
        ).pack(side="left", padx=2)
        
        
        edit_btn = ctk.CTkButton(
            button_frame,
            text="✎",
            width=30,
            height=30,
            fg_color="blue",
            hover_color="darkblue",
            command=partial(self.edit_waitlist_entry, entry)
        ).pack(side="left", padx=2)
        
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
        
        # Load icon images
        check_icon = ctk.CTkImage(Image.open("./icon_cache/check.png"), size=(16, 16))
        x_icon = ctk.CTkImage(Image.open("./icon_cache/x.png"), size=(16, 16))
        pencil_icon = ctk.CTkImage(Image.open("./icon_cache/pencil.png"), size=(16, 16))
        message_icon = ctk.CTkImage(Image.open("./icon_cache/message-circle-more.png"), size=(16, 16))

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
            

            self.waitlist_tree.bind("<Button-1>", self.handle_click)
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
                command=partial(GamingCenterApp.complete_waitlist_entry, self, entry)
            ).pack(side="left", padx=2)
            
            ctk.CTkButton(
                entry_buttons,
                image=x_icon,
                text="",
                width=30,
                height=30,
                fg_color="red",
                hover_color="darkred",
                command=partial(self.remove_waitlist_entry, entry)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                entry_buttons,
                image=pencil_icon,
                text="",
                width=30,
                height=30,
                fg_color="blue",
                hover_color="darkblue",
                command=partial(self.edit_waitlist_entry, entry)
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
                command=partial(self.send_sms_notification, entry)
            ).pack(side="left", padx=2)
        
        # Update count label with current waitlist count
        if hasattr(self, 'count_label'):
            self.count_label.configure(text=str(len(current_waitlist)))

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

class EnhancedTooltip:
    """Simple, reliable tooltip with triangle pointer and visible text"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self._after_id = None
        
        # Bind events
        self.widget.bind('<Enter>', self.show_tooltip)
        self.widget.bind('<Leave>', self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        """Display the tooltip"""
        # Hide any existing tooltip
        self.hide_tooltip()
        
        # Get widget position (centered below widget)
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        # Create tooltip window
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)  # No window decorations
        
        # Create a frame with padding
        frame = tk.Frame(self.tooltip, bg="#333333", bd=1, relief="solid")
        frame.pack(fill="both", expand=True)
        
        # Add the tooltip content with fixed height and proper triangle pointer
        tooltip_content = tk.Frame(frame, bg="#333333")
        tooltip_content.pack(padx=0, pady=0)
        
        # Draw the triangle pointer
        triangle_canvas = tk.Canvas(
            tooltip_content, 
            width=10, 
            height=6,
            bg="#333333", 
            highlightthickness=0
        )
        triangle_canvas.create_polygon(
            0, 6,   # bottom-left
            5, 0,   # top-center
            10, 6,  # bottom-right
            fill="#333333", 
            outline="#333333"
        )
        triangle_canvas.pack(fill="x", pady=0)
        
        # Text content
        text_label = tk.Label(
            tooltip_content,
            text=self.text,
            justify="center",
            font=("Helvetica", 10),
            fg="white",
            bg="#333333",
            padx=8, 
            pady=4
        )
        text_label.pack(fill="both")
        
        # Position the tooltip 
        self.tooltip.update_idletasks()
        tooltip_width = text_label.winfo_width() + 16  # Add padding
        tooltip_height = text_label.winfo_height() + 16  # Add padding
        self.tooltip.geometry(f"{tooltip_width}x{tooltip_height}")
        self.tooltip.geometry(f"+{x - tooltip_width//2}+{y}")
        self._after_id = self.tooltip.after(5000, self.hide_tooltip)
    
    def hide_tooltip(self, event=None):
        if self._after_id:
            self.tooltip.after_cancel(self._after_id)
            self._after_id = None
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


if __name__ == "__main__":
    app = GamingCenterApp()
    app.iconbitmap("icon_cache/GamingCenterApp.ico")
    app.mainloop()
cProfile.run('app.mainloop()', 'restats')