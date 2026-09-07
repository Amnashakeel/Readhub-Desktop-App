import tkinter as tk
import requests
from io import BytesIO
from PIL import Image, ImageTk, ImageDraw
from tkinter import messagebox, ttk, filedialog
from db import get_connection
import datetime
import csv
import webbrowser
import bcrypt
 
class UserDashboard(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#0D1B2A")
        self.controller = controller
        self.user_id = None
        self.user_name = "User"
        self.book_cover_images = []
        self.build_ui()
 
    def build_ui(self):
        # ============================================================
        # SIDEBAR (Left)
        # ============================================================
        self.sidebar = tk.Frame(self, bg="#06090F", width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
 
        tk.Label(self.sidebar, text="📚 ReadHub",
                 font=("Helvetica", 15, "bold"),
                 bg="#06090F", fg="#1E6FFF").pack(pady=(25, 5))
 
        tk.Frame(self.sidebar, bg="#1A2456", height=1).pack(fill="x", padx=15, pady=5)
 
        self.welcome_lbl = tk.Label(self.sidebar, text="👋 Welcome!",
                                     font=("Arial", 11, "bold"),
                                     bg="#06090F", fg="#E1AD01")
        self.welcome_lbl.pack(pady=(5, 20))
 
        menu_items = [
            ("🏠  Home",          self.show_home),
            ("📖  Books",         self.show_books),
            ("📜  My Loans",      self.show_loans),
            ("⭐  Wishlist",      self.show_wishlist),
            ("🔔  Notifications", self.show_notifications),
            ("💸  My Fines",      self.show_fines),
            ("👤  Profile",       self.show_profile),
            ("⚙️  Settings",      self.show_settings),
        ]
 
        for text, cmd in menu_items:
            tk.Button(self.sidebar, text=text,
                      bg="#06090F", fg="#B0BEC5",
                      font=("Arial", 11), bd=0,
                      cursor="hand2", anchor="w",
                      padx=20, pady=12,
                      activebackground="#1E2A4A",
                      activeforeground="white",
                      command=cmd).pack(fill="x")
 
        tk.Frame(self.sidebar, bg="#06090F").pack(expand=True, fill="both")
        tk.Frame(self.sidebar, bg="#1A2456", height=1).pack(fill="x", padx=15, pady=5)
 
        tk.Button(self.sidebar, text="🚪  Logout",
                  bg="#E74C3C", fg="white",
                  font=("Arial", 11, "bold"), bd=0,
                  cursor="hand2", anchor="w",
                  padx=20, pady=12,
                  activebackground="#C0392B",
                  command=self.logout).pack(fill="x", pady=10)
 
        # ============================================================
        # MAIN CONTENT AREA (Right)
        # ============================================================
        self.content = tk.Frame(self, bg="#0D1B2A")
        self.content.pack(side="right", fill="both", expand=True)
 
        self.show_home()
 
    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()
 
    # ================================================================
    # HOME
    # ================================================================
    def show_home(self):
        self.clear_content()
 
        tk.Label(self.content, text="My Dashboard",
                 font=("Helvetica", 22, "bold"),
                 bg="#0D1B2A", fg="white").pack(anchor="w", padx=30, pady=(25, 5))
        tk.Label(self.content, text="Your library activity at a glance",
                 font=("Arial", 11), bg="#0D1B2A", fg="#7F8C8D").pack(anchor="w", padx=30)
 
        cards_frame = tk.Frame(self.content, bg="#0D1B2A")
        cards_frame.pack(fill="x", padx=30, pady=25)
 
        if not self.user_id:
            return
 
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
 
            cursor.execute("SELECT COUNT(*) FROM loans WHERE user_id=%s AND status='borrowed'", (self.user_id,))
            loans_count = cursor.fetchone()[0]
 
            cursor.execute("SELECT COUNT(*) FROM loans WHERE user_id=%s", (self.user_id,))
            total_loans = cursor.fetchone()[0]
 
            cursor.execute("SELECT COALESCE(SUM(amount),0) FROM fines WHERE user_id=%s AND status IN ('unpaid','pending')", (self.user_id,))
            fines = float(cursor.fetchone()[0])
 
            cursor.execute("SELECT COUNT(*) FROM wishlist WHERE user_id=%s", (self.user_id,))
            wish_count = cursor.fetchone()[0]
 
            cursor.execute("SELECT COUNT(*) FROM notifications WHERE user_id=%s AND status='unread'", (self.user_id,))
            notif_count = cursor.fetchone()[0]
 
            cursor.execute("SELECT COUNT(*) FROM loan_requests WHERE user_id=%s AND status='pending'", (self.user_id,))
            pending_count = cursor.fetchone()[0]
 
        except Exception as e:
            print("Stats Error:", e)
            loans_count = total_loans = fines = wish_count = notif_count = pending_count = 0
        finally:
            if conn: conn.close()
 
        # ✅ Cards NON-CLICKABLE — sirf stats display
        stats = [
            ("📖", "Books With Me",  str(loans_count),    "#1E6FFF", "#0A2A6E"),
            ("📚", "Total Borrowed", str(total_loans),    "#2ECC71", "#0A3D1F"),
            ("⏳", "Pending Requests", str(pending_count), "#9B59B6", "#2E1050"),
            ("💸", "Pending Fines",  f"Rs. {fines:.2f}", "#E74C3C", "#4A0F0F"),
            ("⭐", "Wishlist Items", str(wish_count),     "#E1AD01", "#4A3500"),
            ("🔔", "Unread Alerts",  str(notif_count),    "#9B59B6", "#2E1050"),
        ]
 
        for icon, title, value, color, bg in stats:
            self._make_card(cards_frame, icon, title, value, color, bg)
 
        # ===== ROW 2 — LOAN STATUS CHART + RECENT ACTIVITY =====
        conn2 = None
        status_counts = {"borrowed": 0, "returned": 0, "overdue": 0, "pending": 0}
        recent_activity = []
        try:
            conn2 = get_connection()
            cur2 = conn2.cursor()
            cur2.execute("""SELECT status, due_date FROM loans WHERE user_id=%s""", (self.user_id,))
            for status, due_date in cur2.fetchall():
                if status == "borrowed":
                    if due_date and due_date < datetime.date.today():
                        status_counts["overdue"] += 1
                    else:
                        status_counts["borrowed"] += 1
                elif status == "returned":
                    status_counts["returned"] += 1
 
            cur2.execute("""SELECT COUNT(*) FROM loan_requests
                            WHERE user_id=%s AND status='pending'""", (self.user_id,))
            status_counts["pending"] = cur2.fetchone()[0]
 
            cur2.execute("""SELECT b.title, l.borrow_date, l.due_date, l.status
                            FROM loans l JOIN books b ON l.book_id=b.book_id
                            WHERE l.user_id=%s ORDER BY l.loan_id DESC LIMIT 6""", (self.user_id,))
            loan_rows = list(cur2.fetchall())
            today_chk = datetime.date.today()
            loan_rows = [
                (title, bdate, ddate, ("overdue" if status == "borrowed" and ddate and ddate < today_chk else status))
                for (title, bdate, ddate, status) in loan_rows
            ]
 
            cur2.execute("""SELECT b.title, lr.request_date, NULL, lr.status
                            FROM loan_requests lr JOIN books b ON lr.book_id=b.book_id
                            WHERE lr.user_id=%s AND lr.status='pending'
                            ORDER BY lr.request_id DESC LIMIT 6""", (self.user_id,))
            pending_rows = list(cur2.fetchall())
 
            combined = pending_rows + loan_rows
            combined.sort(key=lambda r: r[1] or datetime.date.min, reverse=True)
            recent_activity = combined[:6]
        except Exception as e:
            print("Home chart error:", e)
        finally:
            if conn2:
                conn2.close()
 
        row2 = tk.Frame(self.content, bg="#0D1B2A")
        row2.pack(fill="both", expand=True, padx=30, pady=(10, 20))
 
        left2 = tk.Frame(row2, bg="#0D1B2A", width=280)
        left2.pack(side="left", fill="y", padx=(0, 12))
        left2.pack_propagate(False)
        tk.Label(left2, text="📊 My Loan Status", font=("Helvetica", 12, "bold"),
                 bg="#0D1B2A", fg="white").pack(anchor="w", pady=(0, 6))
        chart_box = tk.Frame(left2, bg="#111D45", highlightthickness=1, highlightbackground="#1A2456")
        chart_box.pack(fill="both", expand=True)
        self._draw_donut_chart(chart_box, status_counts)
 
        right2 = tk.Frame(row2, bg="#0D1B2A")
        right2.pack(side="left", fill="both", expand=True)
        tk.Label(right2, text="📜 Recent Activity", font=("Helvetica", 12, "bold"),
                 bg="#0D1B2A", fg="white").pack(anchor="w", pady=(0, 6))
        table_box = tk.Frame(right2, bg="#111D45", highlightthickness=1, highlightbackground="#1A2456")
        table_box.pack(fill="both", expand=True)
        self._make_activity_table(table_box, recent_activity)
 
    # ================================================================
    # BOOKS SECTION — with Request to Borrow button
    # ================================================================
    def show_books(self):
        self.clear_content()
 
        tk.Label(self.content, text="📖 Browse Books",
                 font=("Helvetica", 20, "bold"),
                 bg="#0D1B2A", fg="white").pack(anchor="w", padx=30, pady=(25, 5))

         # ⭐ Recommended For You section (NEW)
        self.recommend_frame = tk.Frame(self.content, bg="#0D1B2A")
        self.recommend_frame.pack(fill="x", padx=30, pady=(5, 5))
        self._load_recommendations()

 
        top_frame = tk.Frame(self.content, bg="#0D1B2A")
        top_frame.pack(anchor="w", padx=30, pady=10, fill="x")
 
        search_frame = tk.Frame(top_frame, bg="#0D1B2A")
        search_frame.pack(side="left")
 
        tk.Label(search_frame, text="Search:", font=("Arial", 11),
                 bg="#0D1B2A", fg="#B0BEC5").pack(side="left")
 
        self.search_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.search_var,
                 font=("Arial", 11), width=28,
                 bg="#1A2456", fg="white", insertbackground="white",
                 bd=0, highlightthickness=1,
                 highlightbackground="#1E6FFF").pack(side="left", padx=10, ipady=5)
 
        tk.Button(search_frame, text="🔍 Search",
                  bg="#1E6FFF", fg="white", bd=0, cursor="hand2",
                  font=("Arial", 10, "bold"), padx=10,
                  command=self.search_books).pack(side="left")
 
        tk.Button(search_frame, text="↺ All Books",
                  bg="#2ECC71", fg="white", bd=0, cursor="hand2",
                  font=("Arial", 10, "bold"), padx=10,
                  command=self.load_all_books).pack(side="left", padx=5)
 
        # ✅ Request to Borrow button
        tk.Button(top_frame, text="📥 Request to Borrow",
                  bg="#E1AD01", fg="white", bd=0, cursor="hand2",
                  font=("Arial", 10, "bold"), padx=15, pady=6,
                  activebackground="#B8860B",
                  command=self.request_to_borrow_dialog).pack(side="right", padx=5)
 
        self.books_table_frame = tk.Frame(self.content, bg="#0D1B2A")
        self.books_table_frame.pack(fill="x", expand=False, padx=30, pady=10)
 
        self.load_all_books()
 
    def load_all_books(self):
        self._load_books_data()
 
    def search_books(self):
        self._load_books_data(search=self.search_var.get().strip())
 
    def _load_books_data(self, search=None):
        for w in self.books_table_frame.winfo_children():
            w.destroy()

        conn = None
        rows = []
        try:
            conn = get_connection()
            cursor = conn.cursor()
            if search:
                cursor.execute("""SELECT b.book_id, b.title, b.author, COALESCE(b.publisher,'—'),
                                  COALESCE(c.name,'—'), b.available_copies, b.quantity, b.cover_url
                                  FROM books b LEFT JOIN categories c ON b.category_id=c.category_id
                                  WHERE b.title LIKE %s OR b.author LIKE %s""",
                               (f"%{search}%", f"%{search}%"))
            else:
                cursor.execute("""SELECT b.book_id, b.title, b.author, COALESCE(b.publisher,'—'),
                                  COALESCE(c.name,'—'), b.available_copies, b.quantity, b.cover_url
                                  FROM books b LEFT JOIN categories c ON b.category_id=c.category_id
                                  ORDER BY b.book_id DESC""")
            rows = cursor.fetchall()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if conn:
                conn.close()

        if not rows:
            tk.Label(self.books_table_frame,
                     text=f"🔍 No books found for '{search}'" if search else "No books available.",
                     font=("Arial", 11), bg="#0D1B2A", fg="#7F8C8D").pack(pady=30)
            return

        cols = ("ID", "Title", "Author", "Publisher", "Category", "Available", "Total")
        row_count = max(1, min(len(rows), 20))
        self.book_cover_images = []  # reset cache each load
        tree = self._make_books_treeview(self.books_table_frame, cols, height=row_count)

        for row in rows:
            book_data = row[:7]   # everything except cover_url
            cover_url = row[7]
            tag = "avail" if row[5] > 0 else "unavail"
            photo = self._get_book_cover_image(cover_url)
            tree.insert("", "end", image=photo if photo else "", values=book_data, tags=(tag,))

        tree.tag_configure("avail",   background="#111D45", foreground="white")
        tree.tag_configure("unavail", background="#5A1A1A", foreground="white")

   
    # REQUEST TO BORROW DIALOG (creates a PENDING request — Librarian
   
    def request_to_borrow_dialog(self, preset_book_id=None):
        win = tk.Toplevel(self)
        win.title("Request to Borrow")
        win.geometry("400x220")
        win.configure(bg="#0D1B2A")
        win.grab_set()
 
        tk.Label(win, text="📥 Request to Borrow",
                 font=("Helvetica", 16, "bold"),
                 bg="#0D1B2A", fg="white").pack(pady=(20, 15))
 
        tk.Label(win, text="BOOK ID", font=("Arial", 9, "bold"),
                 bg="#0D1B2A", fg="#AAB7B8").pack(anchor="w", padx=30)
        book_id_entry = tk.Entry(win, font=("Arial", 11), width=35,
                                  bg="#1A2456", fg="white", insertbackground="white",
                                  bd=0, highlightthickness=1, highlightbackground="#1E6FFF")
        book_id_entry.pack(padx=30, pady=(2, 15), ipady=6)
        if preset_book_id:
            book_id_entry.insert(0, str(preset_book_id))

        
        def confirm_request():
            book_id = book_id_entry.get().strip()
            if not book_id:
                messagebox.showwarning("Empty", "Please enter a Book ID.", parent=win)
                return
 
            conn = None
            try:
                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute("""SELECT COALESCE(SUM(amount),0) FROM fines
                                  WHERE user_id=%s AND status IN ('unpaid','pending')""", (self.user_id,))
                unpaid_amount = float(cursor.fetchone()[0])
                if unpaid_amount > 0:
                    messagebox.showwarning("Unpaid Fine",
                        f"You have Rs. {unpaid_amount:.2f} in pending/unpaid fines. Please clear it before borrowing another book.",
                        parent=win)
                    return

                cursor.execute("""SELECT COUNT(*) FROM loans
                  WHERE user_id=%s AND status IN ('borrowed','return_pending')""", (self.user_id,))
                borrowed_count = cursor.fetchone()[0]
                cursor.execute("""SELECT COUNT(*) FROM loan_requests
                                  WHERE user_id=%s AND status='pending'""", (self.user_id,))
                pending_count = cursor.fetchone()[0]

                if (borrowed_count + pending_count) >= 3:
                    messagebox.showwarning("Limit Reached",
                        "You already have 3 books borrowed/requested. Please return a book or wait for a pending request before requesting another.",
                        parent=win)
                    return
 
                cursor.execute("SELECT available_copies, title FROM books WHERE book_id=%s", (book_id,))
                result = cursor.fetchone()
                if not result:
                    messagebox.showerror("Not Found", "Book ID not found!", parent=win)
                    return
                
                if result[0] <= 0:
                    add_wish = messagebox.askyesno(
                        "Not Available",
                        f"'{result[1]}' is currently not available.\n\nWould you like to add it to your wishlist?",
                        parent=win)

                    if add_wish:
                        cursor.execute("""SELECT wishlist_id FROM wishlist
                                          WHERE user_id=%s AND book_id=%s""",
                                       (self.user_id, book_id))
                        if cursor.fetchone():
                            messagebox.showinfo("Already in Wishlist",
                                                "This book is already in your wishlist.", parent=win)
                        else:
                            cursor.execute("""INSERT INTO wishlist (user_id, book_id, added_at)
                                              VALUES (%s, %s, NOW())""",
                                           (self.user_id, book_id))
                            conn.commit()
                            win.destroy()
                            messagebox.showinfo("Added",
                                                f"'{result[1]}' added to your wishlist!")
                            return
                    return
                cursor.execute("""SELECT loan_id FROM loans
                                  WHERE user_id=%s AND book_id=%s AND status IN ('borrowed','return_pending')""",
                               (self.user_id, book_id))
                if cursor.fetchone():
                    messagebox.showwarning("Already Borrowed",
                                           f"You already have '{result[1]}' borrowed. Please return it before requesting again.",
                                           parent=win)
                    return
 
                cursor.execute("""INSERT INTO loan_requests (user_id, book_id, request_date, status)
                                  VALUES (%s, %s, CURDATE(), 'pending')""",
                               (self.user_id, book_id))
                conn.commit()
 
                win.destroy()
                messagebox.showinfo("Requested",
                                    f"Request for '{result[1]}' sent! Waiting for Librarian approval.")
 
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)
            finally:
                if conn:
                    conn.close()
 
        tk.Button(win, text="✅ Send Request",
                  bg="#2ECC71", fg="white",
                  font=("Arial", 12, "bold"), bd=0,
                  cursor="hand2", width=22, pady=8,
                  command=confirm_request).pack(pady=5)


    
    # RECOMMENDED FOR YOUcategory-based recommendation)
  
    def _load_recommendations(self):
        for w in self.recommend_frame.winfo_children():
            w.destroy()

        if not hasattr(self, "rec_cover_images"):
            self.rec_cover_images = []
        self.rec_cover_images = []

        if not self.user_id:
            return

        conn = None
        rows = []
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # 1) Find categories user has interacted with (loans + wishlist)
            cursor.execute("""
                SELECT DISTINCT b.category_id
                FROM loans l JOIN books b ON l.book_id = b.book_id
                WHERE l.user_id = %s AND b.category_id IS NOT NULL
                UNION
                SELECT DISTINCT b.category_id
                FROM wishlist w JOIN books b ON w.book_id = b.book_id
                WHERE w.user_id = %s AND b.category_id IS NOT NULL
            """, (self.user_id, self.user_id))
            cat_rows = cursor.fetchall()
            category_ids = [r[0] for r in cat_rows]

            if category_ids:
                fmt = ",".join(["%s"] * len(category_ids))
                cursor.execute(f"""
                    SELECT b.book_id, b.title, b.cover_url
                    FROM books b
                    WHERE b.category_id IN ({fmt})
                      AND b.available_copies > 0
                      AND b.book_id NOT IN (
                          SELECT book_id FROM loans WHERE user_id=%s
                          UNION
                          SELECT book_id FROM wishlist WHERE user_id=%s
                      )
                    ORDER BY b.times_borrowed DESC
                    LIMIT 8
                """, (*category_ids, self.user_id, self.user_id))
                rows = cursor.fetchall()

            # Fallback: no history — show most popular available books
            if not rows:
                cursor.execute("""
                    SELECT book_id, title, cover_url
                    FROM books
                    WHERE available_copies > 0
                    ORDER BY times_borrowed DESC
                    LIMIT 8
                """)
                rows = cursor.fetchall()

        except Exception as e:
            print("Recommendation Error:", e)
        finally:
            if conn:
                conn.close()

        if not rows:
            return

        tk.Label(self.recommend_frame, text="⭐ Recommended For You",
                 font=("Helvetica", 13, "bold"),
                 bg="#0D1B2A", fg="#E1AD01").pack(anchor="w", pady=(0, 8))

        cards_row = tk.Frame(self.recommend_frame, bg="#0D1B2A")
        cards_row.pack(anchor="w")

        for book_id, title, cover_url in rows:
            card = tk.Frame(cards_row, bg="#111D45", width=100, height=170,
                            highlightthickness=1, highlightbackground="#1E6FFF",
                            cursor="hand2")
            card.pack(side="left", padx=6)
            card.pack_propagate(False)

            photo = self._get_book_cover_image(cover_url, size=(85, 110))
            img_lbl = tk.Label(card, image=photo, bg="#111D45")
            img_lbl.image = photo
            self.rec_cover_images.append(photo)
            img_lbl.pack(pady=(8, 4))

            short_title = title if len(title) <= 16 else title[:14] + "…"
            title_lbl = tk.Label(card, text=short_title, font=("Arial", 8, "bold"),
                                 bg="#111D45", fg="white", wraplength=90, justify="center")
            title_lbl.pack()

            for widget in (card, img_lbl, title_lbl):
                widget.bind("<Button-1>", lambda e, bid=book_id: self.request_to_borrow_dialog(preset_book_id=bid))

   
    # the shared _make_treeview used by Loans/Wishlist/Notifications/Fines)
    
    def _make_books_treeview(self, parent, columns, height=15):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Books.Treeview",
                        background="#111D45", foreground="white",
                        rowheight=60, fieldbackground="#111D45",
                        borderwidth=0, relief="flat",
                        bordercolor="#111D45", lightcolor="#111D45", darkcolor="#111D45",
                        font=("Arial", 10))
        style.configure("Books.Treeview.Heading",
                        background="#0A1628", foreground="#E1AD01",
                        font=("Arial", 10, "bold"), relief="flat",
                        bordercolor="#0A1628", lightcolor="#0A1628", darkcolor="#0A1628")
        style.map("Books.Treeview.Heading",
                  background=[("active", "#1A2456"), ("pressed", "#1E6FFF")],
                  foreground=[("active", "#E1AD01"), ("pressed", "white")])
        style.map("Books.Treeview",
                  background=[("selected", "#3A2E00")],
                  foreground=[("selected", "#E1AD01")])
        style.layout("Books.Treeview", [
            ("Books.Treeview.treearea", {"sticky": "nswe"})
        ])

        vsb = ttk.Scrollbar(parent, orient="vertical")
        hsb = ttk.Scrollbar(parent, orient="horizontal")

        tree = ttk.Treeview(parent, columns=columns, show="tree headings",
                            style="Books.Treeview", height=height,
                            yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)

        # Column #0 = cover image
        tree.heading("#0", text="Cover")
        tree.column("#0", width=55, anchor="center", stretch=False)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=130)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(fill="x", expand=False)

        return tree

    def _get_book_cover_image(self, cover_url, size=(40, 55)):
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
        
    
    # MY LOANS SECTION
    
    def show_loans(self):
        self.clear_content()
 
        tk.Label(self.content, text="📜 My Loans",
                 font=("Helvetica", 20, "bold"),
                 bg="#0D1B2A", fg="white").pack(anchor="w", padx=30, pady=(25, 10))
 
        btn_frame = tk.Frame(self.content, bg="#0D1B2A")
        btn_frame.pack(anchor="w", padx=30, pady=5)
 
        tk.Button(btn_frame, text="All",
                  bg="#1E6FFF", fg="white", bd=0, cursor="hand2",
                  font=("Arial", 10, "bold"), padx=12, pady=6,
                  command=lambda: self._load_my_loans()).pack(side="left", padx=3)
 
        tk.Button(btn_frame, text="Active (Borrowed)",
                  bg="#E1AD01", fg="white", bd=0, cursor="hand2",
                  font=("Arial", 10, "bold"), padx=12, pady=6,
                  command=lambda: self._load_my_loans("borrowed")).pack(side="left", padx=3)
 
        tk.Button(btn_frame, text="Pending",
                  bg="#9B59B6", fg="white", bd=0, cursor="hand2",
                  font=("Arial", 10, "bold"), padx=12, pady=6,
                  command=lambda: self._load_my_loans("pending")).pack(side="left", padx=3)
 
        tk.Button(btn_frame, text="Returned",
                  bg="#2ECC71", fg="white", bd=0, cursor="hand2",
                  font=("Arial", 10, "bold"), padx=12, pady=6,
                  command=lambda: self._load_my_loans("returned")).pack(side="left", padx=3)
 
        tk.Button(btn_frame, text="Request Return",
                  bg="#E74C3C", fg="white", bd=0, cursor="hand2",
                  font=("Arial", 10, "bold"), padx=12, pady=6,
                  command=lambda: self.return_selected_loan()).pack(side="left", padx=3)
 
        self.loans_frame = tk.Frame(self.content, bg="#0D1B2A")
        self.loans_frame.pack(fill="x", expand=False, padx=30, pady=5)

        action_frame = tk.Frame(self.content, bg="#0D1B2A")
        action_frame.pack(anchor="w", padx=30, pady=(10, 0))

        tk.Button(action_frame, text="📖 Read Selected Book",
                  bg="#9B59B6", fg="white", bd=0, cursor="hand2",
                  font=("Arial", 10, "bold"), padx=14, pady=6,
                  command=self._read_selected_book).pack(anchor="w")

        self._load_my_loans()
 
    def _load_my_loans(self, status_filter=None):
        for w in self.loans_frame.winfo_children():
            w.destroy()
 
        if not self.user_id:
            return
 
        conn = None
        rows = []
        try:
            conn = get_connection()
            cursor = conn.cursor()
 
            if status_filter == "pending":
                cursor.execute("""SELECT CONCAT('REQ-', lr.request_id), b.title,
                                  lr.request_date, '—', '—', lr.status, NULL
                                  FROM loan_requests lr JOIN books b ON lr.book_id=b.book_id
                                  WHERE lr.user_id=%s AND lr.status='pending'
                                  ORDER BY lr.request_id DESC""", (self.user_id,))
                rows = cursor.fetchall()
 
            elif status_filter in ("borrowed", "returned"):
                cursor.execute("""SELECT l.loan_id, b.title, l.borrow_date, l.due_date,
                                  COALESCE(l.return_date,'—'), l.status, b.preview_link
                                  FROM loans l JOIN books b ON l.book_id=b.book_id
                                  WHERE l.user_id=%s AND l.status=%s
                                  ORDER BY l.loan_id DESC""", (self.user_id, status_filter))
                rows = cursor.fetchall()
 
            else:
                # "All" — combine actual loans with pending requests
                cursor.execute("""SELECT l.loan_id, b.title, l.borrow_date, l.due_date,
                                  COALESCE(l.return_date,'—'), l.status, b.preview_link
                                  FROM loans l JOIN books b ON l.book_id=b.book_id
                                  WHERE l.user_id=%s ORDER BY l.loan_id DESC""", (self.user_id,))
                rows = list(cursor.fetchall())
 
                cursor.execute("""SELECT CONCAT('REQ-', lr.request_id), b.title,
                                  lr.request_date, '—', '—', lr.status, NULL
                                  FROM loan_requests lr JOIN books b ON lr.book_id=b.book_id
                                  WHERE lr.user_id=%s AND lr.status='pending'
                                  ORDER BY lr.request_id DESC""", (self.user_id,))
                rows = list(cursor.fetchall()) + rows
 
        except Exception as e:
            print("Loans Error:", e)
        finally:
            if conn:
                conn.close()
 
        if not rows:
            tk.Label(self.loans_frame, text="No loans found.",
                     font=("Arial", 11), bg="#0D1B2A", fg="#7F8C8D").pack(pady=30)
            return
 
        cols = ("Loan ID", "Book Title", "Borrow Date", "Due Date", "Return Date", "Status")
        row_count = max(1, len(rows))
        tree = self._make_treeview(self.loans_frame, cols, height=row_count)
        self.loans_tree = tree

        self.loan_preview_map = {}
        today = datetime.date.today()
        for row in rows:
            status, due_date = row[5], row[3]
            if status == "borrowed" and isinstance(due_date, datetime.date) and due_date < today:
                status = "overdue"
            display = list(row[:6])
            display[5] = status
            tag = status if status in ("borrowed", "returned", "pending", "overdue", "return_pending") else "returned"
            iid = tree.insert("", "end", values=display, tags=(tag,))
            self.loan_preview_map[iid] = row[6]
 
        tree.tag_configure("borrowed", foreground="#E1AD01")
        tree.tag_configure("returned", foreground="#2ECC71")
        tree.tag_configure("pending",  foreground="#9B59B6")
        tree.tag_configure("overdue",  foreground="#E74C3C")
        tree.tag_configure("return_pending", foreground="#F39C12")

    def _read_selected_book(self):
        if not hasattr(self, "loans_tree") or not self.loans_tree:
            return
        selected = self.loans_tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Please select a book to read.")
            return
        preview_link = self.loan_preview_map.get(selected[0])
        if not preview_link:
            messagebox.showinfo("Not Available", "No preview available for this book.")
            return
        webbrowser.open(preview_link)
    # ================================================================
    # RETURN A BORROWED BOOK (selected row in My Loans)
    # ================================================================
    def return_selected_loan(self):
        if not hasattr(self, "loans_frame"):
            return
        tree = None
        for w in self.loans_frame.winfo_children():
            if isinstance(w, ttk.Treeview):
                tree = w
                break
        if not tree:
            return
 
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Please select a loan to return.")
            return
 
        values = tree.item(selected[0])["values"]
        loan_id, status = values[0], values[5]
 
        if status not in ("borrowed", "overdue"):
            messagebox.showinfo("Not Active", "Only currently borrowed books can have a return requested.")
            return
 
        if not messagebox.askyesno("Confirm", "Request return for this book? The librarian will need to confirm it."):
            return
 
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""UPDATE loans SET status='return_pending' WHERE loan_id=%s""", (loan_id,))
            conn.commit()
            self._load_my_loans()
            messagebox.showinfo("Requested", "Return request sent! Waiting for librarian to confirm.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if conn:
                conn.close()
    # ================================================================
    # WISHLIST SECTION
    # ================================================================
    def show_wishlist(self):
        self.clear_content()
 
        tk.Label(self.content, text="⭐ My Wishlist",
                 font=("Helvetica", 20, "bold"),
                 bg="#0D1B2A", fg="white").pack(anchor="w", padx=30, pady=(25, 10))
 
        btn_frame = tk.Frame(self.content, bg="#0D1B2A")
        btn_frame.pack(anchor="w", padx=30, pady=5)
 
        tk.Button(btn_frame, text="🗑 Remove Selected",
                  bg="#E74C3C", fg="white", bd=0, cursor="hand2",
                  font=("Arial", 10, "bold"), padx=12, pady=6,
                  command=self.remove_wishlist).pack(side="left", padx=3)
 
        tk.Button(btn_frame, text="↺ Refresh",
                  bg="#1E6FFF", fg="white", bd=0, cursor="hand2",
                  font=("Arial", 10, "bold"), padx=12, pady=6,
                  command=self.show_wishlist).pack(side="left", padx=3)
 
        self.wishlist_frame = tk.Frame(self.content, bg="#0D1B2A")
        self.wishlist_frame.pack(fill="x", expand=False, padx=30, pady=5)
 
        if not self.user_id:
            return
 
        conn = None
        rows = []
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT w.wishlist_id, b.title, b.author,
                              b.available_copies, w.added_at
                              FROM wishlist w JOIN books b ON w.book_id=b.book_id
                              WHERE w.user_id=%s ORDER BY w.added_at DESC""",
                           (self.user_id,))
            rows = cursor.fetchall()
        except Exception as e:
            print("Wishlist Error:", e)
        finally:
            if conn:
                conn.close()
 
        if not rows:
            tk.Label(self.wishlist_frame, text="Your wishlist is empty.",
                     font=("Arial", 11), bg="#0D1B2A", fg="#7F8C8D").pack(pady=30)
            return
 
        cols = ("Wishlist ID", "Book Title", "Author", "Available Copies", "Added At")
        row_count = max(1, min(len(rows), 20))
        self.wishlist_tree = self._make_treeview(self.wishlist_frame, cols, height=row_count)
 
        for row in rows:
            tag = "avail" if row[3] > 0 else "unavail"
            self.wishlist_tree.insert("", "end", values=row, tags=(tag,))
 
        self.wishlist_tree.tag_configure("avail",   background="#0A2A1A", foreground="white")
        self.wishlist_tree.tag_configure("unavail", background="#2A0A0A", foreground="#E74C3C")
 
    def remove_wishlist(self):
        if not hasattr(self, "wishlist_tree"):
            return
        selected = self.wishlist_tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Please select an item to remove.")
            return
        wishlist_id = self.wishlist_tree.item(selected[0])["values"][0]
        if not messagebox.askyesno("Confirm", "Remove from wishlist?"):
            return
 
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM wishlist WHERE wishlist_id=%s", (wishlist_id,))
            conn.commit()
            self.show_wishlist()
            messagebox.showinfo("Removed", "Removed from wishlist!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if conn:
                conn.close()
 
    # ================================================================
    # NOTIFICATIONS SECTION
    # ================================================================
    def show_notifications(self):
        self.clear_content()
 
        tk.Label(self.content, text="🔔 Notifications",
                 font=("Helvetica", 20, "bold"),
                 bg="#0D1B2A", fg="white").pack(anchor="w", padx=30, pady=(25, 10))
 
        frame = tk.Frame(self.content, bg="#0D1B2A")
        frame.pack(fill="x", expand=False, padx=30, pady=5)
 
        if not self.user_id:
            return
 
        conn = None
        rows = []
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT notification_id, message, status, created_at
                              FROM notifications WHERE user_id=%s
                              ORDER BY created_at DESC""", (self.user_id,))
            rows = cursor.fetchall()
 
            cursor.execute("""UPDATE notifications SET status='read'
                              WHERE user_id=%s AND status='unread'""", (self.user_id,))
            conn.commit()
 
        except Exception as e:
            print("Notifications Error:", e)
        finally:
            if conn:
                conn.close()
 
        if not rows:
            tk.Label(frame, text="No notifications yet.",
                     font=("Arial", 11), bg="#0D1B2A", fg="#7F8C8D").pack(pady=30)
            return
 
        cols = ("ID", "Message", "Status", "Date")
        row_count = max(1, min(len(rows), 20))
        tree = self._make_treeview(frame, cols, height=row_count)
        tree.column("ID", width=50, anchor="center")
        tree.column("Message", width=500, anchor="w")
        tree.column("Status", width=90, anchor="center")
        tree.column("Date", width=150, anchor="center")
 
        for row in rows:
            tag = "unread" if row[2] == "unread" else "read"
            tree.insert("", "end", values=row, tags=(tag,))
 
        tree.tag_configure("unread", background="#111D45", foreground="#E1AD01")
        tree.tag_configure("read",   background="#111D45", foreground="#7F8C8D")
 
    # ================================================================
    # FINES SECTION
    # ================================================================
    def show_fines(self):
        self.clear_content()

        tk.Label(self.content, text="💸 My Fines",
                 font=("Helvetica", 20, "bold"),
                 bg="#0D1B2A", fg="white").pack(anchor="w", padx=30, pady=(25, 5))

        # ---- Auto-calculate fines for this user's overdue loans ----
        if self.user_id:
            conn_fc = None
            try:
                conn_fc = get_connection()
                cur_fc = conn_fc.cursor()

                fine_rate = 10.00
                cur_fc.execute("SELECT fine_per_day FROM settings WHERE setting_id=1")
                rate_row = cur_fc.fetchone()
                if rate_row:
                    fine_rate = rate_row[0]

                cur_fc.execute("""
                    INSERT INTO fines (loan_id, user_id, amount, status, created_at)
                    SELECT l.loan_id, l.user_id,
                           DATEDIFF(CURDATE(), l.due_date) * %s,
                           'unpaid', CURDATE()
                    FROM loans l
                    WHERE l.user_id = %s
                    AND l.status = 'borrowed'
                    AND l.due_date < CURDATE()
                    AND l.loan_id NOT IN (SELECT loan_id FROM fines)
                """, (fine_rate, self.user_id))

                cur_fc.execute("""
                    UPDATE fines f
                    JOIN loans l ON f.loan_id = l.loan_id
                    SET f.amount = DATEDIFF(CURDATE(), l.due_date) * %s
                    WHERE f.user_id = %s
                    AND f.status = 'unpaid'
                    AND l.due_date < CURDATE()
                """, (fine_rate, self.user_id))

                conn_fc.commit()
            except Exception as e:
                print("Fine auto-calc error:", e)
            finally:
                if conn_fc:
                    conn_fc.close()

        if self.user_id:
            conn = None
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COALESCE(SUM(amount),0) FROM fines WHERE user_id=%s AND status IN ('unpaid','pending')",
                               (self.user_id,))
                actual_fines = float(cursor.fetchone()[0])

                fine_rate = 10.00
                cursor.execute("SELECT fine_per_day FROM settings WHERE setting_id=1")
                rate_row = cursor.fetchone()
                if rate_row:
                    fine_rate = float(rate_row[0])

                cursor.execute("""SELECT due_date FROM loans
                                  WHERE user_id=%s AND status='borrowed' AND due_date < CURDATE()""",
                               (self.user_id,))
                overdue_due_dates = cursor.fetchall()
                live_estimate = sum(
                    (datetime.date.today() - d[0]).days * fine_rate
                    for d in overdue_due_dates if d[0]
                )

                total = actual_fines
                summary = tk.Frame(self.content, bg="#0D1B2A")
                summary.pack(anchor="w", padx=30, pady=5)
                self._make_card(summary, "💸", "Total Pending", f"Rs. {total:.2f}", "#E74C3C", "#4A0F0F")
            except:
                pass
            finally:
                if conn:
                    conn.close()

        frame = tk.Frame(self.content, bg="#0D1B2A")
        frame.pack(fill="x", expand=False, padx=30, pady=10)

        if not self.user_id:
            return

        conn = None
        rows = []
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT fine_id, loan_id, amount, status, created_at
                              FROM fines WHERE user_id=%s
                              ORDER BY created_at DESC""", (self.user_id,))
            rows = cursor.fetchall()
        except Exception as e:
            print("Fines Error:", e)
        finally:
            if conn:
                conn.close()

        if not rows:
            tk.Label(frame, text="No fines. You're all clear! 🎉",
                     font=("Arial", 11), bg="#0D1B2A", fg="#7F8C8D").pack(pady=30)
            return

        cols = ("Fine ID", "Loan ID", "Amount (Rs.)", "Status", "Date")
        row_count = max(1, min(len(rows), 20))
        tree = self._make_treeview(frame, cols, height=row_count)

        fine_row_map = {}
        for row in rows:
            if row[3] == "unpaid":
                tag = "unpaid"
            elif row[3] == "pending":
                tag = "pending"
            else:
                tag = "paid"
            iid = tree.insert("", "end", values=row, tags=(tag,))
            fine_row_map[iid] = row

        tree.tag_configure("unpaid", background="#4A0F0F", foreground="white")
        tree.tag_configure("pending", background="#2E1050", foreground="#9B59B6")
        tree.tag_configure("paid", background="#0A3D1F", foreground="white")

        def pay_selected_fine():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Select", "Please select a fine to pay.")
                return
            fine_id, loan_id, amount, status, date = fine_row_map[selected[0]]
            if status == "paid":
                messagebox.showinfo("Not Payable", "This fine is already paid.")
                return
            if status == "pending":
                messagebox.showinfo("Pending", "This fine is already submitted and awaiting admin verification.")
                return

            conn_chk = None
            try:
                conn_chk = get_connection()
                cur_chk = conn_chk.cursor()
                cur_chk.execute("SELECT status FROM loans WHERE loan_id=%s", (loan_id,))
                loan_row = cur_chk.fetchone()
            except Exception as e:
                messagebox.showerror("Error", str(e))
                return
            finally:
                if conn_chk:
                    conn_chk.close()

            if not loan_row or loan_row[0] != "returned":
                messagebox.showwarning("Return Book First",
                    "Please return the book before paying this fine.")
                return

            self._open_pay_fine_dialog(fine_id, amount)

        button_frame = tk.Frame(self.content, bg="#0D1B2A")
        button_frame.pack(anchor="w", padx=30, pady=(5, 10))

        tk.Button(button_frame, text="💳 Pay Selected Fine",
                  bg="#1E6FFF", fg="white", bd=0, cursor="hand2",
                  font=("Arial", 10, "bold"), padx=14, pady=6,
                  command=pay_selected_fine).pack(anchor="w")

    # ================================================================
    # PAY FINE — Manual Transfer Instructions (JazzCash / Easypaisa)
    # ================================================================
    def _open_pay_fine_dialog(self, fine_id, amount):
        win = tk.Toplevel(self)
        win.title("Pay Fine")
        win.geometry("380x420")
        win.configure(bg="#0D1B2A")
        win.grab_set()

        tk.Label(win, text="💳 Pay Fine",
                 font=("Helvetica", 16, "bold"),
                 bg="#0D1B2A", fg="white").pack(pady=(20, 5))
        tk.Label(win, text=f"Amount: Rs. {amount:.2f}",
                 font=("Arial", 12, "bold"),
                 bg="#0D1B2A", fg="#E1AD01").pack(pady=(0, 15))

        method_frame = tk.Frame(win, bg="#0D1B2A")
        method_frame.pack(pady=5)

        details_card = tk.Frame(win, bg="#111D45",
                                highlightthickness=1, highlightbackground="#1A2456")
        details_card.pack(fill="x", padx=25, pady=15)

        details_lbl = tk.Label(details_card, text="Select a payment method above",
                               font=("Arial", 10), bg="#111D45", fg="#7F8C8D",
                               wraplength=300, justify="left")
        details_lbl.pack(padx=15, pady=20)

        # ⚠️ Apna real JazzCash/Easypaisa number yahan daal dein
        payment_info = {
            "jazzcash": {"number": "0300-1234567", "title": "ReadHub App(JazzCash)"},
            "easypesa": {"number": "0300-1234567", "title": "ReadHub App(Easypaisa)"},
        }

        def show_details(method):
            info = payment_info[method]
            method_name = "JazzCash" if method == "jazzcash" else "Easypaisa"
            details_lbl.config(
                text=f"📱 {method_name}\n\nSend Rs. {amount:.2f} to:\n\n{info['number']}\n{info['title']}\n\nOpen your {method_name} app and transfer the exact amount, then confirm below.",
                fg="white")

        def open_and_show(method):
            show_details(method)
            urls = {
                "jazzcash": "https://www.jazzcash.com.pk/",
                "easypesa": "https://easypaisa.com.pk/",
            }
            webbrowser.open(urls[method])

        tk.Button(method_frame, text="📱 JazzCash",
                  bg="#E74C3C", fg="white", bd=0, cursor="hand2",
                  font=("Arial", 10, "bold"), padx=14, pady=8,
                  command=lambda: open_and_show("jazzcash")).pack(side="left", padx=8)

        tk.Button(method_frame, text="📱 Easypaisa",
                  bg="#2ECC71", fg="white", bd=0, cursor="hand2",
                  font=("Arial", 10, "bold"), padx=14, pady=8,
                  command=lambda: open_and_show("easypesa")).pack(side="left", padx=8)

        def mark_paid():
            if not messagebox.askyesno("Confirm", "Have you completed the payment?", parent=win):
                return
            conn = None
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("UPDATE fines SET status='pending' WHERE fine_id=%s", (fine_id,))
                conn.commit()
                win.destroy()
                messagebox.showinfo("Submitted", "Payment submitted! Waiting for admin verification.")
                self.show_fines()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)
            finally:
                if conn:
                    conn.close()

        tk.Button(win, text="✅ I've Paid",
                  bg="#E1AD01", fg="#0D1B2A",
                  font=("Arial", 11, "bold"), bd=0, cursor="hand2",
                  width=20, pady=8, command=mark_paid).pack(pady=15)
    # ================================================================
    # PROFILE SECTION
    # ================================================================
    def show_profile(self):
        self.clear_content()

        conn = None
        user = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""SELECT user_id, name, email, created_at,
                                  phone, address, profile_pic
                           FROM users WHERE user_id=%s""", (self.user_id,))
            user = cur.fetchone()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
        finally:
            if conn:
                conn.close()

        if not user:
            tk.Label(self.content, text="Profile not found.",
                     font=("Arial", 11), bg="#0D1B2A", fg="#7F8C8D").pack(pady=30)
            return

        uid, name, email, created_at, phone, address, profile_pic = user
        initial = name[0].upper() if name else "U"

        tk.Label(self.content, text="👤 My Profile",
                 font=("Helvetica", 20, "bold"),
                 bg="#0D1B2A", fg="white").pack(anchor="w", padx=30, pady=(25, 10))

        # ---- Profile Header ----
        header_card = tk.Frame(self.content, bg="#0D1B2A")
        header_card.pack(fill="x", padx=30, pady=(0, 15))

        center_col = tk.Frame(header_card, bg="#0D1B2A")
        center_col.pack(pady=15)

        avatar_size = 150
        avatar_frame = tk.Frame(center_col, bg="#0D1B2A", width=avatar_size, height=avatar_size,
                                highlightthickness=0, bd=0)
        avatar_frame.pack()
        avatar_frame.pack_propagate(False)

        self._profile_photo_ref = None

        if profile_pic:
            try:
                hi_res = avatar_size * 4
                img = Image.open(profile_pic).convert("RGBA").resize((hi_res, hi_res))
                mask = Image.new("L", (hi_res, hi_res), 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, hi_res, hi_res), fill=255)
                circular = Image.new("RGBA", (hi_res, hi_res))
                circular.paste(img, (0, 0), mask)
                circular = circular.resize((avatar_size, avatar_size), Image.LANCZOS)
                photo = ImageTk.PhotoImage(circular)
                self._profile_photo_ref = photo
                avatar_lbl = tk.Label(avatar_frame, image=photo, bg="#0D1B2A", bd=0, highlightthickness=0)
            except Exception as e:
                print("Avatar load error:", e, "| path tried:", profile_pic)
                avatar_lbl = tk.Label(avatar_frame, text=initial,
                                      font=("Helvetica", 26, "bold"),
                                      bg="#E1AD01", fg="#0D1B2A", bd=0, highlightthickness=0)
        else:
            avatar_lbl = tk.Label(avatar_frame, text=initial,
                                  font=("Helvetica", 26, "bold"),
                                  bg="#E1AD01", fg="#0D1B2A", bd=0, highlightthickness=0)
            
        avatar_lbl.place(relx=0.5, rely=0.5, anchor="center")

        edit_icon = tk.Label(avatar_frame, text="✏️", font=("Arial", 12),
                             bg="#0D1B2A", fg="white", cursor="hand2")
        edit_icon.place(relx=1.0, rely=1.0, anchor="se")
        edit_icon.bind("<Button-1>", lambda e, uid=uid: self._change_profile_photo(uid))

        # ---- Reading Stats Card ----
        conn3 = None
        total_books, fav_category = 0, "—"
        try:
            conn3 = get_connection()
            cur3 = conn3.cursor()
            cur3.execute("SELECT COUNT(*) FROM loans WHERE user_id=%s", (uid,))
            total_books = cur3.fetchone()[0]

            cur3.execute("""SELECT c.name, COUNT(*) as cnt
                            FROM loans l JOIN books b ON l.book_id=b.book_id
                            JOIN categories c ON b.category_id=c.category_id
                            WHERE l.user_id=%s
                            GROUP BY c.name ORDER BY cnt DESC LIMIT 1""", (uid,))
            fav_row = cur3.fetchone()
            if fav_row:
                fav_category = fav_row[0]
        except Exception as e:
            print("Stats error:", e)
        finally:
            if conn3:
                conn3.close()

        member_since = "—"
        if created_at:
            days = (datetime.date.today() - created_at.date()).days
            months = max(1, days // 30)
            member_since = f"{months} month{'s' if months != 1 else ''}"

        stats_card = tk.Frame(self.content, bg="#0D1B2A")
        stats_card.pack(fill="x", padx=30, pady=(0, 15))

        stats_row = tk.Frame(stats_card, bg="#0D1B2A")
        stats_row.pack(fill="x")

        stats = [
            ("📚", "Total Books Borrowed", str(total_books), "#1E6FFF", "#0A2A6E"),
            ("⭐", "Favorite Category", fav_category, "#E1AD01", "#4A3500"),
            ("🗓️", "Member For", member_since, "#2ECC71", "#0A3D1F"),
        ]
        for icon, title, value, color, bg in stats:
            card = tk.Frame(stats_row, bg=bg, width=180, height=110,
                            highlightthickness=2, highlightbackground=color)
            card.pack(side="left", padx=10)
            card.pack_propagate(False)
            tk.Label(card, text=icon, font=("Arial", 22), bg=bg, fg=color).pack(pady=(12, 2))
            tk.Label(card, text=value, font=("Helvetica", 16, "bold"), bg=bg, fg="white").pack()
            tk.Label(card, text=title, font=("Arial", 8), bg=bg, fg="#B0BEC5").pack(pady=(2, 0))

        if total_books >= 10:
            badge = tk.Frame(stats_card, bg="#4A3500",
                             highlightthickness=1, highlightbackground="#E1AD01")
            badge.pack(fill="x", pady=(10, 0))
            tk.Label(badge, text="📚 Bookworm — 10+ books borrowed!",
                     font=("Arial", 10, "bold"),
                     bg="#4A3500", fg="#E1AD01").pack(pady=8)

        # ---- Personal Information Card ----
        edit_icon.bind("<Button-1>", lambda e, uid=uid: self._change_profile_photo(uid))

        # ---- Personal Information Card ----
        info_card = tk.Frame(self.content, bg="#0D1B2A")
        info_card.pack(fill="x", padx=30, pady=(0, 20))

        info_header = tk.Frame(info_card, bg="#0D1B2A")
        info_header.pack(fill="x", padx=20, pady=(15, 10))

        tk.Label(info_header, text="Personal Information",
                 font=("Helvetica", 12, "bold"),
                 bg="#0D1B2A", fg="#E1AD01").pack(side="left")

        pencil_lbl = tk.Label(info_header, text="✏️", font=("Arial", 12),
                              bg="#0D1B2A", fg="#1E6FFF", cursor="hand2")
        pencil_lbl.pack(side="right")
        pencil_lbl.bind("<Button-1>",
                lambda e: self._edit_profile_dialog(uid, name, email, phone, address))

        all_fields = [
            ("Full Name", name),
            ("Email Address", email),
            ("Phone Number", phone or "—"),
            ("Address", address or "—"),
            ("Joined On", str(created_at)[:16] if created_at else "—"),
        ]
        for label, value in all_fields:
            row = tk.Frame(info_card, bg="#0D1B2A")
            row.pack(fill="x", padx=20, pady=6)
            tk.Label(row, text=label, font=("Arial", 8),
                     bg="#0D1B2A", fg="#7F8C8D").pack(anchor="w")
            tk.Label(row, text=value, font=("Arial", 10, "bold"),
                     bg="#0D1B2A", fg="white").pack(anchor="w", pady=(1, 0))
            tk.Frame(info_card, bg="#1A2456", height=1).pack(fill="x", padx=20, pady=(4, 0))

        tk.Frame(info_card, bg="#0D1B2A", height=10).pack()

        # ---- Borrowing History Card ----
        tk.Label(self.content, text="📖 Borrowing History",
                 font=("Helvetica", 14, "bold"),
                 bg="#0D1B2A", fg="white").pack(anchor="w", padx=30, pady=(10, 10))

        history_frame = tk.Frame(self.content, bg="#0D1B2A")
        history_frame.pack(fill="x", padx=30, pady=(0, 20))

        conn7 = None
        history_rows = []
        try:
            conn7 = get_connection()
            cur7 = conn7.cursor()
            cur7.execute("""SELECT b.title, l.borrow_date, l.due_date,
                            COALESCE(l.return_date, '—'), l.status
                           FROM loans l JOIN books b ON l.book_id=b.book_id
                           WHERE l.user_id=%s
                           ORDER BY l.loan_id DESC""", (uid,))
            history_rows = cur7.fetchall()
        except Exception as e:
            print("History error:", e)
        finally:
            if conn7:
                conn7.close()

        if not history_rows:
            tk.Label(history_frame, text="No borrowing history yet.",
                     font=("Arial", 10), bg="#0D1B2A", fg="#7F8C8D").pack(pady=20)
        else:
            cols = ("Book Title", "Borrow Date", "Due Date", "Return Date", "Status")
            row_count = max(1, min(len(history_rows), 20))
            hist_tree = self._make_treeview(history_frame, cols, height=row_count)
            for row in history_rows:
                tag = row[4] if row[4] in ("borrowed", "returned") else "returned"
                hist_tree.insert("", "end", values=row, tags=(tag,))
            hist_tree.tag_configure("borrowed", background="#0A2A6E", foreground="white")
            hist_tree.tag_configure("returned", background="#0A3D1F", foreground="white")

    # ================================================================
    # EDIT PROFILE DIALOG
    # ================================================================
    def _edit_profile_dialog(self, uid, current_name, current_email, current_phone, current_address):
        win = tk.Toplevel(self)
        win.title("Edit Profile")
        win.geometry("420x420")
        win.configure(bg="#0D1B2A")
        win.grab_set()

        tk.Label(win, text="✏️ Edit Profile",
                 font=("Helvetica", 16, "bold"),
                 bg="#0D1B2A", fg="white").pack(pady=(20, 15))

        fields = [
            ("Full Name *", "name", current_name),
            ("Email *", "email", current_email),
            ("Phone", "phone", current_phone or ""),
            ("Address", "address", current_address or ""),
        ]
        entries = {}
        for lbl, key, default in fields:
            tk.Label(win, text=lbl, font=("Arial", 9, "bold"),
                     bg="#0D1B2A", fg="#AAB7B8").pack(anchor="w", padx=30)
            e = tk.Entry(win, font=("Arial", 11), width=32,
                        bg="#1A2456", fg="white", insertbackground="white",
                        bd=0, highlightthickness=1, highlightbackground="#1E6FFF")
            e.insert(0, default)
            e.pack(padx=30, pady=(2, 10), ipady=5)
            entries[key] = e

        def save():
            new_name = entries["name"].get().strip()
            new_email = entries["email"].get().strip()
            new_phone = entries["phone"].get().strip() or None
            new_address = entries["address"].get().strip() or None
            if not new_name or not new_email:
                messagebox.showwarning("Empty", "Name and Email cannot be empty!", parent=win)
                return

            conn = None
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""UPDATE users
                              SET name=%s, email=%s, phone=%s, address=%s
                              WHERE user_id=%s""",
                           (new_name, new_email, new_phone, new_address, uid))
                conn.commit()
                win.destroy()
                messagebox.showinfo("Success", "Profile updated!")
                self.user_name = new_name
                self.welcome_lbl.config(text=f"👋 Hi, {new_name}!")
                self.show_profile()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)
            finally:
                if conn:
                    conn.close()

        tk.Button(win, text="💾 Save Changes",
                  bg="#2ECC71", fg="white",
                  font=("Arial", 12, "bold"), bd=0, cursor="hand2",
                  width=22, pady=8, command=save).pack(pady=10)

    # ================================================================
    # CHANGE PROFILE PHOTO
    # ================================================================
    def _change_profile_photo(self, uid):
        import os
        import shutil

        file_path = filedialog.askopenfilename(
            title="Select Profile Photo",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if not file_path:
            return

        folder = "profile_pics"
        try:
            os.makedirs(folder, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Folder Error", f"Could not create folder: {e}")
            return

        ext = os.path.splitext(file_path)[1]
        new_filename = f"user_{uid}{ext}"
        new_path = os.path.join(folder, new_filename)

        try:
            shutil.copy(file_path, new_path)
        except Exception as e:
            messagebox.showerror("Copy Error", f"Could not save photo: {e}")
            return

        if not os.path.exists(new_path):
            messagebox.showerror("Error", "File copy failed silently — file not found after copy.")
            return

        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE users SET profile_pic=%s WHERE user_id=%s",
                       (new_path.replace("\\", "/"), uid))
            conn.commit()
            messagebox.showinfo("Success", f"Profile photo updated!\nSaved at: {new_path}")
            self.show_profile()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
        finally:
            if conn:
                conn.close()

    # ================================================================
    # SETTINGS SECTION — Change Password
    # ================================================================
    def show_settings(self):
        self.clear_content()

        tk.Label(self.content, text="⚙️ Settings",
                 font=("Helvetica", 20, "bold"),
                 bg="#0D1B2A", fg="white").pack(anchor="w", padx=30, pady=(25, 10))

        # ---- Change Password Card ----
        pwd_card = tk.Frame(self.content, bg="#111D45",
                            highlightthickness=1, highlightbackground="#1E6FFF")
        pwd_card.pack(fill="x", padx=30, pady=(0, 15))

        tk.Label(pwd_card, text="🔒 Change Password",
                 font=("Helvetica", 12, "bold"),
                 bg="#111D45", fg="#E1AD01").pack(anchor="w", padx=20, pady=(15, 10))

        pwd_row = tk.Frame(pwd_card, bg="#111D45")
        pwd_row.pack(fill="x", padx=20, pady=(0, 20))

        pwd_entries = {}
        for lbl, key in [("Current Password", "current_pwd"), ("New Password", "new_pwd"), ("Confirm Password", "confirm_pwd")]:
            col = tk.Frame(pwd_row, bg="#111D45")
            col.pack(side="left", padx=(0, 15))
            tk.Label(col, text=lbl, font=("Arial", 8),
                     bg="#111D45", fg="#7F8C8D").pack(anchor="w")
            e = tk.Entry(col, font=("Arial", 10), width=18, show="*",
                        bg="#1A2456", fg="white", insertbackground="white",
                        bd=0, highlightthickness=1, highlightbackground="#1E6FFF")
            e.pack(pady=(2, 0), ipady=5)
            pwd_entries[key] = e

        def update_password():
            current_pwd = pwd_entries["current_pwd"].get().strip()
            new_pwd = pwd_entries["new_pwd"].get().strip()
            confirm_pwd = pwd_entries["confirm_pwd"].get().strip()

            if not current_pwd or not new_pwd or not confirm_pwd:
                messagebox.showwarning("Empty", "Please fill all password fields.")
                return
            if new_pwd != confirm_pwd:
                messagebox.showerror("Mismatch", "Passwords do not match.")
                return
            if len(new_pwd) < 6:
                messagebox.showwarning("Weak Password", "Password must be at least 6 characters.")
                return

            conn2 = None
            try:
                conn2 = get_connection()
                cur2 = conn2.cursor()

                cur2.execute("SELECT password FROM users WHERE user_id=%s", (self.user_id,))
                row = cur2.fetchone()
                if not row or not bcrypt.checkpw(current_pwd.encode(), row[0].encode()):
                    messagebox.showerror("Incorrect", "Current password is incorrect.")
                    return

                hashed_pwd = bcrypt.hashpw(new_pwd.encode(), bcrypt.gensalt()).decode()
                cur2.execute("UPDATE users SET password=%s WHERE user_id=%s",
                            (hashed_pwd, self.user_id))
                conn2.commit()
                messagebox.showinfo("Success", "Password updated successfully!")
                pwd_entries["current_pwd"].delete(0, "end")
                pwd_entries["new_pwd"].delete(0, "end")
                pwd_entries["confirm_pwd"].delete(0, "end")
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                if conn2:
                    conn2.close()

        tk.Button(pwd_card, text="🔒 Update Password",
                  bg="#E1AD01", fg="#0D1B2A",
                  font=("Arial", 10, "bold"), bd=0, cursor="hand2",
                  padx=14, pady=6, command=update_password
                  ).pack(anchor="w", padx=20, pady=(0, 20))

        # ---- About Card ----
        about_card = tk.Frame(self.content, bg="#111D45",
                              highlightthickness=1, highlightbackground="#1A2456")
        about_card.pack(fill="x", padx=30, pady=(0, 20))

        tk.Label(about_card, text="ℹ️ About ReadHub",
                 font=("Helvetica", 12, "bold"),
                 bg="#111D45", fg="#E1AD01").pack(anchor="w", padx=20, pady=(15, 10))

        about_info = [
            ("Application", "ReadHub — Library Management System"),
            ("Version", "1.0.0"),
            ("Role", "Member"),
        ]
        for label, value in about_info:
            row = tk.Frame(about_card, bg="#111D45")
            row.pack(fill="x", padx=20, pady=3)
            tk.Label(row, text=label + ":", font=("Arial", 9, "bold"),
                     bg="#111D45", fg="#7F8C8D", width=15, anchor="w").pack(side="left")
            tk.Label(row, text=value, font=("Arial", 9),
                     bg="#111D45", fg="white", anchor="w").pack(side="left")

        tk.Frame(about_card, bg="#111D45", height=15).pack()    
 
    # ================================================================
    # HELPER: NON-CLICKABLE Card
    # ================================================================
    def _make_card(self, parent, icon, title, value, color, bg):
        card = tk.Frame(parent, bg=bg, padx=20, pady=20,
                        highlightthickness=2, highlightbackground=color,
                        cursor="arrow")  # ✅ non-clickable
        card.pack(side="left", padx=10, expand=True, fill="both")
 
        tk.Label(card, text=icon,  font=("Arial", 28),            bg=bg, fg=color).pack()
        tk.Label(card, text=value, font=("Helvetica", 22, "bold"), bg=bg, fg="white").pack(pady=5)
        tk.Label(card, text=title, font=("Arial", 9),              bg=bg, fg="#B0BEC5").pack()
 
    # ================================================================
    # HELPER: DONUT CHART — Loan Status Breakdown
    # ================================================================
    def _draw_donut_chart(self, parent, status_counts):
        total = sum(status_counts.values()) or 1
        canvas = tk.Canvas(parent, bg="#111D45", highlightthickness=0, height=220)
        canvas.pack(fill="both", expand=True, padx=6, pady=8)
        colors = {"borrowed": "#E1AD01", "returned": "#2ECC71", "overdue": "#E74C3C", "pending": "#9B59B6"}
 
        def _draw(event=None):
            canvas.delete("all")
            cw = canvas.winfo_width() or 260
            ch = canvas.winfo_height() or 220
            cx, cy = cw // 2, ch // 2
            r = min(cw, ch) // 2 - 20
 
            start = 90
            for status, color in colors.items():
                val = status_counts.get(status, 0)
                if val == 0:
                    continue
                extent = -(val / total) * 360
                if abs(extent) >= 359.99:
                    extent = -359.99  # Tkinter draws nothing for an exact 360° arc
                canvas.create_arc(cx - r, cy - r, cx + r, cy + r,
                                   start=start, extent=extent,
                                   fill=color, outline="#111D45", width=3)
                start += extent
 
            hole_r = int(r * 0.55)
            canvas.create_oval(cx - hole_r, cy - hole_r,
                                cx + hole_r, cy + hole_r,
                                fill="#111D45", outline="")
 
            active_pct = int((status_counts.get("borrowed", 0) / total) * 100)
            canvas.create_text(cx, cy - 8, text=f"{active_pct}%",
                                fill="white", font=("Helvetica", 16, "bold"))
            canvas.create_text(cx, cy + 12, text="Active",
                                fill="#B0BEC5", font=("Arial", 8))
 
        canvas.bind("<Configure>", _draw)
        canvas.after(80, _draw)
 
        legend = tk.Frame(parent, bg="#111D45")
        legend.pack(fill="x", padx=10, pady=(0, 10))
        labels = {"borrowed": "Borrowed", "returned": "Returned", "overdue": "Overdue", "pending": "Pending"}
        for status, color in colors.items():
            row = tk.Frame(legend, bg="#111D45")
            row.pack(fill="x", pady=2)
            tk.Label(row, text="●", fg=color, bg="#111D45", font=("Arial", 10)).pack(side="left")
            tk.Label(row, text=f"{labels[status]}: {status_counts.get(status, 0)}",
                     fg="#B0BEC5", bg="#111D45", font=("Arial", 8)).pack(side="left", padx=4)
 
    # ================================================================
    # HELPER: Recent Activity Table (no scrollbars, compact)
    # ================================================================
    def _make_activity_table(self, parent, rows):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Activity.Treeview",
                        background="#111D45", foreground="white",
                        rowheight=28, fieldbackground="#111D45",
                        borderwidth=0, relief="flat",
                        bordercolor="#111D45", lightcolor="#111D45", darkcolor="#111D45",
                        font=("Arial", 9))
        style.configure("Activity.Treeview.Heading",
                        background="#0A1628", foreground="#E1AD01",
                        font=("Arial", 9, "bold"), relief="flat",
                        bordercolor="#0A1628", lightcolor="#0A1628", darkcolor="#0A1628")
        style.map("Activity.Treeview",
                  background=[("selected", "#3A2E00")],
                  foreground=[("selected", "#E1AD01")])
        style.layout("Activity.Treeview", [
            ("Activity.Treeview.treearea", {"sticky": "nswe"})
        ])
 
        cols = ("Book", "Borrow Date", "Due Date", "Status")
        row_count = max(1, min(len(rows), 20))
        tree = ttk.Treeview(parent, columns=cols, show="headings",
                             height=row_count, style="Activity.Treeview")
 
        tree.column("Book", width=160, anchor="w")
        tree.column("Borrow Date", width=90, anchor="center")
        tree.column("Due Date", width=90, anchor="center")
        tree.column("Status", width=80, anchor="center")
        for col in cols:
            tree.heading(col, text=col)
 
        tree.tag_configure("borrowed", foreground="#E1AD01")
        tree.tag_configure("returned", foreground="#2ECC71")
        tree.tag_configure("overdue", foreground="#E74C3C")
        tree.tag_configure("pending", foreground="#9B59B6")
 
        if not rows:
            tk.Label(parent, text="No activity yet", font=("Arial", 9),
                     bg="#111D45", fg="#7F8C8D").pack(pady=20)
            return tree
 
        for row in rows:
            status = row[3]
            tag = status if status in ("borrowed", "returned", "overdue", "pending") else "returned"
            display = list(row)
            if display[2] is None:
                display[2] = "—"
            tree.insert("", "end", values=display, tags=(tag,))
 
        tree.pack(fill="both", expand=False, padx=1, pady=1)
        return tree
 
    # ================================================================
    # HELPER: Treeview with Scrollbar
    # ================================================================
    def _make_treeview(self, parent, columns, height=15):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview",
                        background="#111D45", foreground="white",
                        rowheight=30, fieldbackground="#111D45",
                        borderwidth=0, relief="flat",
                        bordercolor="#111D45", lightcolor="#111D45", darkcolor="#111D45",
                        font=("Arial", 10))
        style.configure("Custom.Treeview.Heading",
                        background="#0A1628", foreground="#E1AD01",
                        font=("Arial", 10, "bold"), relief="flat",
                        bordercolor="#0A1628", lightcolor="#0A1628", darkcolor="#0A1628")
        style.map("Custom.Treeview.Heading",
                  background=[("active", "#1A2456"), ("pressed", "#1E6FFF")],
                  foreground=[("active", "#E1AD01"), ("pressed", "white")])
        style.map("Custom.Treeview",
                  background=[("selected", "#3A2E00")],
                  foreground=[("selected", "#E1AD01")])
        style.layout("Custom.Treeview", [
            ("Custom.Treeview.treearea", {"sticky": "nswe"})
        ])
        
        vsb = ttk.Scrollbar(parent, orient="vertical")
        hsb = ttk.Scrollbar(parent, orient="horizontal")
 
        tree = ttk.Treeview(parent, columns=columns, show="headings",
                            style="Custom.Treeview", height=height,
                            yscrollcommand=vsb.set, xscrollcommand=hsb.set)
 
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)
 
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=130)
 
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(fill="x", expand=False)
 
        return tree
    
    # ================================================================
    # LOGOUT & SESSION
    # ================================================================
    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.controller.show_frame("HomePage")
 
    def _generate_loan_alerts(self):
        if not self.user_id:
            return
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""SELECT b.title, l.due_date
                           FROM loans l JOIN books b ON l.book_id=b.book_id
                           WHERE l.user_id=%s AND l.status='borrowed'""", (self.user_id,))
            loans = cur.fetchall()

            today = datetime.date.today()
            for title, due_date in loans:
                if not due_date:
                    continue
                days_left = (due_date - today).days

                if days_left in (1, 2):
                    msg = f"Reminder: '{title}' is due in {days_left} day(s) on {due_date}."
                elif days_left == 0:
                    msg = f"'{title}' is due today!"
                elif days_left < 0:
                    msg = f"'{title}' is overdue! Please return it as soon as possible."
                else:
                    continue

                cur.execute("""SELECT notification_id FROM notifications
                               WHERE user_id=%s AND message=%s""", (self.user_id, msg))
                if not cur.fetchone():
                    cur.execute("""INSERT INTO notifications (user_id, message, status, created_at)
                                   VALUES (%s, %s, 'unread', NOW())""", (self.user_id, msg))

            conn.commit()
        except Exception as e:
            print("Loan alert error:", e)
        finally:
            if conn:
                conn.close()

    def update_session(self, user_id=None, user_name="User", **kwargs):
        self.user_id = user_id
        self.user_name = user_name
        self.welcome_lbl.config(text=f"👋 Hi, {user_name}!")
        self._generate_loan_alerts()
        self.show_home()
