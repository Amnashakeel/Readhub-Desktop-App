import tkinter as tk
from tkinter import ttk
from home import HomePage
from user_dashboard import UserDashboard
from librarian_dashboard import LibrarianDashboard

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("ReadHub – Desktop Application")
        self.geometry("1150x720")
        self.configure(bg="#0A0F2C")

        # ---- Global scrollbar theme (applies to ALL tables, set once at startup) ----
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Vertical.TScrollbar", background="#1A2456", troughcolor="#0D1B2A",
                        bordercolor="#0D1B2A", arrowcolor="#E1AD01", relief="flat")
        style.configure("Horizontal.TScrollbar", background="#1A2456", troughcolor="#0D1B2A",
                        bordercolor="#0D1B2A", arrowcolor="#E1AD01", relief="flat")
        style.map("Vertical.TScrollbar",
                  background=[("pressed", "#1E6FFF"), ("active", "#1E6FFF")],
                  arrowcolor=[("pressed", "#E1AD01"), ("active", "#E1AD01")])
        style.map("Horizontal.TScrollbar",
                  background=[("pressed", "#1E6FFF"), ("active", "#1E6FFF")],
                  arrowcolor=[("pressed", "#E1AD01"), ("active", "#E1AD01")])

        container = tk.Frame(self, bg="#0A0F2C")
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for PageClass in (HomePage, UserDashboard, LibrarianDashboard):
            page_name = PageClass.__name__
            frame = PageClass(container, self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("HomePage")

    def show_frame(self, page_name, **kwargs):
        frame = self.frames.get(page_name)
        if not frame:
            print(f"[ERROR] Page not found: {page_name}")
            return
        if hasattr(frame, "update_session"):
            frame.update_session(**kwargs)
        if page_name == "HomePage":
            frame.show_main()
        frame.tkraise()

if __name__ == "__main__":
    app = App()
    app.mainloop()