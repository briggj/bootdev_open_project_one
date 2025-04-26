# goals_app.py
# (Includes sorting, auto-clear status, AND user-selectable font size)

import customtkinter as ctk
import json
import os
from datetime import date, datetime
import random

# --- Constants ---
MAX_GOALS = 10
DATA_FILE = "goals_data.json"
SETTINGS_FILE = "settings.json" # New file for settings
ENCOURAGING_WORDS = [
    "You've got this!", "Keep going strong!", "Amazing progress!",
    "One day at a time!", "You're doing great!", "Stay focused!",
    "Incredible work!", "Persistence pays off!", "Keep pushing forward!",
    "Celebrate this milestone!", "Look how far you've come!",
    "Keep up the momentum!",
]
STATUS_CLEAR_DELAY_MS = 5000 # milliseconds (5 seconds)
DEFAULT_FONT_SIZE = 16 # Default if no setting is found
MIN_FONT_SIZE = 12
MAX_FONT_SIZE = 24
FONT_SIZE_INCREMENT = 2
AVAILABLE_FONT_SIZES = [str(s) for s in range(MIN_FONT_SIZE, MAX_FONT_SIZE + 1, FONT_SIZE_INCREMENT)]

# --- Helper Functions ---
# (calculate_time_elapsed and get_random_encouragement remain the same)
def calculate_time_elapsed(start_date_str):
    """Calculates time elapsed since the start_date_str (YYYY-MM-DD)."""
    try:
        start_date = date.fromisoformat(start_date_str)
        today = date.today()
        delta = today - start_date

        if delta.days < 0:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            return f"Date {start_date_str} is in the future (current time: {now_str}).", None

        years = delta.days // 365
        remaining_days = delta.days % 365
        days = remaining_days

        parts = []
        if years > 0:
            parts.append(f"{years} year{'s' if years > 1 else ''}")
        if days > 0 or delta.days == 0:
             parts.append(f"{days} day{'s' if days != 1 else ''}")

        if delta.days == 0:
             return "Today is the day!", delta.days
        elif not parts:
             # Fallback if calculation somehow yields no parts for positive days
             return f"{delta.days} day{'s' if delta.days != 1 else ''} ago", delta.days
        else:
             time_str = ', '.join(parts)
             return f"{time_str} ago", delta.days

    except ValueError:
        return "Invalid Date Format (Use YYYY-MM-DD)", None
    except Exception as e:
        print(f"Error calculating time: {e}")
        return "Error calculating time", None

def get_random_encouragement():
    """Returns a random encouraging phrase."""
    return random.choice(ENCOURAGING_WORDS)


