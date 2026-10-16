"""
main.py
The main file to run the Sports Equipment Inventory Management System.
"""
import sys
import tkinter as tk
from tkinter import messagebox
from database import intialise_database
from gui_login import LoginWindow
from gui_dashboard import Dashboard


def main():
    try:
        intialise_database()
    except Exception as error:
        # if the database can't be set up there's no point continuing,
        # show a message instead of just crashing with a big red traceback
        print("Could not start the database:", error)
        messagebox.showerror("Startup Error", "Could not set up the database. Check the app has permission to write inventory.db")
        sys.exit(1)

    app_window = tk.Tk()

    def launch_dashboard(logged_in_user):
        for widget in app_window.winfo_children():
            widget.destroy()
        Dashboard(app_window, logged_in_user, logout_function=launch_login)

    def launch_login():
        for widget in app_window.winfo_children():
            widget.destroy()
        # Reset the native menu for safety
        app_window.config(menu=tk.Menu(app_window))
        LoginWindow(app_window, success_function=launch_dashboard)

    launch_login()
    app_window.mainloop()


if __name__ == "__main__":
    main()