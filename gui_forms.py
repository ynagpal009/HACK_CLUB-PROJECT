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
        self.item.low_stock_threshold = self.thresh_var.get()
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


class ReturnForm: 
    def __init__(self, parent, item, refresh_fn):
        self.item = item
        self.refresh_fn = refresh_fn
        self.win = tk.Toplevel(parent)
        self.win.geometry("560x440")
        self.win.configure(bg=BG_Blue)
        tk.Label(self.win, text="Record Return", bg=Dark_Blue, fg=White, font=("Calibri", 14, "bold"), anchor="w", padx=20, pady=10).pack(fill="x")

        content = tk.Frame(self.win, bg=White, padx=20, pady=20)
        content.pack(fill="both", expand=True, padx=20, pady=20)

        self.records = BorrowRecord().get_active_for_item(item.item_id)
        self.tree = ttk.Treeview(content, columns=("id", "name", "qty", "due"), show="headings", height=5)
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=40)
        self.tree.heading("name", text="Borrower")
        self.tree.column("name", width=180)        
        self.tree.heading("qty", text="Qty")
        self.tree.column("qty", width=60)
        self.tree.heading("due", text="Due Back")
        self.tree.column("due", width=100)
        self.tree.pack(pady=10, fil="x")
        for r in self.records:
            if r.expected_return:
                due_text = r.expected_return
            else:
                due_text = "-"
            self.tree.insert("", "end", iid=r.borrow_id, values=(r.borrow_id, r.borrower_name, r.qty_borrowed, due_text))

        self.err_var = tk.StringVar()
        tk.Label(content, textvariable=self.err_var, fg=Red, bg=White, font=("Calibri", 10, "bold")).pack()

        btn_box = tk.Frame(content, bg=White)
        btn_box.pack(pady=10)
        Flatbutton(btn_box, "Confirm Return", Green, White, self.save).pack(side="left", padx=5)
        Flatbutton(btn_box, "Cancel", Grey, "#000000", self.win.destroy).pack(side="left", padx=5)

    def save(self):
        sel = self.tree.focus()
        if not sel:
            self.err_var.set("Please select a record.")
            return

        rec = None
        for r in self.records:
            if r.borrow_id == int(sel):
                rec = r
                break

        if rec:
            rec.complete_return(str(date.today()))
            self.win.destroy()
            self.refresh_fn()