# --- Main Application Class ---
class GoalsApp(ctk.CTk):
    """
    A GUI application to track goals/habits quit dates,
    display elapsed time, provide encouragement, and allow font size selection.
    """
    def __init__(self):
        super().__init__()

        self.title("Goals! - Keep Track & Stay Motivated")
        # Increased default size slightly more for UI elements
        self.geometry("750x650")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.goals = []
        self.status_clear_job = None
        self.current_font_size = DEFAULT_FONT_SIZE # Set default first

        # --- Font Tuples (will be updated based on current_font_size) ---
        self.REGULAR_FONT = None
        self.INPUT_FONT = None
        self.BUTTON_FONT = None
        self.INFO_DISPLAY_FONT = None
        self.STATUS_FONT = None
        self.FRAME_LABEL_FONT = None
        # --- Load Settings and Initial Font Update ---
        self.load_settings() # Load saved font size, overrides default if successful
        self._update_font_tuples(self.current_font_size) # Create initial font tuples

        # --- Load Goals ---
        self.load_goals() # Load goal data

        # --- Main Layout ---
        self.grid_columnconfigure(0, weight=1)
        # Adjust row configuration for the new settings frame
        self.grid_rowconfigure(0, weight=0) # Input frame
        self.grid_rowconfigure(1, weight=0) # Settings frame
        self.grid_rowconfigure(2, weight=1) # Display frame (should expand)
        self.grid_rowconfigure(3, weight=0) # Status label

        # --- Input Frame ---
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)

        self.label_goal = ctk.CTkLabel(self.input_frame, text="Goal/Habit:", font=self.REGULAR_FONT)
        self.label_goal.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")
        self.entry_goal = ctk.CTkEntry(self.input_frame, placeholder_text="e.g., Quit Caffeine", font=self.INPUT_FONT)
        self.entry_goal.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        self.entry_goal.bind("<Return>", lambda event: self.entry_date.focus_set())

        self.label_date = ctk.CTkLabel(self.input_frame, text="Start/Quit Date:", font=self.REGULAR_FONT)
        self.label_date.grid(row=1, column=0, padx=(10, 5), pady=10, sticky="w")
        self.entry_date = ctk.CTkEntry(self.input_frame, placeholder_text="YYYY-MM-DD", font=self.INPUT_FONT)
        self.entry_date.grid(row=1, column=1, padx=5, pady=10, sticky="ew")
        self.entry_date.bind("<Return>", self.add_goal_event)

        self.add_button = ctk.CTkButton(self.input_frame, text="Add Goal", command=self.add_goal, font=self.BUTTON_FONT)
        self.add_button.grid(row=0, column=2, rowspan=2, padx=(5, 10), pady=10, sticky="ns")

        # --- Settings Frame ---
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.settings_frame.grid_columnconfigure(1, weight=1) # Allow combobox to potentially expand if needed

        self.label_font_size = ctk.CTkLabel(self.settings_frame, text="Font Size:", font=self.REGULAR_FONT)
        self.label_font_size.grid(row=0, column=0, padx=(10, 5), pady=5, sticky="w")

        self.font_size_combobox = ctk.CTkComboBox(
            self.settings_frame,
            values=AVAILABLE_FONT_SIZES,
            command=self.font_size_changed,
            font=self.INPUT_FONT,
            state="readonly" # Prevent typing arbitrary values
        )
        self.font_size_combobox.set(str(self.current_font_size)) # Set initial value
        self.font_size_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="w") # Use sticky "w"

        # --- Goals Display Frame ---
        self.display_frame_container = ctk.CTkFrame(self)
        # Note: Grid row is now 2
        self.display_frame_container.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="nsew")
        self.display_frame_container.grid_rowconfigure(0, weight=1)
        self.display_frame_container.grid_columnconfigure(0, weight=1)

        self.display_frame = ctk.CTkScrollableFrame(
            self.display_frame_container,
            label_text="Your Goals (Sorted by Date)",
            label_font=self.FRAME_LABEL_FONT # Use specific font for the frame label
        )
        self.display_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.display_frame.grid_columnconfigure(0, weight=1)

        # --- Status Label ---
        self.status_label = ctk.CTkLabel(self, text="", text_color="gray", font=self.STATUS_FONT)
        # Note: Grid row is now 3
        self.status_label.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")

        # --- Initial Goal Display ---
        self.update_display() # Draw goals with the loaded font size

    # --- Font and Settings Handling ---

    def _update_font_tuples(self, base_size):
        """Updates the font tuples based on the base size."""
        # Adjust relative sizes as needed
        info_size = base_size + 2
        status_size = base_size - 2 if base_size > MIN_FONT_SIZE else MIN_FONT_SIZE # Prevent status getting too small
        frame_label_size = base_size

        self.REGULAR_FONT = ("", base_size)
        self.INPUT_FONT = ("", base_size)
        self.BUTTON_FONT = ("", base_size)
        self.INFO_DISPLAY_FONT = ("", info_size)
        self.STATUS_FONT = ("", status_size)
        self.FRAME_LABEL_FONT = ("", frame_label_size, "bold")
        # print(f"Updated fonts: Base={base_size}, Info={info_size}, Status={status_size}") # Debug print

    def load_settings(self):
        """Loads settings like font size from the JSON settings file."""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    settings_data = json.load(f)
                    loaded_size = settings_data.get("font_size", DEFAULT_FONT_SIZE)
                    # Validate loaded size
                    if MIN_FONT_SIZE <= loaded_size <= MAX_FONT_SIZE:
                         self.current_font_size = loaded_size
                         print(f"Loaded font size: {self.current_font_size}") # Debug
                    else:
                         print(f"Warning: Loaded font size {loaded_size} out of range. Using default.")
                         self.current_font_size = DEFAULT_FONT_SIZE
                         self.save_settings() # Save the default back
            else:
                 # Settings file doesn't exist, use default and save it
                 print("Settings file not found. Using default font size and creating file.")
                 self.current_font_size = DEFAULT_FONT_SIZE
                 self.save_settings()

        except (json.JSONDecodeError, TypeError, ValueError) as e:
             print(f"Error loading settings from {SETTINGS_FILE}: {e}. Using default.")
             self.current_font_size = DEFAULT_FONT_SIZE
             # Optionally delete the corrupt file or just overwrite it
             self.save_settings()
        except Exception as e:
             print(f"An unexpected error occurred loading settings: {e}. Using default.")
             self.current_font_size = DEFAULT_FONT_SIZE


    def save_settings(self):
        """Saves the current settings (font size) to the JSON file."""
        settings_data = {
            "font_size": self.current_font_size
        }
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings_data, f, indent=4)
            # print(f"Saved font size: {self.current_font_size}") # Debug print
        except Exception as e:
            print(f"Error saving settings to {SETTINGS_FILE}: {e}")
            self.update_status(f"Error saving settings: {e}", "red")

    def font_size_changed(self, selected_size_str):
        """Callback when font size is selected in the ComboBox."""
        try:
            new_size = int(selected_size_str)
            if MIN_FONT_SIZE <= new_size <= MAX_FONT_SIZE:
                if new_size != self.current_font_size:
                    print(f"Changing font size to: {new_size}") # Debug
                    self.current_font_size = new_size
                    self._update_font_tuples(self.current_font_size)
                    self._apply_global_font_settings() # Apply changes to UI
                    self.save_settings() # Save the new setting
            else:
                 print(f"Selected font size {new_size} out of range. Reverting.")
                 # Revert combobox display to the current valid size
                 self.font_size_combobox.set(str(self.current_font_size))

        except ValueError:
             print(f"Invalid font size value selected: {selected_size_str}")
             # Revert combobox display
             self.font_size_combobox.set(str(self.current_font_size))

    def _apply_global_font_settings(self):
        """Applies the current font settings to all relevant static widgets and redraws dynamic ones."""
        # Configure static widgets
        self.label_goal.configure(font=self.REGULAR_FONT)
        self.entry_goal.configure(font=self.INPUT_FONT)
        self.label_date.configure(font=self.REGULAR_FONT)
        self.entry_date.configure(font=self.INPUT_FONT)
        self.add_button.configure(font=self.BUTTON_FONT)
        self.label_font_size.configure(font=self.REGULAR_FONT)
        self.font_size_combobox.configure(font=self.INPUT_FONT)
        self.status_label.configure(font=self.STATUS_FONT)
        # Configure the scrollable frame's label
        self.display_frame.configure(label_font=self.FRAME_LABEL_FONT)

        # Redraw the dynamic goal list using the new fonts
        self.update_display()

    # --- Goal Handling ---

    def load_goals(self):
        """Loads goals from the JSON data file."""
        # (Implementation remains the same as before)
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    self.goals = json.load(f)
            except json.JSONDecodeError:
                self.update_status(f"Warning: Could not read {DATA_FILE}. Starting fresh.", "orange")
                self.goals = []
            except Exception as e:
                self.update_status(f"Error loading goals: {e}", "red")
                self.goals = []
        else:
            self.goals = []

    def save_goals(self):
        """Saves the current goals list to the JSON data file."""
        # (Implementation remains the same as before)
        try:
            self.goals.sort(key=lambda x: x.get('date', '0000-00-00'))
            with open(DATA_FILE, 'w') as f:
                json.dump(self.goals, f, indent=4)
        except Exception as e:
            print(f"Error saving goals: {e}")
            self.update_status(f"Error saving goals: {e}", "red")

    def update_display(self):
        """Clears and redraws the goals in the display frame using current font settings."""
        # (Ensure widgets created here use the dynamic font tuples like self.INFO_DISPLAY_FONT)
        for widget in self.display_frame.winfo_children():
            widget.destroy()

        if not self.goals:
            no_goals_label = ctk.CTkLabel(
                self.display_frame,
                text="No goals added yet. Add one above!",
                font=self.INFO_DISPLAY_FONT # Use dynamic font
            )
            no_goals_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            return

        try:
            self.goals.sort(key=lambda x: date.fromisoformat(x.get('date', '9999-12-31')))
        except ValueError:
             self.update_status("Warning: Invalid date found in saved data during sorting.", "orange")
             self.goals.sort(key=lambda x: x.get('date', '9999-12-31'))

        for index, goal in enumerate(self.goals):
            goal_name = goal.get('name', 'Unnamed Goal')
            goal_date = goal.get('date', 'No Date')

            elapsed_str, _ = calculate_time_elapsed(goal_date)
            encouragement = get_random_encouragement()

            item_frame = ctk.CTkFrame(self.display_frame)
            item_frame.grid(row=index, column=0, padx=5, pady=(3, 4), sticky="ew")
            item_frame.grid_columnconfigure(0, weight=1)
            item_frame.grid_columnconfigure(1, weight=0)

            info_text = f"📌 {goal_name} (Since: {goal_date})\n   └── {elapsed_str} - {encouragement}"
            info_label = ctk.CTkLabel(
                item_frame,
                text=info_text,
                justify="left",
                anchor="w",
                font=self.INFO_DISPLAY_FONT # Use dynamic font
            )
            info_label.grid(row=0, column=0, padx=10, pady=(5,5), sticky="ew")

            delete_button = ctk.CTkButton(
                item_frame,
                text="Delete",
                command=lambda i=index: self.delete_goal(i),
                width=60,
                fg_color="#DB3E3E",
                hover_color="#A92F2F",
                font=self.BUTTON_FONT # Use dynamic font
            )
            delete_button.grid(row=0, column=1, padx=(5, 10), pady=5, sticky="e")

    def add_goal_event(self, event=None):
        # (Implementation remains the same)
        self.add_goal()

    def add_goal(self):
        # (Implementation remains the same)
        goal_name = self.entry_goal.get().strip()
        goal_date_str = self.entry_date.get().strip()

        if not goal_name:
            self.update_status("Goal name cannot be empty.", "orange")
            return
        if not goal_date_str:
            self.update_status("Date cannot be empty.", "orange")
            return

        try:
            valid_date = date.fromisoformat(goal_date_str)
        except ValueError:
            self.update_status("Invalid date format. Use YYYY-MM-DD.", "red")
            return

        for existing_goal in self.goals:
            if existing_goal.get('name', '').lower() == goal_name.lower():
                 self.update_status(f"Goal '{goal_name}' already exists.", "orange")
                 return

        if len(self.goals) >= MAX_GOALS:
            self.update_status(f"Cannot add more than {MAX_GOALS} goals.", "orange")
            return

        new_goal = {"name": goal_name, "date": goal_date_str}
        self.goals.append(new_goal)
        self.save_goals()
        self.update_display()

        self.entry_goal.delete(0, ctk.END)
        self.entry_date.delete(0, ctk.END)
        self.entry_goal.focus_set()
        self.update_status(f"Goal '{goal_name}' added successfully!", "green")


    def delete_goal(self, index):
        # (Implementation remains the same)
        if 0 <= index < len(self.goals):
            try:
                removed_goal = self.goals.pop(index)
                self.save_goals()
                self.update_display()
                self.update_status(f"Goal '{removed_goal.get('name', 'Unknown')}' deleted.", "#A9A9A9")
            except IndexError:
                 self.update_status("Error: Could not delete goal (index issue). Refreshing.", "red")
                 self.update_display()
            except Exception as e:
                 self.update_status(f"Error deleting goal: {e}", "red")
                 self.update_display()
        else:
            self.update_status("Error: Could not delete goal (invalid index).", "red")
            print(f"Error: Invalid index {index} for goals list of length {len(self.goals)}")


    def update_status(self, message, color="gray"):
        # (Implementation remains the same)
        self.status_label.configure(text=message, text_color=color) # Font is handled by apply_global_font_settings

        if self.status_clear_job:
            self.status_label.after_cancel(self.status_clear_job)

        if color != "red":
            self.status_clear_job = self.status_label.after(
                STATUS_CLEAR_DELAY_MS,
                lambda: self.status_label.configure(text="")
            )
        else:
             self.status_clear_job = None

# --- Run the App ---
if __name__ == "__main__":
    app = GoalsApp()
    app.mainloop()