import json
from pathlib import Path
from PyQt6 import QtWidgets


class EventsBackend:
    """Backend class to handle JSON data and table population."""
    
    def __init__(self, json_path="Amr_Work/data/events.json"):
        self.json_path = Path(json_path)
        self.all_events_data = {}
        self.load_json_data()
    
    def load_json_data(self):
        """Load all events data from JSON file."""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                # Convert to dictionary for faster lookup by date
                self.all_events_data = {
                    event["date"]: event["events"]
                    for event in data.get("events", [])
                }
        except FileNotFoundError:
            print(f"Warning: {self.json_path} not found. Creating empty data structure.")
            self.all_events_data = {}
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {self.json_path}")
            self.all_events_data = {}
    
    def get_events_for_date(self, date_str: str):
        """Get events list for a specific date string (YYYY-MM-DD)."""
        return self.all_events_data.get(date_str, [])
    
    def populate_table(self, table_widget: QtWidgets.QTableWidget, date_str: str) -> int:
        """Populate the table widget with events for the given date."""
        events = self.get_events_for_date(date_str)
        
        table_widget.setRowCount(0)
        
        for row, event in enumerate(events):
            table_widget.insertRow(row)
            table_widget.setItem(row, 0, QtWidgets.QTableWidgetItem(event.get("event", "")))
            table_widget.setItem(row, 1, QtWidgets.QTableWidgetItem(event.get("duration", "")))
            table_widget.setItem(row, 2, QtWidgets.QTableWidgetItem(event.get("class", "")))
        
        table_widget.resizeRowsToContents()
        return len(events)
    
    def add_event(self, date_str: str, event_name: str, duration: str, class_name: str):
        """Add a new event to the given date."""
        if date_str not in self.all_events_data:
            self.all_events_data[date_str] = []
        
        new_event = {
            "event": event_name,
            "duration": duration,
            "class": class_name
        }
        self.all_events_data[date_str].append(new_event)
        self.save_json_data()
    
    def delete_all_events_for_date(self, date_str: str):
        """Delete all events for a specific date."""
        if date_str in self.all_events_data:
            self.all_events_data[date_str] = []
            self.save_json_data()
    
    def save_json_data(self):
        """Save current events data back to JSON file."""
        data = {
            "events": [
                {"date": date, "events": events}
                for date, events in self.all_events_data.items()
            ]
        }
        
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.json_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