class UserForm:
    # admin only - lets you make a new staff/admin login or edit one that
    # already exists (existing__user is None means we're making a new one)

    def __init__(self, parent, refresh_fn, existing_user=None):
        self.refresh_fn = refresh_fn
        if existing_user is not None:
            self.user = existing_user
        else:
            self.user = User()
        self.is_new = existing_user is None

        self.win = tk.Toplevel(parent)
        self.win.title("User Account Form")
        self.win.geometry("480x480")
        self.win.configure(bg=BG_Blue)
        self.win.grab_set()

        if existing_user:
            title = "Edit User Account"
        else:
            title = "Add New User Account"
        tk.Label(self.win, text=title, bg=Dark_Blue, fg=White, font=("Calibri", 14, "bold"), anchor="w", padx=20, pady=10).pack(fill="x")

        panel = tk.Frame(self.win, bg=White, padx=30, pady=20)
        panel.pack(fill="both", expand=True, padx=20, pady=20)

        self.username_var = tk.StringVar(value=self.user.username)
        self.fullname_var = tk.StringVar(value=self.user.full_name)
        self.role_var = tk.StringVar(value=self.user.role)
        self.password_var = tk.StringVar()
        self.active_var = tk.BooleanVar(value=bool(self.user.is_active))
        self.error_var = tk.StringVar()

        tk.Label(panel, text="Username *", bg=White, font=("Calibri", 10, "bold")).grid(row=0, column=0, sticky="w", pady=10)
        ttk.Entry(panel, textvariable=self.username_var, width=30).grid(row=0, column=1, sticky="w")

        tk.Label(panel, text="Full Name *", bg=White, font=("Calibri", 10, "bold")).grid(row=1, column=0, sticky="w", pady=10)
        ttk.Entry(panel, textvariable=self.fullname_var, width=30).grid(row=1, column=1, sticky="w")

        tk.Label(panel, text="Role *", bg=White, font=("Calibri", 10, "bold")).grid(row=2, column=0, sticky="w", pady=10)
        ttk.Combobox(panel, textvariable=self.role_var, values=["Admin", "Staff"], state="readonly", width=15).grid(row=2, column=1, sticky="w")

        if self.is_new:
            pw_label = "Password *"
        else:
            pw_label = "New Password (leave blank to keep current)"
        tk.Label(panel, text=pw_label, bg=White, font=("Calibri", 10, "bold")).grid(row=3, column=0, sticky="w", pady=10)
        ttk.Entry(panel, textvariable=self.password_var, show="\u2022", width=30).grid(row=3, column=1, sticky="w")

        tk.Checkbutton(panel, text="Account Active", variable=self.active_var, bg=White, font=("Calibri", 10)).grid(row=4, column=0, columnspan=2, sticky="w", pady=10)

        tk.Label(panel, textvariable=self.error_var, fg=Red, bg=White, font=("Calibri", 10, "bold")).grid(row=5, column=0, columnspan=2)

        btn_box = tk.Frame(panel, bg=White)
        btn_box.grid(row=6, column=0, columnspan=2, pady=15)
        Flatbutton(btn_box, "Save User", Green, White, self.save).pack(side="left", padx=5)
        Flatbutton(btn_box, "Cancel", Grey, "#000000", self.win.destroy).pack(side="left", padx=5)

    def save(self):
        self.user.username = self.username_var.get().strip()
        self.user.full_name = self.fullname_var.get().strip()
        self.user.role = self.role_var.get()

        if self.active_var.get():
            self.user.is_active = 1
        else:
            self.user.is_active = 0 

        new_password = self.password_var.get().strip()
        if new_password == "":
            new_password = None

        ok, msg = self.user.save(new_password=new_password)
        if ok:
            self.win.destroy()
            self.refresh_fn()
        else:
            self.error_var.set(msg)


