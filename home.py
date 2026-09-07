import tkinter as tk
from tkinter import messagebox
import bcrypt
from PIL import Image, ImageTk
from db import get_connection
import re
EMAIL_REGEX = r"^[^@\s.]+@[^@\s.]+\.[^@\s.]+$"
import smtplib
import random
import time
from email.mime.text import MIMEText

SENDER_EMAIL = "amnashakeelpk@gmail.com"
SENDER_APP_PASSWORD = "ytfhvyruotsohwnu"
 
class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller
        self.selected_role = tk.StringVar(value="user")
        self.otp_store = {}
        self.build_ui()
 
    def build_ui(self):
        # ==================== LEFT PANEL ====================
        left = tk.Frame(self, bg="white")
        left.place(relx=0, rely=0, relwidth=0.55, relheight=1)
 
        tk.Label(left, text="WELCOME TO READHUB", font=("Helvetica", 38, "bold"),
                 bg="white", fg="#0A0F2C").pack(pady=(80, 0))
 
 
        try:
            img = Image.open("assets/images/logo.png")
            img = img.resize((500, 500), Image.Resampling.LANCZOS)
            self.logo = ImageTk.PhotoImage(img)
            tk.Label(left, image=self.logo, bg="white").pack(expand=True)
        except:
            tk.Label(left, text="📚", font=("Arial", 90), bg="white").pack(expand=True)
 
        # ==================== RIGHT PANEL ====================
        right = tk.Frame(self, bg="#0A0F2C")
        right.place(relx=0.55, rely=0, relwidth=0.45, relheight=1)
 
        self.dynamic = tk.Frame(right, bg="#0A0F2C")
        self.dynamic.place(relx=0.5, rely=0.5, anchor="center")
 
        self.show_main()
 
    # ==================== MAIN MENU ====================
    def show_main(self):
        self.clear()
        tk.Label(self.dynamic, text="Get Started", font=("Helvetica", 26, "bold"),
                 bg="#0A0F2C", fg="white").pack(pady=(0, 5))
        tk.Label(self.dynamic, text="Welcome to your Account!", font=("Arial", 11),
                 bg="#0A0F2C", fg="#AAB7B8").pack(pady=(0, 35))
 
        self.btn("Login to Account", "#1E6FFF", self.show_login).pack(pady=8)
        self.btn("Create New Account", "#2ECC71", self.show_register).pack(pady=8)
 
    # ==================== LOGIN FORM (UI) ====================
    def show_login(self):
        self.clear()
 
        tk.Label(self.dynamic, text="Login", font=("Helvetica", 24, "bold"),
                 bg="#0A0F2C", fg="white").pack(pady=(0, 5))
        tk.Label(self.dynamic, text="Sign in to your account", font=("Arial", 10),
                 bg="#0A0F2C", fg="#8899AA").pack(pady=(0, 25))
 
        role_frame = tk.Frame(self.dynamic, bg="#1A253A")
        role_frame.pack(pady=(0, 20))
 
        self.librarian_btn = tk.Button(role_frame, text="Librarian", font=("Arial", 10, "bold"),
                                    bg="#2C3E50", fg="white", bd=0, padx=25, pady=8,
                                    cursor="hand2", command=lambda: self.pick_role("librarian"))
        self.librarian_btn.pack(side="left", padx=2)
 
        self.user_btn = tk.Button(role_frame, text="User", font=("Arial", 10, "bold"),
                                   bg="#1E6FFF", fg="white", bd=0, padx=25, pady=8,
                                   cursor="hand2", command=lambda: self.pick_role("user"))
        self.user_btn.pack(side="left", padx=2)
 
        self.role_lbl = tk.Label(self.dynamic, text="Selected: User",
                                  font=("Arial", 9, "bold"), bg="#0A0F2C", fg="#E1AD01")
        self.role_lbl.pack(pady=(0, 25))
 
        self.login_email = self.input_field("Email", width=32)
        self.login_pass  = self.input_field("Password", is_pass=True, width=32)
 
        forgot_lbl = tk.Label(self.dynamic, text="Forgot password?", font=("Arial", 10, "underline"),
                 bg="#0A0F2C", fg="#5DADE2", cursor="hand2")
        forgot_lbl.pack(anchor="e", padx=40, pady=(0, 15))
        forgot_lbl.bind("<Button-1>", lambda e: self.show_forgot_password())
 
        self.btn("Login", "#E1AD01", self.handle_login).pack(pady=(0, 15))
 
        tk.Label(self.dynamic, text="Don't have an account? Register here",
                 font=("Arial", 9, "underline"), bg="#0A0F2C", fg="#2ECC71",
                 cursor="hand2").pack(pady=(0, 25))
        self.dynamic.winfo_children()[-1].bind("<Button-1>", lambda e: self.show_register())
 
        tk.Button(self.dynamic, text="Back", font=("Arial", 10, "bold"),
                  bg="#E6A817", fg="white",
                  bd=0, padx=20, pady=6, cursor="hand2",
                  activebackground="#C8920E", activeforeground="white",
                  command=self.show_main).pack()
 
    def pick_role(self, role):
        self.selected_role.set(role)
        self.librarian_btn.config(bg="#1E6FFF" if role == "librarian" else "#2C3E50")
        self.user_btn.config(bg="#1E6FFF" if role == "user" else "#2C3E50")
        self.role_lbl.config(text=f"Selected: {'Librarian' if role == 'librarian' else 'User'}",
                             fg="#E1AD01")
    # ==================== REGISTER FORM (UI) ====================
    def show_register(self):
        self.clear()
 
        tk.Label(self.dynamic, text="Register", font=("Helvetica", 24, "bold"),
                 bg="#0A0F2C", fg="white").pack(pady=(0, 5))
        tk.Label(self.dynamic, text="Create your new account", font=("Arial", 10),
                 bg="#0A0F2C", fg="#8899AA").pack(pady=(0, 20))
 
        self.reg_name    = self.input_field("Full Name", width=32)
        self.reg_email   = self.input_field("Email", width=32)
        self.reg_phone   = self.input_field("Phone", width=32)
        self.reg_address = self.input_field("Address", width=32)
        self.reg_pass    = self.input_field("Password", is_pass=True, width=32)
        self.reg_cpass   = self.input_field("Confirm Password", is_pass=True, width=32)
    
        
 
        self.btn("Register", "#2ECC71", self.handle_register).pack(pady=(10, 15))
 
        tk.Label(self.dynamic, text="Already have an account? Login here",
                 font=("Arial", 9, "underline"), bg="#0A0F2C", fg="#1E6FFF",
                 cursor="hand2").pack(pady=(0, 25))
        self.dynamic.winfo_children()[-1].bind("<Button-1>", lambda e: self.show_login())
 
        tk.Button(self.dynamic, text="Back", font=("Arial", 10, "bold"),
                  bg="#E6A817", fg="white",
                  bd=0, padx=20, pady=6, cursor="hand2",
                  activebackground="#C8920E", activeforeground="white",
                  command=self.show_main).pack()
 
    # ==================== HANDLERS ====================
    # ==================== FORGOT PASSWORD ====================
    def show_forgot_password(self):
        win = tk.Toplevel(self)
        win.title("Reset Password")
        win.geometry("380x560")
        win.configure(bg="#0D1B2A")
        win.grab_set()

        tk.Label(win, text="Reset Password", font=("Helvetica", 18, "bold"),
                 bg="#0D1B2A", fg="white").pack(pady=(25, 5))
        tk.Label(win, text="Verify your email to reset password", font=("Arial", 9),
                 bg="#0D1B2A", fg="#8899AA").pack(pady=(0, 15))

        role_var = tk.StringVar(value=self.selected_role.get())
        role_frame = tk.Frame(win, bg="#0D1B2A")
        role_frame.pack(pady=(0, 15))
        tk.Radiobutton(role_frame, text="User", variable=role_var, value="user",
                        bg="#0D1B2A", fg="white", selectcolor="#1A2456",
                        activebackground="#0D1B2A", activeforeground="white").pack(side="left", padx=10)
        tk.Radiobutton(role_frame, text="Librarian", variable=role_var, value="librarian",
                        bg="#0D1B2A", fg="white", selectcolor="#1A2456",
                        activebackground="#0D1B2A", activeforeground="white").pack(side="left", padx=10)

        def field(parent, placeholder, is_pass=False):
            e = tk.Entry(parent, font=("Arial", 11), width=30, bg="#1A2456", fg="white",
                         insertbackground="white", bd=0, show="*" if is_pass else "",
                         highlightthickness=1, highlightbackground="#1E6FFF")
            e.pack(padx=30, pady=6, ipady=6)
            return e

        tk.Label(win, text="Email", font=("Arial", 9, "bold"),
                 bg="#0D1B2A", fg="#AAB7B8").pack(anchor="w", padx=30)
        email_e = field(win, "Email")

        status_lbl = tk.Label(win, text="", font=("Arial", 8), bg="#0D1B2A", fg="#E74C3C")
        status_lbl.pack(pady=(0, 5))

        otp_section = tk.Frame(win, bg="#0D1B2A")
        otp_section.pack(fill="x")

        otp_e = {"widget": None}
        pass_e = {"widget": None}
        cpass_e = {"widget": None}

        def send_otp():
            email = email_e.get().strip()
            role = role_var.get()

            if not re.match(EMAIL_REGEX, email):
                status_lbl.config(text="Invalid email format", fg="#E74C3C")
                return

            table = "librarian" if role == "librarian" else "users"
            id_col = "librarian_id" if role == "librarian" else "user_id"

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT {id_col} FROM {table} WHERE email=%s", (email,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                status_lbl.config(text="No account found with this email", fg="#E74C3C")
                return

            status_lbl.config(text="Sending OTP...", fg="#F1C40F")
            win.update()

            sent = self.send_otp_email(email)
            if not sent:
                status_lbl.config(text="Failed to send OTP - check internet", fg="#E74C3C")
                return

            status_lbl.config(text="OTP sent to your email!", fg="#2ECC71")
            send_btn.config(state="disabled", text="OTP Sent")
            email_e.config(state="disabled")

            tk.Label(otp_section, text="Enter OTP", font=("Arial", 9, "bold"),
                     bg="#0D1B2A", fg="#AAB7B8").pack(anchor="w", padx=30)
            otp_e["widget"] = field(otp_section, "Enter OTP")

            tk.Label(otp_section, text="New Password", font=("Arial", 9, "bold"),
                     bg="#0D1B2A", fg="#AAB7B8").pack(anchor="w", padx=30)
            pass_e["widget"] = field(otp_section, "New Password", is_pass=True)

            tk.Label(otp_section, text="Confirm New Password", font=("Arial", 9, "bold"),
                     bg="#0D1B2A", fg="#AAB7B8").pack(anchor="w", padx=30)
            cpass_e["widget"] = field(otp_section, "Confirm Password", is_pass=True)
            submit_btn.pack(pady=15)

        def submit():
            email = email_e.get().strip()
            role = role_var.get()
            otp_input = otp_e["widget"].get().strip()
            new_pwd = pass_e["widget"].get().strip()
            cpwd = cpass_e["widget"].get().strip()

            if not otp_input or not new_pwd or not cpwd:
                messagebox.showwarning("Error", "All fields required", parent=win)
                return

            record = self.otp_store.get(email)
            if not record:
                messagebox.showerror("Error", "Please request OTP first", parent=win)
                return

            if time.time() - record["time"] > 300:
                messagebox.showerror("Error", "OTP expired, please request a new one", parent=win)
                return

            if otp_input != record["code"]:
                messagebox.showerror("Error", "Incorrect OTP", parent=win)
                return

            if new_pwd != cpwd:
                messagebox.showerror("Error", "Passwords don't match", parent=win)
                return
            if len(new_pwd) < 6:
                messagebox.showwarning("Error", "Password must be at least 6 characters", parent=win)
                return
            if not re.search(r"\d", new_pwd) or not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-]", new_pwd):
                messagebox.showwarning("Error", "Password must contain at least 1 number and 1 special character", parent=win)
                return

            table = "librarian" if role == "librarian" else "users"

            conn = get_connection()
            cursor = conn.cursor()
            hashed_pwd = bcrypt.hashpw(new_pwd.encode(), bcrypt.gensalt()).decode()
            cursor.execute(f"UPDATE {table} SET password=%s WHERE email=%s", (hashed_pwd, email))
            conn.commit()
            conn.close()

            del self.otp_store[email]
            win.destroy()
            messagebox.showinfo("Success", "Password reset successfully! Please login with your new password.")

        send_btn = tk.Button(win, text="Send OTP", bg="#5DADE2", fg="white",
                              font=("Arial", 10, "bold"), bd=0, cursor="hand2",
                              width=20, height=1, command=send_otp)
        send_btn.pack(pady=(5, 10))

        submit_btn = tk.Button(win, text="Reset Password", bg="#1E6FFF", fg="white",
                                font=("Arial", 11, "bold"), bd=0, cursor="hand2",
                                width=22, height=2, command=submit)
        
    def handle_login(self):
        email = self.login_email.get().strip()
        pwd   = self.login_pass.get().strip()
        role  = self.selected_role.get()
 
        # ignore placeholder text
        if email == "Email":    email = ""
        if pwd   == "Password": pwd   = ""
 
        if not email or not pwd:
            messagebox.showwarning("Error", "All fields required")
            return
 
        if not re.match(EMAIL_REGEX, email):
            messagebox.showerror("Error", "Invalid email format")
            return
 
        conn   = get_connection()
        cursor = conn.cursor()
 
        table  = "librarian" if role == "librarian" else "users"
        id_col = "librarian_id" if role == "librarian" else "user_id"
 
        col_extra = ", role" if table == "users" else ""
        cursor.execute(f"SELECT {id_col}, name, password{col_extra} FROM {table} WHERE email=%s", (email,))
        row = cursor.fetchone()
        conn.close()
 
        if not row:
            messagebox.showerror("Error", "Invalid email - account not found")
            return
 
        if table == "users":
            user_id, name, hashed_pwd, user_role = row
            if user_role == "inactive":
                messagebox.showerror("Account Deactivated",
                    "This account has been deactivated")
                return
        else:
            user_id, name, hashed_pwd = row
 
        if not bcrypt.checkpw(pwd.encode(), hashed_pwd.encode()):
            messagebox.showerror("Error", "Wrong password")
            return
 
        if role == "librarian":
            self.controller.show_frame("LibrarianDashboard", user_id=user_id, user_name=name, role="librarian")
        else:
            self.controller.show_frame("UserDashboard", user_id=user_id, user_name=name, role="user")
 
    def handle_register(self):


        # clear placeholder text before reading values
        for field, placeholder in [(self.reg_name, "Full Name"), (self.reg_email, "Email"),
                                   (self.reg_phone, "Phone"),    (self.reg_address, "Address"),
                                   (self.reg_pass, "Password"),  (self.reg_cpass, "Confirm Password")]:
            if field.get() == placeholder:
                field.delete(0, "end")
 
        name    = self.reg_name.get().strip()
        email   = self.reg_email.get().strip()
        phone   = self.reg_phone.get().strip()
        address = self.reg_address.get().strip()
        pwd     = self.reg_pass.get().strip()
        cpwd    = self.reg_cpass.get().strip()
 
        if not all([name, email, phone, pwd, cpwd]):
            messagebox.showwarning("Error", "All fields required")
            return

        if len(name) < 3 or not re.match(r"^[A-Za-z\s]+$", name):
            messagebox.showwarning("Error", "Enter a valid full name (letters only, min 3 characters)")
            return

        if not re.match(EMAIL_REGEX, email):
            messagebox.showwarning("Error", "Invalid email")
            return

        if not re.match(r"^03\d{9}$", phone):
            messagebox.showwarning("Error", "Enter a valid phone number (e.g. 03001234567)")
            return

        clean_address = re.sub(r"[^A-Za-z0-9\s]", "", address).strip()
        if len(clean_address) < 8 or len(clean_address.split()) < 2:
            messagebox.showwarning("Error", "Enter a complete address (e.g. House 12, Street 5, Islamabad)")
            return
            
        if pwd != cpwd:
            messagebox.showerror("Error", "Passwords don't match")
            return
        if len(pwd) < 6:
            messagebox.showwarning("Error", "Password must be at least 6 characters")
            return
        if not re.search(r"\d", pwd) or not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-]", pwd):
            messagebox.showwarning("Error", "Password must contain at least 1 number and 1 special character")
            return
        
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            conn.close()
            messagebox.showerror("Error", "Email already registered")
            return
 
        hashed_pwd = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT INTO users (name, email, password, phone, address, role) VALUES (%s,%s,%s,%s,%s,%s)",
            (name, email, hashed_pwd, phone, address, "student")
        )
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Account created! Please login.")
        self.show_login()


    def send_otp_email(self, to_email):
        otp = str(random.randint(100000, 999999))
        self.otp_store[to_email] = {"code": otp, "time": time.time()}

        msg = MIMEText(f"Your ReadHub password reset OTP is: {otp}\nThis code expires in 5 minutes.")
        msg["Subject"] = "ReadHub - Password Reset OTP"
        msg["From"] = f"ReadHub <{SENDER_EMAIL}>"
        msg["To"] = to_email

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
            server.quit()
            return True
        except Exception as e:
            print("OTP send error:", e)
            return False
        
    # ==================== WIDGET HELPERS ====================
    def input_field(self, placeholder, is_pass=False, width=28):
        frame = tk.Frame(self.dynamic, bg="#FFFFFF")
        frame.pack(fill="x", padx=5, pady=6)

       
        tk.Label(frame, text=placeholder, font=("Arial", 8, "bold"),
                 bg="#FFFFFF", fg="#5DADE2").pack(anchor="w", padx=15, pady=(4, 0))

        entry_row = tk.Frame(frame, bg="#FFFFFF")
        entry_row.pack(fill="x")

        e = tk.Entry(entry_row, font=("Arial", 11), bg="#FFFFFF", fg="#333333",
                      bd=0, relief="flat", show="•" if is_pass else "",
                      width=width)
        e.pack(side="left", fill="x", expand=True, ipady=10, padx=(15, 0))

        if is_pass:
            eye_btn = tk.Label(entry_row, text="👁", font=("Arial", 11), bg="#FFFFFF",
                                fg="#AAAAAA", cursor="hand2")
            eye_btn.pack(side="right", padx=(5, 15))

            def toggle_eye(event):
                if e.cget("show") == "•":
                    e.config(show="")
                    eye_btn.config(fg="#1E6FFF")
                else:
                    e.config(show="•")
                    eye_btn.config(fg="#AAAAAA")

            eye_btn.bind("<Button-1>", toggle_eye)

        border = tk.Frame(frame, bg="#DDDDDD", height=2)
        border.pack(fill="x", side="bottom")

        e.bind("<FocusIn>",  lambda ev, b=border: b.config(bg="#1E6FFF"))
        e.bind("<FocusOut>", lambda ev, b=border: b.config(bg="#DDDDDD"))

        return e
    def btn(self, text, color, cmd):
        b = tk.Button(self.dynamic, text=text, bg=color, fg="white",
                       font=("Arial", 11, "bold"), width=22, height=2,
                       bd=0, cursor="hand2", activebackground=color, command=cmd)
        b.bind("<Enter>", lambda e: e.widget.config(bg=self.darken(color)))
        b.bind("<Leave>", lambda e: e.widget.config(bg=color))
        return b

    def clear(self):
        for w in self.dynamic.winfo_children():
            w.destroy()

    def darken(self, hex_color):
        return hex_color