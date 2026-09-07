import tkinter as tk
from tkinter import messagebox, ttk
from db import get_connection
 
 
class CategoryModule:
    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.cat_tree = None
        self.cat_frame = None
 
    # ================================================================
    # MAIN UI
    # ================================================================
    def show_categories_ui(self):
        for w in self.parent.winfo_children():
            w.destroy()
 
        # ---- Top bar: Title (left) + Add Button (right) ----
        tk.Label(self.parent, text="📂 Manage Categories",
                 font=("Helvetica", 20, "bold"),
                 bg="#0D1B2A", fg="white").pack(anchor="w", padx=30, pady=(25, 5))
 
        # ---- Action Buttons (left-aligned, below title) ----
        btn_frame = tk.Frame(self.parent, bg="#0D1B2A")
        btn_frame.pack(anchor="w", padx=30, pady=8)
 
        tk.Button(btn_frame, text="➕ Add Category",
                  bg="#2ECC71", fg="white", bd=0, cursor="hand2",
                  font=("Arial", 10, "bold"), padx=12, pady=6,
                  activebackground="#27AE60", activeforeground="white",
                  command=self.add_category_dialog).pack(side="left")

 
        # ---- Treeview Frame ----
        self.cat_frame = tk.Frame(self.parent, bg="#0D1B2A")
        self.cat_frame.pack(fill="x", expand=False, padx=30, pady=(0, 15))
 
        self._load_categories()
 
    # ================================================================
    # LOAD / REFRESH TABLE
    # ================================================================
    def _load_categories(self):
        if not self.cat_frame:
            return
        for w in self.cat_frame.winfo_children():
            w.destroy()
 
        conn = None
        rows = []
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.category_id, c.name, COUNT(b.book_id) AS total
                FROM   categories c
                LEFT JOIN books b ON c.category_id = b.category_id
                GROUP  BY c.category_id, c.name
                ORDER  BY c.name
            """)
            rows = cursor.fetchall()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
        finally:
            if conn:
                conn.close()
 
        # Height = exact rows count (min 1, max 20)
        row_count = max(1, min(len(rows), 20))
 
        # Delete (#4) then Edit (#5)
        cols = ("ID", "Category Name", "Total Books", "Delete", "Edit")
        self.cat_tree = self._make_treeview(self.cat_frame, cols, height=row_count)
 
        for row in rows:
            self.cat_tree.insert("", "end", values=row + ("🗑", "✏"))
 
    # ================================================================
    # INLINE CLICK — detect 🗑 or ✏
    # ================================================================
    def _on_tree_click(self, event):
        region = self.cat_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
 
        col    = self.cat_tree.identify_column(event.x)
        row_id = self.cat_tree.identify_row(event.y)
        if not row_id:
            return

        self.cat_tree.selection_remove(self.cat_tree.selection())

        # Column #4 = Delete 🗑
        if col == "#4":
            self._delete_category_by_row(row_id)
            self.cat_tree.selection_remove(row_id)
            return "break"
 
        # Column #5 = Edit ✏
        elif col == "#5":
            self.edit_category_dialog(row_id)
            self.cat_tree.selection_remove(row_id)
            return "break"

 
    # ================================================================
    # ADD CATEGORY
    # ================================================================
    def add_category_dialog(self):
        if self.cat_tree:
            self.cat_tree.selection_remove(self.cat_tree.selection())
        win = tk.Toplevel()
        win.title("Add Category")
        win.geometry("360x190")
        win.configure(bg="#0D1B2A")
        win.grab_set()
        win.resizable(False, False)
 
        tk.Label(win, text="Add New Category",
                 font=("Helvetica", 14, "bold"),
                 bg="#0D1B2A", fg="white").pack(pady=(22, 12))
 
        tk.Label(win, text="Category Name *",
                 font=("Arial", 9, "bold"),
                 bg="#0D1B2A", fg="#AAB7B8").pack(anchor="w", padx=30)
 
        entry = tk.Entry(win, font=("Arial", 11), width=32,
                         bg="#1A2456", fg="white",
                         insertbackground="white", bd=0,
                         highlightthickness=1,
                         highlightbackground="#1E6FFF")
        entry.pack(padx=30, pady=(3, 12), ipady=5)
        entry.focus_set()
 
        def save():
            name = entry.get().strip()
            if not name:
                messagebox.showwarning("Empty", "Please enter a category name.", parent=win)
                return
            conn = None
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT category_id FROM categories WHERE name=%s", (name,))
                if cursor.fetchone():
                    messagebox.showwarning("Duplicate",
                                           f'Category "{name}" already exists!', parent=win)
                    return
                cursor.execute("INSERT INTO categories (name) VALUES (%s)", (name,))
                conn.commit()
                win.destroy()
                messagebox.showinfo("Added", f'Category "{name}" added successfully!')
                self._load_categories()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)
            finally:
                if conn:
                    conn.close()
 
        entry.bind("<Return>", lambda e: save())
 
        tk.Button(win, text="💾 Save Category",
                  bg="#2ECC71", fg="white",
                  font=("Arial", 11, "bold"), bd=0,
                  cursor="hand2", width=20, pady=7,
                  command=save).pack(pady=4)
 
    # ================================================================
    # EDIT CATEGORY (called from inline ✏ click)
    # ================================================================
    def edit_category_dialog(self, row_id=None):
        if not self.cat_tree:
            return
 
        if row_id is None:
            selected = self.cat_tree.selection()
            if not selected:
                messagebox.showwarning("Select", "Please select a category to edit.")
                return
            row_id = selected[0]
 
        values   = self.cat_tree.item(row_id)["values"]
        cat_id   = values[0]
        old_name = values[1]

        if self.cat_tree:
            self.cat_tree.selection_remove(self.cat_tree.selection())

        win = tk.Toplevel()
        win.title("Edit Category")
        win.geometry("360x190")
        win.configure(bg="#0D1B2A")
        win.grab_set()
        win.resizable(False, False)
 
        tk.Label(win, text="Rename Category",
                 font=("Helvetica", 14, "bold"),
                 bg="#0D1B2A", fg="white").pack(pady=(22, 12))
 
        tk.Label(win, text="New Category Name *",
                 font=("Arial", 9, "bold"),
                 bg="#0D1B2A", fg="#AAB7B8").pack(anchor="w", padx=30)
 
        entry = tk.Entry(win, font=("Arial", 11), width=32,
                         bg="#1A2456", fg="white",
                         insertbackground="white", bd=0,
                         highlightthickness=1,
                         highlightbackground="#1E6FFF")
        entry.insert(0, old_name)
        entry.pack(padx=30, pady=(3, 12), ipady=5)
        entry.focus_set()
        entry.select_range(0, tk.END)
 
        def save():
            new_name = entry.get().strip()
            if not new_name:
                messagebox.showwarning("Empty", "Category name cannot be empty.", parent=win)
                return
            if new_name == old_name:
                win.destroy()
                return
            conn = None
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT category_id FROM categories WHERE name=%s AND category_id!=%s",
                    (new_name, cat_id))
                if cursor.fetchone():
                    messagebox.showwarning("Duplicate",
                                           f'Category "{new_name}" already exists!', parent=win)
                    return
                cursor.execute(
                    "UPDATE categories SET name=%s WHERE category_id=%s",
                    (new_name, cat_id))
                conn.commit()
                win.destroy()
                messagebox.showinfo("Updated", f'Renamed to "{new_name}" successfully!')
                self._load_categories()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)
            finally:
                if conn:
                    conn.close()
 
        entry.bind("<Return>", lambda e: save())
 
        tk.Button(win, text="💾 Save Changes",
                  bg="#1E6FFF", fg="white",
                  font=("Arial", 11, "bold"), bd=0,
                  cursor="hand2", width=20, pady=7,
                  command=save).pack(pady=4)
 
    # ================================================================
    # DELETE CATEGORY (called from inline 🗑 click)
    # ================================================================
    def _delete_category_by_row(self, row_id):
        values   = self.cat_tree.item(row_id)["values"]
        cat_id   = values[0]
        cat_name = values[1]
        book_cnt = values[2]
 
        msg = f'Delete category "{cat_name}"?'
        if book_cnt and int(book_cnt) > 0:
            msg += (f"\n\n⚠️  {book_cnt} book(s) are in this category."
                    "\nThey will become 'Uncategorized' but will NOT be deleted.")
 
        if not messagebox.askyesno("Confirm Delete", msg):
            return
 
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE books SET category_id=NULL WHERE category_id=%s", (cat_id,))
            cursor.execute(
                "DELETE FROM categories WHERE category_id=%s", (cat_id,))
            conn.commit()
            messagebox.showinfo("Deleted", f'Category "{cat_name}" deleted.')
            self._load_categories()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if conn:
                conn.close()
 
    # ================================================================
    # TREEVIEW HELPER
    # ================================================================
    def _make_treeview(self, parent, columns, height=10):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Cat.Treeview",
                        background="#111D45", foreground="white",
                        rowheight=32, fieldbackground="#111D45",
                        borderwidth=0, relief="flat",
                        bordercolor="#111D45", lightcolor="#111D45", darkcolor="#111D45",
                        font=("Arial", 10))
        style.configure("Cat.Treeview.Heading",
                        background="#0A1628", foreground="#E1AD01",
                        font=("Arial", 10, "bold"), relief="flat",
                        bordercolor="#0A1628", lightcolor="#0A1628", darkcolor="#0A1628")
        style.map("Cat.Treeview.Heading",
                  background=[("active", "#1A2456"), ("pressed", "#1E6FFF")],
                  foreground=[("active", "#E1AD01"), ("pressed", "white")])
        # Selected row — mustard instead of blue
        style.map("Cat.Treeview",
                  background=[("selected", "#3A2E00")],
                  foreground=[("selected", "#E1AD01")])
        style.layout("Cat.Treeview", [
            ("Cat.Treeview.treearea", {"sticky": "nswe"})
        ])
        
        vsb = ttk.Scrollbar(parent, orient="vertical")
        tree = ttk.Treeview(parent, columns=columns, show="headings",
                            style="Cat.Treeview",
                            height=height,
                            yscrollcommand=vsb.set)
        vsb.config(command=tree.yview)
 
        tree.column("ID",            width=60,  anchor="center")
        tree.column("Category Name", width=300, anchor="w")
        tree.column("Total Books",   width=120, anchor="center")
        tree.column("Delete",        width=50,  anchor="center", stretch=False)
        tree.column("Edit",          width=50,  anchor="center", stretch=False)
 
        for col in columns:
            tree.heading(col, text=col)
 
        vsb.pack(side="right", fill="y")
        tree.pack(fill="x", expand=False)
 
        # Single click → Delete or Edit
        tree.bind("<Button-1>", self._on_tree_click)
        # Double click → Edit dialog
        tree.bind("<Double-1>", lambda e: self.edit_category_dialog())
 
        return tree