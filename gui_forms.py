"""
gui_forms.py
All the popup windows that open on top of the Dashboard - adding/editing
equipment, borrowing, returning, managing accounts and the reports.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
from datetime import date, timedelta
from models import Equipment, BorrowRecord, User

Dark_Blue = "#1F4E79"
BG_Blue = "#EBF3FB"
White = "#FFFFFF"
Green = "#27AE60"
Red = "#E74C3C"
Grey = "#F2F2F2"


class Flatbutton(tk.Frame):
    # using a Label inside a Frame instead of a normal button becuase
    # ttk buttons wouldn't chnage colour on mac, they just stayed grey
    # no matter what bg colour i gave them
    def __init__(self, parent, text, bg_color, fg_color, command, width=12):
        super().__init__(parent, bg=bg_color, cursor="hand2")
        self.command = command
        self.lbl = tk.Label(self, text=text, bg=bg_color, fg=fg_color, font=("Calibri", 11, "bold"), width=width)
        self.lbl.pack(padx=5, pady=5)
        self.bind("<Button-1>", self.on_click)
        self.lbl.bind("<Button-1>", self.on_click)

    def on_click(self, event):
        self.command()


class EquipmentForm:
    def __init__(self, parent, refresh_fn, existing_item=None):
        self.refresh_fn = refresh_fn 
        if existing_item is not None:
            self.item = existing_item 
        else:
            self.item = Equipment()

        self.win = tk.Toplevel(parent)
        self.win.title("Equipment Form")
        self.win.geometry("600x550")
        self.win.configure(bg=BG_Blue)
        self.win.grab_set()

        if self.item.total_qty:
            qty_start_value = str(self.item.total_qty)
        else:
            qty_start_value = ""

        self.name_var = tk.StringVar(value=self.item.item_name)
        self.cat_var = tk.StringVar(value=self.item.category)
        self.cond_var = tk.StringVar(value=self.item.condition_status)
        self.qty_var = tk.StringVar(value=qty_start_value)
        self.thresh_var = tk.StringVar(value=str(self.item.low_stock_threshold))
        self.loc_var = tk.StringVar(value=self.item.location)
        self.notes_var = tk.StringVar(value=self.item.notes)
        self.error_var = tk.StringVar()

        if existing_item:
            title = "Edit Equipment Item"
        else:
            title = "Add New Equipment Item"
        tk.Label(self.win, text=title, bg=Dark_Blue, fg=White, font=("Calibri", 14, "bold"), anchor="w", padx=20, pady=10).pack(fill="x")

        card = tk.Frame(self.win, bg=White, padx=30, pady=20)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(card, text="Item Name *", bg=White, font=("Calibri", 10, "bold")).grid(row=0, column=0, sticky="w", pady=10)
        ttk.Entry(card, textvariable=self.name_var, width=45).grid(row=0, column=1, columnspan=3, sticky="w")

        tk.Label(card, text="Category *", bg=White, font=("Calibri", 10, "bold")).grid(row=1, column=0, sticky="w", pady=10)
        ttk.Combobox(card, textvariable=self.cat_var, values=["Athletics", "Balls", "Ball Sports", "Racquet Sports", "Bat Sports",
        "Gym"], state="readonly", width=15).grid(row=1, column=1, sticky="w")

        tk.Label(card, text="Condition *", bg=White, font=("Calibri", 10, "bold")).grid(row=1, column=2, sticky="w", padx=10)
        ttk.Combobox(card, textvariable=self.cond_var, values=["New", "Good", "Poor", "Damaged"], state="readonly", width=12).grid(row=1, column=3, sticky="w")

        tk.Label(card, text="Total Qty *", bg=White, font=("Calibri", 10, "bold")).grid(row=2, column=0, sticky="w", pady=10)
        ttk.Entry(card, textvariable=self.qty_var, width=17).grid(row=2, column=1, sticky="w")

        tk.Label(card, text="Low-Stock Alert *", bg=White, font=("Calibri", 10, "bold")).grid(row=2, column=2, sticky="w", padx=10)
        ttk.Entry(card, textvariable=self.thresh_var, width=14).grid(row=2, column=3, sticky="w")

        tk.Label(card, text="Storage Location *", bg=White, font=("Calibri", 10, "bold")).grid(row=3, column=0, sticky="w", pady=10)
        ttk.Entry(card, textvariable=self.loc_var, width=45).grid(row=3, column=1, columnspan=3, sticky="w", pady=10)

        tk.Label(card, text="Notes", bg=White, font=("Calibri", 10, "bold")).grid(row=4, column=0, sticky="w", pady=10)
        ttk.Entry(card, textvariable=self.notes_var, width=45).grid(row=4, column=1, columnspan=3, sticky="w")

        if self.item.item_id:
            id_text = f"Auto-generated Item ID: {self.item.item_id} (read-only)"
        else:
            id_text = "Auto-generated Item ID: assigned on save"
        tk.Label(card, text=id_text, bg=BG_Blue, fg=Dark_Blue, font=("Calibri", 10)).grid(row=5, column=0, columnspan=4, pady=15, sticky="ew", ipady=5)

        tk.Label(card, textvariable=self.error_var, fg=Red, bg=White, font=("Calibri", 10, "bold")).grid(row=6, column=0, columnspan=4)

        btn_box = tk.Frame(card, bg=White)
        btn_box.grid(row=7, column=0, columnspan=4, pady=10)
        Flatbutton(btn_box, "Save Item", Green, White, self.save).pack(side="left", padx=5)
        Flatbutton(btn_box, "Clear Form", Red, White, self.clear).pack(side="left", padx=5)
        Flatbutton(btn_box, "Cancel", Grey, "#000000", self.win.destroy).pack(side="left", padx=5)

    def clear(self):
        self.name_var.set("")
        self.cat_var.set("")
        self.cond_var.set("")
        self.qty_var.set("")
        self.loc_var.set("")
        self.notes_var.set("")
        self.error_var.set("")

    def save(self):
        self.item.item_name = self.name_var.get()
        self.item.category = self.cat_var.get()
        self.item.condition_status = self.cond_var.get()
        self.item.location = self.loc_var.get()
        self.item.total_qty = self.qty_var.get()
        self.item.low_stock_threshod = self.thresh_var.get()
        self.item.notes = self.notes_var.get()

        ok, msg = self.item.save()
        if ok:
            self.win.destroy()
            self.refresh_fn()
        else:
            self.error_var.set(msg)


class BorrowForm:
    def __init__(self, parent, item, refresh_fn, user_name):
        self.item = item
        self.refresh_fn = refresh_fn
        self.user_name = user_name
        self.win = tk.Toplevel(parent)
        self.win.geometry("500x460")
        self.win.configure(bg=BG_Blue)
        tk.Label(self.win, text=f"Borrowing: {item.item_name}", bg=Dark_Blue, fg=White,font=("Calibri", 14, "bold"), anchor="w", padx=20, pady=10).pack(fill="x")

        form_box = tk.Frame(self.win, bg=White, padx=30, pady=20)
        form_box.pack(fill="both", expand=True, padx=20, pady=20)

        self.name_var = tk.StringVar()
        self.qty_var = tk.StringVar(value="1")
        self.days_var = tk.StringVar(value="7")
        self.err_var = tk.StringVar()

        tk.Label(form_box, text=f"Available: {item.available_qty}", bg=White, fg=Dark_Blue, font=("Calibri", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,10))

        tk.Label(form_box, text="Borrower Name *", bg=White, font=("Calibri", 10, "bold")).grid(row=1, column=0, sticky="w", pady=10)
        ttk.Entry(form_box, textvariable=self.name_var, width=30).grid(row=1, column=1, pady=10)

        tk.Label(form_box, text="Quantity *", bg=White, font=("Calibri", 10, "bold")).grid(row=2, column=0, sticky="w", pady=10)
        ttk.Entry(form_box, textvariable=self.qty_var, width=15).grid(row=2, column=1, sticky="w", pady=10)

        tk.Label(form_box, text="Expected Return (days) *", bg=White, font=("Calibri", 10, "bold")).grid(row=3, column=0, sticky="w", pady=10)
        ttk.Entry(form_box,textvariable=self.days_var, width=15).grid(row=3, column=1, sticky="w", pady=10)

        tk.Label(form_box, textvariable=self.err_var, fg=Red, bg=White, font=("Calibri", 10, "bold")).grid(row=4, column=0, columnspan=2, pady=10)

        btn_box = tk.Frame(form_box, bg=White)
        btn_box.grid(row=5, column=0, columnspan=2, pady=10)
        Flatbutton(btn_box, "Confirm", Green, White, self.save).pack(side="left", padx=5)
        Flatbutton(btn_box, "Cancel", Grey, "#000000", self.win.destroy).pack(side="left", padx=5)

    def save(self):
        try:
            days = int(self.days_var.get())
            if days < 0 or days > 90:
                raise ValueError
        except ValueError:
            self.err_var.set("Expected return must be between 0 and 90 days.")
            return

        rec = BorrowRecord()
        rec.item_id = self.item.item_id
        rec.borrower_name = self.name_var.get()
        rec.qty_borrowed = self.qty_var.get()
        rec.recorded_by = self.user_name
        rec.expected_return = str(date.today() + timedelta(days=days))
        ok, msg = rec.save()
        if ok:
            self.win.destroy()
            self.refresh_fn()
        else:
            self.err_var.set(msg)

class ReturnForm: pass
class AccountsWindow: pass
class ReportWindow: pass
class BorrowLogWindow: pass