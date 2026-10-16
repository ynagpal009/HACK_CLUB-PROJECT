"""
gui_dashboard.py
The main screen after loggin in - the inventory table, toolbar, 
and the custom menu bar.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from models import Equipment 
from gui_forms import EquipmentForm, BorrowForm, ReturnForm, AccountsWindow, ReportWindow, BorrowLogWindow

Dark_Blue = "#1F4E79"
Light_Grey = "#F2F2F2"
Amber = "#FFF3CD"
White = "#FFFFFF"

# the treeview columns use short ids (name, avail etc) but the actual
# database columns are called item_name, available_qty etc - this maps
# one to the other so clicking a heading sorts the right column
COLUMN_TO_DB_FIELD = {
    "id": "item_id",
    "name": "item_name",
    "category": "category",
    "total": "total_qty",
    "avail": "available_qty",
    "location": "location",
    # status (Available / Low Stock) isn't a real column, so just
    # sort by available_qty since that's what decides the status anyway
    "status": "available_qty",
}


class FlatButton(tk.Frame):
    # same button as gui_forms.FlatButton, just copied here so this file
    # doesn't need too import gui_forms only for one small class
    def __init__(self, parent, text, bg_color, fg_color, command, width=None):
        super().__init__(parent, bg=bg_color, cursor="hand2")
        self.command = command
        self.lbl = tk.Label(self, text=text, bg=bg_color, fg=fg_color, font=("Calibri", 10, "bold"))
        if width:
            self.lbl.config(width=width)
        self.lbl.pack(padx=10, pady=6)
        self.bind("<Button-1>", self.on_click)
        self.lbl.bind("<Button-1>", self.on_click)

    def on_click(self, event):
        self.command()


class Dashboard:
    def __init__(self, root_window, current_user, logout_function):
       self.window = root_window
       self.user = current_user
       self.logout_fn = logout_function
       self.sort_col = "name" #UI key; mapped to a DB column via COLUMN_TO_DB_FIELD
       self.sort_asc = True
       self.window.title(f"HPE Inventory Management System - Welcome, {self.user.full_name} ({self.user.role})")
       self.window.geometry("1100x650")
       self.window.configure(bg=White)
       self.build_ui()
       self.refresh_table()

    def build_ui(self):
        #1. Custom Menu Bar (Fixes Mac Native Menu Bug)
        menu_bar = tk.Frame(self.window, bg=Dark_Blue, height=40)
        menu_bar.pack(fill="x")

        self.make_menu(menu_bar, "File", [("Log Out", self.logout_fn), ("-", None), ("Exit", self.window.destroy)])

        inv_opts = [("Refresh Table", self.refresh_table)]
        if self.user.is_admin():
            inv_opts.append(("-", None))
            inv_opts.append(("Add Item", self.add_item))
            inv_opts.append(("Edit Item", self.edit_item))
            inv_opts.append(("Delete Item",  self.delete_item))
        self.make_menu(menu_bar, "Inventory", inv_opts)
        
        self.make_menu(menu_bar, "Borrowing", [("Borrow Item", self.borrow_item), ("Return Item", self.return_item), ("-", None), ("View Borrowing Log", self.view_borrow_log)])

        # Reports and Accounts are Admin_Only.
        if self.user.is_admin():
            self.make_menu(menu_bar, "Reports", [("View Report", self.view_report), ("Export CSV", self.export_csv)])
            self.make_menu(menu_bar, "Accounts", [("Manage Users", self.manage_accounts)])

        # 2. Toolbar
        toolbar = tk.Frame(self.window, bg=Light_Grey, pady=10, padx=10)
        toolbar.pack(fill="x")

        if self.user.is_admin():
            FlatButton(toolbar, "+ Add Item", "#2E75B6", White, self.add_item).pack(side="left", padx=5)
            FlatButton(toolbar, "Edit Item", "#E67E22", White, self.edit_item).pack(side="left", padx=5)
            FlatButton(toolbar, "Delete", "#E74C3c", White, self.delete_item).pack(side="left", padx=5)
            tk.Frame(toolbar, bg="#CCCCCC", width=2).pack(side="left", fill="y", padx=10)

        FlatButton(toolbar, "Borrow", "#27AE60", White, self.borrow_item).pack(side="left", padx=5)
        FlatButton(toolbar, "Return", "#27AE60", White, self.return_item).pack(side="left", padx=5)
        FlatButton(toolbar, "Who's Borrowed?", "#8E44AD", White, self.view_borrow_log).pack(side="left", padx=5)

        if self.user.is_admin():
            FlatButton(toolbar, "Manage Users", Dark_Blue, White, self.manage_accounts).pack(side="left", padx=5)

        self.search_val = tk.StringVar()
        search_entry = tk.Entry(toolbar, textvariable=self.search_val, width=25, font=("Calibri", 11))
        search_entry.pack(side="right", padx=10, ipady=4)
        search_entry.bind("<Return>", self.handle_search_enter)
        FlatButton(toolbar, "Search", "#FFFFFF", "#000000", self.refresh_table).pack(side="right")
        tk.Label(toolbar, text="Search (name / category / ID):", bg=Light_Grey, font=("Calibri", 11)).pack(side="right")

        # 3. Table Area
        table_frame = tk.Frame(self.window, bg=White)
        table_frame.pack(fill="both", expand=True)

        scroll = ttk.Scrollbar(table_frame, orient="vertical")
        scroll.pack(side="right", fill="y")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", background=Dark_Blue, foreground=White, font=("Calibri", 11, "bold"))

        # readonly comboboxes go grey with the clam theme bby default
        # this makes them white again to match the rest of the form 
        style.map("TCombobox", fieldbackground=[("readonly", White)])
        style.map("TCombobox", selectbackground=[("readonly", White)])
        style.map("TCombobox", selectforeground=[("readonly", "#000000")])

        self.tree = ttk.Treeview(table_frame, columns=("id", "name", "category", "total", "avail", "location", "status"), show="headings", yscrollcommand=scroll.set)
        scroll.config(command=self.tree.yview)

        # setting up each column separately instead of a loop, so each
        # heading just calls its own sort method, simpler than trying
        # to remember which column got clicked
        self.tree.heading("id", text="ID", command=self.sort_by_id)
        self.tree.column("id", width=60, anchor="center")

        self.tree.heading("name", text="Item Name", command=self.sort_by_name)
        self.tree.column("name", width=250, anchor="w")

        self.tree.heading("category", text="Category", command=self.sort_by_category)
        self.tree.column("category", width=150, anchor="center")

        self.tree.heading("total", text="Total", command=self.sort_by_total)
        self.tree.column("total", width=80, anchor="center")

        self.tree.heading("avail", text="Availiable", command=self.sort_by_total)
        self.tree.column("avail", width=80, anchor="center")

        self.tree.heading("location", text="Location", command=self.sort_by_location)
        self.tree.column("location", width=180, anchor="w")

        self.tree.heading("status", text="status", command=self.sort_by_status)
        self.tree.column("status", width=120, anchor="center")

        self.tree.tag_configure("low", background=Amber)
        self.tree.tag_configure("alt", background="#F5F9FF")
        self.tree.pack(fill="both", expand=True)

        self.status_msg = tk.StringVar()
        tk.Label(self.window, textvariable=self.status_msg, bg= Light_Grey, anchor="w", padx=10, pady=5).pack(fill="x", side="bottom")

    def make_menu(self, menu_bar, text, options):
        # builds one of the top menu labels (File, Inventory etc) with
        # its own dropdown. "-" in the options list means a divider line
        lbl = tk.Label(menu_bar, text=text, bg=Dark_Blue, fg=White, font=("Calibri", 11), cursor="hand2", padx=15, pady=8)
        lbl.pack(side="left")
        dropdown = tk.Menu(self.window, tearoff=0, font=("Calibri", 10))
        for label, cmd in options:
            if label == "-":
                dropdown.add_separator()
            else:
                dropdown.add_command(label=label, command=cmd)

        def show_dropdown(event):
            dropdown.post(event.x_root, event.y_root)

        lbl.bind("<Button-1>", show_dropdown)

    def handle_search_enter(self, event):
        self.refresh_table()

    # one method per column, each just calls sort_by with that column's name
    def sort_by_id(self):
        self.sort_by("name")

    def sort_by_name(self):
        self.sort_by("name")

    def sort_by_category(self):
        self.sort_by("category")

    def sort_by_total(self):
        self.sort_by("total")

    def sort_by_avail(self):
        self.sort_by("available")
    
    def sort_by_location(self):
        self.sort_by("location")

    def sort_by_status(self):
        self.sort_by("status")

    def sort_by(self, col):
        if self.sort_col == col:
            self.sort_asc = not self.sort_asc
        else:
            self.sort_asc = True
        self.sort_col = col
        self.refresh_table()

    def refresh_table(self):
        for r in self.tree.get_children():
            self.tree.delete(r)

        db_field = COLUMN_TO_DB_FIELD.get(self.sort_col, "item_name")
        items = Equipment().get_all(self.search_val.get(), db_field, self.sort_asc)

        low_count = 0
        row_number = 0 
        for item in items:
            if item.is_low_stock():
                stat = "⚠ Low Stock"
                tag = "low"
                low_count += 1
            else:
                stat = "Available"
                if row_number % 2 == 0:
                    tag = "normal"
                else:
                    tag = "alt"

            item_id_text = f"E{item.item_id:03}"
            self.tree.insert("", "end", iid=item.item_id,
                             values=(item_id_text, item.item_name, item.category, item.total_qty, item.available_qty, item.location, stat),
                             tags=(tag,))
            row_number += 1 

            if self.sort_asc:
                direction_text = "asc"
            else:
                direction_text = "desc"
            self.status_msg.set(f"{len(items)} items | {low_count} low stock | Sort: {self.sort_col} ({direction_text})")

    def get_selected(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showwarning("Error", "Please select an item.")
            return None
        return Equipment().get_by_id(int(sel))

    def add_item(self):
        EquipmentForm(self.window, self.refresh_table)

    def edit_item(self):
        item = self.get_selected()
        if item:
            EquipmentForm(self.window, self.refresh_table, item)

    def delete_item(self):
        item = self.get_selected()
        if item and messagebox.askyesno("Delete", f"Delete {item.item_name}?"):
            ok, msg = item.delete()
            if ok:
                self.refresh_table()
            else:
                messagebox.showerror("Error", msg)

    def borrow_item(self):
        item = self.get_selected()
        if item:
            if item.available_qty <= 0:
                messagebox.showerror("Error", "No stock available.")
            else:
                BorrowForm(self.window, item, self.refresh_table, self.user.username)

    def return_item(self):
        item = self.get_selected()
        if item:
            ReturnForm(self.window, item, self.refresh_table)

    def manage_accounts(self):
        AccountsWindow(self.window, self.user)

    def view_borrow_log(self):
        BorrowLogWindow(self.window)

    def view_report(self):
        ReportWindow(self.window)

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
            writer.writerow(["ID", "Name", "Category", "Total", "Available", "Location"])
            for i in Equipment().get_all():
                writer.writerow([i.item_id, i.item_name, i.category, i.total_qty, i.available_qty, i.location])
        messagebox.showinfo("Success", f"Data exported to {path}")