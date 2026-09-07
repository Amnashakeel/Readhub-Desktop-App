import tkinter as tk
import datetime
import bcrypt
import subprocess
from PIL import Image, ImageTk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk, ImageDraw
from tkinter import filedialog
from book_module import BookModule
from categories_module import CategoryModule
from db import get_connection

 
class LibrarianDashboard(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#0D1B2A")
        self.controller = controller
        self.librarian_id = None
        self.librarian_name = "Librarian"
        self.build_ui()
 
    # ================================================================
    # BUILD UI — Sidebar + Content Area
    # ================================================================
    def build_ui(self):
        # ---- SIDEBAR ----
        self.sidebar = tk.Frame(self, bg="#06090F", width=230)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
 
        tk.Label(self.sidebar, text="📚 ReadHub",
                 font=("Helvetica", 15, "bold"),
                 bg="#06090F", fg="#1E6FFF").pack(pady=(25, 5))
 
        tk.Frame(self.sidebar, bg="#1A2456", height=1).pack(fill="x", padx=15, pady=5)
 
        self.librarian_lbl = tk.Label(self.sidebar, text="🔑Librarian",
                                   font=("Arial", 11, "bold"),
                                   bg="#06090F", fg="#E1AD01")
        self.librarian_lbl.pack(pady=(5, 20))
 
        menu_items = [
            ("🏠  Dashboard",     self.show_home),
            ("📚  Manage Books",  self.show_books),
            ("📂  Categories",    self.show_categories),
            ("👥  Manage Users",  self.show_users),
            ("⏳  Pending Requests", self.show_pending_requests),
            ("📜  View Loans",    self.show_loans),
            ("💸  Fines",         self.show_fines),
            ("🔔  Notifications", self.show_notifications),
            ("📊  Reports",       self.show_reports),
            ("👤  Profile",       self.show_profile),
            ("⚙️  Settings",      self.show_settings),
        ]
 
        for text, cmd in menu_items:
            btn = tk.Button(self.sidebar, text=text,
                            bg="#06090F", fg="#B0BEC5",
                            font=("Arial", 11), bd=0,
                            cursor="hand2", anchor="w",
                            padx=20, pady=12,
                            activebackground="#1E2A4A",
                            activeforeground="white",
                            command=cmd)
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#1E2A4A", fg="white"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#06090F", fg="#B0BEC5"))
 
        tk.Frame(self.sidebar, bg="#06090F").pack(expand=True, fill="both")
        tk.Frame(self.sidebar, bg="#1A2456", height=1).pack(fill="x", padx=15, pady=5)
 
        tk.Button(self.sidebar, text="🚪  Logout",
                  bg="#E74C3C", fg="white",
                  font=("Arial", 11, "bold"), bd=0,
                  cursor="hand2", anchor="w",
                  padx=20, pady=12,
                  activebackground="#C0392B",
                  command=self.logout).pack(fill="x", pady=10)
 
        # ---- MAIN CONTENT ----
        self.content = tk.Frame(self, bg="#0D1B2A")
        self.content.pack(side="right", fill="both", expand=True)
 
        self.show_home()
 
    # ================================================================
    # SCROLL HELPER
    # ================================================================
    def _make_scroll_area(self):
        for widget in self.content.winfo_children():
            widget.destroy()
 
        canvas = tk.Canvas(self.content, bg="#0D1B2A", highlightthickness=0)
        vsb = ttk.Scrollbar(self.content, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
 
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
 
        scroll_frame = tk.Frame(canvas, bg="#0D1B2A")
        window_id = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
 
        def _on_canvas_resize(event):
            canvas.itemconfig(window_id, width=event.width)
        canvas.bind("<Configure>", _on_canvas_resize)
 
        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scroll_frame.bind("<Configure>", _on_frame_configure)
 
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
 
        return scroll_frame
 
    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()
 
    # ================================================================
    # HOME - DASHBOARD
    # ================================================================
    def show_home(self):
        main = self._make_scroll_area()
 
        # ===== FETCH ALL DATA FROM DB =====
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
 
            # Total books
            cursor.execute("SELECT COUNT(*) FROM books")
            total_books = cursor.fetchone()[0]
 
            # Available copies
            cursor.execute("SELECT COALESCE(SUM(available_copies),0) FROM books")
            avail_books = cursor.fetchone()[0]
 
            # Total members (students)
            cursor.execute("SELECT COUNT(*) FROM users WHERE role='student'")
            total_members = cursor.fetchone()[0]
 
            # Active loans (currently borrowed)
            cursor.execute("SELECT COUNT(*) FROM loans WHERE status='borrowed'")
            active_loans = cursor.fetchone()[0]
 
            # Overdue books
            cursor.execute("""SELECT COUNT(*) FROM loans
                              WHERE due_date < CURDATE() AND status='borrowed'""")
            overdue_books = cursor.fetchone()[0]
 
            # Monthly circulation (issued this month)
            cursor.execute("""SELECT COUNT(*) FROM loans
                              WHERE MONTH(borrow_date)=MONTH(CURDATE())
                              AND YEAR(borrow_date)=YEAR(CURDATE())""")
            monthly = cursor.fetchone()[0]
 
            # Returns THIS month only
            cursor.execute("""SELECT COUNT(*) FROM loans
                              WHERE status='returned'
                              AND return_date IS NOT NULL
                              AND MONTH(return_date)=MONTH(CURDATE())
                              AND YEAR(return_date)=YEAR(CURDATE())""")
            returned = cursor.fetchone()[0]
 
            # Average books per member
            cursor.execute("""SELECT ROUND(AVG(loan_count),1)
                              FROM (SELECT COUNT(*) as loan_count
                                    FROM loans GROUP BY user_id) t""")
            avg_books = cursor.fetchone()[0] or 0
 
            # Out of stock books
            cursor.execute("SELECT COUNT(*) FROM books WHERE available_copies=0")
            out_of_stock = cursor.fetchone()[0]
 
            # Unpaid fines count
            cursor.execute("SELECT COUNT(*) FROM fines WHERE status='unpaid'")
            unpaid_fines = cursor.fetchone()[0]
 
            # New members this month
            cursor.execute("""SELECT COUNT(*) FROM users
                              WHERE MONTH(created_at)=MONTH(CURDATE())
                              AND YEAR(created_at)=YEAR(CURDATE())""")
            new_members = cursor.fetchone()[0]
 
            # Recent 6 loans
            cursor.execute("""SELECT l.loan_id, u.name, b.title,
                                     l.borrow_date, l.due_date, l.status
                              FROM loans l
                              JOIN users u ON l.user_id=u.user_id
                              JOIN books b ON l.book_id=b.book_id
                              ORDER BY l.loan_id DESC LIMIT 6""")
            recent_loans = cursor.fetchall()
 
            # Top 4 active members
            cursor.execute("""SELECT u.name, u.user_id, COUNT(l.loan_id) as cnt
                              FROM users u
                              JOIN loans l ON u.user_id=l.user_id
                              GROUP BY u.user_id, u.name
                              ORDER BY cnt DESC LIMIT 4""")
            top_members = cursor.fetchall()
 
            # Book categories with counts
            cursor.execute("""SELECT COALESCE(c.name,'Uncategorized'), COUNT(b.book_id)
                              FROM books b
                              LEFT JOIN categories c ON b.category_id=c.category_id
                              GROUP BY c.category_id, c.name
                              ORDER BY COUNT(b.book_id) DESC""")
            categories = cursor.fetchall()
 
        except Exception as e:
            print(f"DB Error: {e}")
            total_books = avail_books = total_members = active_loans = overdue_books = 0
            monthly = returned = avg_books = out_of_stock = unpaid_fines = new_members = 0
            recent_loans = []
            top_members = []
            categories = []
        finally:
            if conn:
                conn.close()
 
        # ===== HEADER =====
        header = tk.Frame(main, bg="#0D1B2A")
        header.pack(fill="x", padx=25, pady=(20, 5))
 
        tk.Label(header, text="Librarian Dashboard",
                 font=("Helvetica", 20, "bold"),
                 bg="#0D1B2A", fg="white").pack(side="left")
 
        # ===== ROW 1 — STAT CARDS =====
        cards_row = tk.Frame(main, bg="#0D1B2A")
        cards_row.pack(fill="x", padx=25, pady=(12, 8))
 
        stat_data = [
            ("📚", "Total Books",   str(total_books),   "#1E6FFF", "#0A2A6E"),
            ("📗", "Available",     str(avail_books),   "#2ECC71", "#0A3D1F"),
            ("👥", "Total Members", str(total_members), "#9B59B6", "#2E1050"),
            ("📖", "Active Loans",  str(active_loans),  "#E1AD01", "#4A3500"),
            ("⚠️", "Overdue",       str(overdue_books), "#E74C3C", "#4A0F0F"),
        ]
 
        for icon, title, value, color, bg_color in stat_data:
            card = tk.Frame(cards_row, bg=bg_color, padx=12, pady=14,
                            highlightthickness=2, highlightbackground=color)
            card.pack(side="left", padx=5, expand=True, fill="both")
            tk.Label(card, text=icon,  font=("Arial", 20),            bg=bg_color, fg=color).pack()
            tk.Label(card, text=value, font=("Helvetica", 17, "bold"), bg=bg_color, fg="white").pack(pady=3)
            tk.Label(card, text=title, font=("Arial", 8),              bg=bg_color, fg="#B0BEC5").pack()
 
        # ===== ROW 2 — TRANSACTIONS (left) + CATEGORIES CHART (right) =====
        row2 = tk.Frame(main, bg="#0D1B2A")
        row2.pack(fill="x", padx=25, pady=(8, 8))
 
        # -- LEFT: Recent Transactions --
        left2 = tk.Frame(row2, bg="#0D1B2A")
        left2.pack(side="left", fill="both", expand=True)
 
        hdr2l = tk.Frame(left2, bg="#0D1B2A")
        hdr2l.pack(fill="x", pady=(0, 6))
        tk.Label(hdr2l, text="📜 Recent Transactions",
                 font=("Helvetica", 11, "bold"),
                 bg="#0D1B2A", fg="white").pack(side="left")
        tk.Button(hdr2l, text="View All",
                  font=("Arial", 8), bg="#1E6FFF", fg="white",
                  bd=0, padx=8, pady=3, cursor="hand2",
                  command=self.show_loans).pack(side="right")
 
        trans_wrap = tk.Frame(left2, bg="#111D45",
                              highlightthickness=1, highlightbackground="#1A2456")
        trans_wrap.pack(fill="x")
 
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Trans.Treeview",
                        background="#111D45", foreground="white",
                        rowheight=26, fieldbackground="#111D45",
                        borderwidth=0, relief="flat",
                        bordercolor="#111D45", lightcolor="#111D45", darkcolor="#111D45",
                        font=("Arial", 8))
        style.configure("Trans.Treeview.Heading",
                        background="#0A1628", foreground="#E1AD01",
                        font=("Arial", 8, "bold"), relief="flat",
                        bordercolor="#0A1628", lightcolor="#0A1628", darkcolor="#0A1628")
        style.map("Trans.Treeview", background=[("selected", "#1E6FFF")])
        style.layout("Trans.Treeview", [
            ("Trans.Treeview.treearea", {"sticky": "nswe"})
        ])
 
        trans_cols = ("ID", "User", "Book", "Borrow Date", "Due Date", "Status")
        trans_tree = ttk.Treeview(trans_wrap, columns=trans_cols,
                                  show="headings", height=6,
                                  style="Trans.Treeview")
        trans_tree.column("ID",          width=35,  anchor="center")
        trans_tree.column("User",        width=90,  anchor="w")
        trans_tree.column("Book",        width=140, anchor="w")
        trans_tree.column("Borrow Date", width=80,  anchor="center")
        trans_tree.column("Due Date",    width=80,  anchor="center")
        trans_tree.column("Status",      width=70,  anchor="center")
        for col in trans_cols:
            trans_tree.heading(col, text=col)
 
        trans_tree.tag_configure("borrowed", foreground="#E1AD01")
        trans_tree.tag_configure("returned", foreground="#2ECC71")
        trans_tree.tag_configure("overdue",  foreground="#E74C3C")
 
        for row in recent_loans:
            tag = row[5] if row[5] in ("borrowed", "returned", "overdue") else "returned"
            trans_tree.insert("", "end", values=row, tags=(tag,))
 
        trans_tree.pack(fill="both", expand=True, padx=1, pady=1)
 
        # -- RIGHT: Book Categories Horizontal Bar Chart --
        right2 = tk.Frame(row2, bg="#0D1B2A", width=300,
                   height=max(240, 12 + len(categories) * 30 + 10 + 40))
        right2.pack(side="right", fill="both", padx=(12, 0))
        right2.pack_propagate(False)
 
        tk.Label(right2, text="📂 Book Categories",
                 font=("Helvetica", 11, "bold"),
                 bg="#0D1B2A", fg="white").pack(anchor="w", pady=(0, 6))
 
        cat_box = tk.Frame(right2, bg="#111D45",
                           highlightthickness=1, highlightbackground="#1A2456")
        cat_box.pack(fill="both", expand=True)
 
        self._draw_category_chart(cat_box, categories)
 
        # ===== ROW 3 — TOP MEMBERS + LIBRARY STATS + ALERTS =====
        row3 = tk.Frame(main, bg="#0D1B2A")
        row3.pack(fill="x", padx=25, pady=(8, 20))
 
        row3.columnconfigure(0, weight=1, uniform="row3")
        row3.columnconfigure(1, weight=1, uniform="row3")
        row3.columnconfigure(2, weight=1, uniform="row3")
 
        # ---- TOP ACTIVE MEMBERS ----
        mem_col = tk.Frame(row3, bg="#0D1B2A")
        mem_col.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
 
        tk.Label(mem_col, text="⭐ Top Active Members",
                 font=("Helvetica", 11, "bold"),
                 bg="#0D1B2A", fg="white").pack(anchor="w", pady=(0, 6))
 
        mem_box = tk.Frame(mem_col, bg="#111D45",
                           highlightthickness=1, highlightbackground="#1A2456")
        mem_box.pack(fill="both", expand=True)
 
        member_colors = ["#1E6FFF", "#2ECC71", "#9B59B6", "#E1AD01"]
        max_count = max(m[2] for m in top_members) if top_members else 1
 
        if not top_members:
            tk.Label(mem_box, text="No data available",
                     font=("Arial", 9), bg="#111D45", fg="#7F8C8D").pack(pady=20)
        else:
            for i, (name, uid, count) in enumerate(top_members):
                clr = member_colors[i % len(member_colors)]
                mf = tk.Frame(mem_box, bg="#111D45")
                mf.pack(fill="x", padx=8, pady=5)
 
                tk.Label(mf, text=f"#{i+1}",
                         font=("Arial", 8, "bold"),
                         bg=clr, fg="white", width=3, padx=4).pack(side="left")
 
                info = tk.Frame(mf, bg="#111D45")
                info.pack(side="left", fill="x", expand=True, padx=6)
                tk.Label(info, text=name, font=("Arial", 9, "bold"),
                         bg="#111D45", fg="white", anchor="w").pack(anchor="w")
                tk.Label(info, text=f"UID: {uid}", font=("Arial", 7),
                         bg="#111D45", fg="#7F8C8D", anchor="w").pack(anchor="w")
 
                right_info = tk.Frame(mf, bg="#111D45")
                right_info.pack(side="right")
                tk.Label(right_info, text=f"{count} books",
                         font=("Arial", 8, "bold"),
                         bg="#111D45", fg="#2ECC71").pack(anchor="e")
                bar_frame = tk.Frame(right_info, bg="#1A2456", width=60, height=4)
                bar_frame.pack(anchor="e")
                bar_frame.pack_propagate(False)
                fill_w = int((count / max_count) * 60)
                tk.Frame(bar_frame, bg=clr, width=fill_w, height=4).pack(side="left")
 
        # ---- LIBRARY STATISTICS ----
        stat_col = tk.Frame(row3, bg="#0D1B2A")
        stat_col.grid(row=0, column=1, sticky="nsew", padx=6)
 
        tk.Label(stat_col, text="📊 Library Statistics",
                 font=("Helvetica", 11, "bold"),
                 bg="#0D1B2A", fg="white").pack(anchor="w", pady=(0, 6))
 
        stat_box = tk.Frame(stat_col, bg="#111D45",
                            highlightthickness=1, highlightbackground="#1A2456")
        stat_box.pack(fill="both", expand=True)
 
        top_stat = tk.Frame(stat_box, bg="#111D45")
        top_stat.pack(fill="x", padx=12, pady=(10, 4))
 
        tk.Label(top_stat, text="📖  Monthly Circulation",
                 font=("Arial", 9), bg="#111D45",
                 fg="#B0BEC5", anchor="w").pack(anchor="w")
 
        tk.Label(top_stat, text=f"{monthly:,} books",
                 font=("Helvetica", 20, "bold"),
                 bg="#111D45", fg="#1E6FFF").pack(anchor="w", pady=(2, 6))
 
        badge_row = tk.Frame(stat_box, bg="#111D45")
        badge_row.pack(fill="x", padx=12, pady=(0, 8))
 
        this_month_badge = tk.Frame(badge_row, bg="#1E3A5F", padx=8, pady=4)
        this_month_badge.pack(side="left", padx=(0, 8))
        tk.Label(this_month_badge, text="This Month",
                 font=("Arial", 7), bg="#1E3A5F",
                 fg="#7FB3E8").pack()
        tk.Label(this_month_badge, text=f"{monthly} books",
                 font=("Arial", 9, "bold"),
                 bg="#1E3A5F", fg="white").pack()
 
        returns_badge = tk.Frame(badge_row, bg="#0A3D2A", padx=8, pady=4)
        returns_badge.pack(side="left")
        tk.Label(returns_badge, text="Returns",
                 font=("Arial", 7), bg="#0A3D2A",
                 fg="#7FD4A8").pack()
        tk.Label(returns_badge, text=f"{returned} books",
                 font=("Arial", 9, "bold"),
                 bg="#0A3D2A", fg="white").pack()
 
        tk.Frame(stat_box, bg="#1A2456", height=1).pack(fill="x", padx=12)
 
        lib_stats = [
            ("🆕", "New Members This Month", str(new_members), "#9B59B6"),
            ("👤", "Avg Books / Member",      str(avg_books),   "#E1AD01"),
            ("📴", "Out of Stock",            str(out_of_stock),"#E74C3C"),
        ]
 
        for ico, lbl, val, clr in lib_stats:
            sf = tk.Frame(stat_box, bg="#111D45")
            sf.pack(fill="x", padx=12, pady=5)
            tk.Label(sf, text=f"{ico}  {lbl}",
                     font=("Arial", 9), bg="#111D45",
                     fg="#B0BEC5", anchor="w").pack(side="left", fill="x", expand=True)
            tk.Label(sf, text=val,
                     font=("Arial", 11, "bold"),
                     bg="#111D45", fg=clr).pack(side="right")
            tk.Frame(stat_box, bg="#1A2456", height=1).pack(fill="x", padx=12)
 
        # ---- ALERTS & NOTIFICATIONS ----
        alert_col = tk.Frame(row3, bg="#0D1B2A")
        alert_col.grid(row=0, column=2, sticky="nsew", padx=(6, 0))
 
        tk.Label(alert_col, text="🔔 Alerts & Notifications",
                 font=("Helvetica", 11, "bold"),
                 bg="#0D1B2A", fg="white").pack(anchor="w", pady=(0, 6))
 
        alert_box = tk.Frame(alert_col, bg="#111D45",
                             highlightthickness=1, highlightbackground="#1A2456")
        alert_box.pack(fill="both", expand=True)
 
        alerts = [
            (
                "⚠️",
                f"{overdue_books} Book{'s' if overdue_books != 1 else ''} Overdue",
                f"{'Action needed — fine applied' if overdue_books > 0 else 'No overdue books'}",
                "#E74C3C", "#3D0F0F"
            ),
            (
                "📴",
                f"{out_of_stock} Book{'s' if out_of_stock != 1 else ''} Out of Stock",
                f"{'Restock soon' if out_of_stock > 0 else 'All books available'}",
                "#F39C12", "#3D2A00"
            ),
            (
                "💸",
                f"Rs.{unpaid_fines} Fines Pending",
                f"{'Collect from members' if unpaid_fines > 0 else 'No pending fines'}",
                "#E1AD01", "#4A3500"
            ),
            (
                "✅",
                "System Running Fine",
                "All operations normal",
                "#2ECC71", "#0A3D1F"
            ),
        ]
 
        for ico, title, subtitle, clr, bg_a in alerts:
            af = tk.Frame(alert_box, bg=bg_a, padx=10, pady=7)
            af.pack(fill="x", padx=8, pady=4)
 
            tk.Label(af, text=ico, font=("Arial", 12),
                     bg=bg_a, fg=clr).pack(side="left", padx=(0, 8))
 
            text_col = tk.Frame(af, bg=bg_a)
            text_col.pack(side="left", fill="x", expand=True)
 
            tk.Label(text_col, text=title,
                     font=("Arial", 9, "bold"),
                     bg=bg_a, fg=clr, anchor="w").pack(anchor="w")
            tk.Label(text_col, text=subtitle,
                     font=("Arial", 8),
                     bg=bg_a, fg=clr, anchor="w").pack(anchor="w")
 
    # ================================================================
    # HORIZONTAL BAR CHART
    # ================================================================
    def _draw_category_chart(self, parent, categories):
        if not categories:
            categories = [("No Data", 0)]
 
        bar_colors = ["#1E6FFF", "#2ECC71", "#E1AD01",
                      "#9B59B6", "#E74C3C", "#1ABC9C", "#F39C12"]
 
        row_h   = 30
        pad_top = 12
        pad_bot = 10
        label_w = 88
 
        chart_h = pad_top + len(categories) * row_h + pad_bot
 
        canvas = tk.Canvas(parent, bg="#111D45",
                           highlightthickness=0,
                           height=chart_h)
        canvas.pack(fill="x", padx=6, pady=8)
 
        max_val = max(c[1] for c in categories) if categories else 1
 
        def _draw(event=None):
            canvas.delete("all")
            cw = canvas.winfo_width()
            if cw < 80:
                cw = 260
 
            count_w = 28
            bar_area = cw - label_w - count_w - 16
 
            for i, (cname, ccount) in enumerate(categories):
                clr  = bar_colors[i % len(bar_colors)]
                y0   = pad_top + i * row_h
                y_mid = y0 + row_h // 2
 
                display_name = cname[:13] + "…" if len(cname) > 13 else cname
                canvas.create_text(
                    8, y_mid,
                    text=display_name, anchor="w",
                    fill="#B0BEC5", font=("Arial", 8)
                )
 
                bx  = label_w
                by1 = y_mid - 8
                by2 = y_mid + 8
                canvas.create_rectangle(
                    bx, by1, bx + bar_area, by2,
                    fill="#1A2456", outline=""
                )
 
                if max_val > 0 and ccount > 0:
                    fill_w = max(4, int((ccount / max_val) * bar_area))
                    canvas.create_rectangle(
                        bx, by1, bx + fill_w, by2,
                        fill=clr, outline=""
                    )
 
                canvas.create_text(
                    bx + bar_area + 4, y_mid,
                    text=str(ccount), anchor="w",
                    fill=clr, font=("Arial", 8, "bold")
                )
 
        canvas.bind("<Configure>", _draw)
        canvas.after(80, _draw)
 
    # ================================================================
    # TREEVIEW HELPER
    # ================================================================
    def _make_treeview(self, parent, columns):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Librarian.Treeview",
                        background="#111D45", foreground="white",
                        rowheight=30, fieldbackground="#111D45",
                        borderwidth=0, relief="flat",
                        bordercolor="#111D45", lightcolor="#111D45", darkcolor="#111D45",
                        font=("Arial", 10))
        style.configure("Librarian.Treeview.Heading",
                        background="#1E6FFF", foreground="white",
                        font=("Arial", 10, "bold"), relief="flat",
                        bordercolor="#1E6FFF", lightcolor="#1E6FFF", darkcolor="#1E6FFF")
        style.map("Librarian.Treeview", background=[("selected", "#1E6FFF")])
        style.layout("Librarian.Treeview", [
            ("Librarian.Treeview.treearea", {"sticky": "nswe"})
        ])
 
        vsb = ttk.Scrollbar(parent, orient="vertical")
        hsb = ttk.Scrollbar(parent, orient="horizontal")
        tree = ttk.Treeview(parent, columns=columns, show="headings",
                            style="Librarian.Treeview",
                            yscrollcommand=vsb.set,
                            xscrollcommand=hsb.set)
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=130)
        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)
        return tree
 
    # ================================================================
    # SHOW BOOKS
    # ================================================================
    def show_books(self):
        self.clear_content()
        bm = BookModule(self.content)
        bm.show_books_ui()
 
    # ================================================================
    # SHOW CATEGORIES
    # ================================================================
    def show_categories(self):
        self.clear_content()
        cm = CategoryModule(self.content)
        cm.show_categories_ui()
 
    # ================================================================
    # SHOW USERS
    # ================================================================
    def show_users(self):
        sf = self._make_scroll_area()
        sf.update_idletasks()
 
        tk.Label(sf, text="👥 Manage Users",
                 font=("Helvetica", 18, "bold"),
                 bg="#0D1B2A", fg="white").pack(padx=25, pady=(20, 5), anchor="w")
 
        top_row = tk.Frame(sf, bg="#0D1B2A")
        top_row.pack(fill="x", padx=25, pady=(0, 10))
 
        # ✅ Add User button LEFT side — green, same style as books
        tk.Button(top_row, text="➕  Add User",
                  bg="#2ECC71", fg="white",
                  font=("Arial", 10, "bold"), bd=0,
                  cursor="hand2", padx=12, pady=6,
                  activebackground="#27AE60",
                  command=lambda: self.add_user_dialog(lambda: load_users(search_var.get().strip())
                 )).pack(side="left", padx=(0, 10))
                
 
        # ✅ Search box with inline ✕ clear button
        search_wrap = tk.Frame(top_row, bg="#1A2456",
                               highlightthickness=1, highlightbackground="#1E6FFF")
        search_wrap.pack(side="left", ipady=2)
 
        search_var = tk.StringVar()
        tk.Entry(search_wrap, textvariable=search_var,
                 font=("Arial", 10), width=28,
                 bg="#1A2456", fg="white",
                 insertbackground="white", bd=0,
                 relief="flat").pack(side="left", ipady=5, padx=(8, 0))
 
        clear_btn = tk.Label(search_wrap, text="✕",
                             font=("Arial", 10, "bold"),
                             bg="#1A2456", fg="#7F8C8D",
                             cursor="hand2", padx=6)
        clear_btn.pack(side="left")
        clear_btn.bind("<Enter>", lambda e: clear_btn.config(fg="#E74C3C"))
        clear_btn.bind("<Leave>", lambda e: clear_btn.config(fg="#7F8C8D"))
        clear_btn.bind("<Button-1>", lambda e: search_var.set(""))
 
        tk.Label(search_wrap, text="🔍", font=("Arial", 12),
                 bg="#1A2456", fg="#B0BEC5", padx=4).pack(side="left")
 
        # ✅ Users frame — height shrinks to fit rows
        users_frame = tk.Frame(sf, bg="#0D1B2A")
        users_frame.pack(fill="x", expand=False, padx=25, pady=5)
 
        def load_users(search=""):
            # Clear old table
            for w in users_frame.winfo_children():
                w.destroy()
 
            conn = None
            rows = []
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT user_id, name, email,
                           COALESCE(phone, '—'), created_at
                    FROM users
                    WHERE role NOT IN ('librarian', 'inactive')
                    AND (%s = '' OR name LIKE %s OR email LIKE %s)
                    ORDER BY created_at DESC
                """, (search, f"%{search}%", f"%{search}%"))
                rows = cur.fetchall()
            except Exception as e:
                messagebox.showerror("DB Error", str(e))
            finally:
                if conn:
                    conn.close()
 
            # ✅ Treeview height = exact row count
            row_count = max(1, min(len(rows), 20))
 
            style = ttk.Style()
            style.theme_use("clam")
            style.configure("User.Treeview",
                            background="#111D45", foreground="white",
                            rowheight=30, fieldbackground="#111D45",
                            borderwidth=0, relief="flat",
                            bordercolor="#111D45", lightcolor="#111D45", darkcolor="#111D45",
                            font=("Arial", 10))
            style.configure("User.Treeview.Heading",
                            background="#0A1628", foreground="#E1AD01",
                            font=("Arial", 10, "bold"), relief="flat",
                            bordercolor="#0A1628", lightcolor="#0A1628", darkcolor="#0A1628")
            # ✅ Heading hover fix
            style.map("User.Treeview.Heading",
                      background=[("active", "#1A2456"), ("pressed", "#1E6FFF")],
                      foreground=[("active", "#E1AD01"), ("pressed", "white")])
            # ✅ Selected row mustard instead of blue
            style.map("User.Treeview",
                      background=[("selected", "#3A2E00")],
                      foreground=[("selected", "#E1AD01")])
            style.layout("User.Treeview", [
                ("User.Treeview.treearea", {"sticky": "nswe"})
            ])
            
            cols = ("ID", "Name", "Email", "Phone", "Joined", "Actions")
            vsb = ttk.Scrollbar(users_frame, orient="vertical")
            hsb = ttk.Scrollbar(users_frame, orient="horizontal")
            tree = ttk.Treeview(users_frame, columns=cols, show="headings",
                                style="User.Treeview", height=row_count,
                                yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            vsb.config(command=tree.yview)
            hsb.config(command=tree.xview)
 
            tree.column("ID",      width=60,  anchor="center")
            tree.column("Name",    width=150, anchor="w")
            tree.column("Email",   width=200, anchor="w")
            tree.column("Phone",   width=110, anchor="center")
            tree.column("Joined",  width=150, anchor="center")
            tree.column("Actions", width=80,  anchor="center", stretch=False)
 
            for col in cols:
                tree.heading(col, text=col)
 
            vsb.pack(side="right",  fill="y")
            hsb.pack(side="bottom", fill="x")
            tree.pack(fill="x", expand=False)
 
            for row in rows:
                tree.insert("", "end", values=row + ("🗑️",))

 
            # ✅ Inline click — left half ✏️ edit, right half 🗑️ delete
            def on_tree_click(event):
                region = tree.identify("region", event.x, event.y)
                if region != "cell":
                    return
                col_id = tree.identify_column(event.x)
                row_id = tree.identify_row(event.y)
                if not row_id:
                    return
                tree.selection_remove(tree.selection())


                if col_id == "#6":  # Actions column
                    values = tree.item(row_id)["values"]
                    user_id = values[0]
                    name    = values[1]
                    if not messagebox.askyesno("Confirm",
                            f"'{name}' want to deactivate "
                            ):
                        return
                    conn2 = None
                    try:
                        conn2 = get_connection()
                        cur2  = conn2.cursor()
                        cur2.execute(
                            "UPDATE users SET role='inactive' WHERE user_id=%s", (user_id,))
                        conn2.commit()
                        messagebox.showinfo("Deactivated",
                            f"'{name}' account deactivated.")
                        load_users(search_var.get().strip())
                    except Exception as ex:
                        messagebox.showerror("Error", str(ex))
                    finally:
                        if conn2:
                            conn2.close()
 
            tree.bind("<Button-1>", on_tree_click)
 
        load_users()
 
        search_var.trace_add("write",
            lambda *a: load_users(search_var.get().strip()))

 
    # ADD USER DIALOG
    # ================================================================
    def add_user_dialog(self, reload_fn=None):
        win = tk.Toplevel(self)
        win.title("Add New User")
        win.configure(bg="#0D1B2A")
        win.geometry("420x480")
        win.grab_set()
 
        tk.Label(win, text="➕ Add New User",
                 font=("Helvetica", 16, "bold"),
                 bg="#0D1B2A", fg="white").pack(pady=(20, 15))
 
        fields = [
            ("Full Name *",  "name",     "",  ""),
            ("Email *",      "email",    "",  ""),
            ("Phone",        "phone",    "",  ""),
            ("Password *",   "password", "",  "*"),
        ]
        entries = {}
        for lbl, key, default, show in fields:
            tk.Label(win, text=lbl, font=("Arial", 9, "bold"),
                     bg="#0D1B2A", fg="#AAB7B8").pack(anchor="w", padx=30)
            e = tk.Entry(win, font=("Arial", 11), width=30,
                         bg="#1A2456", fg="white",
                         insertbackground="white", bd=0, show=show,
                         highlightthickness=1, highlightbackground="#1E6FFF")
            e.insert(0, default)
            e.pack(padx=30, pady=(2, 10), ipady=5)
            entries[key] = e
 
        def save():
            name     = entries["name"].get().strip()
            email    = entries["email"].get().strip()
            phone    = entries["phone"].get().strip() or None
            password = entries["password"].get().strip()
 
            if not name or not email or not password:
                messagebox.showwarning("Empty",
                    "First enter Name , Email and password!",
                    parent=win)
                return
 
            conn = None
            try:
                conn = get_connection()
                cur  = conn.cursor()
                hashed_pwd = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                cur.execute("""
                    INSERT INTO users (name, email, phone, password, role)
                    VALUES (%s, %s, %s, %s, 'student')
                """, (name, email, phone, hashed_pwd))
                conn.commit()

                win.destroy()
                messagebox.showinfo("success","user added successfully!")
                if reload_fn:
                   reload_fn()
                
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)
            finally:
                if conn:
                    conn.close()
 
        tk.Button(win, text="➕  Add User",
                  bg="#1E6FFF", fg="white",
                  font=("Arial", 12, "bold"), bd=0,
                  cursor="hand2", width=20, pady=8,
                  activebackground="#155FCC",
                  command=save).pack(pady=10)
 
        tk.Button(win, text="Cancel",
                  bg="#1A2456", fg="#B0BEC5",
                  font=("Arial", 10), bd=0,
                  cursor="hand2", width=20, pady=6,
                  command=win.destroy).pack()

    
    # SHOW PENDING REQUESTS (Approve/Reject + Issue Date/Due Date)
    
    def show_pending_requests(self):
        sf = self._make_scroll_area()
        tk.Label(sf, text="⏳ Pending Borrow Requests",
                 font=("Helvetica", 18, "bold"),
                 bg="#0D1B2A", fg="white").pack(padx=25, pady=(20, 10), anchor="w")

        req_frame = tk.Frame(sf, bg="#0D1B2A")
        req_frame.pack(fill="x", expand=False, padx=25, pady=5)

        def load_requests():
            for w in req_frame.winfo_children():
                w.destroy()

            conn = None
            rows = []
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT lr.request_id, u.name, b.title, lr.request_date,
                           lr.user_id, lr.book_id
                    FROM loan_requests lr
                    JOIN users u ON lr.user_id = u.user_id
                    JOIN books b ON lr.book_id = b.book_id
                    WHERE lr.status = 'pending'
                    ORDER BY lr.request_id DESC
                """)
                rows = cur.fetchall()
            except Exception as e:
                messagebox.showerror("DB Error", str(e))
            finally:
                if conn:
                    conn.close()

            if not rows:
                tk.Label(req_frame, text="No pending requests 🎉",
                         font=("Arial", 11), bg="#0D1B2A", fg="#7F8C8D").pack(pady=20)
                return

            row_count = max(1, min(len(rows), 20))

            style = ttk.Style()
            style.theme_use("clam")
            style.configure("Req.Treeview",
                            background="#111D45", foreground="white",
                            rowheight=30, fieldbackground="#111D45",
                            borderwidth=0, relief="flat",
                            bordercolor="#111D45", lightcolor="#111D45", darkcolor="#111D45",
                            font=("Arial", 10))
            style.configure("Req.Treeview.Heading",
                            background="#0A1628", foreground="#E1AD01",
                            font=("Arial", 10, "bold"), relief="flat",
                            bordercolor="#0A1628", lightcolor="#0A1628", darkcolor="#0A1628")
            style.map("Req.Treeview.Heading",
                      background=[("active", "#1A2456"), ("pressed", "#1E6FFF")],
                      foreground=[("active", "#E1AD01"), ("pressed", "white")])
            style.map("Req.Treeview",
                      background=[("selected", "#3A2E00")],
                      foreground=[("selected", "#E1AD01")])
            style.layout("Req.Treeview", [
                ("Req.Treeview.treearea", {"sticky": "nswe"})
            ])

            cols = ("Req ID", "User", "Book", "Requested On", "Action")
            vsb = ttk.Scrollbar(req_frame, orient="vertical")
            hsb = ttk.Scrollbar(req_frame, orient="horizontal")
            tree = ttk.Treeview(req_frame, columns=cols, show="headings",
                                style="Req.Treeview", height=row_count,
                                yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            vsb.config(command=tree.yview)
            hsb.config(command=tree.xview)

            tree.column("Req ID",       width=60,  anchor="center")
            tree.column("User",         width=150, anchor="w")
            tree.column("Book",         width=220, anchor="w")
            tree.column("Requested On", width=120, anchor="center")
            tree.column("Action",       width=140, anchor="center")

            for col in cols:
                tree.heading(col, text=col)

            vsb.pack(side="right",  fill="y")
            hsb.pack(side="bottom", fill="x")
            tree.pack(fill="x", expand=False)

            data_map = {}
            for row in rows:
                req_id, uname, title, req_date, uid, bid = row
                iid = tree.insert("", "end",
                                  values=(req_id, uname, title, req_date, "✔ Approve   ✖ Reject"))
                data_map[iid] = {"request_id": req_id, "user_id": uid, "book_id": bid}

            def on_click(event):
                region = tree.identify("region", event.x, event.y)
                if region != "cell":
                    return
                col_id = tree.identify_column(event.x)
                row_id = tree.identify_row(event.y)
                if not row_id or col_id != "#5":
                    return
                data = data_map.get(row_id)
                if not data:
                    return

                bbox = tree.bbox(row_id, col_id)
                if not bbox:
                    return
                relative_x = event.x - bbox[0]
                mid = bbox[2] // 2

                if relative_x < mid:
                    approve_dialog(data)
                else:
                    reject_request(data)

            tree.bind("<Button-1>", on_click)

        def approve_dialog(data):
            win = tk.Toplevel(self)
            win.title("Approve & Issue Book")
            win.geometry("380x330")
            win.configure(bg="#0D1B2A")
            win.grab_set()
            win.resizable(False, False)

            tk.Label(win, text="✔ Approve & Issue Book",
                     font=("Helvetica", 15, "bold"),
                     bg="#0D1B2A", fg="white").pack(pady=(20, 15))

            loan_days = 14
            conn_lp = None
            try:
                conn_lp = get_connection()
                cur_lp = conn_lp.cursor()
                cur_lp.execute("SELECT loan_period_days FROM settings WHERE setting_id=1")
                lp_row = cur_lp.fetchone()
                if lp_row:
                    loan_days = lp_row[0]
            except Exception as e:
                print("Loan period fetch error:", e)
            finally:
                if conn_lp:
                    conn_lp.close()

            today = datetime.date.today().strftime("%Y-%m-%d")
            default_due = (datetime.date.today() + datetime.timedelta(days=loan_days)).strftime("%Y-%m-%d")

            tk.Label(win, text="ISSUE DATE (YYYY-MM-DD)", font=("Arial", 9, "bold"),
                     bg="#0D1B2A", fg="#AAB7B8").pack(anchor="w", padx=30)

            issue_entry = tk.Entry(win, font=("Arial", 11), width=30,
                                    bg="#243158", fg="#AAB7B8", insertbackground="white",
                                    bd=0, highlightthickness=1, highlightbackground="#1E6FFF")
            issue_entry.insert(0, today)
            issue_entry.config(state="disabled")
            issue_entry.pack(padx=30, pady=(2, 12), ipady=6)

            tk.Label(win, text="DUE DATE (YYYY-MM-DD)", font=("Arial", 9, "bold"),
                     bg="#0D1B2A", fg="#AAB7B8").pack(anchor="w", padx=30)
            due_entry = tk.Entry(win, font=("Arial", 11), width=30,
                                  bg="#243158", fg="#AAB7B8", insertbackground="white",
                                  bd=0, highlightthickness=1, highlightbackground="#1E6FFF")
            due_entry.insert(0, default_due)
            due_entry.config(state="disabled")
            due_entry.pack(padx=30, pady=(2, 15), ipady=6)

            def confirm():
                issue_date = today
                due_date = default_due   # system-calculated, librarian cannot alter
                conn = None
                try:
                    conn = get_connection()
                    cur = conn.cursor()

                    cur.execute("""SELECT COUNT(*) FROM loans
                                   WHERE user_id=%s AND status IN ('borrowed','return_pending')""", (data["user_id"],))
                    borrowed_count = cur.fetchone()[0]

                    cur.execute("""SELECT COUNT(*) FROM loan_requests
                                  WHERE user_id=%s AND status='pending' AND request_id != %s""",
                               (data["user_id"], data["request_id"]))
                    other_pending_count = cur.fetchone()[0]

                    if (borrowed_count + other_pending_count) >= 3:
                        messagebox.showerror("Limit Reached",
                            "This user already has 3 books borrowed/pending. Cannot issue more until they return one.",
                            parent=win)
                        return

                    cur.execute("SELECT available_copies, title FROM books WHERE book_id=%s",
                                (data["book_id"],))
                    book = cur.fetchone()
                    if not book or book[0] <= 0:
                        messagebox.showerror("Not Available",
                                             "This book is no longer available.", parent=win)
                        return
                    cur.execute("""
                        INSERT INTO loans (user_id, book_id, borrow_date, due_date, status)
                        VALUES (%s, %s, %s, %s, 'borrowed')
                    """, (data["user_id"], data["book_id"], issue_date, due_date))

                    cur.execute("UPDATE books SET available_copies = available_copies - 1 WHERE book_id=%s",
                                (data["book_id"],))

                    cur.execute("UPDATE loan_requests SET status='approved' WHERE request_id=%s",
                                (data["request_id"],))

                    cur.execute("""
                        INSERT INTO notifications (user_id, message, status, created_at)
                        VALUES (%s, %s, 'unread', NOW())
                    """, (data["user_id"], f"Your request for '{book[1]}' was approved. Due date: {due_date}"))

                    conn.commit()
                    win.destroy()
                    load_requests()
                    messagebox.showinfo("Success", "Book issued successfully!")

                except Exception as e:
                    messagebox.showerror("Error", str(e), parent=win)
                finally:
                    if conn:
                        conn.close()

            tk.Button(win, text="✅ Confirm & Issue",
                      bg="#2ECC71", fg="white",
                      font=("Arial", 12, "bold"), bd=0,
                      cursor="hand2", width=22, pady=8,
                      command=confirm).pack(pady=5)

        def reject_request(data):
            if not messagebox.askyesno("Confirm", "Reject this request?"):
                return
            conn = None
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("UPDATE loan_requests SET status='rejected' WHERE request_id=%s",
                            (data["request_id"],))
                cur.execute("""
                    INSERT INTO notifications (user_id, message, status, created_at)
                    VALUES (%s, %s, 'unread', NOW())
                """, (data["user_id"], "Your borrow request was rejected."))
                conn.commit()
                messagebox.showinfo("Rejected", "Request rejected.")
                load_requests()
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                if conn:
                    conn.close()

        load_requests()    
 
    # ================================================================
    # SHOW LOANS
    # ================================================================
    def show_loans(self):
        sf = self._make_scroll_area()
        tk.Label(sf, text="📜 View Loans",
                 font=("Helvetica", 18, "bold"),
                 bg="#0D1B2A", fg="white").pack(padx=25, pady=(20, 5), anchor="w")
 
        top_row = tk.Frame(sf, bg="#0D1B2A")
        top_row.pack(fill="x", padx=25, pady=(0, 10))
 
        # ✅ Search box with inline ✕
        search_wrap = tk.Frame(top_row, bg="#1A2456",
                               highlightthickness=1, highlightbackground="#1E6FFF")
        search_wrap.pack(side="left", ipady=2)
 
        search_var = tk.StringVar()
        tk.Entry(search_wrap, textvariable=search_var,
                 font=("Arial", 10), width=25,
                 bg="#1A2456", fg="white",
                 insertbackground="white", bd=0,
                 relief="flat").pack(side="left", ipady=5, padx=(8, 0))
 
        clear_btn = tk.Label(search_wrap, text="✕",
                             font=("Arial", 10, "bold"),
                             bg="#1A2456", fg="#7F8C8D",
                             cursor="hand2", padx=6)
        clear_btn.pack(side="left")
        clear_btn.bind("<Enter>", lambda e: clear_btn.config(fg="#E74C3C"))
        clear_btn.bind("<Leave>", lambda e: clear_btn.config(fg="#7F8C8D"))
        clear_btn.bind("<Button-1>", lambda e: search_var.set(""))
 
        tk.Label(search_wrap, text="🔍", font=("Arial", 12),
                 bg="#1A2456", fg="#B0BEC5", padx=4).pack(side="left")
 
        # ✅ Filter buttons — proper design instead of ugly dropdown
        filter_var = tk.StringVar(value="All")
        filter_frame = tk.Frame(top_row, bg="#0D1B2A")
        filter_frame.pack(side="left", padx=(12, 0))
 
        filter_btns = {}
        filters = [("All", "#1E6FFF"), ("borrowed", "#E1AD01"),
                   ("returned", "#2ECC71"), ("overdue", "#E74C3C")]
 
        def set_filter(f):
            filter_var.set(f)
            for name, btn in filter_btns.items():
                if name == f:
                    clr = dict(filters)[name]
                    btn.config(bg=clr, fg="#0D1B2A" if name != "borrowed" else "#0D1B2A",
                               relief="flat")
                else:
                    btn.config(bg="#1A2456", fg="#B0BEC5", relief="flat")
            load_loans(search_var.get().strip(), f)
 
        for fname, fcolor in filters:
            b = tk.Button(filter_frame, text=fname.capitalize(),
                          bg="#1A2456", fg="#B0BEC5",
                          font=("Arial", 9, "bold"), bd=0,
                          cursor="hand2", padx=10, pady=5,
                          relief="flat",
                          activebackground=fcolor,
                          activeforeground="#0D1B2A",
                          command=lambda f=fname: set_filter(f))
            b.pack(side="left", padx=2)
            filter_btns[fname] = b
 
        # Set All as active by default
        filter_btns["All"].config(bg="#1E6FFF", fg="white")
 
        # ✅ Frame — height fits rows
        loans_frame = tk.Frame(sf, bg="#0D1B2A")
        loans_frame.pack(fill="x", expand=False, padx=25, pady=5)
 
        def load_loans(search="", status_filter="All"):
            for w in loans_frame.winfo_children():
                w.destroy()
 
            conn = None
            rows = []
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT l.loan_id, u.name, b.title,
                           l.borrow_date, l.due_date,
                           CASE
                               WHEN l.status = 'borrowed' AND l.due_date < CURDATE() THEN 'overdue'
                               ELSE l.status
                           END as display_status
                    FROM loans l
                    JOIN users u ON l.user_id = u.user_id
                    JOIN books b ON l.book_id = b.book_id
                    WHERE (%s = '' OR u.name LIKE %s OR b.title LIKE %s)
                    ORDER BY l.loan_id DESC
                """, (search, f"%{search}%", f"%{search}%"))
 
                all_rows = cur.fetchall()
                rows = [r for r in all_rows
                        if status_filter == "All" or r[5] == status_filter]
 
            except Exception as e:
                messagebox.showerror("DB Error", str(e))
            finally:
                if conn:
                    conn.close()
 
            row_count = max(1, min(len(rows), 20))
 
            style = ttk.Style()
            style.theme_use("clam")
            style.configure("Loan.Treeview",
                            background="#111D45", foreground="white",
                            rowheight=30, fieldbackground="#111D45",
                            borderwidth=0, relief="flat",
                            bordercolor="#111D45", lightcolor="#111D45", darkcolor="#111D45",
                            font=("Arial", 10))
            style.configure("Loan.Treeview.Heading",
                            background="#0A1628", foreground="#E1AD01",
                            font=("Arial", 10, "bold"), relief="flat",
                            bordercolor="#0A1628", lightcolor="#0A1628", darkcolor="#0A1628")
            style.map("Loan.Treeview.Heading",
                      background=[("active", "#1A2456"), ("pressed", "#1E6FFF")],
                      foreground=[("active", "#E1AD01"), ("pressed", "white")])
            # ✅ Selected row — mustard, NOT full red/green/yellow row
            style.map("Loan.Treeview",
                      background=[("selected", "#3A2E00")],
                      foreground=[("selected", "#E1AD01")])
            style.layout("Loan.Treeview", [
                ("Loan.Treeview.treearea", {"sticky": "nswe"})
            ])

            cols = ("Loan ID", "User", "Book", "Borrow Date", "Due Date", "Status", "Action")
            vsb = ttk.Scrollbar(loans_frame, orient="vertical")
            hsb = ttk.Scrollbar(loans_frame, orient="horizontal")
            tree = ttk.Treeview(loans_frame, columns=cols, show="headings",
                                style="Loan.Treeview", height=row_count,
                                yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            vsb.config(command=tree.yview)
            hsb.config(command=tree.xview)
 
            tree.column("Loan ID",     width=70,  anchor="center")
            tree.column("User",        width=140, anchor="w")
            tree.column("Book",        width=210, anchor="w")
            tree.column("Borrow Date", width=120, anchor="center")
            tree.column("Due Date",    width=120, anchor="center")
            tree.column("Status",      width=90,  anchor="center")
            tree.column("Action",      width=130, anchor="center")
 
            for col in cols:
                tree.heading(col, text=col)
 
            vsb.pack(side="right",  fill="y")
            hsb.pack(side="bottom", fill="x")
            tree.pack(fill="x", expand=False)
 
            loan_id_map = {}
            for row in rows:
                loan_id, uname, title, bdate, ddate, status = row
                vals = list(row)
                if status == "overdue":
                    vals[5] = "⚠ overdue"
                    vals.append("↩ Mark Returned")
                elif status == "returned":
                    vals[5] = "✓ returned"
                    vals.append("—")
                elif status == "borrowed":
                    vals[5] = "● borrowed"
                    vals.append("↩ Mark Returned")
                elif status == "return_pending":
                    vals[5] = "⏳ return pending"
                    vals.append("✔ Confirm Return")
                iid = tree.insert("", "end", values=vals, tags=(status,))
                loan_id_map[iid] = {"loan_id": loan_id, "status": status}
 
            # Only color the STATUS text — background stays dark navy
            tree.tag_configure("borrowed", foreground="#E1AD01")
            tree.tag_configure("returned", foreground="#2ECC71")
            tree.tag_configure("overdue",  foreground="#E74C3C")
            tree.tag_configure("return_pending", foreground="#F39C12")
 
            def on_tree_click(event):
                region = tree.identify("region", event.x, event.y)
                if region != "cell":
                    return
                col_id = tree.identify_column(event.x)
                row_id = tree.identify_row(event.y)
                tree.after(1, lambda: tree.selection_remove(tree.selection()))
 
                if not row_id or col_id != "#7":
                    return
 
                info = loan_id_map.get(row_id)
                if not info or info["status"] == "returned":
                    return

                confirm_msg = ("Confirm this return request?" if info["status"] == "return_pending"
                               else "Mark this book as returned?")
                if not messagebox.askyesno("Confirm", confirm_msg):
                    return
 
                conn2 = None
                try:
                    conn2 = get_connection()
                    cur2 = conn2.cursor()
 
                    cur2.execute("SELECT book_id, due_date, user_id FROM loans WHERE loan_id=%s",
                                (info["loan_id"],))
                    loan_row = cur2.fetchone()
                    if not loan_row:
                        return
                    book_id, due_date, uid = loan_row
 
                    import datetime as _dt
                    today = _dt.date.today()
 
                    cur2.execute("""
                        UPDATE loans SET status='returned', return_date=%s WHERE loan_id=%s
                    """, (today.strftime("%Y-%m-%d"), info["loan_id"]))
 
                    cur2.execute("""
                        UPDATE books SET available_copies = available_copies + 1 WHERE book_id=%s
                    """, (book_id,))

             # ---- Notify wishlist users that this book is now available ----
                    cur2.execute("SELECT title FROM books WHERE book_id=%s", (book_id,))
                    book_title_row = cur2.fetchone()
                    book_title = book_title_row[0] if book_title_row else "A book"

                    cur2.execute("SELECT user_id FROM wishlist WHERE book_id=%s", (book_id,))
                    wishlist_users = cur2.fetchall()
                    for (wuser_id,) in wishlist_users:
                        cur2.execute("""
                            INSERT INTO notifications (user_id, message, status, created_at)
                            VALUES (%s, %s, 'unread', NOW())
                        """, (wuser_id, f"'{book_title}' is now available! You can request to borrow it."))
        
 
                    if due_date and due_date < today:
                        days_late = (today - due_date).days

                        fine_rate = 10.00
                        cur2.execute("SELECT fine_per_day FROM settings WHERE setting_id=1")
                        rate_row = cur2.fetchone()
                        if rate_row:
                            fine_rate = rate_row[0]

                        fine_amount = days_late * fine_rate
                        cur2.execute("SELECT fine_id FROM fines WHERE loan_id=%s", (info["loan_id"],))
                        existing = cur2.fetchone()
                        if not existing:
                            cur2.execute("""
                                INSERT INTO fines (loan_id, user_id, amount, status, created_at)
                                VALUES (%s, %s, %s, 'unpaid', CURDATE())
                            """, (info["loan_id"], uid, fine_amount))
 
                    conn2.commit()
                    messagebox.showinfo("Returned", "Book marked as returned.")
                    load_loans(search_var.get().strip(), filter_var.get())
                except Exception as e:
                    messagebox.showerror("Error", str(e))
                finally:
                    if conn2:
                        conn2.close()
 
            tree.bind("<Button-1>", on_tree_click)
 
        load_loans()
 
        search_var.trace_add("write",
            lambda *a: load_loans(search_var.get().strip(), filter_var.get()))

 
    # ================================================================
    # SHOW FINES
    # ================================================================
    def show_fines(self):
        sf = self._make_scroll_area()
        tk.Label(sf, text="💸 Fines",
                 font=("Helvetica", 18, "bold"),
                 bg="#0D1B2A", fg="white").pack(padx=25, pady=(20, 5), anchor="w")
 
                # Auto calculate fines from DB
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()

            fine_rate = 10.00
            cur.execute("SELECT fine_per_day FROM settings WHERE setting_id=1")
            rate_row = cur.fetchone()
            if rate_row:
                fine_rate = rate_row[0]

            cur.execute("""
                INSERT INTO fines (loan_id, user_id, amount, status, created_at)
                SELECT l.loan_id, l.user_id,
                       DATEDIFF(CURDATE(), l.due_date) * %s,
                       'unpaid', CURDATE()
                FROM loans l
                WHERE l.status = 'borrowed'
                AND l.due_date < CURDATE()
                AND l.loan_id NOT IN (SELECT loan_id FROM fines)
            """, (fine_rate,))
            cur.execute("""
                UPDATE fines f
                JOIN loans l ON f.loan_id = l.loan_id
                SET f.amount = DATEDIFF(CURDATE(), l.due_date) * %s
                WHERE f.status = 'unpaid'
                AND l.due_date < CURDATE()
            """, (fine_rate,))
            conn.commit()
        except Exception as e:
            messagebox.showerror("DB Error", f"Fine calculation error: {e}")
        finally:
            if conn:
                conn.close()
 
        top_row = tk.Frame(sf, bg="#0D1B2A")
        top_row.pack(fill="x", padx=25, pady=(0, 10))
 
        # ✅ Search box with inline ✕
        search_wrap = tk.Frame(top_row, bg="#1A2456",
                               highlightthickness=1, highlightbackground="#1E6FFF")
        search_wrap.pack(side="left", ipady=2)
 
        search_var = tk.StringVar()
        tk.Entry(search_wrap, textvariable=search_var,
                 font=("Arial", 10), width=25,
                 bg="#1A2456", fg="white",
                 insertbackground="white", bd=0,
                 relief="flat").pack(side="left", ipady=5, padx=(8, 0))
 
        clear_btn = tk.Label(search_wrap, text="✕",
                             font=("Arial", 10, "bold"),
                             bg="#1A2456", fg="#7F8C8D",
                             cursor="hand2", padx=6)
        clear_btn.pack(side="left")
        clear_btn.bind("<Enter>", lambda e: clear_btn.config(fg="#E74C3C"))
        clear_btn.bind("<Leave>", lambda e: clear_btn.config(fg="#7F8C8D"))
        clear_btn.bind("<Button-1>", lambda e: search_var.set(""))
 
        tk.Label(search_wrap, text="🔍", font=("Arial", 12),
                 bg="#1A2456", fg="#B0BEC5", padx=4).pack(side="left")
 
        # ✅ Filter buttons instead of ugly dropdown
        filter_var = tk.StringVar(value="All")
        filter_frame = tk.Frame(top_row, bg="#0D1B2A")
        filter_frame.pack(side="left", padx=(12, 0))
 
        filter_btns = {}
        filters = [("All", "#1E6FFF"), ("unpaid", "#E74C3C"), ("pending", "#E1AD01"), ("paid", "#2ECC71")]
 
        def set_filter(f):
            filter_var.set(f)
            for name, btn in filter_btns.items():
                if name == f:
                    clr = dict(filters)[name]
                    btn.config(bg=clr, fg="white", relief="flat")
                else:
                    btn.config(bg="#1A2456", fg="#B0BEC5", relief="flat")
            load_fines(search_var.get().strip(), f)
 
        for fname, fcolor in filters:
            b = tk.Button(filter_frame,
                          text=fname.capitalize(),
                          bg="#1A2456", fg="#B0BEC5",
                          font=("Arial", 9, "bold"), bd=0,
                          cursor="hand2", padx=10, pady=5,
                          relief="flat",
                          activebackground=fcolor,
                          activeforeground="white",
                          command=lambda f=fname: set_filter(f))
            b.pack(side="left", padx=2)
            filter_btns[fname] = b
 
        # All active by default
        filter_btns["All"].config(bg="#1E6FFF", fg="white")
 
        # ✅ Fines frame — height fits rows
        fines_frame = tk.Frame(sf, bg="#0D1B2A")
        fines_frame.pack(fill="x", expand=False, padx=25, pady=5)
 
        def load_fines(search="", status_filter="All"):
            for w in fines_frame.winfo_children():
                w.destroy()
 
            conn = None
            rows = []
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT f.fine_id, u.name, b.title,
                           f.amount, f.status, f.created_at
                    FROM fines f
                    JOIN users u ON f.user_id = u.user_id
                    JOIN loans l ON f.loan_id = l.loan_id
                    JOIN books b ON l.book_id = b.book_id
                    WHERE (%s = '' OR u.name LIKE %s)
                    AND (%s = 'All' OR f.status = %s)
                    ORDER BY f.created_at DESC
                """, (search, f"%{search}%", status_filter, status_filter))
                rows = cur.fetchall()
            except Exception as e:
                messagebox.showerror("DB Error", str(e))
            finally:
                if conn:
                    conn.close()
 
            row_count = max(1, min(len(rows), 20))
 
            style = ttk.Style()
            style.theme_use("clam")
            style.configure("Fine.Treeview",
                            background="#111D45", foreground="white",
                            rowheight=30, fieldbackground="#111D45",
                            borderwidth=0, relief="flat",
                            bordercolor="#111D45", lightcolor="#111D45", darkcolor="#111D45",
                            font=("Arial", 10))
            style.configure("Fine.Treeview.Heading",
                            background="#0A1628", foreground="#E1AD01",
                            font=("Arial", 10, "bold"), relief="flat",
                            bordercolor="#0A1628", lightcolor="#0A1628", darkcolor="#0A1628")
            # ✅ Heading hover fix
            style.map("Fine.Treeview.Heading",
                      background=[("active", "#1A2456"), ("pressed", "#1E6FFF")],
                      foreground=[("active", "#E1AD01"), ("pressed", "white")])
            # ✅ Mustard selected row
            style.map("Fine.Treeview",
                       background=[("selected", "#3A2E00")],
                       foreground=[("selected", "#E1AD01")])
            style.layout("Fine.Treeview", [
                ("Fine.Treeview.treearea", {"sticky": "nswe"})
            ])
            
            cols = ("Fine ID", "User", "Book", "Amount (Rs.)", "Status", "Date")
            vsb = ttk.Scrollbar(fines_frame, orient="vertical")
            hsb = ttk.Scrollbar(fines_frame, orient="horizontal")
            tree = ttk.Treeview(fines_frame, columns=cols, show="headings",
                                style="Fine.Treeview", height=row_count,
                                yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            vsb.config(command=tree.yview)
            hsb.config(command=tree.xview)
 
            tree.column("Fine ID",      width=70,  anchor="center")
            tree.column("User",         width=130, anchor="w")
            tree.column("Book",         width=200, anchor="w")
            tree.column("Amount (Rs.)", width=110, anchor="center")
            tree.column("Status",       width=90,  anchor="center")
            tree.column("Date",         width=150, anchor="center")
 
            for col in cols:
                tree.heading(col, text=col)
 
            vsb.pack(side="right",  fill="y")
            hsb.pack(side="bottom", fill="x")
            tree.pack(fill="x", expand=False)
 
            # ✅ All rows white text — only Status column shows color via icon
            for row in rows:
                display = list(row)
                status  = display[4]
                # Status column — icon only, row stays white
                if status == "unpaid":
                    display[4] = "✕ unpaid"
                elif status == "pending":
                    display[4] = "⏳ pending"
                elif status == "paid":
                    display[4] = "✓ paid"
                tree.insert("", "end", values=display, tags=(status,))
 
            # Only status text colored, background stays dark navy
            tree.tag_configure("unpaid",  foreground="#E74C3C")
            tree.tag_configure("pending", foreground="#E1AD01")
            tree.tag_configure("paid",    foreground="#2ECC71")

            # Store tree reference for mark_as_paid
            fines_frame._tree = tree
 
        load_fines()
 
        search_var.trace_add("write",
            lambda *a: load_fines(search_var.get().strip(), filter_var.get()))
 
        # ✅ Mark as Paid button
        btn_row = tk.Frame(sf, bg="#0D1B2A")
        btn_row.pack(fill="x", padx=25, pady=(8, 20))
 
        def mark_as_paid():
            tree = getattr(fines_frame, "_tree", None)
            if not tree:
                return
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Select Fine", "select fine first")
                return
 
            values  = tree.item(selected[0])["values"]
            fine_id = values[0]
            status  = values[4]
 
            if "pending" not in str(status):
                messagebox.showinfo("Not Payable",
                    "Only fines with 'pending' status (submitted by user) can be approved.")
                return
 
            if not messagebox.askyesno("Confirm",
                    f"Approve Fine ID {fine_id} as paid?"):
                return
 
            conn = None
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE fines SET status='paid' WHERE fine_id=%s", (fine_id,))
                conn.commit()
                messagebox.showinfo("Success", "Fine approved and marked as paid! ✅")
                load_fines(search_var.get().strip(), filter_var.get())
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                if conn:
                    conn.close()

        def reject_fine():
            tree = getattr(fines_frame, "_tree", None)
            if not tree:
                return
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Select Fine", "select fine first")
                return

            values  = tree.item(selected[0])["values"]
            fine_id = values[0]
            status  = values[4]

            if "pending" not in str(status):
                messagebox.showinfo("Not Rejectable",
                    "Only fines with 'pending' status can be rejected.")
                return

            if not messagebox.askyesno("Confirm",
                    f"Reject Fine ID {fine_id}? It will go back to 'unpaid'."):
                return

            conn = None
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE fines SET status='unpaid' WHERE fine_id=%s", (fine_id,))
                conn.commit()
                messagebox.showinfo("Rejected", "Fine payment rejected, status set back to unpaid.")
                load_fines(search_var.get().strip(), filter_var.get())
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                if conn:
                    conn.close()
 
        tk.Button(btn_row, text="✅  Approve Payment",
                  bg="#2ECC71", fg="#0D1B2A",
                  font=("Arial", 10, "bold"), bd=0,
                  cursor="hand2", padx=14, pady=6,
                  activebackground="#27AE60",
                  command=mark_as_paid).pack(side="left", padx=(0, 8))

        tk.Button(btn_row, text="✖  Reject Payment",
                  bg="#E74C3C", fg="white",
                  font=("Arial", 10, "bold"), bd=0,
                  cursor="hand2", padx=14, pady=6,
                  activebackground="#C0392B",
                  command=reject_fine).pack(side="left")
 
 
    # ================================================================
    # SHOW NOTIFICATIONS
    # ================================================================
    def show_notifications(self):
        sf = self._make_scroll_area()
        tk.Label(sf, text="🔔 Notifications",
                 font=("Helvetica", 18, "bold"),
                 bg="#0D1B2A", fg="white").pack(padx=25, pady=(20, 5), anchor="w")
 
        # ---- Auto notifications from DB ----
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO notifications (user_id, message, created_at, status)
                SELECT l.user_id,
                       CONCAT('Book "', b.title, '" is due in 2 days on ',
                              DATE_FORMAT(l.due_date, '%d/%m/%Y'), '. Please return on time.'),
                       NOW(), 'unread'
                FROM loans l
                JOIN books b ON l.book_id = b.book_id
                WHERE l.status = 'borrowed'
                AND l.due_date = CURDATE() + INTERVAL 2 DAY
                AND NOT EXISTS (
                    SELECT 1 FROM notifications n
                    WHERE n.user_id = l.user_id
                    AND DATE(n.created_at) = CURDATE()
                    AND n.message LIKE CONCAT('%', b.title, '%due in 2 days%')
                )
            """)
            cur.execute("""
                INSERT INTO notifications (user_id, message, created_at, status)
                SELECT l.user_id,
                       CONCAT('Book "', b.title, '" is overdue by ',
                              DATEDIFF(CURDATE(), l.due_date), ' days. Fine Rs.',
                              DATEDIFF(CURDATE(), l.due_date) * (SELECT fine_per_day FROM settings WHERE setting_id=1), ' applied.'),
                       NOW(), 'unread'
                FROM loans l
                JOIN books b ON l.book_id = b.book_id
                WHERE l.status = 'borrowed'
                AND l.due_date < CURDATE()
                AND NOT EXISTS (
                    SELECT 1 FROM notifications n
                    WHERE n.user_id = l.user_id
                    AND DATE(n.created_at) = CURDATE()
                    AND n.message LIKE CONCAT('%', b.title, '%is overdue%')
                )
            """)
            cur.execute("""
                INSERT INTO notifications (user_id, message, created_at, status)
                SELECT f.user_id,
                       CONCAT('You have an unpaid fine of Rs.', f.amount,
                              ' for book "', b.title, '". Please clear it soon.'),
                       NOW(), 'unread'
                FROM fines f
                JOIN loans l ON f.loan_id = l.loan_id
                JOIN books b ON l.book_id = b.book_id
                WHERE f.status = 'unpaid'
                AND NOT EXISTS (
                    SELECT 1 FROM notifications n
                    WHERE n.user_id = f.user_id
                    AND DATE(n.created_at) = CURDATE()
                    AND n.message LIKE CONCAT('%unpaid fine%', b.title, '%')
                )
            """)
            conn.commit()
        except Exception as e:
            messagebox.showerror("DB Error", f"Auto notification error: {e}")
        finally:
            if conn:
                conn.close()
 
        # ---- Send Notification Section ----
        send_frame = tk.Frame(sf, bg="#111D45",
                              highlightthickness=1, highlightbackground="#1E6FFF")
        send_frame.pack(fill="x", padx=25, pady=(0, 10))
 
        tk.Label(send_frame, text="📨 Send Notification to User",
                 font=("Arial", 11, "bold"),
                 bg="#111D45", fg="white").pack(anchor="w", padx=15, pady=(10, 5))
 
        input_row = tk.Frame(send_frame, bg="#111D45")
        input_row.pack(fill="x", padx=15, pady=(0, 10))
 
        tk.Label(input_row, text="User:", font=("Arial", 10),
                 bg="#111D45", fg="#AAB7B8").pack(side="left")
 
        user_var = tk.StringVar()
        user_dropdown = tk.OptionMenu(input_row, user_var, "")
        user_dropdown.config(bg="#1A2456", fg="white", font=("Arial", 10),
                             bd=0, activebackground="#1E6FFF",
                             activeforeground="white")
        user_dropdown["menu"].config(bg="#1A2456", fg="white", font=("Arial", 10))
        user_dropdown.pack(side="left", padx=5)
 
        user_map = {}
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT user_id, name FROM users WHERE role='student' ORDER BY name")
            users = cur.fetchall()
            menu = user_dropdown["menu"]
            menu.delete(0, "end")
            for uid, uname in users:
                user_map[uname] = uid
                menu.add_command(label=uname,
                                 command=lambda val=uname: user_var.set(val))
            if users:
                user_var.set(users[0][1])
        except:
            pass
        finally:
            if conn:
                conn.close()
 
        tk.Label(input_row, text="Message:", font=("Arial", 10),
                 bg="#111D45", fg="#AAB7B8").pack(side="left", padx=(10, 5))
 
        msg_entry = tk.Entry(input_row, width=30, font=("Arial", 10),
                             bg="#1A2456", fg="white", insertbackground="white",
                             bd=0, highlightthickness=1, highlightbackground="#1E6FFF")
        msg_entry.pack(side="left", padx=5, ipady=4)
 
        tk.Button(input_row, text="Send 📨",
                  bg="#1E6FFF", fg="white", bd=0, cursor="hand2",
                  font=("Arial", 10, "bold"), padx=10, pady=4,
                  command=lambda: send_msg()).pack(side="left", padx=5)
 
        # ---- Search + Filter ----
        top_row = tk.Frame(sf, bg="#0D1B2A")
        top_row.pack(fill="x", padx=25, pady=(0, 10))
 
        # ✅ Search with inline ✕
        search_wrap = tk.Frame(top_row, bg="#1A2456",
                               highlightthickness=1, highlightbackground="#1E6FFF")
        search_wrap.pack(side="left", ipady=2)
 
        search_var = tk.StringVar()
        tk.Entry(search_wrap, textvariable=search_var,
                 font=("Arial", 10), width=25,
                 bg="#1A2456", fg="white",
                 insertbackground="white", bd=0,
                 relief="flat").pack(side="left", ipady=5, padx=(8, 0))
 
        clear_btn = tk.Label(search_wrap, text="✕",
                             font=("Arial", 10, "bold"),
                             bg="#1A2456", fg="#7F8C8D",
                             cursor="hand2", padx=6)
        clear_btn.pack(side="left")
        clear_btn.bind("<Enter>", lambda e: clear_btn.config(fg="#E74C3C"))
        clear_btn.bind("<Leave>", lambda e: clear_btn.config(fg="#7F8C8D"))
        clear_btn.bind("<Button-1>", lambda e: search_var.set(""))
 
        tk.Label(search_wrap, text="🔍", font=("Arial", 12),
                 bg="#1A2456", fg="#B0BEC5", padx=4).pack(side="left")
 
        # ✅ Filter buttons instead of dropdown
        filter_var = tk.StringVar(value="All")
        filter_frame = tk.Frame(top_row, bg="#0D1B2A")
        filter_frame.pack(side="left", padx=(12, 0))
 
        filter_btns = {}
        filters = [("All", "#1E6FFF"), ("unread", "#E1AD01"), ("read", "#7F8C8D")]
 
        def set_filter(f):
            filter_var.set(f)
            for name, btn in filter_btns.items():
                if name == f:
                    clr = dict(filters)[name]
                    btn.config(bg=clr, fg="#0D1B2A" if name == "unread" else "white",
                               relief="flat")
                else:
                    btn.config(bg="#1A2456", fg="#B0BEC5", relief="flat")
            load_notifs(search_var.get().strip(), f)
 
        for fname, fcolor in filters:
            b = tk.Button(filter_frame,
                          text=fname.capitalize(),
                          bg="#1A2456", fg="#B0BEC5",
                          font=("Arial", 9, "bold"), bd=0,
                          cursor="hand2", padx=10, pady=5,
                          relief="flat",
                          activebackground=fcolor,
                          activeforeground="white",
                          command=lambda f=fname: set_filter(f))
            b.pack(side="left", padx=2)
            filter_btns[fname] = b
 
        filter_btns["All"].config(bg="#1E6FFF", fg="white")
 
        # ---- Notifications table frame ----
        notifs_frame = tk.Frame(sf, bg="#0D1B2A")
        notifs_frame.pack(fill="x", expand=False, padx=25, pady=5)
 
        def load_notifs(search="", status_filter="All"):
            for w in notifs_frame.winfo_children():
                w.destroy()
 
            conn = None
            rows = []
            try:
                conn = get_connection()
                cur = conn.cursor()
 
                if status_filter == "unread":
                    read_condition = "AND n.status = 'unread'"
                elif status_filter == "read":
                    read_condition = "AND n.status = 'read'"
                else:
                    read_condition = ""
 
                cur.execute(f"""
                    SELECT n.notification_id, u.name,
                           n.message, n.created_at, n.status
                    FROM notifications n
                    JOIN users u ON n.user_id = u.user_id
                    WHERE (%s = '' OR u.name LIKE %s)
                    {read_condition}
                    ORDER BY n.created_at DESC
                """, (search, f"%{search}%"))
                rows = cur.fetchall()
            except Exception as e:
                messagebox.showerror("DB Error", str(e))
            finally:
                if conn:
                    conn.close()
 
            row_count = max(1, min(len(rows), 20))
 
            style = ttk.Style()
            style.theme_use("clam")
            style.configure("Notif.Treeview",
                            background="#111D45", foreground="white",
                            rowheight=30, fieldbackground="#111D45",
                            borderwidth=0, relief="flat",
                            bordercolor="#111D45", lightcolor="#111D45", darkcolor="#111D45",
                            font=("Arial", 10))
            style.configure("Notif.Treeview.Heading",
                            background="#0A1628", foreground="#E1AD01",
                            font=("Arial", 10, "bold"), relief="flat",
                            bordercolor="#0A1628", lightcolor="#0A1628", darkcolor="#0A1628")
            # ✅ Heading hover fix
            style.map("Notif.Treeview.Heading",
                      background=[("active", "#1A2456"), ("pressed", "#1E6FFF")],
                      foreground=[("active", "#E1AD01"), ("pressed", "white")])
            # ✅ Mustard selected row
            style.map("Notif.Treeview",
                       background=[("selected", "#3A2E00")],
                       foreground=[("selected", "#E1AD01")])
            style.layout("Notif.Treeview", [
                ("Notif.Treeview.treearea", {"sticky": "nswe"})
            ])
            
            cols = ("ID", "User", "Message", "Date", "Status")
            vsb = ttk.Scrollbar(notifs_frame, orient="vertical")
            hsb = ttk.Scrollbar(notifs_frame, orient="horizontal")
            tree = ttk.Treeview(notifs_frame, columns=cols, show="headings",
                                style="Notif.Treeview", height=row_count,
                                yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            vsb.config(command=tree.yview)
            hsb.config(command=tree.xview)
 
            tree.column("ID",      width=50,  anchor="center")
            tree.column("User",    width=120, anchor="w")
            tree.column("Message", width=400, anchor="w")
            tree.column("Date",    width=150, anchor="center")
            tree.column("Status",  width=80,  anchor="center")
 
            for col in cols:
                tree.heading(col, text=col)
 
            vsb.pack(side="right",  fill="y")
            hsb.pack(side="bottom", fill="x")
            tree.pack(fill="x", expand=False)
 
            # ✅ Row white — only Status column colored
            for row in rows:
                display = list(row)
                status  = display[4]
                if status == "unread":
                    display[4] = "● unread"
                else:
                    display[4] = "✓ read"
                tree.insert("", "end", values=display, tags=(status,))
 
            tree.tag_configure("unread", foreground="#E1AD01")
            tree.tag_configure("read",   foreground="#7F8C8D")
 
        load_notifs()
 
        def send_msg():
            selected_user = user_var.get()
            msg = msg_entry.get().strip()
            uid = user_map.get(selected_user)
            if not uid or not msg:
                messagebox.showwarning("Empty", "User aur Message dono chahiye!")
                return
            conn2 = None
            try:
                conn2 = get_connection()
                cur2 = conn2.cursor()
                cur2.execute(
                    "INSERT INTO notifications (user_id, message, status) VALUES (%s,%s,'unread')",
                    (uid, msg))
                conn2.commit()
                messagebox.showinfo("Sent", "Notification sent! ✅")
                msg_entry.delete(0, "end")
                load_notifs(search_var.get().strip(), filter_var.get())
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                if conn2:
                    conn2.close()
 
        search_var.trace_add("write",
            lambda *a: load_notifs(search_var.get().strip(), filter_var.get()))
 
        
    # ================================================================
    # SHOW REPORTS
    # ================================================================
    def show_reports(self):
        sf = self._make_scroll_area()
 
        # ---- Header ----
        header = tk.Frame(sf, bg="#0D1B2A")
        header.pack(fill="x", padx=25, pady=(20, 5))
        tk.Label(header, text="📊 Reports",
                 font=("Helvetica", 18, "bold"),
                 bg="#0D1B2A", fg="white").pack(side="left")
 
        # ---- Summary Cards (always visible) ----
        cards_frame = tk.Frame(sf, bg="#0D1B2A")
        cards_frame.pack(fill="x", padx=25, pady=(10, 5))
 
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM books")
            total_books = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM loans")
            total_loans = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM fines WHERE status='unpaid'")
            unpaid = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM users WHERE role != 'librarian'")
            members = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM loans WHERE status='borrowed'")
            active = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM loans WHERE due_date < CURDATE() AND status='borrowed'")
            overdue = cur.fetchone()[0]
            cur.execute("SELECT COALESCE(SUM(amount),0) FROM fines WHERE status='unpaid'")
            total_fine = cur.fetchone()[0]
        except:
            total_books = total_loans = unpaid = members = active = overdue = total_fine = 0
        finally:
            if conn:
                conn.close()

        def export_summary():
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt")],
                initialfile="Library_Summary_Report.txt"
            )
            if not file_path:
                return
            try:
                import datetime
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("========== LIBRARY REPORT ==========\n")
                    f.write(f"Generated On     : {datetime.datetime.now().strftime('%d/%m/%Y %I:%M %p')}\n\n")
                    f.write(f"Total Books      : {total_books}\n")
                    f.write(f"Available Books  : {total_books - active}\n")
                    f.write(f"Issued Books     : {active}\n")
                    f.write(f"Total Users      : {members}\n")
                    f.write(f"Active Loans     : {active}\n")
                    f.write(f"Overdue Books    : {overdue}\n")
                    f.write(f"Total Fine       : Rs. {total_fine}\n")
                    f.write("=====================================\n")

                messagebox.showinfo("Exported", f"Summary report saved!\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        for ico, lbl, val, clr, bg_c in [
            ("📚", "Total Books",   str(total_books),   "#1E6FFF", "#0A2A6E"),
            ("👥", "Total Members", str(members),       "#9B59B6", "#2E1050"),
            ("📜", "Total Loans",   str(total_loans),   "#2ECC71", "#0A3D1F"),
            ("📖", "Active Loans",  str(active),        "#E1AD01", "#4A3500"),
            ("⚠️", "Overdue",       str(overdue),       "#E74C3C", "#4A0F0F"),
            ("💸", "Unpaid Fines",  f"Rs.{total_fine}", "#E74C3C", "#4A0F0F"),
        ]:
            c = tk.Frame(cards_frame, bg=bg_c, padx=12, pady=14,
                         highlightthickness=2, highlightbackground=clr)
            c.pack(side="left", padx=5, expand=True, fill="both")
            tk.Label(c, text=ico, font=("Arial", 20), bg=bg_c, fg=clr).pack()
            tk.Label(c, text=val, font=("Helvetica", 16, "bold"),
                     bg=bg_c, fg="white").pack(pady=3)
            tk.Label(c, text=lbl, font=("Arial", 8),
                     bg=bg_c, fg="#B0BEC5").pack()
 
        tk.Frame(sf, bg="#1A2456", height=1).pack(fill="x", padx=25, pady=(12, 8))
 
        # ✅ Report buttons — Books, Users, Fines (no dropdown)
        btn_bar = tk.Frame(sf, bg="#0D1B2A")
        btn_bar.pack(fill="x", padx=25, pady=(0, 10))

    
        tk.Button(sf, text="📄 Export Summary Report",
                  bg="#2ECC71", fg="white",
                  font=("Arial", 9, "bold"), bd=0,
                  cursor="hand2", padx=12, pady=6,
                  activebackground="#27AE60",
                  command=export_summary).pack(anchor="w", padx=25, pady=(0, 10))
 
        tk.Label(btn_bar, text="Detailed Report:",
                 font=("Arial", 10, "bold"),
                 bg="#0D1B2A", fg="#B0BEC5").pack(side="left", padx=(0, 12))
 
        report_btns = {}
        report_options = [
            ("Books Report", "#1E6FFF"),
            ("Users Report", "#9B59B6"),
            ("Fines Report", "#E74C3C"),
        ]
 
        section_lbl = tk.Label(sf, text="",
                               font=("Helvetica", 11, "bold"),
                               bg="#0D1B2A", fg="#E1AD01")
        section_lbl.pack(anchor="w", padx=25, pady=(0, 5))
 
        table_frame = tk.Frame(sf, bg="#0D1B2A")
        table_frame.pack(fill="x", expand=False, padx=25, pady=(0, 20))
 
        def make_rep_treeview(parent, cols, rows):
            style = ttk.Style()
            style.theme_use("clam")
            style.configure("Rep.Treeview",
                            background="#111D45", foreground="white",
                            rowheight=30, fieldbackground="#111D45",
                            borderwidth=0, relief="flat",
                            bordercolor="#111D45", lightcolor="#111D45", darkcolor="#111D45",
                            font=("Arial", 10))
            style.configure("Rep.Treeview.Heading",
                            background="#0A1628", foreground="#E1AD01",
                            font=("Arial", 10, "bold"), relief="flat",
                            bordercolor="#0A1628", lightcolor="#0A1628", darkcolor="#0A1628")
            style.map("Rep.Treeview.Heading",
                      background=[("active", "#1A2456"), ("pressed", "#1E6FFF")],
                      foreground=[("active", "#E1AD01"), ("pressed", "white")])
            style.map("Rep.Treeview",
                      background=[("selected", "#3A2E00")],
                      foreground=[("selected", "#E1AD01")])
            style.layout("Rep.Treeview", [
                ("Rep.Treeview.treearea", {"sticky": "nswe"})
            ])

            row_count = max(1, min(len(rows), 20))
            vsb = ttk.Scrollbar(parent, orient="vertical")
            hsb = ttk.Scrollbar(parent, orient="horizontal")
            tree = ttk.Treeview(parent, columns=cols, show="headings",
                                style="Rep.Treeview", height=row_count,
                                yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            vsb.config(command=tree.yview)
            hsb.config(command=tree.xview)
            for col in cols:
                tree.heading(col, text=col)
            vsb.pack(side="right",  fill="y")
            hsb.pack(side="bottom", fill="x")
            tree.pack(fill="x", expand=False)
            return tree
 
        def load_detail(report_type):
            for name, btn in report_btns.items():
                if name == report_type:
                    btn.config(bg=dict(report_options)[name], fg="white")
                else:
                    btn.config(bg="#1A2456", fg="#B0BEC5")
 
            for w in table_frame.winfo_children():
                w.destroy()
 
            section_lbl.config(text=f"📋 {report_type}")
 
            conn = None
            try:
                conn = get_connection()
                cur = conn.cursor()
 
                if report_type == "Books Report":
                    cur.execute("""
                        SELECT b.book_id, b.title, b.author,
                               COALESCE(c.name, 'Uncategorized'),
                               b.quantity, b.available_copies,
                               COUNT(l.loan_id) as total_issued
                        FROM books b
                        LEFT JOIN categories c ON b.category_id = c.category_id
                        LEFT JOIN loans l ON b.book_id = l.book_id
                        GROUP BY b.book_id, b.title, b.author,
                                 c.name, b.quantity, b.available_copies
                        ORDER BY total_issued DESC
                    """)
                    rows = cur.fetchall()
                    cols = ("ID", "Title", "Author", "Category",
                            "Total Copies", "Available", "Times Issued")
                    tree = make_rep_treeview(table_frame, cols, rows)
                    tree.column("ID",           width=40,  anchor="center")
                    tree.column("Title",        width=190, anchor="w")
                    tree.column("Author",       width=130, anchor="w")
                    tree.column("Category",     width=110, anchor="center")
                    tree.column("Total Copies", width=90,  anchor="center")
                    tree.column("Available",    width=80,  anchor="center")
                    tree.column("Times Issued", width=90,  anchor="center")
                    for row in rows:
                        tag = "zero" if row[5] == 0 else ""
                        tree.insert("", "end", values=row, tags=(tag,))
                    tree.tag_configure("zero", foreground="#E74C3C")
 
                elif report_type == "Users Report":
                    cur.execute("""
                        SELECT u.user_id, u.name, u.email,
                               COUNT(DISTINCT l.loan_id),
                               COUNT(DISTINCT CASE WHEN l.status='borrowed'
                                     THEN l.loan_id END),
                               COALESCE(SUM(CASE WHEN f.status='unpaid'
                                     THEN f.amount ELSE 0 END), 0)
                        FROM users u
                        LEFT JOIN loans l ON u.user_id = l.user_id
                        LEFT JOIN fines f ON u.user_id = f.user_id
                        WHERE u.role != 'librarian'
                        GROUP BY u.user_id, u.name, u.email
                        ORDER BY 4 DESC
                    """)
                    rows = cur.fetchall()
                    cols = ("ID", "Name", "Email",
                            "Total Loans", "Active Loans", "Pending Fine (Rs.)")
                    tree = make_rep_treeview(table_frame, cols, rows)
                    tree.column("ID",                 width=40,  anchor="center")
                    tree.column("Name",               width=150, anchor="w")
                    tree.column("Email",              width=210, anchor="w")
                    tree.column("Total Loans",        width=90,  anchor="center")
                    tree.column("Active Loans",       width=90,  anchor="center")
                    tree.column("Pending Fine (Rs.)", width=130, anchor="center")
                    for row in rows:
                        tag = "fine" if row[5] > 0 else ""
                        tree.insert("", "end", values=row, tags=(tag,))
                    tree.tag_configure("fine", foreground="#E74C3C")
 
                elif report_type == "Fines Report":
                    cur.execute("""
                        SELECT f.fine_id, u.name, b.title,
                               f.amount, f.status, f.created_at,
                               DATEDIFF(CURDATE(), l.due_date)
                        FROM fines f
                        JOIN users u ON f.user_id = u.user_id
                        JOIN loans l ON f.loan_id = l.loan_id
                        JOIN books b ON l.book_id = b.book_id
                        ORDER BY f.status ASC, f.amount DESC
                    """)
                    rows = cur.fetchall()
                    cols = ("Fine ID", "User", "Book",
                            "Amount (Rs.)", "Status", "Issued Date", "Overdue Days")
                    tree = make_rep_treeview(table_frame, cols, rows)
                    tree.column("Fine ID",      width=70,  anchor="center")
                    tree.column("User",         width=130, anchor="w")
                    tree.column("Book",         width=190, anchor="w")
                    tree.column("Amount (Rs.)", width=100, anchor="center")
                    tree.column("Status",       width=90,  anchor="center")
                    tree.column("Issued Date",  width=130, anchor="center")
                    tree.column("Overdue Days", width=100, anchor="center")
                    for row in rows:
                        display = list(row)
                        status  = display[4]
                        display[4] = "✕ unpaid" if status == "unpaid" else "✓ paid"
                        tree.insert("", "end", values=display, tags=(status,))
                    tree.tag_configure("unpaid", foreground="#E74C3C")
                    tree.tag_configure("paid",   foreground="#2ECC71")
 
            except Exception as e:
                messagebox.showerror("DB Error", str(e))
            finally:
                if conn:
                    conn.close()
 
        for rname, rcolor in report_options:
            b = tk.Button(btn_bar,
                          text=rname,
                          bg="#1A2456", fg="#B0BEC5",
                          font=("Arial", 9, "bold"), bd=0,
                          cursor="hand2", padx=12, pady=6,
                          relief="flat",
                          activebackground=rcolor,
                          activeforeground="white",
                          command=lambda r=rname: load_detail(r))
            b.pack(side="left", padx=4)
            report_btns[rname] = b

    # ================================================================
    # SHOW PROFILE
    # ================================================================
    def show_profile(self):
        sf = self._make_scroll_area()

        conn = None
        librarian = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""SELECT librarian_id, name, email, created_at,
                                  phone, address, profile_pic
                           FROM librarian WHERE librarian_id=%s""", (self.librarian_id,))
            librarian = cur.fetchone()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
        finally:
            if conn:
                conn.close()

        if not librarian:
            tk.Label(sf, text="Profile not found.",
                     font=("Arial", 11), bg="#0D1B2A", fg="#7F8C8D").pack(pady=30)
            return

        lib_id, name, email, created_at, phone, address, profile_pic = librarian
        initial = name[0].upper() if name else "L"

        tk.Label(sf, text="👤 My Profile",
                 font=("Helvetica", 18, "bold"),
                 bg="#0D1B2A", fg="white").pack(padx=25, pady=(20, 10), anchor="w")

        # ---- Profile Header (no border, no duplicate text) ----
        header_card = tk.Frame(sf, bg="#0D1B2A")
        header_card.pack(fill="x", padx=25, pady=(0, 15))

        center_col = tk.Frame(header_card, bg="#0D1B2A")
        center_col.pack(pady=15)

        avatar_size = 150
        avatar_frame = tk.Frame(center_col, bg="#0D1B2A", width=avatar_size, height=avatar_size,
                                highlightthickness=0, bd=0)
        avatar_frame.pack()
        avatar_frame.pack_propagate(False)

        photo_path = profile_pic if profile_pic else "assets/images/librarian_profimg.png"
        self._profile_photo_ref = None

        try:
            hi_res = avatar_size * 4
            img = Image.open(photo_path).convert("RGBA").resize((hi_res, hi_res))
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
            print("Avatar load error:", e, "| path tried:", photo_path)
            avatar_lbl = tk.Label(avatar_frame, text=initial,
                                  font=("Helvetica", 26, "bold"),
                                  bg="#E1AD01", fg="#0D1B2A", bd=0, highlightthickness=0)
        avatar_lbl.place(relx=0.5, rely=0.5, anchor="center")

        edit_icon = tk.Label(avatar_frame, text="✏️", font=("Arial", 12),
                             bg="#0D1B2A", fg="white", cursor="hand2")
        edit_icon.place(relx=1.0, rely=1.0, anchor="se")
        edit_icon.bind("<Button-1>", lambda e, lid=lib_id: self._change_profile_photo(lid))

        
        # ---- Personal Information Card (vertical list) ----
        info_card = tk.Frame(sf, bg="#0D1B2A")
        info_card.pack(fill="x", padx=25, pady=(0, 20))

        info_header = tk.Frame(info_card, bg="#0D1B2A")
        info_header.pack(fill="x", padx=20, pady=(15, 10))

        tk.Label(info_header, text="Personal Information",
                 font=("Helvetica", 12, "bold"),
                 bg="#111D45", fg="#E1AD01").pack(side="left")

        pencil_lbl = tk.Label(info_header, text="✏️", font=("Arial", 12),
                              bg="#111D45", fg="#1E6FFF", cursor="hand2")
        pencil_lbl.pack(side="right")
        pencil_lbl.bind("<Button-1>",
                lambda e: self._edit_profile_dialog(lib_id, name, email, phone, address))

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

    # ================================================================
    # EDIT PROFILE DIALOG (Name / Email / Phone / Address)
    # ================================================================
    def _edit_profile_dialog(self, lib_id, current_name, current_email, current_phone, current_address):
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
                cur.execute("""UPDATE librarian
                              SET name=%s, email=%s, phone=%s, address=%s
                              WHERE librarian_id=%s""",
                           (new_name, new_email, new_phone, new_address, lib_id))
                conn.commit()
                win.destroy()
                messagebox.showinfo("Success", "Profile updated!")
                self.librarian_name = new_name
                self.librarian_lbl.config(text=f"🔑 {new_name}")
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
    def _change_profile_photo(self, lib_id):
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
        new_filename = f"librarian_{lib_id}{ext}"
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
            cur.execute("UPDATE librarian SET profile_pic=%s WHERE librarian_id=%s",
                       (new_path.replace("\\", "/"), lib_id))
            conn.commit()
            messagebox.showinfo("Success", f"Profile photo updated!\nSaved at: {new_path}")
            self.show_profile()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
        finally:
            if conn:
                conn.close()

    # ================================================================
    # SHOW SETTINGS
    # ================================================================
    def show_settings(self):
        sf = self._make_scroll_area()

        conn = None
        fine_rate, loan_days = 10.00, 14
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT fine_per_day, loan_period_days FROM settings WHERE setting_id=1")
            row = cur.fetchone()
            if row:
                fine_rate, loan_days = row
        except Exception as e:
            print("Settings load error:", e)
        finally:
            if conn:
                conn.close()

        tk.Label(sf, text="⚙️ Settings",
                 font=("Helvetica", 18, "bold"),
                 bg="#0D1B2A", fg="white").pack(padx=25, pady=(20, 10), anchor="w")

        # ---- Change Password Card ----
        pwd_card = tk.Frame(sf, bg="#111D45",
                            highlightthickness=1, highlightbackground="#1E6FFF")
        pwd_card.pack(fill="x", padx=25, pady=(0, 15))

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

                cur2.execute("SELECT password FROM librarian WHERE librarian_id=%s", (self.librarian_id,))
                row = cur2.fetchone()
                if not row or not bcrypt.checkpw(current_pwd.encode(), row[0].encode()):
                    messagebox.showerror("Incorrect", "Current password is incorrect.")
                    return

                hashed_pwd = bcrypt.hashpw(new_pwd.encode(), bcrypt.gensalt()).decode()
                cur2.execute("UPDATE librarian SET password=%s WHERE librarian_id=%s",
                            (hashed_pwd, self.librarian_id))
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

        # ---- Library Settings Card ----
        lib_card = tk.Frame(sf, bg="#111D45",
                            highlightthickness=1, highlightbackground="#1A2456")
        lib_card.pack(fill="x", padx=25, pady=(0, 15))

        header_row = tk.Frame(lib_card, bg="#111D45")
        header_row.pack(fill="x", padx=20, pady=(15, 5))

        tk.Label(header_row, text="📚 Library Settings",
                 font=("Helvetica", 12, "bold"),
                 bg="#111D45", fg="#E1AD01").pack(side="left")

        fields_row = tk.Frame(lib_card, bg="#111D45")
        fields_row.pack(fill="x", padx=20, pady=(10, 10))

        col1 = tk.Frame(fields_row, bg="#111D45")
        col1.pack(side="left", padx=(0, 20))
        tk.Label(col1, text="Fine Rate (Rs./day)", font=("Arial", 8),
                 bg="#111D45", fg="#7F8C8D").pack(anchor="w")
        fine_entry = tk.Entry(col1, font=("Arial", 11), width=15,
                              bg="#1A2456", fg="white", insertbackground="white",
                              bd=0, highlightthickness=1, highlightbackground="#1E6FFF")
        fine_entry.insert(0, str(fine_rate))
        fine_entry.pack(pady=(4, 0), ipady=5)

        col2 = tk.Frame(fields_row, bg="#111D45")
        col2.pack(side="left")
        tk.Label(col2, text="Default Loan Period (days)", font=("Arial", 8),
                 bg="#111D45", fg="#7F8C8D").pack(anchor="w")
        loan_entry = tk.Entry(col2, font=("Arial", 11), width=15,
                              bg="#1A2456", fg="white", insertbackground="white",
                              bd=0, highlightthickness=1, highlightbackground="#1E6FFF")
        loan_entry.insert(0, str(loan_days))
        loan_entry.pack(pady=(4, 0), ipady=5)

        def save_settings():
            try:
                new_fine = float(fine_entry.get().strip())
                new_days = int(loan_entry.get().strip())
                if new_fine < 0 or new_days < 1:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid",
                    "Fine rate must be a positive number and loan period a positive integer.")
                return

            conn2 = None
            try:
                conn2 = get_connection()
                cur2 = conn2.cursor()
                cur2.execute("""UPDATE settings SET fine_per_day=%s, loan_period_days=%s
                               WHERE setting_id=1""", (new_fine, new_days))
                conn2.commit()
                messagebox.showinfo("Saved", "Settings updated successfully!")
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                if conn2:
                    conn2.close()

        tk.Button(lib_card, text="💾 Save Settings",
                  bg="#2ECC71", fg="white", bd=0, cursor="hand2",
                  font=("Arial", 10, "bold"), padx=14, pady=6,
                  command=save_settings).pack(anchor="w", padx=20, pady=(0, 20))


        # ---- Database Backup Card ----
        backup_card = tk.Frame(sf, bg="#111D45",
                              highlightthickness=1, highlightbackground="#1A2456")
        backup_card.pack(fill="x", padx=25, pady=(0, 15))

        tk.Label(backup_card, text="🗄️ Database Backup",
                 font=("Helvetica", 12, "bold"),
                 bg="#111D45", fg="#E1AD01").pack(anchor="w", padx=20, pady=(15, 5))

        tk.Label(backup_card, text="Create a backup copy of the entire database for safekeeping.",
                 font=("Arial", 9), bg="#111D45", fg="#7F8C8D").pack(anchor="w", padx=20, pady=(0, 10))

        def backup_database():
            save_path = filedialog.asksaveasfilename(
                defaultextension=".sql",
                filetypes=[("SQL files", "*.sql")],
                initialfile=f"readhub_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.sql",
                title="Save Database Backup As"
            )
            if not save_path:
                return  # user cancelled

            try:
                result = subprocess.run(
                    [
                        "mysqldump",
                        "-u", "root",
                        "Amna@2026!",
                        "readhub"
                    ],
                    stdout=open(save_path, "w"),
                    stderr=subprocess.PIPE,
                    text=True
                )
                if result.returncode != 0:
                    messagebox.showerror("Backup Failed", result.stderr)
                else:
                    messagebox.showinfo("Success", f"Backup saved successfully at:\n{save_path}")
            except FileNotFoundError:
                messagebox.showerror("Error", "mysqldump not found. Make sure MySQL is installed and added to PATH.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(backup_card, text="🗄️ Backup Database Now",
                  bg="#1E6FFF", fg="white", bd=0, cursor="hand2",
                  font=("Arial", 10, "bold"), padx=14, pady=6,
                  command=backup_database).pack(anchor="w", padx=20, pady=(0, 20))

        # ---- About Card ----
        about_card = tk.Frame(sf, bg="#111D45",
                              highlightthickness=1, highlightbackground="#1A2456")
        about_card.pack(fill="x", padx=25, pady=(0, 20))

        tk.Label(about_card, text="ℹ️ About ReadHub",
                 font=("Helvetica", 12, "bold"),
                 bg="#111D45", fg="#E1AD01").pack(anchor="w", padx=20, pady=(15, 10))

        about_info = [
            ("Application", "ReadHub — Library Management System"),
            ("Version", "1.0.0"),
            ("Built With", "Python (Tkinter) + MySQL"),
            ("Developed By", "Amna Shakeel"),
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
    # LOGOUT & SESSION
    # ================================================================
    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.controller.show_frame("HomePage")
 
    def update_session(self, user_id=None, user_name="Librarian", **kwargs):
        self.librarian_id   = user_id
        self.librarian_name = user_name
        self.librarian_lbl.config(text=f"🔑 {user_name}")
        self.show_home()