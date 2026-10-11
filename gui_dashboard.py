import tkinter as tk

class Dashboard:
    def __init__(self, root_window, current_user, logout_function):
        self.window = root_window
        self.user = current_user
        self.logout_fn = logout_function

        self.window.title("Dashboard - MVP")
        self.window.geometry("600x400")

        # Simple placeholder label
        tk.Label(self.window, text=f"Welcome, {self.user.full_name}!", font=("Calibri", 16)).pack(pady=50)
        tk.Button(self.window, text="Log Out", command=self.logout_fn).pack()
         



