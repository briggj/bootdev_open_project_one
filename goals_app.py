import customtkinter as ctk
import json
import os
from datetime import date, datetime
import random

# --- Constants ---
MAX_GOALS = 10
DATA_FILE = "goals_data.json"
ENCOURAGING_WORDS = [
    "You've got this!",
    "Keep going strong!",
    "Amazing progress!",
    "One day at a time!",
    "You're doing great!",
    "Stay focused!",
    "Incredible work!",
    "Persistence pays off!",
    "Keep pushing forward!",
    "Celebrate this milestone!",
]

# --- Helper Functions ---
def calculate_time_elapsed(start_date_str):
    """Calculates time elapsed since the start_date_str (YYYY-MM-DD)."""
    try:
        start_date = date.fromisoformat(start_date_str)
        today = date.today()
        delta = today - start_date

        if delta.days < 0:
            return "Date is in the future!", None # Handle future dates

        years = delta.days // 365
        remaining_days = delta.days % 365
        # Simple approximation for months - can be improved if needed
        # months = remaining_days // 30
        # days = remaining_days % 30
        # Using years and days is more precise without complex month calculation
        days = remaining_days

        parts = []
        if years > 0:
            parts.append(f"{years} year{'s' if years > 1 else ''}")
        # if months > 0:
        #     parts.append(f"{months} month{'s' if months > 1 else ''}")
        if days >= 0: # Always show days unless it's exactly 0 years/months
             parts.append(f"{days} day{'s' if days != 1 else ''}")

        if not parts:
             return "Today is the day!", delta.days
        else:
             return f"{', '.join(parts)} ago", delta.days

    except ValueError:
        return "Invalid Date Format", None
    except Exception as e:
        print(f"Error calculating time: {e}")
        return "Error", None

def get_random_encouragement():
    """Returns a random encouraging phrase."""
    return random.choice(ENCOURAGING_WORDS)

