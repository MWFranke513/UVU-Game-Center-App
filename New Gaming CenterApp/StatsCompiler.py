import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime, timedelta
from collections import defaultdict
import textwrap
import os
import math
import csv

class StatsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Gaming Center Statistics")
        self.geometry("1000x800")  # Increase window size
        self.stats_manager = StatsManager()
        
        # Add debug button for diagnostics
        debug_button = ttk.Button(self, text="Diagnose Log Parsing", command=self.run_diagnostics)
        debug_button.pack(side='bottom', pady=5)
        
        self.setup_ui()
        self.update_stats()

    def run_diagnostics(self):
        # Run and display diagnostics
        diagnostics = self.stats_manager.diagnose_log_parsing()
        messagebox.showinfo("Log Parsing Diagnostics", diagnostics)

    def setup_ui(self):
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)

        # Create tabs
        summary_tab = ttk.Frame(self.notebook)
        station_tab = ttk.Frame(self.notebook)
        games_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(summary_tab, text='Summary Statistics')
        self.notebook.add(station_tab, text='Station Details')
        self.notebook.add(games_tab, text='Game Rankings')

        # Setup each tab
        self.setup_summary_tab(summary_tab)
        self.setup_station_tab(station_tab)
        self.setup_games_tab(games_tab)

        # Export button at the bottom
        export_frame = ttk.Frame(self)
        export_frame.pack(fill='x', padx=10, pady=5)
        ttk.Button(export_frame, text="Export to Excel", command=self.export_to_excel).pack(side='right')

    def setup_summary_tab(self, parent):
        # Time period selector
        period_frame = ttk.Frame(parent)
        period_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(period_frame, text="Time Period:").pack(side='left')
        period_choices = ['Today', 'Last 7 Days', 'Last 30 Days', 'All Time']
        self.period_var = tk.StringVar(value='Today')
        period_dropdown = ttk.Combobox(period_frame, textvariable=self.period_var, values=period_choices, state='readonly')
        period_dropdown.pack(side='left', padx=5)
        period_dropdown.bind('<<ComboboxSelected>>', self.update_stats)
        
        # Create frames for different stat sections
        total_usage_frame = ttk.LabelFrame(parent, text="Total Usage Statistics")
        total_usage_frame.pack(fill='x', padx=10, pady=5)
        
        # Total usage stats
        self.total_time_label = ttk.Label(total_usage_frame, text="")
        self.total_time_label.pack(anchor='w', padx=5, pady=2)
        self.total_sessions_label = ttk.Label(total_usage_frame, text="")
        self.total_sessions_label.pack(anchor='w', padx=5, pady=2)
        self.avg_session_label = ttk.Label(total_usage_frame, text="")
        self.avg_session_label.pack(anchor='w', padx=5, pady=2)
        
        # Station type breakdown
        type_frame = ttk.LabelFrame(parent, text="Usage by Station Type")
        type_frame.pack(fill='x', padx=10, pady=5)
        self.type_tree = ttk.Treeview(type_frame, columns=('Station Type', 'Sessions', 'Total Time', 'Avg Time'), show='headings', height=5)
        self.type_tree.heading('Station Type', text='Station Type')
        self.type_tree.heading('Sessions', text='Sessions')
        self.type_tree.heading('Total Time', text='Total Time')
        self.type_tree.heading('Avg Time', text='Avg Time')
        self.type_tree.pack(fill='x', padx=5, pady=5)

        # Graph for total usage
        self.total_usage_graph = tk.Canvas(total_usage_frame, width=400, height=300)
        self.total_usage_graph.pack(side='right', padx=5, pady=5)

    def setup_station_tab(self, parent):
        # Station selector
        select_frame = ttk.Frame(parent)
        select_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(select_frame, text="Select Station:").pack(side='left')
        self.station_var = tk.StringVar()
        self.station_dropdown = ttk.Combobox(select_frame, textvariable=self.station_var, state='readonly')
        self.station_dropdown.pack(side='left', padx=5)
        self.station_dropdown.bind('<<ComboboxSelected>>', self.update_station_stats)

        # Populate station dropdown with available stations
        stations = self.stats_manager.get_all_stations()
        self.station_dropdown['values'] = stations

        # Station statistics display
        stats_frame = ttk.LabelFrame(parent, text="Station Statistics")
        stats_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.station_tree = ttk.Treeview(stats_frame, columns=('Metric', 'Value'), show='headings', height=10)
        self.station_tree.heading('Metric', text='Metric')
        self.station_tree.heading('Value', text='Value')
        self.station_tree.pack(fill='both', expand=True, padx=5, pady=5)

        # Graph for station type breakdown
        self.station_type_graph = tk.Canvas(stats_frame, width=400, height=300)
        self.station_type_graph.pack(side='right', padx=5, pady=5)

    def setup_games_tab(self, parent):
        # Game rankings tree
        self.games_tree = ttk.Treeview(parent, columns=('Rank', 'Game', 'Sessions', 'Total Time'), show='headings', height=15)
        self.games_tree.heading('Rank', text='Rank')
        self.games_tree.heading('Game', text='Game')
        self.games_tree.heading('Sessions', text='Sessions')
        self.games_tree.heading('Total Time', text='Total Time')
        self.games_tree.pack(fill='both', expand=True, padx=10, pady=5)

        # Graph for game rankings
        self.game_rankings_graph = tk.Canvas(parent, width=9000, height=300)
        self.game_rankings_graph.pack(side='right', padx=5, pady=5)

    def update_stats(self, event=None):
        period = self.period_var.get()
        stats = self.stats_manager.get_summary_stats(period)
        
        # Update summary labels
        self.total_time_label.config(text=f"Total Time: {stats['total_time']}")
        self.total_sessions_label.config(text=f"Total Sessions: {stats['total_sessions']}")
        self.avg_session_label.config(text=f"Average Session: {stats['avg_session']}")

        # Update station type tree
        self.type_tree.delete(*self.type_tree.get_children())
        for station_type, type_stats in stats['station_types'].items():
            self.type_tree.insert('', 'end', values=(
                station_type,
                type_stats['sessions'],
                type_stats['total_time'],
                type_stats['avg_time']
            ))

        # Update game rankings
        self.update_game_rankings()

        # Update graphs
        self.update_summary_graph(stats)
        self.update_station_type_graph(stats['station_types'])

    def update_station_stats(self, event=None):
        station = self.station_var.get()
        stats = self.stats_manager.get_station_stats(station)
        
        self.station_tree.delete(*self.station_tree.get_children())
        for metric, value in stats.items():
            self.station_tree.insert('', 'end', values=(metric, value))

    def update_game_rankings(self):
        rankings = self.stats_manager.get_game_rankings(self.period_var.get())
        
        self.games_tree.delete(*self.games_tree.get_children())
        for rank, (game, stats) in enumerate(rankings.items(), 1):
            self.games_tree.insert('', 'end', values=(
                rank,
                game,
                stats['sessions'],
                stats['total_time']
            ))

        # Update game rankings graph
        self.update_game_rankings_graph(rankings)

    def update_summary_graph(self, stats):
        self.total_usage_graph.delete("all")
        total_time = stats['total_time']
        total_sessions = stats['total_sessions']
        avg_session = stats['avg_session']

        # Draw bar graph for total usage
        bar_width = 100
        bar_spacing = 20
        x_start = 20
        y_start = 250
        max_height = 200

        self.total_usage_graph.create_rectangle(x_start, y_start, x_start + bar_width, y_start - int(total_time.split(':')[0]) * 2, fill="blue")
        self.total_usage_graph.create_text(x_start + bar_width / 2, y_start + 20, text=f"Total Time: {total_time}", anchor="center")

        x_start += bar_width + bar_spacing
        self.total_usage_graph.create_rectangle(x_start, y_start, x_start + bar_width, y_start - total_sessions * 2, fill="green")
        self.total_usage_graph.create_text(x_start + bar_width / 2, y_start + 20, text=f"Total Sessions: {total_sessions}", anchor="center")

        x_start += bar_width + bar_spacing
        self.total_usage_graph.create_rectangle(x_start, y_start, x_start + bar_width, y_start - int(avg_session.split(':')[0]) * 2, fill="red")
        self.total_usage_graph.create_text(x_start + bar_width / 2, y_start + 20, text=f"Avg Session: {avg_session}", anchor="center")



    def update_station_type_graph(self, station_types):
        self.station_type_graph.delete("all")
        
        # Calculate total sessions and ensure it's not zero
        total_sessions = sum(type_stats['sessions'] for type_stats in station_types.values())
        if total_sessions == 0:
            print("Error: Total sessions is 0, cannot generate pie chart.")
            return  # Exit early if there are no sessions to display

        start_angle = 0
        radius = 150
        center_x, center_y = 200, 150

        # Debugging: Check if station types are being processed
        print(f"Station types: {station_types}")
        
        for station_type, type_stats in station_types.items():
            sessions = type_stats['sessions']
            angle = 360 * (sessions / total_sessions)

            # Debugging: Output the calculated angles
            print(f"Station Type: {station_type}, Sessions: {sessions}, Angle: {angle}")

            # Create the pie chart section (arc)
            self.station_type_graph.create_arc(center_x - radius, center_y - radius, center_x + radius, center_y + radius,
                                            start=start_angle, extent=angle, fill=self.get_station_color(station_type))
            
            mid_angle = start_angle + angle / 2
            text_x = center_x + radius * 0.7 * math.cos(math.radians(mid_angle))
            text_y = center_y + radius * 0.7 * math.sin(math.radians(mid_angle))

            # Create the text on the pie chart (adjust placement as needed)
            self.station_type_graph.create_text(text_x, text_y, text=f"{station_type}: {sessions}", anchor="center")
            
            # Update the start_angle for the next section
            start_angle += angle

        # Debugging: Confirm the pie chart is being created
        print("Pie chart created successfully.")


    def update_game_rankings_graph(self, rankings):
        self.game_rankings_graph.delete("all")
        max_sessions = max(stats['sessions'] for stats in rankings.values())

        bar_width = 50
        bar_spacing = 50
        x_start = -100
        y_start = 250
        max_height = 200
        text_padding = 10

        for rank, (game, stats) in enumerate(rankings.items(), 1):
            sessions = stats['sessions']
            height = (sessions / max_sessions) * max_height

            # Draw bars
            self.game_rankings_graph.create_rectangle(x_start + rank * (bar_width + bar_spacing), y_start,
                                                    x_start + rank * (bar_width + bar_spacing) + bar_width,
                                                    y_start - height, fill="blue")

            # Wrapping the game name to ensure readability
            wrapped_text = textwrap.fill(game, width=12)  # Adjust width for wrapping
            self.game_rankings_graph.create_text(x_start + rank * (bar_width + bar_spacing) + bar_width / 2,
                                                y_start + text_padding + 20, text=wrapped_text, anchor="center")

    def export_to_excel(self):
        self.stats_manager.export_daily_stats()

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
                    
                    try:
                        if line.startswith('Date:'):
                            entry['timestamp'] = datetime.strptime(line[6:], '%Y-%m-%d %H:%M:%S.%f')
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
                            # Ensure all required keys are present before adding
                            if all(key in entry for key in ['timestamp', 'station_type', 'station_number', 'duration']):
                                if self._is_within_period(entry.get('timestamp', ''), period):
                                    data.append(entry.copy())
                            entry = {}
                    except Exception as parse_error:
                        print(f"Error parsing line: {line}")
                        print(f"Error details: {parse_error}")
                        entry = {}
        except FileNotFoundError:
            print(f"Error: Log file {self.log_file} not found!")
            return []
        except Exception as e:
            print(f"Unexpected error reading log file: {e}")
            return []
        
        print(f"Parsed {len(data)} entries")
        return data

    def _is_within_period(self, timestamp, period):
        if not timestamp:
            return False
            
        date = timestamp.date()
        today = datetime.now().date()
        
        if period == 'Today':
            return date == today
        elif period == 'Last 7 Days':
            return (today - date).days <= 7
        elif period == 'Last 30 Days':
            return (today - date).days <= 30
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
            if 'game' in entry and entry['game']:
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