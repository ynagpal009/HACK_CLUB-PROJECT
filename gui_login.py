'''
gui_login.py
Gui for the login page the user sees when opening the application. This is the first thing they see, 
and it will handle the login process and redirect to the main application if successful.
'''
import tkinter as tk
from tkinter import ttk
from models import User 

Dark_Blue = "#1F4E79"
Accent_Blue = "#2E75B6"
Light_Blue = "#EBF3FB"
Card_Grey = "#F8F9FA"
Error_background = "#FDECEA"
Error_text = "#C0392B"
White = "#FFFFFF"

# Custom Mac-Safe Button
class FlatButton(tk.Frame):
    def __init__(self, parent, text, bg_color, fg_color, command, width=None):
        super().__init__(parent, bg=bg_color, cursor="hand2")
        self.command = command
        self.lbl = tk.Label(self, text=text, bg=bg_color, fg=fg_color, font=("Calibri", 12, "bold"))
        if width:
            self.lbl.config(width=width)
        self.lbl.pack(padx=10, pady=8)
        self.bind("<Button-1>", self.on_click)
        self.lbl.bind("<Button-1>", self.on_click)

    def on_click(self, event): 
        self.command()

class LoginWindow:
    def __init__(self, root_window, success_function):
        self.window = root_window
        self.success_function = success_function
        self.window.title("HPE Inventory Management System")
        self.window.geometry("500x500") # Scaled up so nothing chops off
        self.window.configure(bg=White)
        self.build_ui()

    def build_ui(self):
        header_frame = tk.Frame(self.window, bg=Dark_Blue, pady=25)
        header_frame.pack(fill="x")
        tk.Label(header_frame, text="Random School", bg=Dark_Blue, fg=White, font=("Calibri", 16, "bold")).pack()
        tk.Label(header_frame, text="HPE Equipment Inventory", bg=Dark_Blue, fg=Light_Blue, font=("Calibri", 16, "bold")).pack()

        # The Card Container
        card = tk.Frame(self.window, bg=Card_Grey, padx=40, pady=30, bd=1, relief="solid")
        card.pack(expand=True, pady=20)

        tk.Label(card, text="Sign In", bg=Card_Grey, fg=Dark_Blue, font=("Calibri", 18, "bold")).pack(anchor="center", pady=(0, 15))

        tk.Label(card, text="Username", bg=Card_Grey, font=("Calibri", 11, "bold")).pack(anchor="w")
        self.username_input = tk.StringVar()
        ttk.Entry(card, textvariable=self.username_input, font=("Calibri", 12), width=35).pack(anchor="w")

        tk.Label(card, text="Password", bg=Card_Grey, font=("Calibri", 11, "bold")).pack(anchor="w")
        self.password_input = tk.StringVar()        
        ttk.Entry(card, textvariable=self.password_input, show="*", font =("Calibri", 12), width=35).pack(pady=(0, 15))

        self.error_var = tk.StringVar()
        self.error_lbl = tk.Label(card, textvariable=self.error_var, bg=Error_background, fg=Error_text, font=("Calibri", 10, "bold"), padx=10, pady=5)

        FlatButton(card, "Sign In", Accent_Blue, White, self.attempt_login).pack(fill="x", pady=(15,0))

        self.window.bind("<Return>", self.handle_enter)

    def handle_enter(self, event):
        self.attempt_login()

    def attempt_login(self):
        uname = self.username_input.get()
        pwd = self.password_input.get()
        if not uname or not pwd:
            self.error_var.set("Please enter username and password.")
            self.error_lbl.pack(fill="x")
            return

        user = User().authenticate(uname, pwd)
        if user:
            self.error_lbl.pack_forget()
            self.success_function(user)
        else:
            self.error_var.set("x Incorrect usrname or password.")
            self.error_lbl.pack(fill="x")
            self.password_input.set("")
