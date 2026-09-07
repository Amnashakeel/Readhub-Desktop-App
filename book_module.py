import tkinter as tk
import requests
from io import BytesIO
from PIL import Image, ImageTk
from tkinter import messagebox, ttk
from db import get_connection
 
 
class BookModule:
    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.books_tree = None
        self.books_frame = None
        self.book_cover_images = []
        self.book_search_var = tk.StringVar()
 
    # ================================================================
    # MAIN UI
    # ================================================================
    def show_books_ui(self):
        for w in self.parent.winfo_children():
            w.destroy()
 
        tk.Label(self.parent, text="📚 Manage Books",
                 font=("Helvetica", 20, "bold"),
                 bg="#0D1B2A", fg="white").pack(anchor="w", padx=30, pady=(25, 5))
 
        # ---- Action Buttons ----
        btn_frame = tk.Frame(self.parent, bg="#0D1B2A")
        btn_frame.pack(anchor="w", padx=30, pady=8)
 
        tk.Button(btn_frame, text="➕ Add Book",
                  bg="#2ECC71", fg="white", bd=0, cursor="hand2",
                  font=("Arial", 10, "bold"), padx=12, pady=6,
                  activebackground="#27AE60", activeforeground="white",
                  command=self.add_book_dialog).pack(side="left", padx=(0, 6))
 
        # ---- Search Bar (with inline ✕ clear button) ----
        search_frame = tk.Frame(self.parent, bg="#0D1B2A")
        search_frame.pack(anchor="w", padx=30, pady=(0, 8))
 
        tk.Label(search_frame, text="Search:",
                 font=("Arial", 10), bg="#0D1B2A", fg="#B0BEC5").pack(side="left")
 
        search_box = tk.Frame(search_frame, bg="#1A2456",
                              highlightthickness=1, highlightbackground="#1E6FFF")
        search_box.pack(side="left", padx=8)
 
        search_entry = tk.Entry(search_box, textvariable=self.book_search_var,
                                font=("Arial", 10), width=28, bg="#1A2456",
                                fg="white", insertbackground="white", bd=0,
                                relief="flat")
        search_entry.pack(side="left", ipady=5, padx=(8, 0))
 
        clear_btn = tk.Label(search_box, text="✕", font=("Arial", 10, "bold"),
                             bg="#1A2456", fg="#7F8C8D", cursor="hand2", padx=6)
        clear_btn.pack(side="left")
        clear_btn.bind("<Button-1>", lambda e: self._clear_search())
        clear_btn.bind("<Enter>", lambda e: clear_btn.config(fg="#E74C3C"))
        clear_btn.bind("<Leave>", lambda e: clear_btn.config(fg="#7F8C8D"))
 
        tk.Label(search_box, text="🔍", font=("Arial", 10),
                 bg="#1A2456", fg="#B0BEC5", padx=4).pack(side="left")
 
        self.book_search_var.trace_add("write", lambda *args: self._search_books())
 
        # ---- Books Table ----
        self.books_frame = tk.Frame(self.parent, bg="#0D1B2A")
        self.books_frame.pack(fill="x", expand=False, padx=30, pady=(0, 15))
        self._load_books_table()
 
    # ================================================================
    # LOAD / REFRESH TABLE
    # ================================================================
    def _load_books_table(self, search=None):
        if not self.books_frame:
            return
        for w in self.books_frame.winfo_children():
            w.destroy()

        cols = ("ID", "Title", "Author", "Publisher", "Category",
                "Available", "Total", "ISBN", "Delete", "Edit")

        conn = None
        rows = []
        try:
            conn = get_connection()
            cursor = conn.cursor()
            if search:
                cursor.execute("""
                    SELECT b.book_id, b.title, b.author,
                           COALESCE(b.publisher, '—'),
                           COALESCE(c.name, '—'),
                           b.available_copies, b.quantity,
                           COALESCE(b.isbn, '—'), b.cover_url
                    FROM   books b
                    LEFT JOIN categories c ON b.category_id = c.category_id
                    WHERE  b.title  LIKE %s
                    OR     b.author LIKE %s
                    OR     c.name   LIKE %s
                    ORDER  BY b.book_id DESC
                """, (f"%{search}%", f"%{search}%", f"%{search}%"))
            else:
                cursor.execute("""
                    SELECT b.book_id, b.title, b.author,
                           COALESCE(b.publisher, '—'),
                           COALESCE(c.name, '—'),
                           b.available_copies, b.quantity,
                           COALESCE(b.isbn, '—'), b.cover_url
                    FROM   books b
                    LEFT JOIN categories c ON b.category_id = c.category_id
                    ORDER  BY b.book_id DESC
                """)
            rows = cursor.fetchall()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
        finally:
            if conn:
                conn.close()

        row_count = max(1, min(len(rows), 20))
        self.book_cover_images = []  # reset cache each load
        self.books_tree = self._make_books_treeview(self.books_frame, cols, height=row_count)

        for i, row in enumerate(rows):
            book_data = row[:8]     # everything except cover_url
            cover_url = row[8]
            display_row = book_data + ("🗑", "✏")
            photo = self._get_book_cover_image(cover_url)

            if row[5] <= 0:
                tag = "unavail"
            elif i % 2 == 0:
                tag = "even"
            else:
                tag = "odd"

            self.books_tree.insert("", "end", image=photo if photo else "", values=display_row, tags=(tag,))

        self.books_tree.tag_configure("even",
                                      background="#111D45",
                                      foreground="white")
        self.books_tree.tag_configure("odd",
                                      background="#111D45",
                                      foreground="white")
        self.books_tree.tag_configure("unavail",
                                      background="#5A1A1A",
                                      foreground="white")
 
    def _search_books(self):
        self._load_books_table(search=self.book_search_var.get().strip())
 
    def _clear_search(self):
        self.book_search_var.set("")
        self._load_books_table()

    # ================================================================
    # book cover image -- thumbnail
    # ================================================================
    def _get_book_cover_image(self, cover_url, size=(35, 48)):
        """Downloads and caches a small cover thumbnail. Returns None on failure."""
        if not cover_url:
            return None
        try:
            img_data = requests.get(cover_url, timeout=5).content
            img = Image.open(BytesIO(img_data)).resize(size)
            photo = ImageTk.PhotoImage(img)
            self.book_cover_images.append(photo)  # keep reference (avoid GC)
            return photo
        except Exception as e:
            print("Cover load error:", e)
            return None

    def _make_books_treeview(self, parent, columns, height=15):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("BooksCover.Treeview",
                        background="#111D45", foreground="white",
                        rowheight=55, fieldbackground="#111D45",
                        borderwidth=0, relief="flat",
                        bordercolor="#0D1B2A", lightcolor="#111D45", darkcolor="#111D45",
                        font=("Arial", 10))
        style.configure("BooksCover.Treeview.Heading",
                        background="#06090F", foreground="#E1AD01",
                        font=("Arial", 10, "bold"), relief="flat",
                        bordercolor="#06090F", lightcolor="#06090F", darkcolor="#06090F")
        style.map("BooksCover.Treeview.Heading",
                  background=[("active", "#1A2456"), ("pressed", "#1E6FFF")],
                  foreground=[("active", "#E1AD01"), ("pressed", "white")])
        style.map("BooksCover.Treeview",
                  background=[("selected", "#3A2E00")],
                  foreground=[("selected", "#E1AD01")])
        style.layout("BooksCover.Treeview", [
            ("BooksCover.Treeview.treearea", {"sticky": "nswe"})
        ])
        style.configure("Vertical.TScrollbar", background="#1A2456", troughcolor="#0D1B2A",
                        bordercolor="#0D1B2A", arrowcolor="#E1AD01", relief="flat")
        style.configure("Horizontal.TScrollbar", background="#1A2456", troughcolor="#0D1B2A",
                        bordercolor="#0D1B2A", arrowcolor="#E1AD01", relief="flat")

        vsb = ttk.Scrollbar(parent, orient="vertical")
        hsb = ttk.Scrollbar(parent, orient="horizontal")
        tree = ttk.Treeview(parent, columns=columns, show="tree headings",
                            style="BooksCover.Treeview",
                            height=height,
                            yscrollcommand=vsb.set,
                            xscrollcommand=hsb.set)
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)

        tree.heading("#0", text="Cover")
        tree.column("#0", width=50, anchor="center", stretch=False)

        col_widths = {
            "ID": 55, "Title": 200, "Author": 130, "Publisher": 110,
            "Category": 100, "Available": 75, "Total": 55, "ISBN": 110,
            "Delete": 45, "Edit": 45,
        }
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=col_widths.get(col, 110))

        tree.column("Title", anchor="w")
        tree.column("Author", anchor="w")
        tree.column("Delete", anchor="center", stretch=False)
        tree.column("Edit", anchor="center", stretch=False)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(fill="x", expand=False)

        tree.bind("<Button-1>", self._on_tree_click)
        tree.bind("<Double-1>", lambda e: self.edit_book_dialog())

        return tree
 
    # ================================================================
    # INLINE ACTION — click on Delete (#9) or Edit (#10) column
    # ================================================================
    def _on_tree_click(self, event):
        region = self.books_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
 
        col    = self.books_tree.identify_column(event.x)
        row_id = self.books_tree.identify_row(event.y)
 
        if not row_id:
            return
 
        self.books_tree.selection_remove(self.books_tree.selection())
 
        if col == "#9":
            self._delete_book_by_row(row_id)
            self.books_tree.selection_remove(row_id)
            return "break"
 
        elif col == "#10":
            self.edit_book_dialog(row_id)
            self.books_tree.selection_remove(row_id)
            return "break"
 
    # ================================================================
    # FETCH CATEGORIES HELPER
    # ================================================================
    def _fetch_categories(self):
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT category_id, name FROM categories ORDER BY name")
            return cursor.fetchall()
        except:
            return []
        finally:
            if conn:
                conn.close()
 
    # ================================================================
    # GOOGLE BOOKS API HELPER
    # ================================================================
    def _fetch_from_google_books(self, query, max_results=5):
        """Returns a LIST of matching books (title, author, publisher, isbn, cover_url)."""
        try:
            url = "https://www.googleapis.com/books/v1/volumes"
            params = {"q": query, "maxResults": max_results, "key": "AIzaSyD1gc22AcSksFZRUITjO7_Qw_dBlWA6sWo"}
            res = requests.get(url, params=params, timeout=8)

            if res.status_code != 200:
                print("Google Books API bad status:", res.status_code, res.text)
                return []

            data = res.json()
            if "items" not in data:
                return []

            results = []
            for item in data["items"]:
                info = item.get("volumeInfo", {})
                results.append({
                    "title": info.get("title", ""),
                    "author": ", ".join(info.get("authors", [])),
                    "publisher": info.get("publisher", ""),
                    "isbn": next((i["identifier"] for i in info.get("industryIdentifiers", [])), ""),
                    "cover_url": info.get("imageLinks", {}).get("thumbnail", ""),
                    "preview_link": info.get("previewLink", "")
                })
            return results
        
        except requests.exceptions.RequestException as e:
            print("Google Books network error:", e)
            messagebox.showerror("Network Error",
                                 "Internet connection check karo. Error: " + str(e))
            return []
        except Exception as e:
            print("Google Books API error:", e)
            return []
        
    # ================================================================
    # ADD BOOK DIALOG
    # ================================================================
    def add_book_dialog(self):
        if self.books_tree:
            self.books_tree.selection_remove(self.books_tree.selection())
 
        win = tk.Toplevel()
        win.title("Add New Book")
        win.geometry("430x750")
        win.configure(bg="#0D1B2A")
        win.grab_set()
        win.resizable(False, True)
 
        tk.Label(win, text="➕ Add New Book",
                 font=("Helvetica", 16, "bold"),
                 bg="#0D1B2A", fg="white").pack(pady=(20, 12))
 
        fields = [
            ("Title *",    "title"),
            ("Author",     "author"),
            ("Publisher",  "publisher"),
            ("Edition",    "edition"),
            ("ISBN",       "isbn"),
            ("Quantity *", "quantity"),
        ]
        entries = {}
        for lbl, key in fields:
            tk.Label(win, text=lbl, font=("Arial", 9, "bold"),
                     bg="#0D1B2A", fg="#AAB7B8").pack(anchor="w", padx=30)
            e = tk.Entry(win, font=("Arial", 11), width=36,
                         bg="#1A2456", fg="white",
                         insertbackground="white", bd=0,
                         highlightthickness=1,
                         highlightbackground="#1E6FFF")
            e.pack(padx=30, pady=(2, 7), ipady=5)
            entries[key] = e
 
        # ---- Cover preview + fetch state ----
        cover_url_holder = {"url": ""}
        preview_link_holder = {"url": ""}
        cover_preview_lbl = tk.Label(win, bg="#0D1B2A")
        cover_preview_lbl.pack(pady=(0, 5))
 
        def fetch_from_google():
            query = entries["isbn"].get().strip() or entries["title"].get().strip()
            if not query:
                messagebox.showwarning("Empty", "Please type a Title or ISBN first.", parent=win)
                return
 
            results = self._fetch_from_google_books(query)
            if not results:
                messagebox.showerror("Not Found", "No matching book found on Google Books.", parent=win)
                return
 
            # ---- Popup: choose correct book from list ----
            pick_win = tk.Toplevel(win)
            pick_win.title("Select the Correct Book")
            pick_win.geometry("380x350")
            pick_win.configure(bg="#0D1B2A")
            pick_win.grab_set()
 
            tk.Label(pick_win, text="Select the correct book:",
                     font=("Helvetica", 13, "bold"),
                     bg="#0D1B2A", fg="white").pack(pady=10)
 
            def choose(result):
                entries["title"].delete(0, tk.END); entries["title"].insert(0, result["title"])
                entries["author"].delete(0, tk.END); entries["author"].insert(0, result["author"])
                entries["publisher"].delete(0, tk.END); entries["publisher"].insert(0, result["publisher"])
                if result["isbn"]:
                    entries["isbn"].delete(0, tk.END); entries["isbn"].insert(0, result["isbn"])
 
                cover_url_holder["url"] = result["cover_url"]
                preview_link_holder["url"] = result.get("preview_link", "")

                if result["cover_url"]:
                    try:
                        img_data = requests.get(result["cover_url"], timeout=8).content
                        img = Image.open(BytesIO(img_data)).resize((80, 110))
                        photo = ImageTk.PhotoImage(img)
                        cover_preview_lbl.config(image=photo)
                        cover_preview_lbl.image = photo
                    except Exception as e:
                        print("Cover load error:", e)
 
                pick_win.destroy()
 
            for r in results:
                row = tk.Frame(pick_win, bg="#111D45", highlightthickness=1,
                               highlightbackground="#1E6FFF")
                row.pack(fill="x", padx=15, pady=5)
 
                text = f"{r['title']}\n by {r['author'] or 'Unknown'}"
                tk.Label(row, text=text, font=("Arial", 10),
                         bg="#111D45", fg="white", justify="left",
                         anchor="w", wraplength=300).pack(side="left", padx=10, pady=8, fill="x", expand=True)
 
                tk.Button(row, text="✔ Select", bg="#2ECC71", fg="white", bd=0,
                          cursor="hand2", font=("Arial", 9, "bold"),
                          command=lambda res=r: choose(res)).pack(side="right", padx=8)
 
        # ---- Fetch button (was missing before — now added) ----
        tk.Button(win, text="🔍 Fetch Real Book Data (Google)",
                  bg="#1E6FFF", fg="white", bd=0, cursor="hand2",
                  font=("Arial", 10, "bold"), padx=10, pady=6,
                  command=fetch_from_google).pack(pady=(0, 10))
 
        # ---- Category Dropdown ----
        tk.Label(win, text="Category", font=("Arial", 9, "bold"),
                 bg="#0D1B2A", fg="#AAB7B8").pack(anchor="w", padx=30)
 
        categories = self._fetch_categories()
        cat_names  = [c[1] for c in categories] if categories else ["Uncategorized"]
        cat_var    = tk.StringVar(value=cat_names[0])
 
        cat_dropdown = tk.OptionMenu(win, cat_var, *cat_names)
        cat_dropdown.config(font=("Arial", 11), bg="#1A2456", fg="white", bd=0,
                            highlightthickness=1, highlightbackground="#1E6FFF",
                            activebackground="#1E6FFF", activeforeground="white",
                            width=32)
        cat_dropdown["menu"].config(bg="#1A2456", fg="white", font=("Arial", 10))
        cat_dropdown.pack(padx=30, pady=(2, 10), anchor="w")
 
        def save():
            data = {k: v.get().strip() for k, v in entries.items()}
            if not data["title"] or not data["author"] or not data["quantity"]:
                messagebox.showwarning("Required",
                                       "Title, Author and Quantity are required!",
                                       parent=win)
                return
            try:
                qty = int(data["quantity"])
                if qty < 1:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid",
                                     "Quantity must be a positive number!",
                                     parent=win)
                return

            if data["isbn"]:
                conn_chk = None
                try:
                    conn_chk = get_connection()
                    cur_chk = conn_chk.cursor()
                    cur_chk.execute("SELECT book_id FROM books WHERE isbn=%s", (data["isbn"],))
                    if cur_chk.fetchone():
                        messagebox.showwarning("Duplicate ISBN",
                                               "A book with this ISBN already exists!",
                                               parent=win)
                        return
                finally:
                    if conn_chk:
                        conn_chk.close()
 
 
            cat_id = None
            for cid, cname in categories:
                if cname == cat_var.get():
                    cat_id = cid
                    break
 
            conn = None
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO books
                        (title, author, publisher, edition, isbn,
                         quantity, available_copies, category_id, cover_url, preview_link)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (data["title"], data["author"],
                      data["publisher"] or None,
                      data["edition"]   or None,
                      data["isbn"]      or None,
                      qty, qty, cat_id,
                      cover_url_holder["url"] or None,
                      preview_link_holder["url"] or None))
                conn.commit()
                win.destroy()
                messagebox.showinfo("Added", "Book added successfully!")
                self._load_books_table()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)
            finally:
                if conn:
                    conn.close()
 
        tk.Button(win, text="💾 Save Book",
                  bg="#2ECC71", fg="white",
                  font=("Arial", 12, "bold"), bd=0,
                  cursor="hand2", width=22, pady=8,
                  command=save).pack(pady=8)
 
    # ================================================================
    # EDIT BOOK DIALOG
    # ================================================================
    def edit_book_dialog(self, row_id=None):
        if not self.books_tree:
            return
 
        if row_id is None:
            selected = self.books_tree.selection()
            if not selected:
                messagebox.showwarning("Select", "Please select a book to edit.")
                return
            row_id = selected[0]
 
        if self.books_tree:
            self.books_tree.selection_remove(self.books_tree.selection())
 
        row_vals = self.books_tree.item(row_id)["values"]
        book_id  = row_vals[0]
 
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.book_id, b.title, b.author, b.publisher,
                       b.edition, b.isbn, b.quantity,
                       b.available_copies, b.category_id
                FROM   books b
                WHERE  b.book_id = %s
            """, (book_id,))
            book = cursor.fetchone()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        finally:
            if conn:
                conn.close()
 
        if not book:
            messagebox.showerror("Error", "Book not found.")
            return
 
        (bid, title, author, publisher, edition,
         isbn, quantity, available, old_cat_id) = book
 
        win = tk.Toplevel()
        win.title("Edit Book")
        win.geometry("430x590")
        win.configure(bg="#0D1B2A")
        win.grab_set()
        win.resizable(False, False)
 
        tk.Label(win, text="✏️ Edit Book",
                 font=("Helvetica", 16, "bold"),
                 bg="#0D1B2A", fg="white").pack(pady=(20, 12))
 
        field_defs = [
            ("Title *",    "title",     str(title     or "")),
            ("Author *",   "author",    str(author    or "")),
            ("Publisher",  "publisher", str(publisher or "")),
            ("Edition",    "edition",   str(edition   or "")),
            ("ISBN",       "isbn",      str(isbn      or "")),
            ("Quantity *", "quantity",  str(quantity  or "")),
        ]
        entries = {}
        for lbl, key, default in field_defs:
            tk.Label(win, text=lbl, font=("Arial", 9, "bold"),
                     bg="#0D1B2A", fg="#AAB7B8").pack(anchor="w", padx=30)
            e = tk.Entry(win, font=("Arial", 11), width=36,
                         bg="#1A2456", fg="white",
                         insertbackground="white", bd=0,
                         highlightthickness=1,
                         highlightbackground="#1E6FFF")
            e.insert(0, default)
            e.pack(padx=30, pady=(2, 7), ipady=5)
            entries[key] = e
 
        tk.Label(win, text="Category", font=("Arial", 9, "bold"),
                 bg="#0D1B2A", fg="#AAB7B8").pack(anchor="w", padx=30)
 
        categories = self._fetch_categories()
        cat_names  = [c[1] for c in categories] if categories else ["Uncategorized"]
 
        current_cat = "Uncategorized"
        for cid, cname in categories:
            if cid == old_cat_id:
                current_cat = cname
                break
 
        cat_var = tk.StringVar(value=current_cat)
        cat_dropdown = tk.OptionMenu(win, cat_var, *cat_names)
        cat_dropdown.config(font=("Arial", 11), bg="#1A2456", fg="white", bd=0,
                            highlightthickness=1, highlightbackground="#1E6FFF",
                            activebackground="#1E6FFF", activeforeground="white",
                            width=32)
        cat_dropdown["menu"].config(bg="#1A2456", fg="white", font=("Arial", 10))
        cat_dropdown.pack(padx=30, pady=(2, 10), anchor="w")
 
        def save():
            data = {k: v.get().strip() for k, v in entries.items()}
            if not data["title"] or not data["author"] or not data["quantity"]:
                messagebox.showwarning("Required",
                                       "Title, Author and Quantity are required!",
                                       parent=win)
                return
            try:
                new_qty = int(data["quantity"])
                if new_qty < 1:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid",
                                     "Quantity must be a positive number!",
                                     parent=win)
                return
 
            qty_diff  = new_qty - quantity
            new_avail = max(0, available + qty_diff)
 
            new_cat_id = None
            for cid, cname in categories:
                if cname == cat_var.get():
                    new_cat_id = cid
                    break
 
            conn2 = None
            try:
                conn2 = get_connection()
                cursor2 = conn2.cursor()
                cursor2.execute("""
                    UPDATE books
                    SET    title            = %s,
                           author           = %s,
                           publisher        = %s,
                           edition          = %s,
                           isbn             = %s,
                           quantity         = %s,
                           available_copies = %s,
                           category_id      = %s
                    WHERE  book_id = %s
                """, (data["title"], data["author"],
                      data["publisher"] or None,
                      data["edition"]   or None,
                      data["isbn"]      or None,
                      new_qty, new_avail,
                      new_cat_id, book_id))
                conn2.commit()
                win.destroy()
                messagebox.showinfo("Updated", "Book updated successfully!")
                self._load_books_table()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)
            finally:
                if conn2:
                    conn2.close()
 
        tk.Button(win, text="💾 Save Changes",
                  bg="#1E6FFF", fg="white",
                  font=("Arial", 12, "bold"), bd=0,
                  cursor="hand2", width=22, pady=8,
                  command=save).pack(pady=8)
 
    # ================================================================
    # DELETE BOOK (called from inline 🗑 click)
    # ================================================================
    def _delete_book_by_row(self, row_id):
        row_vals   = self.books_tree.item(row_id)["values"]
        book_id    = row_vals[0]
        book_title = row_vals[1]
 
        conn = None
        active_loans = 0
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT COUNT(*) FROM loans
                              WHERE book_id=%s AND status='borrowed'""", (book_id,))
            active_loans = cursor.fetchone()[0]
        except:
            pass
        finally:
            if conn:
                conn.close()
 
        msg = f'Delete "{book_title}" (ID: {book_id})?'
        if active_loans > 0:
            msg += (f"\n\n⚠️  This book has {active_loans} active loan(s)!"
                    "\nDeleting may cause issues with loan records.")
 
        if not messagebox.askyesno("Confirm Delete", msg):
            return
 
        conn2 = None
        try:
            conn2 = get_connection()
            cursor2 = conn2.cursor()
            cursor2.execute("DELETE FROM books WHERE book_id=%s", (book_id,))
            conn2.commit()
            messagebox.showinfo("Deleted", f'"{book_title}" deleted successfully.')
            self._load_books_table()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if conn2:
                conn2.close()
 
    # ================================================================
    # TREEVIEW HELPER
    # ================================================================
    def _make_treeview(self, parent, columns, height=15):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Book.Treeview",
                        background="#111D45",
                        foreground="white",
                        rowheight=32,
                        fieldbackground="#111D45",
                        borderwidth=0, relief="flat",
                        bordercolor="#111D45", lightcolor="#111D45", darkcolor="#111D45",
                        font=("Arial", 10))
        style.configure("Book.Treeview.Heading",
                        background="#0A1628",
                        foreground="#E1AD01",
                        font=("Arial", 10, "bold"),
                        relief="flat",
                        bordercolor="#0A1628", lightcolor="#0A1628", darkcolor="#0A1628")
        style.map("Book.Treeview.Heading",
                  background=[("active", "#1A2456"), ("pressed", "#1E6FFF")],
                  foreground=[("active", "#E1AD01"), ("pressed", "white")])
        style.map("Book.Treeview",
                  background=[("selected", "#3A2E00")],
                  foreground=[("selected", "#E1AD01")])
        style.layout("Book.Treeview", [
            ("Book.Treeview.treearea", {"sticky": "nswe"})
        ])
 
        vsb = ttk.Scrollbar(parent, orient="vertical")
        hsb = ttk.Scrollbar(parent, orient="horizontal")
        tree = ttk.Treeview(parent, columns=columns, show="headings",
                            style="Book.Treeview",
                            height=height,
                            yscrollcommand=vsb.set,
                            xscrollcommand=hsb.set)
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)
 
        col_widths = {
            "ID":        55,
            "Title":     200,
            "Author":    130,
            "Publisher": 110,
            "Category":  100,
            "Available": 75,
            "Total":     55,
            "ISBN":      110,
            "Delete":    45,
            "Edit":      45,
        }
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center",
                        width=col_widths.get(col, 110))
 
        tree.column("Title",  anchor="w")
        tree.column("Author", anchor="w")
        tree.column("Delete", anchor="center", stretch=False)
        tree.column("Edit",   anchor="center", stretch=False)
 
        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(fill="x", expand=False)
 
        tree.bind("<Button-1>", self._on_tree_click)
        tree.bind("<Double-1>", lambda e: self.edit_book_dialog())
 
        return tree