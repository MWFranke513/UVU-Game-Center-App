import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import math
import os
from datetime import datetime, timedelta
import csv
from collections import defaultdict
import textwrap
from tkinter import messagebox

## NOTE: More date range filters need to be added. All options should include: Today, Yesterday, Last 7 Days, Last 30 Days, This Month, Last Month, This Semester, Last Semester,This Year, Last Year, All Time

class StatsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Gaming Center Statistics")
        # Increase window size and set minimum dimensions
        self.geometry("1200x900")  
        self.minsize(900, 700)
        
        # Initialize stats manager
        self.stats_manager = StatsManager()
        
        # Set theme colors and appearance
        self.configure_theme()
        self.setup_treeview_style()
        
        # Initialize tooltip manager
        self.tooltip_texts = {}
        
        # Setup UI components
        self.setup_ui()
        
        # Update statistics
        self.update_stats()
        
        # Ensure window takes focus when opened
        self.lift()
        self.focus_force()
        self.grab_set()
        
        # Add debug button (hidden by default)
        self.debug_button = ctk.CTkButton(
            self, 
            text="Diagnose Log Parsing", 
            command=self.run_diagnostics,
            fg_color="gray30",
            hover_color="gray40",
            corner_radius=6
        )
        self.debug_button.place(relx=0.97, rely=0.98, anchor="se")

    def configure_theme(self):
        """Configure the app theme colors and appearance"""
        # Set CustomTkinter appearance mode and default color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        
        # Define theme colors
        self.colors = {
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
        
        # Define font configurations
        self.fonts = {
            "heading": ("Roboto", 18, "bold"),
            "subheading": ("Roboto", 16, "normal"),
            "body": ("Roboto", 12, "normal"),
            "small": ("Roboto", 10, "normal"),
            "label": ("Roboto", 12, "bold"),
        }

    def run_diagnostics(self):
        """Run and display diagnostics"""
        diagnostics = self.stats_manager.diagnose_log_parsing()
        messagebox.showinfo("Log Parsing Diagnostics", diagnostics)

    def setup_treeview_style(self):
        """Customize the ttk.Style for treeviews to match the dark theme."""
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure Treeview style
        style.configure(
            "Custom.Treeview", 
            background="#2a2a2a",
            foreground="white",
            fieldbackground="#2a2a2a",
            rowheight=30,
            borderwidth=0,
            font=("Roboto", 11)
        )
        
        # Configure Treeview Heading style
        style.configure(
            "Custom.Treeview.Heading", 
            background="#383838",
            foreground="white",
            relief="flat",
            font=("Roboto", 12, "bold"),
            padding=5
        )
        
        # Map colors for selected items
        style.map(
            "Custom.Treeview", 
            background=[("selected", self.colors["primary"])],
            foreground=[("selected", "white")]
        )

    def setup_ui(self):
        """Set up the main UI components"""
        # Create main container frame with grid layout
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Configure grid layout
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=0)  # Header
        self.main_frame.grid_rowconfigure(1, weight=1)  # Content
        
        # Create header with filters and title
        self.create_header(self.main_frame)
        
        # Create notebook for tabbed interface
        self.notebook = ctk.CTkTabview(
            self.main_frame, 
            corner_radius=10,
            segmented_button_selected_color=self.colors["primary"],
            segmented_button_selected_hover_color=self.colors["secondary"],
            segmented_button_unselected_color="#3a3a3a",
            segmented_button_unselected_hover_color="#4a4a4a",
            command=self.on_tab_change
        )
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Create tabs with modern styling
        summary_tab = self.notebook.add("Summary")
        station_tab = self.notebook.add("Station Details")
        games_tab = self.notebook.add("Game Rankings")
        
        # Set up content for each tab
        self.setup_summary_tab(summary_tab)
        self.setup_station_tab(station_tab)
        self.setup_games_tab(games_tab)
        
        # Add export button container at bottom
        self.create_footer(self.main_frame)
        
        # Initialize tooltips
        self.setup_tooltips()
        
    def create_header(self, parent):
        """Create header section with title and filters"""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)
        
        # Title 
        title_label = ctk.CTkLabel(
            header_frame, 
            text="Gaming Center Statistics", 
            font=("Roboto", 24, "bold"),
            text_color=self.colors["text_light"]
        )
        title_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # Filter container on right side
        filter_frame = ctk.CTkFrame(
            header_frame, 
            fg_color=self.colors["card_bg"],
            corner_radius=10
        )
        filter_frame.grid(row=0, column=1, sticky="e", padx=10, pady=10)
        
        # Time period selector
        ctk.CTkLabel(
            filter_frame, 
            text="Time Period:", 
            font=self.fonts["label"]
        ).pack(side="left", padx=(15, 5), pady=10)
        
        period_choices = [
            'Today', 'Yesterday', 'Last 7 Days', 'Last 30 Days', 
            'This Month', 'Last Month', 'This Semester', 'Last Semester', 
            'This Year', 'Last Year', 'All Time'
        ]
        self.period_var = tk.StringVar(value='Today')
        period_dropdown = ctk.CTkComboBox(
            filter_frame, 
            variable=self.period_var, 
            values=period_choices,
            state='readonly',
            width=180, 
            height=32,
            corner_radius=6,
            dropdown_hover_color=self.colors["hover"],
            button_color=self.colors["primary"],
            button_hover_color=self.colors["secondary"],
            dropdown_fg_color=self.colors["card_bg"],
        )
        period_dropdown.pack(side="left", padx=(5, 15), pady=10)
        period_dropdown.configure(command=self.update_stats)
    
    def create_footer(self, parent):
        """Create footer with export button and other actions"""
        footer_frame = ctk.CTkFrame(parent, fg_color="transparent", height=50)
        footer_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        footer_frame.grid_columnconfigure(0, weight=1)
        
        # Export button
        export_button = ctk.CTkButton(
            footer_frame, 
            text="Export Data", 
            command=self.export_to_excel,
            height=36,
            corner_radius=8,
            font=self.fonts["label"],
            hover_color=self.colors["secondary"],
            image=self.get_icon("export"),
            compound="left"
        )
        export_button.pack(side="right", padx=10, pady=5)
        
        # Status indicator
        self.status_label = ctk.CTkLabel(
            footer_frame,
            text="",
            font=self.fonts["small"],
            text_color="gray70"
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
    def setup_tooltips(self):
        """Set up tooltips for UI elements"""
        # Define tooltip texts
        self.tooltip_texts = {
            "export_button": "Export current statistics to CSV files",
            "period_dropdown": "Select the time period for statistics",
            "station_dropdown": "Select a specific station to view detailed statistics",
            "total_time": "Total usage time across all stations",
            "total_sessions": "Total number of user sessions",
            "avg_session": "Average duration of all sessions",
            "station_usage": "Breakdown of usage by station type",
            "game_rankings": "Most popular games based on play time"
        }
        
        # Tooltip implementation can be added here if desired
        # For a full tooltip implementation, consider adding a create_tooltip() method
    
    def get_icon(self, icon_name):
        """Return icon image for buttons - placeholder function"""
        # This would normally load icons from resources
        # For now, just returning None as placeholder
        return None
    
    def on_tab_change(self):
        """Handle tab change events"""
        # Update content when tab changes
        active_tab = self.notebook.get()
        if active_tab == "Summary":
            self.update_stats()
        elif active_tab == "Station Details":
            self.update_station_stats(None)
        elif active_tab == "Game Rankings":  
            self.update_game_rankings()
            
    def create_stat_card(self, parent, title, row=0, column=0, rowspan=1, colspan=1, padx=10, pady=10):
        """Create a consistent card-style container for statistics"""
        # The method signature declares 'colspan' but the grid method uses 'columnspan'
        # So we need to use 'columnspan' in the grid method calls
    
        card = ctk.CTkFrame(
            parent, 
            fg_color=self.colors["card_bg"],
            corner_radius=10, 
            border_width=0
        )
        card.grid(row=row, column=column, rowspan=rowspan, columnspan=colspan, 
                sticky="nsew", padx=padx, pady=pady)
        
        # Add a shadow effect (using a frame behind with slight offset)
        shadow = ctk.CTkFrame(
            parent,
            fg_color="gray20",
            corner_radius=10,
            border_width=0
        )
        
        # Handle both tuple and integer padding for shadow
        shadow_padx = self._add_padding_offset(padx, 2)
        shadow_pady = self._add_padding_offset(pady, 2)
        
        shadow.grid(row=row, column=column, rowspan=rowspan, columnspan=colspan, 
                  sticky="nsew", padx=shadow_padx, pady=shadow_pady)
        card.lift()  # Put the card in front of the shadow
        
        # Card title
        title_label = ctk.CTkLabel(
            card, 
            text=title, 
            font=self.fonts["subheading"],
            anchor="w", 
            text_color=self.colors["text_light"]
        )
        title_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        # Separator
        separator = ctk.CTkFrame(card, height=1, fg_color="gray40")
        separator.pack(fill="x", padx=15, pady=(5, 10))
        
        # Container for content
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        return content_frame, card

    def _add_padding_offset(self, padding, offset):
        """Add offset to padding value, handling both tuple and integer formats"""
        if isinstance(padding, tuple):
            # If padding is a tuple (left, right), add offset to both values
            return (padding[0] + offset, padding[1] + offset)
        else:
            # If padding is a single integer value
            return padding + offset

    def setup_summary_tab(self, parent):
        """Set up the summary tab with key statistics"""
        # Configure the grid layout for summary tab
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_rowconfigure(0, weight=0)  # Top row for overview cards
        parent.grid_rowconfigure(1, weight=1)  # Bottom row for data grids and charts
        
        # Top Row - Key Metrics cards, side by side
        # Left card - Usage Statistics
        usage_content, usage_card = self.create_stat_card(
            parent, "Usage Statistics", row=0, column=0, padx=(0, 5), pady=(0, 10)
        )
        
        # Configure usage content frame with grid layout
        usage_content.grid_columnconfigure(0, weight=2)  # Label column
        usage_content.grid_columnconfigure(1, weight=3)  # Value column
        
        # Placeholder for metric labels
        self.total_time_label = self.create_metric_display(
            usage_content, "Total Usage Time:", 0, icon_name="time"
        )
        self.total_sessions_label = self.create_metric_display(
            usage_content, "Total Sessions:", 1, icon_name="sessions"
        )
        self.avg_session_label = self.create_metric_display(
            usage_content, "Average Session:", 2, icon_name="average"
        )
        
        # Right card - Usage Chart
        chart_content, chart_card = self.create_stat_card(
            parent, "Usage Trends", row=0, column=1, padx=(5, 0), pady=(0, 10)
        )
        
        # Prepare canvas for the chart
        self.summary_chart_frame = chart_content
        self.create_matplotlib_frame(chart_content)
        self.summary_chart_canvas = self.create_matplotlib_graph(self.summary_chart_frame)
        self.summary_chart_canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        # Bottom row - Station Type Breakdown
        station_type_content, station_type_card = self.create_stat_card(
            parent, "Station Type Breakdown", row=1, column=0, colspan=2
        )
        
        # Create dual-pane layout for table and chart
        station_type_content.grid_columnconfigure(0, weight=3)  # Table column
        station_type_content.grid_columnconfigure(1, weight=2)  # Chart column
        station_type_content.grid_rowconfigure(0, weight=1)
        
        # Table frame
        tree_frame = ctk.CTkFrame(station_type_content, fg_color="transparent")
        tree_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)
        
        # Create treeview for station types
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
        
        # Configure column widths
        self.type_tree.column('Station Type', width=150, anchor='w')
        self.type_tree.column('Sessions', width=80, anchor='center')
        self.type_tree.column('Total Time', width=100, anchor='center')
        self.type_tree.column('Avg Time', width=100, anchor='center')
        
        # Add scrollbar
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.type_tree.yview)
        self.type_tree.configure(yscrollcommand=tree_scrollbar.set)
        tree_scrollbar.pack(side="right", fill="y")
        self.type_tree.pack(fill="both", expand=True)
        
        # Chart frame for station type breakdown
        chart_frame = ctk.CTkFrame(station_type_content, fg_color="transparent")
        chart_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=5)
        
        # Create pie chart for station type breakdown
        self.station_type_graph_frame = chart_frame
        self.station_type_graph = self.create_matplotlib_graph(chart_frame)
        self.station_type_graph.get_tk_widget().pack(fill="both", expand=True)

    def create_metric_display(self, parent, label_text, row, icon_name=None):
        """Create a metric display with icon, label and value"""
        # Icon (placeholder - would normally load an actual icon)
        if icon_name:
            icon_label = ctk.CTkLabel(
                parent, 
                text="●",  # Placeholder circle for icon
                font=("Roboto", 16),
                width=20,
                text_color=self.colors["accent"]
            )
            icon_label.grid(row=row, column=0, sticky="w", padx=(0, 5), pady=(10, 10))
        
        # Metric name label
        ctk.CTkLabel(
            parent,
            text=label_text,
            font=self.fonts["body"],
            anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=(30, 10), pady=(10, 10))
        
        # Value label (to be updated with data)
        value_label = ctk.CTkLabel(
            parent,
            text="Loading...",
            font=self.fonts["heading"],
            anchor="e",
            text_color=self.colors["accent"]
        )
        value_label.grid(row=row, column=1, sticky="e", padx=(10, 0), pady=(10, 10))
        
        return value_label

    def setup_station_tab(self, parent):
        """Set up the station details tab"""
        # Configure the grid layout
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=0)  # Selector area
        parent.grid_rowconfigure(1, weight=1)  # Station stats area
        
        # Station selector card
        selector_content, selector_card = self.create_stat_card(
            parent, "Station Selection", row=0, column=0, pady=(0, 10)
        )
        
        # Station selector dropdown
        ctk.CTkLabel(
            selector_content,
            text="Select Station:",
            font=self.fonts["body"]
        ).pack(side="left", padx=(5, 10), pady=10)
        
        self.station_var = tk.StringVar()
        self.station_dropdown = ctk.CTkComboBox(
            selector_content,
            variable=self.station_var,
            state='readonly',
            width=250,
            height=32,
            corner_radius=6,
            dropdown_hover_color=self.colors["hover"],
            button_color=self.colors["primary"],
            button_hover_color=self.colors["secondary"],
            dropdown_fg_color=self.colors["card_bg"]
        )
        self.station_dropdown.pack(side="left", padx=10, pady=10)
        self.station_dropdown.configure(command=self.update_station_stats)
        
        # Populate the dropdown
        stations = self.stats_manager.get_all_stations()
        self.station_dropdown.configure(values=stations)
        
        # Station details area with split layout
        details_content, details_card = self.create_stat_card(
            parent, "Station Statistics", row=1, column=0
        )
        
        # Configure split view for details content
        details_content.grid_columnconfigure(0, weight=1)  # Left side
        details_content.grid_columnconfigure(1, weight=1)  # Right side
        details_content.grid_rowconfigure(0, weight=1)
        
        # Left side - Station metrics
        left_frame = ctk.CTkFrame(details_content, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)
        
        # Station stats treeview
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
        
        # Add scrollbar for treeview
        tree_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.station_tree.yview)
        self.station_tree.configure(yscrollcommand=tree_scrollbar.set)
        tree_scrollbar.pack(side="right", fill="y")
        self.station_tree.pack(fill="both", expand=True)
        
        # Right side - Station usage chart
        right_frame = ctk.CTkFrame(details_content, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=5)
        
        # Create the station chart
        self.station_chart_frame = right_frame
        self.station_type_usage_graph = self.create_matplotlib_graph(right_frame)
        self.station_type_usage_graph.get_tk_widget().pack(fill="both", expand=True)

    def setup_games_tab(self, parent):
        """Set up the game rankings tab"""
        # Configure grid layout
        parent.grid_columnconfigure(0, weight=4)  # Table area
        parent.grid_columnconfigure(1, weight=3)  # Chart area
        parent.grid_rowconfigure(0, weight=1)
        
        # Game rankings card - left side
        games_content, games_card = self.create_stat_card(
            parent, "Game Rankings", row=0, column=0, padx=(0, 5)
        )
        
        # Games treeview
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
        
        # Configure column widths
        self.games_tree.column('Rank', width=50, anchor='center')
        self.games_tree.column('Game', width=220, anchor='w')
        self.games_tree.column('Sessions', width=80, anchor='center')
        self.games_tree.column('Total Time', width=120, anchor='center')
        
        # Add scrollbar for treeview
        game_scrollbar = ttk.Scrollbar(games_content, orient="vertical", command=self.games_tree.yview)
        self.games_tree.configure(yscrollcommand=game_scrollbar.set)
        game_scrollbar.pack(side="right", fill="y")
        self.games_tree.pack(fill="both", expand=True)
        
        # Game chart card - right side
        chart_content, chart_card = self.create_stat_card(
            parent, "Game Popularity", row=0, column=1, padx=(5, 0)
        )
        
        # Create the game rankings chart
        self.game_rankings_frame = chart_content
        self.game_rankings_graph = self.create_matplotlib_graph(chart_content)
        self.game_rankings_graph.get_tk_widget().pack(fill="both", expand=True)

    def create_matplotlib_frame(self, parent):
        """Create a frame for matplotlib graphs"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True)
        return frame

    def create_matplotlib_graph(self, parent):
        """Create a Matplotlib graph with a dark theme."""
        plt.style.use('dark_background')
        fig, ax = plt.subplots()
        
        # Set background colors to match UI
        fig.patch.set_facecolor(self.colors["card_bg"])
        ax.set_facecolor(self.colors["card_bg"])
        
        # Style text elements
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        
        # Tight layout for better space usage
        fig.tight_layout(pad=3.0)
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        return canvas

    def update_stats(self, event=None):
        """Update all statistics based on selected time period"""
        period = self.period_var.get()
        
        # Show loading status
        self.status_label.configure(text=f"Loading {period} statistics...")
        self.update_idletasks()  # Force UI update
        
        # Get statistics
        stats = self.stats_manager.get_summary_stats(period)
        
        # Update summary labels with a subtle animation effect
        self.animate_label_update(self.total_time_label, stats['total_time'])
        self.animate_label_update(self.total_sessions_label, str(stats['total_sessions']))
        self.animate_label_update(self.avg_session_label, stats['avg_session'])

        # Update station type tree
        self.type_tree.delete(*self.type_tree.get_children())
        for station_type, type_stats in stats['station_types'].items():
            self.type_tree.insert('', 'end', values=(
                station_type,
                type_stats['sessions'],
                type_stats['total_time'],
                type_stats['avg_time']
            ))

        # Update game rankings if that tab is active
        if self.notebook.get() == "Game Rankings":
            self.update_game_rankings()

        # Update graphs
        self.update_summary_graph(stats)
        self.update_station_type_graph(stats['station_types'])
        
        # Clear status
        self.status_label.configure(text=f"Showing statistics for: {period}")

    def animate_label_update(self, label, new_value):
        """Animate the update of a label value with a fade effect"""
        # Set the new value with a slight delay for visual effect
        label.configure(text=new_value)
        
        # You could implement a proper animation here if desired
        # For now, just triggering a UI update
        self.update_idletasks()

    def update_station_stats(self, event=None):
        """Update the station statistics display"""
        station = self.station_var.get()
        if not station:
            return
            
        # Show loading status
        self.status_label.configure(text=f"Loading statistics for {station}...")
        self.update_idletasks()  # Force UI update
        
        # Get statistics for selected station
        stats = self.stats_manager.get_station_stats(station)
        
        # Clear existing data
        self.station_tree.delete(*self.station_tree.get_children())
        
        # Insert new data
        highlight_keys = ['Total Sessions', 'Total Time', 'Average Session']
        for metric, value in stats.items():
            # Highlight important metrics
            tag = "highlight" if metric in highlight_keys else ""
            item_id = self.station_tree.insert('', 'end', values=(metric, value), tags=(tag,))
            
            # Add highlight color
            if tag:
                self.station_tree.tag_configure("highlight", background=self.colors["primary"])
        
        # Update station usage chart
        self.update_station_usage_graph(station)
        
        # Clear status
        self.status_label.configure(text=f"Showing statistics for: {station}")

    def update_game_rankings(self):
        """Update the game rankings display"""
        rankings = self.stats_manager.get_game_rankings(self.period_var.get())
        
        # Clear existing data
        self.games_tree.delete(*self.games_tree.get_children())
        
        # Insert new data with special formatting for top 3
        for rank, (game, stats) in enumerate(rankings.items(), 1):
            tag = f"rank{rank}" if rank <= 3 else ""
            self.games_tree.insert('', 'end', values=(
                rank,
                game,
                stats['sessions'],
                stats['total_time']
            ), tags=(tag,))
        
        # Configure tags for top rankings
        self.games_tree.tag_configure("rank1", background="#ffd700")  # Gold
        self.games_tree.tag_configure("rank1", foreground="#1a1a1a")  # Dark text
        self.games_tree.tag_configure("rank2", background="#c0c0c0")  # Silver
        self.games_tree.tag_configure("rank2", foreground="#1a1a1a")  # Dark text
        self.games_tree.tag_configure("rank3", background="#cd7f32")  # Bronze
        self.games_tree.tag_configure("rank3", foreground="#1a1a1a")  # Dark text
        
        # Update game rankings chart
        self.update_game_rankings_graph(rankings)

    def update_summary_graph(self, stats):
        """Update the summary graph using Matplotlib."""
        # Clear the previous graph
        fig = self.summary_chart_canvas.figure
        fig.clear()
        
        # Extract data for visualization
        total_time = self._convert_time_to_minutes(stats['total_time'])
        total_sessions = stats['total_sessions']
        avg_session = self._convert_time_to_minutes(stats['avg_session'])
        
        # Create a bar plot
        ax = fig.add_subplot(111)
        
        # Create x positions and labels with proper spacing
        x_pos = [0, 1, 2]
        categories = ['Total Time\n(hours)', 'Total\nSessions', 'Avg Session\n(minutes)']
        
        # Convert total_time to hours for better scale
        total_time_hours = total_time / 60
        
        # Use adjusted values for better visualization
        values = [total_time_hours, total_sessions, avg_session]
        colors = [self.colors["primary"], self.colors["secondary"], self.colors["accent"]]
        
        # Create bars with fancy styling
        bars = ax.bar(x_pos, values, color=colors, width=0.6)
        
        # Add a subtle glow/shadow effect to bars
        for bar in bars:
            # Get the bar's position and dimensions
            x, y = bar.get_xy()
            w, h = bar.get_width(), bar.get_height()
            
            # Add value labels on top of bars
            if values[bars.index(bar)] > 0:
                label = f"{values[bars.index(bar)]:.1f}" if isinstance(values[bars.index(bar)], float) else f"{values[bars.index(bar)]}"
                ax.text(x + w/2, h + (max(values) * 0.02), label, 
                        ha='center', va='bottom', color='white', fontweight='bold')
        
        # Customize appearance
        ax.set_xticks(x_pos)
        ax.set_xticklabels(categories)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('gray')
        ax.spines['bottom'].set_color('gray')
        
        # Set title with custom styling
        ax.set_title(f"Usage Summary: {self.period_var.get()}", color='white', fontsize=12, pad=10)
        
        # Ensure tight layout
        fig.tight_layout()
        
        # Update the canvas
        self.summary_chart_canvas.draw()

    def update_station_type_graph(self, station_types):
        """Update the station type breakdown pie chart"""
        # Clear the previous graph
        fig = self.station_type_graph.figure
        fig.clear()
        
        # Get the data
        labels = list(station_types.keys())
        sessions = [type_stats['sessions'] for type_stats in station_types.values()]
        
        # Skip if no data
        if sum(sessions) == 0:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "No data available", 
                    ha='center', va='center', fontsize=12, color='white')
            fig.tight_layout()
            self.station_type_graph.draw()
            return
        
        # Create a pie chart with modern styling
        ax = fig.add_subplot(111)
        
        # Generate styled colors for pie segments
        colors = [self.get_station_color(label) for label in labels]
        
        # Create exploded pie chart for visual emphasis on the largest segment
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
        
        # Make percentage labels more visible
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        # Set title
        ax.set_title("Station Usage Distribution", color='white', fontsize=12)
        
        # Ensure tight layout
        fig.tight_layout()
        
        # Update the canvas
        self.station_type_graph.draw()

    def update_station_usage_graph(self, station):
        """Update the graph displaying usage patterns for a specific station"""
        # Clear the previous graph
        fig = self.station_type_usage_graph.figure
        fig.clear()
        
        if not station:
            return
            
        # This would be enhanced with actual time-series data
        # For now, create a placeholder visualization
        ax = fig.add_subplot(111)
        
        # Extract station type from station string
        station_type = station.split()[0] if ' ' in station else station
        
        # Create placeholder data - this would be replaced with actual historical data
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        # Create random-ish usage pattern based on station name hash
        import hashlib
        seed = int(hashlib.md5(station.encode()).hexdigest(), 16) % 1000
        np.random.seed(seed)
        
        # Generate usage patterns for morning/afternoon/evening
        morning = np.random.randint(0, 5, 7)
        afternoon = np.random.randint(1, 8, 7)
        evening = np.random.randint(2, 10, 7)
        
        # Create a stacked bar chart
        width = 0.6
        ax.bar(days, morning, width, label='Morning', color=self.colors["primary"])
        ax.bar(days, afternoon, width, bottom=morning, label='Afternoon', color=self.colors["secondary"])
        ax.bar(days, evening, width, bottom=morning+afternoon, label='Evening', color=self.colors["accent"])
        
        # Customize appearance
        ax.set_title(f"Weekly Usage Pattern: {station}", color='white', fontsize=12)
        ax.set_ylabel("Hours Used", color='white')
        ax.legend(loc='upper right', facecolor=self.colors["card_bg"], edgecolor='gray')
        
        # Remove spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('gray')
        ax.spines['bottom'].set_color('gray')
        
        # Ensure tight layout
        fig.tight_layout()
        
        # Update the canvas
        self.station_type_usage_graph.draw()

    def update_game_rankings_graph(self, rankings):
        """Update the game rankings visualization"""
        # Clear the previous graph
        fig = self.game_rankings_graph.figure
        fig.clear()
        
        # Skip if no data
        if not rankings:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "No game data available", 
                    ha='center', va='center', fontsize=12, color='white')
            fig.tight_layout()
            self.game_rankings_graph.draw()
            return
        
        # Get the data (limit to top 8 for readability)
        games = list(rankings.keys())[:8]
        sessions = [stats['sessions'] for game, stats in rankings.items()][:8]
        
        # Create horizontal bar chart
        ax = fig.add_subplot(111)
        
        # Create gradient colors based on ranking
        colors = self._generate_color_gradient(
            self.colors["primary"], 
            self.colors["accent"], 
            len(games)
        )
        
        # Create the horizontal bars with styled appearance
        bars = ax.barh(
            games, 
            sessions, 
            color=colors,
            height=0.5, 
            edgecolor='white',
            linewidth=0.5
        )
        
        # Add value labels inside bars
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(
                width - (max(sessions) * 0.05),  # Slightly inside the bar
                bar.get_y() + bar.get_height()/2,
                f"{sessions[i]}",
                va='center',
                color='white',
                fontweight='bold'
            )
        
        # Customize appearance
        ax.set_title("Most Popular Games", color='white', fontsize=12)
        ax.set_xlabel("Number of Sessions", color='white')
        
        # Improve y-axis labels (wrap long game names)
        labels = [textwrap.fill(game, 20) for game in games]
        ax.set_yticks(range(len(games)))
        ax.set_yticklabels(labels)
        
        # Remove spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('gray')
        ax.spines['bottom'].set_color('gray')
        
        # Ensure tight layout
        fig.tight_layout()
        
        # Update the canvas
        self.game_rankings_graph.draw()

    def _convert_time_to_minutes(self, time_str):
        """Convert a time string to minutes."""
        try:
            # Handle the case where time includes days
            if 'day' in time_str:
                days_part, time_part = time_str.split(', ')
                days = int(days_part.split()[0])
                hours, minutes, seconds = map(int, time_part.split(':'))
                return days * 24 * 60 + hours * 60 + minutes
            else:
                # Handle HH:MM:SS format
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
        
        return 0  # Default if parsing fails

    def _generate_color_gradient(self, start_color, end_color, steps):
        """Generate a gradient of colors between start and end colors"""
        # Convert hex colors to RGB
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
        
        # Get RGB values
        start_rgb = hex_to_rgb(start_color)
        end_rgb = hex_to_rgb(end_color)
        
        # Create gradient
        colors = []
        for i in range(steps):
            # Linear interpolation
            r = start_rgb[0] + (end_rgb[0] - start_rgb[0]) * i / (steps-1)
            g = start_rgb[1] + (end_rgb[1] - start_rgb[1]) * i / (steps-1)
            b = start_rgb[2] + (end_rgb[2] - start_rgb[2]) * i / (steps-1)
            colors.append(rgb_to_hex((r, g, b)))
        
        return colors

    def get_station_color(self, station_type):
        """Return a color for a station type with better color assignments"""
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
        return color_map.get(station_type, self.colors["primary"])

    def export_to_excel(self):
        """Export statistics to Excel/CSV files"""
        try:
            # Show loading status
            self.status_label.configure(text="Exporting data...")
            self.update_idletasks()
            
            # Perform the export
            result = self.stats_manager.export_daily_stats()
            
            # Show completion message with animation
            self.status_label.configure(text="✓ Export complete!")
            
            # Flash success message
            messagebox.showinfo("Export Complete", 
                               f"Statistics have been exported to the 'statistics' folder.")
            
            # Reset status after delay
            self.after(3000, lambda: self.status_label.configure(text=""))
            
        except Exception as e:
            # Show error message
            self.status_label.configure(text="❌ Export failed")
            messagebox.showerror("Export Error", f"Failed to export data: {str(e)}")


class StatsManager:
    def __init__(self):
        # Determine the correct path for the log file
        self.log_file = self.find_log_file()
        self.export_dir = "statistics"
        
        # Check if log file exists
        if not os.path.exists(self.log_file):
            print(f"Warning: Log file {self.log_file} does not exist!")
        
        # Create export directory if it doesn't exist
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)

    def find_log_file(self):
        # List of potential log file locations
        potential_locations = [
            "usage_log.txt",  # Current directory
            os.path.join(os.path.dirname(__file__), "usage_log.txt"),  # Same directory as script
            os.path.join(os.path.expanduser("~"), "usage_log.txt"),  # User home directory
        ]
        
        for location in potential_locations:
            if os.path.exists(location):
                print(f"Log file found at: {location}")
                return location
        
        print("No log file found. Using default: usage_log.txt")
        return "usage_log.txt"

    def diagnose_log_parsing(self):
        diagnostic_info = []
        
        diagnostic_info.append(f"Log File Path: {os.path.abspath(self.log_file)}")
        diagnostic_info.append(f"Log File Exists: {os.path.exists(self.log_file)}")
        
        try:
            with open(self.log_file, 'r') as f:
                diagnostic_info.append("First 10 lines of log file:")
                for _ in range(10):
                    line = f.readline().strip()
                    diagnostic_info.append(line)
                    if not line:
                        break
        except Exception as e:
            diagnostic_info.append(f"Error reading log file: {e}")
        
        # Attempt to parse log file
        try:
            data = self.parse_log_file('All Time')
            diagnostic_info.append(f"Total entries parsed: {len(data)}")
            if data:
                diagnostic_info.append("Sample parsed entry:")
                diagnostic_info.append(str(data[0] if data else "No entries found"))
        except Exception as e:
            diagnostic_info.append(f"Error parsing log file: {e}")
        
        return "\n".join(diagnostic_info)

    def parse_log_file(self, period='Today'):
        data = []
        try:
            with open(self.log_file, 'r') as f:
                print(f"Successfully opened {self.log_file}")
                entry = {}
                for line in f:
                    line = line.strip()
                    self.process_log_line(line, entry, period, data)
        except FileNotFoundError:
            print(f"Error: Log file {self.log_file} not found!")
            return data
        except Exception as e:
            print(f"Unexpected error reading log file: {e}")
            return data

        print(f"Parsed {len(data)} entries")
        return data

    def process_log_line(self, line, entry, period, data):
        try:
            if line.startswith('Date:'):
                timestamp_str = line[6:]  # Extract the timestamp string
                try:
                    entry['timestamp'] = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    entry['timestamp'] = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            elif line.startswith('Station Type:'):
                entry['station_type'] = line[13:]
            elif line.startswith('Station Number:'):
                entry['station_number'] = line[15:]
            elif line.startswith('User Name:'):
                entry['user_name'] = line[11:]
            elif line.startswith('Duration:'):
                entry['duration'] = line[10:]
            elif line.startswith('Game:'):
                entry['game'] = line[6:] if line[6:] else 'N/A'
            elif line.startswith('Controllers:'):
                entry['controllers'] = line[13:] if line[13:] else 'N/A'
            elif line.startswith('-' * 50):
                if self.is_valid_entry(entry):
                    if self._is_within_period(entry.get('timestamp', ''), period):
                        data.append(entry.copy())
                    entry.clear()  # Clear entry for the next record
        except Exception as parse_error:
            print(f"Error parsing line: {line}")
            print(f"Error details: {parse_error}")

    def is_valid_entry(self, entry):
        required_keys = ['timestamp', 'station_type', 'station_number', 'duration']
        return all(key in entry for key in required_keys)

    def _is_within_period(self, timestamp, period):
        if not timestamp:
            return False
            
        date = timestamp.date()
        today = datetime.now().date()
        
        if period == 'Today':
            return date == today
        elif period == 'Yesterday':
            return date == today - timedelta(days=1)
        elif period == 'Last 7 Days':
            return (today - date).days <= 7
        elif period == 'Last 30 Days':
            return (today - date).days <= 30
        elif period == 'This Month':
            return date.year == today.year and date.month == today.month
        elif period == 'Last Month':
            last_month = today.replace(day=1) - timedelta(days=1)
            return date.year == last_month.year and date.month == last_month.month
        elif period == 'This Semester':
            # Assuming semesters are Jan-Apr and Sep-Dec
            if today.month >= 1 and today.month <= 4:
                return date.year == today.year and date.month >= 1 and date.month <= 4
            elif today.month >= 9 and today.month <= 12:
                return date.year == today.year and date.month >= 9 and date.month <= 12
        elif period == 'Last Semester':
            # Assuming semesters are Jan-Apr and Sep-Dec
            if today.month >= 1 and today.month <= 4:
                last_semester_start = today.replace(year=today.year - 1, month=9, day=1)
                last_semester_end = today.replace(year=today.year - 1, month=12, day=31)
            else:
                last_semester_start = today.replace(month=1, day=1)
                last_semester_end = today.replace(month=4, day=30)
            return last_semester_start <= date <= last_semester_end
        elif period == 'This Year':
            return date.year == today.year
        elif period == 'Last Year':
            return date.year == today.year - 1
        else:  # All Time
            return True

    def _parse_duration(self, duration_str):
        try:
            h, m, s = map(int, duration_str.split(':'))
            return timedelta(hours=h, minutes=m, seconds=s)
        except:
            return timedelta(0)

    def get_summary_stats(self, period='Today'):
        data = self.parse_log_file(period)
        
        total_time = timedelta(0)
        station_types = defaultdict(lambda: {'sessions': 0, 'total_time': timedelta(0)})
        excluded_station_types = {'PoolTable', 'Ping-Pong', 'Air Hockey', 'Foosball'}
        
        for entry in data:
            if entry['station_type'] in excluded_station_types:
                continue
            
            duration = self._parse_duration(entry['duration'])
            total_time += duration
            
            station_type = entry['station_type']
            station_types[station_type]['sessions'] += 1
            station_types[station_type]['total_time'] += duration
        
        # Calculate averages for station types
        for type_stats in station_types.values():
            if type_stats['sessions'] > 0:
                type_stats['avg_time'] = type_stats['total_time'] / type_stats['sessions']
            else:
                type_stats['avg_time'] = timedelta(0)
                
            # Convert timedelta to string representation
            type_stats['total_time'] = str(type_stats['total_time']).split('.')[0]
            type_stats['avg_time'] = str(type_stats['avg_time']).split('.')[0]
        
        return {
            'total_time': str(total_time).split('.')[0],
            'total_sessions': len(data),
            'avg_session': str(total_time / len(data) if data else timedelta(0)).split('.')[0],
            'station_types': dict(station_types)
        }

    def get_station_stats(self, station):
        data = self.parse_log_file('All Time')
        station_data = [entry for entry in data if entry['station_type'] + ' ' + entry['station_number'] == station]
        
        if not station_data:
            return {'No Data': 'No usage recorded for this station'}
            
        durations = [self._parse_duration(entry['duration']) for entry in station_data]
        
        return {
            'Total Sessions': len(station_data),
            'Total Time': str(sum(durations, timedelta())).split('.')[0],
            'Average Session': str(sum(durations, timedelta()) / len(durations)).split('.')[0],
            'Longest Session': str(max(durations)).split('.')[0],
            'Shortest Session': str(min(durations)).split('.')[0],
            'Last Used': station_data[-1]['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        }

    def get_game_rankings(self, period='Today'):
        data = self.parse_log_file(period)
        games = defaultdict(lambda: {'sessions': 0, 'total_time': timedelta(0)})
        
        for entry in data:
            if 'game' in entry and entry['game'] and entry['game'] != 'N/A':
                game = entry['game']
                duration = self._parse_duration(entry['duration'])
                games[game]['sessions'] += 1
                games[game]['total_time'] += duration
        
        # Convert timedelta to string and sort by sessions
        for game_stats in games.values():
            game_stats['total_time'] = str(game_stats['total_time']).split('.')[0]
            
        return dict(sorted(games.items(), key=lambda x: x[1]['sessions'], reverse=True))

    def get_all_stations(self):
        data = self.parse_log_file('All Time')
        stations = set()
        for entry in data:
            station = f"{entry['station_type']} {entry['station_number']}"
            stations.add(station)
        return list(stations)

    def export_daily_stats(self):
        today = datetime.now().date()
        base_filename = f"gaming_center_stats_{today.strftime('%Y-%m-%d')}"
        
        # Get statistics for today
        daily_stats = self.get_summary_stats('Today')
        game_rankings = self.get_game_rankings('Today')
        
        # Export summary statistics
        summary_file = os.path.join(self.export_dir, f"{base_filename}_summary.csv")
        with open(summary_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total Time', daily_stats['total_time']])
            writer.writerow(['Total Sessions', daily_stats['total_sessions']])
            writer.writerow(['Average Session Time', daily_stats['avg_session']])
        
        # Export station usage statistics
        station_file = os.path.join(self.export_dir, f"{base_filename}_station_usage.csv")
        with open(station_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Station Type', 'Sessions', 'Total Time', 'Average Time'])
            for station_type, stats in daily_stats['station_types'].items():
                writer.writerow([
                    station_type,
                    stats['sessions'],
                    stats['total_time'],
                    stats['avg_time']
                ])
        
        # Export game rankings
        rankings_file = os.path.join(self.export_dir, f"{base_filename}_game_rankings.csv")
        with open(rankings_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Game', 'Sessions', 'Total Time'])
            for game, stats in game_rankings.items():
                writer.writerow([
                    game,
                    stats['sessions'],
                    stats['total_time']
                ])

class GamingCenter:
    def __init__(self, root):
        self.root = root
        self.root.title("UVU Gaming Center")
        self.setup_menu()
        self.setup_ui()

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Add Reports menu
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Reports", menu=reports_menu)
        reports_menu.add_command(label="View Statistics", command=self.show_stats_window)

    def show_stats_window(self):
        stats_window = StatsWindow(self.root)
        stats_window.grab_set()  # Make the window modal
    
    def setup_ui(self):
        # Placeholder for any main window UI setup
        pass


    # Rest of the existing GamingCenter class implementation remains the same

    if __name__ == "__main__":
        root = tk.Tk()
        root.mainloop()