class AccountsWindow:
    # admin only screen - shows all logins and lets you add new ones,
    # edit them, or turn them on/off

    def __init__(self, parent, current_user):
        self.current_user = current_user
        self.win = tk.Toplevel(parent)
        self.win.title("Manage User Accounts")
        self.win.geometry("640x460")
        self.win.configure(bg=White)
        self.win.grab_set()

        tk.Label(self.win, text="User Accounts", bg=Dark_Blue, fg=White, font=("Calibri", 14, "bold"), anchor="w", padx=20, pady=10).pack(fill="x")

        toolbar = tk.Frame(self.win, bg=Grey, pady=8, padx=10)
        toolbar.pack(fill="x")
        Flatbutton(toolbar, "+ Add User", "#2E75B6", White, self.add_user, width=10).pack(side="left", padx=5)
        Flatbutton(toolbar, "Edit User", "#E67E22", White, self.edit_user, width=10).pack(side="left", padx=5)
        Flatbutton(toolbar, "Toggle Active", Dark_Blue, White, self.toggle_active, width=12).pack(side="left", padx=5)

        table_frame = tk.Frame(self.win, bg=White)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree = ttk.Treeview(table_frame, columns=("id", "username", "name", "role", "status"), show="headings")
        self.tree.heading("id", text="id")
        self.tree.column("id", width=40, anchor="center")
        self.tree.heading("username", text="Username")
        self.tree.column("username", width=130, anchor="w")
        self.tree.heading("name", text="Full Name")
        self.tree.column("name", width=180, anchor="w")
        self.tree.heading("role", text="Role")
        self.tree.column("role", width=80, anchor="center")
        self.tree.heading("status", text="Status")
        self.tree.column("status", width=90, anchor="center")
        self.tree.pack(fill="both", expand=True)

        self.refresh()

    def refresh(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        for user in User().get_all():
            if user.is_active:
                status = "Active"
            else:
                status = "Deactivated"
            self.tree.insert("", "end", iid=user.user_id, values=(user.user_id, user.username, user.full_name, user.role, status))

    def get_selected(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showwarning("Error", "Please select a user.")
            return None

        for user in User().get_all():
            if user.user_id == int(sel):
                return user
        return None

    def add_user(self):
        UserForm(self.win, self.refresh)

    def edit_user(self):
        user = self.get_selected()
        if user:
            UserForm(self.win, self.refresh, user)

    def toggle_active(self):
        user = self.get_selected()
        if not user:
            return
        if user.user_id == self.current_user.user_id:
            messagebox.showerror("Error", "You cannot deactivate your own account while logged in.")
            return
        user.set_active(not user.is_active)
        self.refresh()
    
            
class BorrowLogWindow: 
    # shows everything currently on loan, or the full history if you
    # switch the radio button. 


    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("Borrowing Log")
        self.win.geometry("760x480")
        self.win.configure(bg=White)

        tk.Label(self.win, text="Borrowing Log", bg=Dark_Blue, fg=White, font=("Calibri", 14, "bold"), anchor="w", padx=20, pady=10).pack(fill="x")

        toolbar = tk.Frame(self.win, bg=BG_Blue, pady=8, padx=10)
        toolbar.pack(fill="x")

        self.mode_var = tk.StringVar(value="active")
        tk.Radiobutton(toolbar, text="Currently Borrowed", variable=self.mode_var, value="active",
                       bg=BG_Blue, font=("Calibri", 10), command=self.refresh).pack(side="left", padx=5)
        tk.Radiobutton(toolbar, text="Full History", variable=self.mode_var, value="history",
                       bg=BG_Blue, font=("Calibri", 10), command=self.refresh).pack(side="left", padx=5)
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(toolbar, textvariable=self.search_var, width=25, font=("Calibri", 10))
        search_entry.pack(side="right", padx=5)
        search_entry.bind("<Return>", self.handle_search_enter)
        Flatbutton(toolbar, "Search", White, "#000000", self.refresh, width=8).pack(side="right")
        tk.Label(toolbar, text="Search borrower/item:", bg=BG_Blue, font=("Calibri", 10)).pack(side="right", padx=(10, 0))

        table_frame = tk.Frame(self.win, bg=White)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree = ttk.Treeview(table_frame, columns=("item", "borrower", "qty", "borrowed", "due", "returned", "status"), show="headings")
        self.tree.heading("item", text="Item")
        self.tree.column("item", width=170, anchor="w")
        self.tree.heading("borrower", text="Borrower")
        self.tree.column("borrower", width=140, anchor="w")
        self.tree.heading("qty", text="Qty")
        self.tree.column("qty", width=50, anchor="center")
        self.tree.heading("borrowed", text="Borrowed On")
        self.tree.column("borrowed", width=100, anchor="center")
        self.tree.heading("due", text="Due Back")
        self.tree.column("due", width=100, anchor="center")
        self.tree.heading("returned", text="Returned On")
        self.tree.column("returned", width=100, anchor="center")
        self.tree.heading("status", text="Status")
        self.tree.column("status", width=90, anchor="center")
        self.tree.pack(fill="both", expand=True)

        self.count_var = tk.StringVar()
        tk.Label(self.win, textvariable=self.count_var, bg="#F2F2F2", anchor="w", padx=10, pady=5).pack(fill="x", side="bottom")

        self.refresh()

    def handle_search_enter(self, event):
        self.refresh()

    def refresh(self):
        for r in self.tree.get_children():
            self.tree.delete(r)

        if self.mode_var.get() == "active":
            all_active = BorrowRecord().get_all_active()
            # If searching while in "active" mode, filter by borrower or
            # item name for a consistent search experience.
            text = self.search_var.get().strip().lower()
            records = []
            for r in all_active:
                if text == "" or text in r.borrower_name.lower() or text in r.item_name.lower():
                    records.append(r)
        else:
            records = BorrowRecord().get_history(self.search_var.get())

        today_text = str(date.today())
        for rec in records:
            is_overdue = rec.status == "Borrowed" and rec.expected_return and rec.expected_return < today_text
            if is_overdue:
                row_tags = ("overdue",)
            else:
                row_tags = ()

            if rec.expected_return:
                due_text = rec.expected_return
            else:
                due_text = "-"

            if rec.return_date:
                returned_text = rec.return_date
            else:
                returned_text = "-"

            self.tree.insert("", "end", values=(
                rec.item_name, rec.borrower_name, rec.qty_borrowed,
                rec.borrow_date, due_text, returned_text, rec.status
            ), tags=row_tags)

        self.tree.tag_configure("overdue", background="#FDECEA")
        self.count_var.set(f"{len(records)} record(s)")


class ReportWindow:
    # admin only - shows the numbers Mr Ellis wanted (totals, low stock,
    # categories) and lets him export the full list as CSV

    def __init__(self, parent):
        summary = Equipment().get_summary()

        self.win = tk.Toplevel(parent)
        self.win.title("Inventory Summary Report")
        self.win.geometry("560x520")
        self.win.configure(bg=White)

        tk.Label(self.win, text="Inventory Summary Report", bg=Dark_Blue, fg=White, font=("Calibri", 14, "bold"), anchor="w", padx=20, pady=10).pack(fill="x")

        body = tk.Frame(self.win, bg=White, padx=25, pady=15)
        body.pack(fill="both", expand=True)

        stats = [
            ("Total distinct items:", summary["total_items"]),
            ("Total units held:", summary["total_qty"]),
            ("Units currently available:", summary["total_available"]),
            ("Units currently borrowed:", summary["total_borrowed"]),
            ("Items below low-stock threshold:", len(summary["low_stock_items"])),
        ]
        row_number = 0 
        for label, value in stats:
            tk.Label(body, text=label, bg=White, font=("Calibri", 11)).grid(row=row_number, column=0, sticky="w", pady=4)
            tk.Label(body, text=str(value), bg=White, font=("Calibri", 11, "bold"), fg=Dark_Blue).grid(row=row_number, column=1, sticky="w", padx=10)
            row_number += 1

        tk.Label(body, text="By Category:", bg=White, font=("Calibri", 11, "bold")).grid(row=row_number, column=0, sticky="w", pady=(15, 4))
        row_number += 1

        cat_text = ""
        for cat, count in summary["categories"].items():
            if cat_text != "":
                cat_text += ", "
            cat_text += f"{cat} ({count})"
        if cat_text == "":
            cat_text = "No items recorded."
        tk.Label(body, text=cat_text, bg=White, font=("Calibri", 10), wraplength=480, justify="left").grid(row=row_number, column=0, columnspan=2, sticky="w")
        row_number += 1

        tk.Label(body, text="Low-Stock Items:", bg=White, font=("Calibri", 11, "bold")).grid(row=row_number, column=0, sticky="w", pady=(15, 4))
        row_number += 1

        low_frame = tk.Frame(body, bg=White)
        low_frame.grid(row=row_number, column=0, columnspan=2, sticky="ew")
        low_tree = ttk.Treeview(low_frame, columns=("name", "avail", "thresh"), show="headings", height=6)
        low_tree.heading("name", text="Item Name")
        low_tree.column("name", width=250)
        low_tree.heading("avail", text="Available")
        low_tree.column("avail", width=90, anchor="center")
        low_tree.heading("thresh", text="Threshold")
        low_tree.column("thresh", width=90, anchor="center")
        low_tree.pack(fill="x")
        for item in summary["low_stock_items"]:
            low_tree.insert("", "end", values=(item.item_name, item.available_qty, item.low_stock_threshold))

        btn_box = tk.Frame(self.win, bg=White, pady=15)
        btn_box.pack()
        Flatbutton(btn_box, "Export Full CSV", Green, White, self.export_csv).pack(side="left", padx=5)
        Flatbutton(btn_box, "Close", Grey, "#000000", self.win.destroy).pack(side="left", padx=5)

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV file", "*.csv")],
            initialfile="inventory_report.csv",
            title="Save Inventory Report As"
        )
        if not path:
            return
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Category", "Total", "Available", "Location", "Condition", "Low Stock Threshold"])
            for i in Equipment().get_all():
                writer.writerow([i.item_id, i.item_name, i.category, i.total_qty, i.available_qty, i.location, i.condition_status, i.low_stock_threshold])
        messagebox.showinfo("Success", f"Data exported to {path}")