# --- Main Application Class ---
class GoalsApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Goals! - Keep Track & Stay Motivated")
        self.geometry("650x550") # Adjusted size
        ctk.set_appearance_mode("System") # Options: "System", "Dark", "Light"
        ctk.set_default_color_theme("blue") # Options: "blue", "green", "dark-blue"

        self.goals = []
        self.load_goals()

        # --- Main Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Input Frame ---
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)

        self.label_goal = ctk.CTkLabel(self.input_frame, text="Goal/Habit:")
        self.label_goal.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")
        self.entry_goal = ctk.CTkEntry(self.input_frame, placeholder_text="e.g., Quit Caffeine")
        self.entry_goal.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        self.label_date = ctk.CTkLabel(self.input_frame, text="Start/Quit Date:")
        self.label_date.grid(row=1, column=0, padx=(10, 5), pady=10, sticky="w")
        self.entry_date = ctk.CTkEntry(self.input_frame, placeholder_text="YYYY-MM-DD")
        self.entry_date.grid(row=1, column=1, padx=5, pady=10, sticky="ew")

        self.add_button = ctk.CTkButton(self.input_frame, text="Add Goal", command=self.add_goal)
        self.add_button.grid(row=0, column=2, rowspan=2, padx=(5, 10), pady=10, sticky="ns")

        # --- Goals Display Frame ---
        self.display_frame_container = ctk.CTkFrame(self)
        self.display_frame_container.grid(row=1, column=0, padx=20, pady=(10, 10), sticky="nsew")
        self.display_frame_container.grid_rowconfigure(0, weight=1)
        self.display_frame_container.grid_columnconfigure(0, weight=1)

        self.display_frame = ctk.CTkScrollableFrame(self.display_frame_container, label_text="Your Goals")
        self.display_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.display_frame.grid_columnconfigure(0, weight=1) # Make content expand


        # --- Status Label ---
        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.grid(row=2, column=0, padx=20, pady=(5, 10), sticky="ew")

        # --- Initial Display ---
        self.update_display()

    def load_goals(self):
        """Loads goals from the JSON data file."""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    self.goals = json.load(f)
            except json.JSONDecodeError:
                print(f"Error: Could not decode JSON from {DATA_FILE}.")
                self.goals = [] # Start fresh if file is corrupt
            except Exception as e:
                print(f"Error loading goals: {e}")
                self.goals = []
        else:
            self.goals = []

    def save_goals(self):
        """Saves the current goals list to the JSON data file."""
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(self.goals, f, indent=4)
        except Exception as e:
            print(f"Error saving goals: {e}")
            self.update_status(f"Error saving goals: {e}", "red")


    def update_display(self):
        """Clears and redraws the goals in the display frame."""
        # Clear existing widgets in the scrollable frame
        for widget in self.display_frame.winfo_children():
            widget.destroy()

        if not self.goals:
            no_goals_label = ctk.CTkLabel(self.display_frame, text="No goals added yet. Add one above!")
            no_goals_label.grid(row=0, column=0, padx=10, pady=10)
            return

        # Sort goals perhaps? Optional - by date or name
        # self.goals.sort(key=lambda x: x['date']) # Example sort by date

        for index, goal in enumerate(self.goals):
            goal_name = goal.get('name', 'Unnamed Goal')
            goal_date = goal.get('date', 'No Date')

            elapsed_str, _ = calculate_time_elapsed(goal_date)
            encouragement = get_random_encouragement()

            # Create a frame for each goal entry
            item_frame = ctk.CTkFrame(self.display_frame)
            item_frame.grid(row=index, column=0, padx=5, pady=5, sticky="ew")
            item_frame.grid_columnconfigure(0, weight=1) # Allow text to expand
            item_frame.grid_columnconfigure(1, weight=0) # Keep button fixed size

            info_text = f"{goal_name} (Since: {goal_date})\n{elapsed_str} - {encouragement}"
            info_label = ctk.CTkLabel(item_frame, text=info_text, justify="left", anchor="w")
            info_label.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

            # Pass index to delete function using lambda
            delete_button = ctk.CTkButton(
                item_frame,
                text="Delete",
                command=lambda i=index: self.delete_goal(i),
                width=60,
                fg_color="red", # Or use theme colors
                hover_color="darkred"
            )
            delete_button.grid(row=0, column=1, padx=10, pady=5)

    def add_goal(self):
        """Adds a new goal from the input fields."""
        goal_name = self.entry_goal.get().strip()
        goal_date_str = self.entry_date.get().strip()

        if not goal_name:
            self.update_status("Goal name cannot be empty.", "orange")
            return
        if not goal_date_str:
            self.update_status("Date cannot be empty.", "orange")
            return

        # Validate date format before adding
        try:
            date.fromisoformat(goal_date_str)
        except ValueError:
            self.update_status("Invalid date format. Use YYYY-MM-DD.", "red")
            return

        if len(self.goals) >= MAX_GOALS:
            self.update_status(f"Cannot add more than {MAX_GOALS} goals.", "orange")
            return

        # Add the new goal
        new_goal = {"name": goal_name, "date": goal_date_str}
        self.goals.append(new_goal)
        self.save_goals()
        self.update_display()

        # Clear input fields
        self.entry_goal.delete(0, ctk.END)
        self.entry_date.delete(0, ctk.END)
        self.update_status(f"Goal '{goal_name}' added successfully!", "green")


    def delete_goal(self, index):
        """Deletes a goal at the given index."""
        if 0 <= index < len(self.goals):
            removed_goal = self.goals.pop(index)
            self.save_goals()
            self.update_display()
            self.update_status(f"Goal '{removed_goal['name']}' deleted.", "gray")
        else:
            self.update_status("Error: Could not delete goal (invalid index).", "red")

    def update_status(self, message, color="gray"):
        """Updates the status label text and color."""
        self.status_label.configure(text=message, text_color=color)
        # Optional: Clear status after a few seconds
        # self.status_label.after(5000, lambda: self.status_label.configure(text=""))


# --- Run the App ---
if __name__ == "__main__":
    app = GoalsApp()
    app.mainloop()