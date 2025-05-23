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

    # def show_stats_window(self):
    #     stats_window = StatsWindow(self.root)
    #     stats_window.grab_set()  # Make the window modal
    
    def setup_ui(self):
        # Placeholder for any main window UI setup
        pass


    # Rest of the existing GamingCenter class implementation remains the same

    if __name__ == "__main__":
        root = tk.Tk()
        root.mainloop()