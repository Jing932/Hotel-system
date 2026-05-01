import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
import random

# ===================== GLOBAL DATA STORAGE =====================
rooms = [
    {"room_no": "101", "type": "Single", "price": "80",  "status": "Available", "floor": "1"},
    {"room_no": "102", "type": "Double", "price": "120", "status": "Available", "floor": "1"},
    {"room_no": "103", "type": "Double", "price": "120", "status": "Available", "floor": "1"},
    {"room_no": "201", "type": "Deluxe", "price": "200", "status": "Available", "floor": "2"},
    {"room_no": "202", "type": "Suite",  "price": "350", "status": "Available", "floor": "2"},
    {"room_no": "203", "type": "Single", "price": "80",  "status": "Available", "floor": "2"},
    {"room_no": "301", "type": "Suite",  "price": "350", "status": "Available", "floor": "3"},
    {"room_no": "302", "type": "Deluxe", "price": "200", "status": "Available", "floor": "3"},
]

members = []
reservations = []
checkins = []       # active check-ins
history = []        # checkout history
transactions = []   # all financial transactions
housekeeping_log = []
folio_items = []    # extra charges per room

users = {"admin": "123", "manager": "manager123"}
current_user = {"name": "admin"}

# ===================== ROOT WINDOW =====================
root = tk.Tk()
root.title("CHMS1 HOTEL - Hotel Management System")
root.geometry("1280x820")
root.resizable(True, True)
root.configure(bg="#2c3144")

# ===================== COLORS =====================
BG_LOGIN      = "#254edb"
BG_DASH       = "#2c3144"
BG_TOPBAR     = "#1a1d2b"
WHITE         = "#ffffff"
C_CHECKIN     = "#9932cc"
C_ROOMRACK    = "#3498db"
C_RESERVATION = "#e74c3c"
C_NIGHTAUDIT  = "#2ecc71"
C_REPORT      = "#2980b9"
C_PROPERTY    = "#f39c12"
C_HOUSEKEEP   = "#1abc9c"
C_HISTORY     = "#e84393"
C_MEMBER      = "#00bcd4"
C_LEDGER      = "#27ae60"
C_MANAGE      = "#e67e22"
C_BIGDATA     = "#f39c12"
C_FOLIO       = "#9b59b6"
C_TRANSACTION = "#8e44ad"

# ===================== HELPERS =====================
def clear(frame=None):
    target = frame if frame else root
    for w in target.winfo_children():
        w.destroy()

def topbar(title_text="CHMS1 HOTEL", back_cmd=None):
    bar = tk.Frame(root, bg=BG_TOPBAR, height=42)
    bar.pack(fill=tk.X)
    bar.pack_propagate(False)

    left = tk.Frame(bar, bg=BG_TOPBAR)
    left.pack(side=tk.LEFT, fill=tk.Y)

    if back_cmd:
        tk.Button(left, text="◀ Back", command=back_cmd,
                  bg="#3498db", fg=WHITE, font=("Arial", 9, "bold"),
                  bd=0, padx=8, pady=2, cursor="hand2").pack(side=tk.LEFT, padx=6, pady=8)

    tk.Label(left, text=f"CHMS1 HOTEL   ✉  🔔  ⏻  👤  Hi, {current_user['name']}",
             bg=BG_TOPBAR, fg=WHITE, font=("Arial", 10)).pack(side=tk.LEFT, padx=6)

    def update_clock():
        now = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
        lbl_time.config(text=f"System Date Time: {now}")
        bar.after(1000, update_clock)

    lbl_time = tk.Label(bar, text="", bg=BG_TOPBAR, fg=WHITE, font=("Arial", 10))
    lbl_time.pack(side=tk.RIGHT, padx=12)
    update_clock()
    return bar

def section_title(parent, text):
    tk.Label(parent, text=text, bg=BG_DASH, fg=WHITE,
             font=("Arial", 16, "bold"), anchor="w").pack(fill=tk.X, padx=20, pady=(14, 6))

def dash_btn(parent, text, color, cmd, row, col, rowspan=1, colspan=1):
    btn = tk.Button(parent, text=text, bg=color, fg=WHITE,
                    font=("Arial", 11, "bold"), relief=tk.FLAT,
                    activebackground=color, activeforeground=WHITE,
                    cursor="hand2", wraplength=120, command=cmd)
    btn.grid(row=row, column=col, rowspan=rowspan, columnspan=colspan,
             sticky="nsew", padx=4, pady=4, ipadx=6, ipady=28)
    return btn

def styled_entry(parent, width=28, show=None):
    e = tk.Entry(parent, font=("Arial", 12), width=width,
                 bg="#3d4261", fg=WHITE, insertbackground=WHITE,
                 relief=tk.FLAT, bd=4)
    if show:
        e.config(show=show)
    return e

def lbl(parent, text, bold=False, size=12, color=WHITE, anchor="w"):
    f = "bold" if bold else "normal"
    tk.Label(parent, text=text, bg=BG_DASH, fg=color,
             font=("Arial", size, f), anchor=anchor).pack(anchor="w", padx=20, pady=(4, 0))

def field(parent, label, entry_widget):
    tk.Label(parent, text=label, bg=BG_DASH, fg=WHITE,
             font=("Arial", 11), anchor="w").pack(anchor="w", padx=20, pady=(8, 0))
    entry_widget.pack(anchor="w", padx=20, pady=(2, 0))
    return entry_widget

def make_table(parent, columns, col_widths=None):
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Custom.Treeview",
                    background="#3d4261", foreground=WHITE,
                    rowheight=28, fieldbackground="#3d4261",
                    font=("Arial", 10))
    style.configure("Custom.Treeview.Heading",
                    background="#1a1d2b", foreground=WHITE,
                    font=("Arial", 10, "bold"))
    style.map("Custom.Treeview", background=[("selected", "#5c6bc0")])

    frame = tk.Frame(parent, bg=BG_DASH)
    frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=8)

    sb = ttk.Scrollbar(frame, orient=tk.VERTICAL)
    sb.pack(side=tk.RIGHT, fill=tk.Y)

    tree = ttk.Treeview(frame, columns=columns, show="headings",
                        style="Custom.Treeview", yscrollcommand=sb.set)
    sb.config(command=tree.yview)

    for i, col in enumerate(columns):
        w = col_widths[i] if col_widths else 140
        tree.heading(col, text=col.replace("_", " ").title())
        tree.column(col, width=w, anchor="center")

    tree.pack(fill=tk.BOTH, expand=True)
    return tree

def action_btn(parent, text, color, cmd):
    tk.Button(parent, text=text, bg=color, fg=WHITE,
              font=("Arial", 11, "bold"), relief=tk.FLAT,
              activebackground=color, cursor="hand2",
              padx=16, pady=8, command=cmd).pack(side=tk.LEFT, padx=6, pady=8)

def get_room(room_no):
    for r in rooms:
        if r["room_no"] == room_no:
            return r
    return None

def get_checkin(room_no):
    for c in checkins:
        if c["room_no"] == room_no:
            return c
    return None

def get_member(name):
    for m in members:
        if m["name"].lower() == name.lower():
            return m
    return None

def add_transaction(type_, room_no, guest, amount, desc=""):
    transactions.append({
        "id": f"TXN{len(transactions)+1:04d}",
        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "type": type_,
        "room_no": room_no,
        "guest": guest,
        "amount": amount,
        "desc": desc
    })

# ===================== LOGIN PAGE =====================
def show_login():
    clear()
    root.title("CHMS1 HOTEL - Login")

    # top bar (no back button)
    bar = tk.Frame(root, bg=BG_TOPBAR, height=42)
    bar.pack(fill=tk.X)
    bar.pack_propagate(False)
    tk.Label(bar, text="CHMS1 HOTEL   ✉  🔔  ⏻  👤  Hi, customer",
             bg=BG_TOPBAR, fg=WHITE, font=("Arial", 10)).pack(side=tk.LEFT, padx=10)

    def upd():
        now = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
        tl.config(text=f"System Date Time: {now}")
        bar.after(1000, upd)
    tl = tk.Label(bar, text="", bg=BG_TOPBAR, fg=WHITE, font=("Arial", 10))
    tl.pack(side=tk.RIGHT, padx=12)
    upd()

    # gradient-like blue background
    main = tk.Frame(root, bg=BG_LOGIN)
    main.pack(fill=tk.BOTH, expand=True)

    # centre column
    centre = tk.Frame(main, bg=BG_LOGIN)
    centre.place(relx=0.5, rely=0.5, anchor="center")

    # logo row
    logo_row = tk.Frame(centre, bg=BG_LOGIN)
    logo_row.pack(pady=(0, 20))

    # draw a shield-like canvas logo
    canvas = tk.Canvas(logo_row, width=80, height=90, bg=BG_LOGIN, highlightthickness=0)
    canvas.pack(side=tk.LEFT, padx=10)
    canvas.create_polygon(40, 5, 75, 20, 75, 55, 40, 85, 5, 55, 5, 20, fill="#1a3aaf", outline=WHITE, width=2)
    canvas.create_text(40, 45, text="一中", fill="#ff4444", font=("Arial", 13, "bold"))

    title_frame = tk.Frame(logo_row, bg=BG_LOGIN)
    title_frame.pack(side=tk.LEFT)
    tk.Label(title_frame, text="CHMS1 HOTEL", bg=BG_LOGIN, fg=WHITE,
             font=("Arial", 26, "bold")).pack(anchor="w")
    tk.Label(title_frame, text="Hotel Management System", bg=BG_LOGIN, fg="#c0d0ff",
             font=("Arial", 13, "italic")).pack(anchor="w")

    # form card
    card = tk.Frame(centre, bg="#1e3ba8", bd=0)
    card.pack(pady=10, ipadx=30, ipady=20)

    def placeholder(e, default, is_pwd=False):
        if e.get() == default:
            e.delete(0, tk.END)
            e.config(fg=WHITE)
            if is_pwd:
                e.config(show="*")

    def restore(e, default):
        if not e.get():
            e.insert(0, default)
            e.config(fg="#aaaaaa", show="")

    def mk_entry(ph, is_pwd=False):
        e = tk.Entry(card, font=("Arial", 13), width=34,
                     bg=WHITE, fg="#aaaaaa", relief=tk.FLAT, bd=0)
        e.insert(0, ph)
        e.bind("<FocusIn>",  lambda ev, _e=e, _ph=ph, _p=is_pwd: placeholder(_e, _ph, _p))
        e.bind("<FocusOut>", lambda ev, _e=e, _ph=ph: restore(_e, _ph))
        frm = tk.Frame(card, bg="#cccccc", pady=1)
        frm.pack(pady=6, padx=10)
        tk.Frame(frm, bg=WHITE, pady=4).pack()
        e_frm = tk.Frame(frm, bg=WHITE, padx=8, pady=4)
        e_frm.pack()
        e2 = tk.Entry(e_frm, font=("Arial", 13), width=34, bg=WHITE, fg="#aaaaaa",
                      relief=tk.FLAT, bd=0)
        e2.insert(0, ph)
        e2.bind("<FocusIn>",  lambda ev, _e=e2, _ph=ph, _p=is_pwd: placeholder(_e, _ph, _p))
        e2.bind("<FocusOut>", lambda ev, _e=e2, _ph=ph: restore(_e, _ph))
        return e2

    # simpler approach - plain entries with rounded look via frame
    def plain_entry(ph, is_pwd=False):
        outer = tk.Frame(card, bg="#3a5ad9", pady=1, padx=1)
        outer.pack(pady=6, padx=20)
        inner = tk.Frame(outer, bg=WHITE, padx=6, pady=6)
        inner.pack()
        e = tk.Entry(inner, font=("Arial", 13), width=34,
                     bg=WHITE, fg="#888888", relief=tk.FLAT, bd=0)
        e.insert(0, ph)
        if is_pwd:
            def on_focus(ev):
                if e.get() == ph:
                    e.delete(0, tk.END)
                    e.config(fg="#222222", show="*")
        else:
            def on_focus(ev):
                if e.get() == ph:
                    e.delete(0, tk.END)
                    e.config(fg="#222222")
        def on_blur(ev):
            if not e.get():
                e.insert(0, ph)
                e.config(fg="#888888", show="")
        e.bind("<FocusIn>",  on_focus)
        e.bind("<FocusOut>", on_blur)
        e.pack()
        return e

    e_acct    = plain_entry("Login account")
    e_pwd     = plain_entry("Password", is_pwd=True)
    e_confirm = plain_entry("Confirm Password", is_pwd=True)

    # captcha row
    cap_frame = tk.Frame(card, bg=WHITE, bd=1, relief=tk.SOLID)
    cap_frame.pack(pady=6, padx=20, fill=tk.X)
    cap_var = tk.BooleanVar()
    tk.Checkbutton(cap_frame, variable=cap_var, bg=WHITE).pack(side=tk.LEFT, padx=6)
    tk.Label(cap_frame, text="I'm not a robot", bg=WHITE,
             font=("Arial", 11), fg="#333333").pack(side=tk.LEFT)
    tk.Label(cap_frame, text="reCAPTCHA\n☁", bg=WHITE,
             font=("Arial", 8), fg="#aaaaaa").pack(side=tk.RIGHT, padx=10)

    # login button
    def do_login():
        acc = e_acct.get()
        pwd = e_pwd.get()
        if acc == "Login account" or pwd == "Password":
            messagebox.showerror("Error", "Please enter your credentials.")
            return
        if not cap_var.get():
            messagebox.showwarning("CAPTCHA", "Please confirm you are not a robot.")
            return
        if acc in users and users[acc] == pwd:
            current_user["name"] = acc
            show_dashboard()
        else:
            messagebox.showerror("Login Failed", "Invalid account or password.\nTest: admin / 123")

    btn_login = tk.Button(card, text="Login", command=do_login,
                          bg="#e8e8e8", fg="#222222", font=("Arial", 15, "bold"),
                          width=30, relief=tk.FLAT, pady=10, cursor="hand2")
    btn_login.pack(pady=10, padx=20)
    root.bind("<Return>", lambda e: do_login())

    # links
    link_f = tk.Frame(centre, bg=BG_LOGIN)
    link_f.pack(pady=10)
    for i, (txt, cmd) in enumerate([("Sign up", show_signup),
                                     ("About us", show_about),
                                     ("Forgot Password?", show_forgot)]):
        if i > 0:
            tk.Label(link_f, text="|", bg=BG_LOGIN, fg=WHITE,
                     font=("Arial", 12)).grid(row=0, column=i*2-1)
        lk = tk.Label(link_f, text=txt, bg=BG_LOGIN, fg=WHITE,
                      font=("Arial", 12, "underline"), cursor="hand2")
        lk.grid(row=0, column=i*2, padx=20)
        lk.bind("<Button-1>", lambda e, c=cmd: c())

# ===================== SIGN UP =====================
def show_signup():
    win = tk.Toplevel(root)
    win.title("Sign Up")
    win.geometry("400x380")
    win.configure(bg=BG_DASH)
    win.grab_set()

    tk.Label(win, text="Create New Account", bg=BG_DASH, fg=WHITE,
             font=("Arial", 14, "bold")).pack(pady=16)

    def row(label):
        tk.Label(win, text=label, bg=BG_DASH, fg=WHITE, font=("Arial", 11)).pack(anchor="w", padx=30)
        e = tk.Entry(win, font=("Arial", 11), width=30, bg="#3d4261", fg=WHITE,
                     insertbackground=WHITE, relief=tk.FLAT, bd=4)
        e.pack(padx=30, pady=3)
        return e

    e_user = row("Username:")
    e_p1   = row("Password:")
    e_p1.config(show="*")
    e_p2   = row("Confirm Password:")
    e_p2.config(show="*")

    def register():
        u, p1, p2 = e_user.get().strip(), e_p1.get(), e_p2.get()
        if not u or not p1:
            messagebox.showwarning("Error", "All fields required.", parent=win); return
        if p1 != p2:
            messagebox.showerror("Error", "Passwords do not match.", parent=win); return
        if u in users:
            messagebox.showerror("Error", "Username already exists.", parent=win); return
        users[u] = p1
        messagebox.showinfo("Success", f"Account '{u}' created!\nYou can now login.", parent=win)
        win.destroy()

    tk.Button(win, text="Register", command=register,
              bg=C_LEDGER, fg=WHITE, font=("Arial", 12, "bold"),
              relief=tk.FLAT, padx=20, pady=8).pack(pady=16)

# ===================== ABOUT US =====================
def show_about():
    win = tk.Toplevel(root)
    win.title("About Us")
    win.geometry("480x300")
    win.configure(bg=BG_DASH)
    win.grab_set()
    tk.Label(win, text="CHMS1 HOTEL", bg=BG_DASH, fg=WHITE,
             font=("Arial", 18, "bold")).pack(pady=20)
    tk.Label(win, text="Hotel Management System v2.0\n\n"
             "A comprehensive solution for managing hotel operations\n"
             "including reservations, check-ins, housekeeping,\n"
             "financial reporting and member management.\n\n"
             "© 2026 CHMS1 HOTEL. All rights reserved.",
             bg=BG_DASH, fg="#c0c8e8", font=("Arial", 11),
             justify=tk.CENTER).pack(padx=20)
    tk.Button(win, text="Close", command=win.destroy,
              bg=C_ROOMRACK, fg=WHITE, font=("Arial", 11),
              relief=tk.FLAT, padx=16, pady=6).pack(pady=16)

# ===================== FORGOT PASSWORD =====================
def show_forgot():
    win = tk.Toplevel(root)
    win.title("Forgot Password")
    win.geometry("400x260")
    win.configure(bg=BG_DASH)
    win.grab_set()
    tk.Label(win, text="Reset Password", bg=BG_DASH, fg=WHITE,
             font=("Arial", 14, "bold")).pack(pady=16)

    tk.Label(win, text="Username:", bg=BG_DASH, fg=WHITE, font=("Arial", 11)).pack(anchor="w", padx=30)
    e_user = tk.Entry(win, font=("Arial", 11), width=30, bg="#3d4261", fg=WHITE,
                      insertbackground=WHITE, relief=tk.FLAT, bd=4)
    e_user.pack(padx=30, pady=3)

    tk.Label(win, text="New Password:", bg=BG_DASH, fg=WHITE, font=("Arial", 11)).pack(anchor="w", padx=30)
    e_pwd = tk.Entry(win, font=("Arial", 11), width=30, bg="#3d4261", fg=WHITE,
                     insertbackground=WHITE, relief=tk.FLAT, bd=4, show="*")
    e_pwd.pack(padx=30, pady=3)

    def reset():
        u, p = e_user.get().strip(), e_pwd.get()
        if u not in users:
            messagebox.showerror("Error", "Username not found.", parent=win); return
        users[u] = p
        messagebox.showinfo("Success", "Password reset successfully!", parent=win)
        win.destroy()

    tk.Button(win, text="Reset Password", command=reset,
              bg=C_RESERVATION, fg=WHITE, font=("Arial", 12, "bold"),
              relief=tk.FLAT, padx=16, pady=8).pack(pady=16)

# ===================== DASHBOARD =====================
def show_dashboard():
    clear()
    root.title("CHMS1 HOTEL - Dashboard")
    topbar()

    body = tk.Frame(root, bg=BG_DASH)
    body.pack(fill=tk.BOTH, expand=True)

    # title bar
    tk.Label(body, text="Dashboard", bg="#1a1d2b", fg=WHITE,
             font=("Arial", 13, "bold"), anchor="w", pady=6).pack(fill=tk.X, padx=0)

    # separator
    tk.Frame(body, bg="#3d4261", height=1).pack(fill=tk.X)

    # button grid
    grid = tk.Frame(body, bg=BG_DASH)
    grid.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    sections = [
        ("General", [
            ("Check-in",    C_CHECKIN,     show_checkin,     0, 0),
            ("Room Rack",   C_ROOMRACK,    show_roomrack,    0, 1),
            ("Reservation", C_RESERVATION, show_reservation, 1, 0),
            ("Night Audit", C_NIGHTAUDIT,  show_nightaudit,  1, 1),
        ]),
        ("Room Status", [
            ("Manager Report", C_REPORT,    show_report,      0, 0),
            ("Property Status",C_PROPERTY,  show_property,    0, 1),
            ("House Keeping",  C_HOUSEKEEP, show_housekeeping,1, 0, 1, 2),
        ]),
        ("Management", [
            ("History",    C_HISTORY, show_history,  0, 0),
            ("Member",     C_MEMBER,  show_member,   0, 1),
            ("City Ledger",C_LEDGER,  show_ledger,   1, 0),
            ("Management", C_MANAGE,  show_management,1, 1),
        ]),
        ("Data", [
            ("Big Data with\nRevenue Management", C_BIGDATA,     show_bigdata,    0, 0, 1, 2),
            ("Folio",                             C_FOLIO,       show_folio,      1, 0),
            ("Transaction",                       C_TRANSACTION, show_transaction,1, 1),
        ]),
    ]

    grid.columnconfigure(0, weight=1)
    grid.columnconfigure(1, weight=1)
    grid.columnconfigure(2, weight=1)
    grid.columnconfigure(3, weight=1)
    grid.rowconfigure(0, weight=1)

    for col_idx, (sec_title, btns) in enumerate(sections):
        sec = tk.LabelFrame(grid, text=sec_title, bg=BG_DASH, fg=WHITE,
                            font=("Arial", 10, "bold"), bd=1, relief=tk.GROOVE)
        sec.grid(row=0, column=col_idx, sticky="nsew", padx=6, pady=6)
        sec.columnconfigure(0, weight=1)
        sec.columnconfigure(1, weight=1)
        sec.rowconfigure(0, weight=1)
        sec.rowconfigure(1, weight=1)

        for item in btns:
            text, color, cmd = item[0], item[1], item[2]
            r, c = item[3], item[4]
            rs = item[5] if len(item) > 5 else 1
            cs = item[6] if len(item) > 6 else 1
            dash_btn(sec, text, color, cmd, r, c, rs, cs)

    # bottom separator
    tk.Frame(body, bg="#3d4261", height=1).pack(fill=tk.X, side=tk.BOTTOM)
    tk.Label(body, text="", bg=BG_DASH, height=3).pack(side=tk.BOTTOM)

# ===================== CHECK-IN =====================
def show_checkin():
    clear()
    root.title("CHMS1 HOTEL - Check-in")
    topbar("Check-in", show_dashboard)

    body = tk.Frame(root, bg=BG_DASH)
    body.pack(fill=tk.BOTH, expand=True)
    section_title(body, "🏨  Check-in")

    # form
    form = tk.Frame(body, bg=BG_DASH)
    form.pack(anchor="center", pady=10)

    def frow(label, w=28, show=None):
        tk.Label(form, text=label, bg=BG_DASH, fg=WHITE,
                 font=("Arial", 11), anchor="w").grid(sticky="w", pady=(8,0), padx=10)
        e = tk.Entry(form, font=("Arial", 12), width=w, bg="#3d4261", fg=WHITE,
                     insertbackground=WHITE, relief=tk.FLAT, bd=4)
        if show: e.config(show=show)
        e.grid(sticky="w", padx=10)
        return e

    e_name    = frow("Guest Name:")
    e_phone   = frow("Phone Number:")
    e_id      = frow("ID / Passport No:")
    e_email   = frow("Email:")

    tk.Label(form, text="Select Room:", bg=BG_DASH, fg=WHITE,
             font=("Arial", 11)).grid(sticky="w", pady=(8,0), padx=10)
    avail = [f"{r['room_no']} | {r['type']} | RM{r['price']}/night"
             for r in rooms if r["status"] == "Available"]
    combo_room = ttk.Combobox(form, values=avail, font=("Arial", 11), width=30)
    combo_room.grid(sticky="w", padx=10)

    tk.Label(form, text="Check-in Date:", bg=BG_DASH, fg=WHITE,
             font=("Arial", 11)).grid(sticky="w", pady=(8,0), padx=10)
    e_cin = tk.Entry(form, font=("Arial", 12), width=28, bg="#3d4261", fg=WHITE,
                     insertbackground=WHITE, relief=tk.FLAT, bd=4)
    e_cin.insert(0, date.today().strftime("%d/%m/%Y"))
    e_cin.grid(sticky="w", padx=10)

    tk.Label(form, text="Check-out Date:", bg=BG_DASH, fg=WHITE,
             font=("Arial", 11)).grid(sticky="w", pady=(8,0), padx=10)
    e_cout = tk.Entry(form, font=("Arial", 12), width=28, bg="#3d4261", fg=WHITE,
                      insertbackground=WHITE, relief=tk.FLAT, bd=4)
    e_cout.insert(0, (date.today() + timedelta(days=1)).strftime("%d/%m/%Y"))
    e_cout.grid(sticky="w", padx=10)

    tk.Label(form, text="Number of Guests:", bg=BG_DASH, fg=WHITE,
             font=("Arial", 11)).grid(sticky="w", pady=(8,0), padx=10)
    combo_guests = ttk.Combobox(form, values=["1","2","3","4"], font=("Arial", 11), width=8)
    combo_guests.set("1")
    combo_guests.grid(sticky="w", padx=10)

    tk.Label(form, text="Payment Method:", bg=BG_DASH, fg=WHITE,
             font=("Arial", 11)).grid(sticky="w", pady=(8,0), padx=10)
    combo_pay = ttk.Combobox(form, values=["Cash","Credit Card","Debit Card","Online Transfer"],
                              font=("Arial", 11), width=20)
    combo_pay.set("Cash")
    combo_pay.grid(sticky="w", padx=10)

    # right side - current checkins
    right = tk.Frame(body, bg=BG_DASH)
    right.pack(fill=tk.BOTH, expand=True, padx=20)
    tk.Label(right, text="Current Check-ins", bg=BG_DASH, fg=WHITE,
             font=("Arial", 12, "bold")).pack(anchor="w", pady=(10,4))

    cols = ["Room","Guest","Phone","Check-in","Check-out","Amount"]
    tree = make_table(right, cols, [80,150,120,110,110,100])

    def refresh_tree():
        tree.delete(*tree.get_children())
        for c in checkins:
            tree.insert("", tk.END, values=(
                c["room_no"], c["guest"], c["phone"],
                c["cin"], c["cout"], f"RM {c['amount']}"
            ))

    refresh_tree()

    def do_checkin():
        name  = e_name.get().strip()
        phone = e_phone.get().strip()
        id_no = e_id.get().strip()
        sel   = combo_room.get()
        cin   = e_cin.get().strip()
        cout  = e_cout.get().strip()
        pay   = combo_pay.get()

        if not all([name, phone, sel, cin, cout]):
            messagebox.showwarning("Warning", "Please fill in all required fields."); return

        room_no = sel.split(" | ")[0]
        room = get_room(room_no)
        if not room:
            messagebox.showerror("Error", "Room not found."); return

        # calc nights & amount
        try:
            d1 = datetime.strptime(cin, "%d/%m/%Y")
            d2 = datetime.strptime(cout, "%d/%m/%Y")
            nights = max(1, (d2 - d1).days)
        except:
            nights = 1
        amount = nights * int(room["price"])

        room["status"] = "Occupied"
        checkin_rec = {
            "room_no": room_no, "guest": name, "phone": phone,
            "id_no": id_no, "cin": cin, "cout": cout,
            "nights": nights, "amount": amount,
            "payment": pay, "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        checkins.append(checkin_rec)
        add_transaction("Check-in", room_no, name, amount, f"{nights} night(s)")

        # update member points
        m = get_member(name)
        if not m:
            members.append({"name": name, "phone": phone, "email": "",
                            "points": amount // 10, "stays": 1,
                            "joined": date.today().strftime("%d/%m/%Y"),
                            "tier": "Silver"})
        else:
            m["points"] += amount // 10
            m["stays"]  += 1

        messagebox.showinfo("Check-in Success",
                            f"Room {room_no} checked in!\nGuest: {name}\n"
                            f"Nights: {nights}\nTotal: RM {amount}")
        combo_room["values"] = [f"{r['room_no']} | {r['type']} | RM{r['price']}/night"
                                 for r in rooms if r["status"] == "Available"]
        combo_room.set("")
        e_name.delete(0, tk.END); e_phone.delete(0, tk.END)
        e_id.delete(0, tk.END)
        refresh_tree()

    btn_row = tk.Frame(body, bg=BG_DASH)
    btn_row.pack(anchor="w", padx=20, pady=8)
    action_btn(btn_row, "✔  Confirm Check-in", C_CHECKIN, do_checkin)
    action_btn(btn_row, "◀ Back", C_ROOMRACK, show_dashboard)

# ===================== CHECK-OUT (from Room Rack) =====================
def do_checkout(room_no):
    rec = get_checkin(room_no)
    if not rec:
        messagebox.showerror("Error", f"No active check-in for room {room_no}."); return

    extra = sum(f["amount"] for f in folio_items if f["room_no"] == room_no)
    total = rec["amount"] + extra

    confirm = messagebox.askyesno("Check-out",
        f"Room: {room_no}\nGuest: {rec['guest']}\n"
        f"Room Charges: RM {rec['amount']}\nExtra Charges: RM {extra}\n"
        f"TOTAL: RM {total}\n\nConfirm check-out?")
    if not confirm: return

    room = get_room(room_no)
    if room:
        room["status"] = "Cleaning"

    history.append({**rec, "checkout_time": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "extra": extra, "total": total})
    add_transaction("Check-out", room_no, rec["guest"], total, "Full settlement")
    checkins.remove(rec)

    # housekeeping task
    housekeeping_log.append({
        "room_no": room_no, "task": "Post-checkout cleaning",
        "status": "Pending", "assigned": "Housekeeping Staff",
        "date": date.today().strftime("%d/%m/%Y")
    })

    messagebox.showinfo("Check-out Complete",
                        f"Room {room_no} checked out.\nTotal Collected: RM {total}")
    show_roomrack()

# ===================== ROOM RACK =====================
def show_roomrack():
    clear()
    root.title("CHMS1 HOTEL - Room Rack")
    topbar("Room Rack", show_dashboard)

    body = tk.Frame(root, bg=BG_DASH)
    body.pack(fill=tk.BOTH, expand=True)
    section_title(body, "🛏  Room Rack")

    # add room
    add_bar = tk.Frame(body, bg="#1a1d2b")
    add_bar.pack(fill=tk.X, padx=20, pady=4)

    def lbl2(t):
        tk.Label(add_bar, text=t, bg="#1a1d2b", fg=WHITE,
                 font=("Arial", 10)).pack(side=tk.LEFT, padx=4)

    def ent(w=8):
        e = tk.Entry(add_bar, font=("Arial", 10), width=w,
                     bg="#3d4261", fg=WHITE, insertbackground=WHITE, relief=tk.FLAT, bd=3)
        e.pack(side=tk.LEFT, padx=4)
        return e

    lbl2("Room No:"); e_rno = ent(6)
    lbl2("Floor:");   e_fl  = ent(4)
    lbl2("Type:")
    cb_type = ttk.Combobox(add_bar, values=["Single","Double","Deluxe","Suite"],
                            font=("Arial", 10), width=9)
    cb_type.pack(side=tk.LEFT, padx=4)
    lbl2("Price (RM):"); e_price = ent(6)

    def add_room():
        rno = e_rno.get().strip()
        fl  = e_fl.get().strip()
        typ = cb_type.get()
        pr  = e_price.get().strip()
        if not all([rno, typ, pr]):
            messagebox.showwarning("Warning", "Fill all fields."); return
        if get_room(rno):
            messagebox.showerror("Error", f"Room {rno} already exists."); return
        rooms.append({"room_no": rno, "type": typ, "price": pr,
                      "status": "Available", "floor": fl or "1"})
        refresh_tree()
        e_rno.delete(0, tk.END); e_fl.delete(0, tk.END); e_price.delete(0, tk.END)
        cb_type.set("")
        messagebox.showinfo("Success", f"Room {rno} added!")

    tk.Button(add_bar, text="+ Add Room", command=add_room,
              bg=C_ROOMRACK, fg=WHITE, font=("Arial", 10, "bold"),
              relief=tk.FLAT, padx=10, pady=4).pack(side=tk.LEFT, padx=8)

    # filter bar
    flt_bar = tk.Frame(body, bg=BG_DASH)
    flt_bar.pack(fill=tk.X, padx=20, pady=4)
    tk.Label(flt_bar, text="Filter:", bg=BG_DASH, fg=WHITE, font=("Arial", 10)).pack(side=tk.LEFT)
    flt_var = tk.StringVar(value="All")
    for val in ["All","Available","Occupied","Cleaning","Maintenance"]:
        tk.Radiobutton(flt_bar, text=val, variable=flt_var, value=val,
                       bg=BG_DASH, fg=WHITE, selectcolor=BG_DASH,
                       font=("Arial", 10), command=lambda: refresh_tree()
                       ).pack(side=tk.LEFT, padx=6)

    # table
    cols = ["Room No","Floor","Type","Price (RM)","Status","Guest","Action"]
    tree = make_table(body, cols, [90,70,90,100,110,160,100])

    STATUS_COLORS = {
        "Available":   "#27ae60",
        "Occupied":    "#e74c3c",
        "Cleaning":    "#f39c12",
        "Maintenance": "#7f8c8d",
    }

    def refresh_tree():
        tree.delete(*tree.get_children())
        flt = flt_var.get()
        for r in rooms:
            if flt != "All" and r["status"] != flt:
                continue
            ci = get_checkin(r["room_no"])
            guest = ci["guest"] if ci else "-"
            action = "Check-out" if r["status"] == "Occupied" else \
                     "Set Available" if r["status"] in ("Cleaning","Maintenance") else "-"
            tree.insert("", tk.END, values=(
                r["room_no"], r["floor"], r["type"], r["price"], r["status"], guest, action
            ))

    refresh_tree()

    def on_tree_click(event):
        row = tree.identify_row(event.y)
        col = tree.identify_column(event.x)
        if not row: return
        vals = tree.item(row, "values")
        room_no = vals[0]
        status  = vals[4]
        if col == "#7":  # Action column
            if status == "Occupied":
                do_checkout(room_no)
            elif status in ("Cleaning", "Maintenance"):
                r = get_room(room_no)
                if r: r["status"] = "Available"
                refresh_tree()

    tree.bind("<ButtonRelease-1>", on_tree_click)

    # legend
    leg = tk.Frame(body, bg=BG_DASH)
    leg.pack(anchor="w", padx=20, pady=4)
    for status, color in STATUS_COLORS.items():
        tk.Label(leg, text="  ", bg=color).pack(side=tk.LEFT, padx=2)
        tk.Label(leg, text=status, bg=BG_DASH, fg=WHITE, font=("Arial", 9)).pack(side=tk.LEFT, padx=4)

    btn_row = tk.Frame(body, bg=BG_DASH)
    btn_row.pack(anchor="w", padx=20, pady=6)
    action_btn(btn_row, "🔄 Refresh", C_ROOMRACK, refresh_tree)
    action_btn(btn_row, "◀ Back", "#555", show_dashboard)

# ===================== RESERVATION =====================
def show_reservation():
    clear()
    root.title("CHMS1 HOTEL - Reservation")
    topbar("Reservation", show_dashboard)

    body = tk.Frame(root, bg=BG_DASH)
    body.pack(fill=tk.BOTH, expand=True)
    section_title(body, "📋  Reservation")

    # form + list side by side
    pane = tk.Frame(body, bg=BG_DASH)
    pane.pack(fill=tk.BOTH, expand=True, padx=20)

    left = tk.Frame(pane, bg=BG_DASH)
    left.pack(side=tk.LEFT, fill=tk.Y, padx=(0,20))

    def frow(label, w=26):
        tk.Label(left, text=label, bg=BG_DASH, fg=WHITE,
                 font=("Arial", 11)).pack(anchor="w", pady=(8,0))
        e = tk.Entry(left, font=("Arial", 11), width=w, bg="#3d4261", fg=WHITE,
                     insertbackground=WHITE, relief=tk.FLAT, bd=4)
        e.pack(anchor="w")
        return e

    e_guest = frow("Guest Name:")
    e_phone = frow("Phone:")
    e_email = frow("Email:")

    tk.Label(left, text="Room Type:", bg=BG_DASH, fg=WHITE,
             font=("Arial", 11)).pack(anchor="w", pady=(8,0))
    cb_type = ttk.Combobox(left, values=["Single","Double","Deluxe","Suite"],
                            font=("Arial", 11), width=24)
    cb_type.pack(anchor="w")

    e_cin  = frow("Arrival Date (DD/MM/YYYY):")
    e_cout = frow("Departure Date (DD/MM/YYYY):")
    e_cin.insert(0, (date.today() + timedelta(days=1)).strftime("%d/%m/%Y"))
    e_cout.insert(0, (date.today() + timedelta(days=2)).strftime("%d/%m/%Y"))

    tk.Label(left, text="Guests:", bg=BG_DASH, fg=WHITE,
             font=("Arial", 11)).pack(anchor="w", pady=(8,0))
    cb_guests = ttk.Combobox(left, values=["1","2","3","4"], font=("Arial", 11), width=6)
    cb_guests.set("1"); cb_guests.pack(anchor="w")

    e_special = frow("Special Requests:")

    right = tk.Frame(pane, bg=BG_DASH)
    right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    tk.Label(right, text="All Reservations", bg=BG_DASH, fg=WHITE,
             font=("Arial", 12, "bold")).pack(anchor="w", pady=(0,4))

    cols = ["Ref","Guest","Phone","Type","Arrival","Departure","Status"]
    tree = make_table(right, cols, [80,130,110,90,100,100,90])

    def refresh():
        tree.delete(*tree.get_children())
        for r in reservations:
            tree.insert("", tk.END, values=(
                r["ref"], r["guest"], r["phone"], r["type"],
                r["cin"], r["cout"], r["status"]
            ))

    refresh()

    def make_reservation():
        guest = e_guest.get().strip()
        phone = e_phone.get().strip()
        typ   = cb_type.get()
        cin   = e_cin.get().strip()
        cout  = e_cout.get().strip()
        if not all([guest, phone, typ, cin, cout]):
            messagebox.showwarning("Warning", "Fill all required fields."); return

        ref = f"RES{len(reservations)+1:04d}"
        reservations.append({
            "ref": ref, "guest": guest, "phone": phone,
            "email": e_email.get(), "type": typ,
            "cin": cin, "cout": cout,
            "guests": cb_guests.get(), "special": e_special.get(),
            "status": "Confirmed",
            "created": datetime.now().strftime("%d/%m/%Y %H:%M")
        })
        messagebox.showinfo("Reserved", f"Reservation {ref} confirmed!\nGuest: {guest}")
        e_guest.delete(0, tk.END); e_phone.delete(0, tk.END)
        e_email.delete(0, tk.END); e_special.delete(0, tk.END)
        refresh()

    def cancel_reservation():
        sel = tree.focus()
        if not sel:
            messagebox.showwarning("Warning", "Select a reservation to cancel."); return
        ref = tree.item(sel, "values")[0]
        for r in reservations:
            if r["ref"] == ref:
                r["status"] = "Cancelled"; break
        refresh()

    btn_row = tk.Frame(left, bg=BG_DASH)
    btn_row.pack(anchor="w", pady=12)
    action_btn(btn_row, "📋 Make Reservation", C_RESERVATION, make_reservation)

    btn_row2 = tk.Frame(right, bg=BG_DASH)
    btn_row2.pack(anchor="w")
    action_btn(btn_row2, "❌ Cancel Selected", "#c0392b", cancel_reservation)

# ===================== NIGHT AUDIT =====================
def show_nightaudit():
    clear()
    root.title("CHMS1 HOTEL - Night Audit")
    topbar("Night Audit", show_dashboard)

    body = tk.Frame(root, bg=BG_DASH)
    body.pack(fill=tk.BOTH, expand=True)
    section_title(body, "🌙  Night Audit")

    tk.Label(body, text=f"Audit Date: {date.today().strftime('%d/%m/%Y')}",
             bg=BG_DASH, fg="#f39c12", font=("Arial", 13, "bold")).pack(anchor="w", padx=20)

    # Summary cards
    cards = tk.Frame(body, bg=BG_DASH)
    cards.pack(fill=tk.X, padx=20, pady=10)

    occupied   = sum(1 for r in rooms if r["status"] == "Occupied")
    available  = sum(1 for r in rooms if r["status"] == "Available")
    total_rev  = sum(t["amount"] for t in transactions if t["type"] == "Check-in")
    night_rev  = sum(c["amount"] for c in checkins)

    stats = [
        ("Occupied Rooms", str(occupied), "#e74c3c"),
        ("Available Rooms", str(available), "#27ae60"),
        ("Active Guests", str(len(checkins)), "#3498db"),
        ("Tonight Revenue", f"RM {night_rev}", "#f39c12"),
        ("Total Revenue", f"RM {total_rev}", "#9b59b6"),
    ]
    for title, val, color in stats:
        card = tk.Frame(cards, bg=color, padx=20, pady=14)
        card.pack(side=tk.LEFT, padx=6)
        tk.Label(card, text=val, bg=color, fg=WHITE, font=("Arial", 18, "bold")).pack()
        tk.Label(card, text=title, bg=color, fg=WHITE, font=("Arial", 9)).pack()

    # Audit table
    tk.Label(body, text="Tonight's Active Check-ins", bg=BG_DASH, fg=WHITE,
             font=("Arial", 12, "bold")).pack(anchor="w", padx=20, pady=(14,4))

    cols = ["Room","Guest","Check-in","Check-out","Nights","Amount","Payment"]
    tree = make_table(body, cols, [80,150,100,100,70,100,120])
    for c in checkins:
        tree.insert("", tk.END, values=(
            c["room_no"], c["guest"], c["cin"], c["cout"],
            c["nights"], f"RM {c['amount']}", c.get("payment","Cash")
        ))

    # Post balances button
    def post_balances():
        if not checkins:
            messagebox.showinfo("Night Audit", "No active check-ins to post."); return
        for c in checkins:
            add_transaction("Night Audit Post", c["room_no"], c["guest"],
                            int(c["amount"]) // c["nights"], "Nightly balance post")
        messagebox.showinfo("Night Audit Complete",
                            f"Posted balances for {len(checkins)} room(s).\n"
                            f"Total: RM {night_rev}")

    btn_row = tk.Frame(body, bg=BG_DASH)
    btn_row.pack(anchor="w", padx=20, pady=10)
    action_btn(btn_row, "📊 Post All Balances", C_NIGHTAUDIT, post_balances)
    action_btn(btn_row, "◀ Back", "#555", show_dashboard)

# ===================== MANAGER REPORT =====================
def show_report():
    clear()
    root.title("CHMS1 HOTEL - Manager Report")
    topbar("Manager Report", show_dashboard)

    body = tk.Frame(root, bg=BG_DASH)
    body.pack(fill=tk.BOTH, expand=True)
    section_title(body, "📊  Manager Report")

    # KPI cards
    cards = tk.Frame(body, bg=BG_DASH)
    cards.pack(fill=tk.X, padx=20, pady=8)

    total_rooms   = len(rooms)
    occupied      = sum(1 for r in rooms if r["status"] == "Occupied")
    occ_rate      = round(occupied / total_rooms * 100) if total_rooms else 0
    total_rev     = sum(t["amount"] for t in transactions)
    avg_rate      = round(sum(int(r["price"]) for r in rooms) / total_rooms) if total_rooms else 0
    revpar        = round(total_rev / total_rooms) if total_rooms else 0

    kpis = [
        ("Occupancy Rate", f"{occ_rate}%", "#3498db"),
        ("Total Revenue",  f"RM {total_rev}", "#27ae60"),
        ("Avg Room Rate",  f"RM {avg_rate}", "#f39c12"),
        ("RevPAR",         f"RM {revpar}", "#9b59b6"),
        ("Total Rooms",    str(total_rooms), "#e74c3c"),
        ("Occupied",       str(occupied), "#1abc9c"),
    ]
    for title, val, color in kpis:
        c = tk.Frame(cards, bg=color, padx=16, pady=12)
        c.pack(side=tk.LEFT, padx=5)
        tk.Label(c, text=val, bg=color, fg=WHITE, font=("Arial", 16, "bold")).pack()
        tk.Label(c, text=title, bg=color, fg=WHITE, font=("Arial", 9)).pack()

    # Tabs
    nb = ttk.Notebook(body)
    nb.pack(fill=tk.BOTH, expand=True, padx=20, pady=8)

    style = ttk.Style()
    style.configure("TNotebook", background=BG_DASH, borderwidth=0)
    style.configure("TNotebook.Tab", background="#3d4261", foreground=WHITE,
                    font=("Arial", 10, "bold"), padding=[12,6])
    style.map("TNotebook.Tab", background=[("selected","#5c6bc0")])

    for tab_name, data_func in [
        ("Room Summary", lambda: show_room_tab(nb)),
        ("Revenue by Day", lambda: show_rev_tab(nb)),
        ("Guest List", lambda: show_guest_tab(nb)),
    ]:
        frame = tk.Frame(nb, bg=BG_DASH)
        nb.add(frame, text=tab_name)

    def show_room_tab(parent):
        f = tk.Frame(parent, bg=BG_DASH)
        parent.add(f, text="Room Summary")
        cols = ["Room","Type","Price","Status","Guest"]
        t = make_table(f, cols, [90,100,100,110,160])
        for r in rooms:
            ci = get_checkin(r["room_no"])
            t.insert("", tk.END, values=(
                r["room_no"], r["type"], f"RM {r['price']}",
                r["status"], ci["guest"] if ci else "-"))

    def show_rev_tab(parent):
        f = tk.Frame(parent, bg=BG_DASH)
        parent.add(f, text="Revenue by Day")
        cols = ["Date","Transactions","Revenue"]
        t = make_table(f, cols, [150,150,150])
        by_date = {}
        for tx in transactions:
            d = tx["date"].split()[0]
            by_date.setdefault(d, [0, 0])
            by_date[d][0] += 1
            by_date[d][1] += tx["amount"]
        for d, (cnt, amt) in sorted(by_date.items()):
            t.insert("", tk.END, values=(d, cnt, f"RM {amt}"))

    def show_guest_tab(parent):
        f = tk.Frame(parent, bg=BG_DASH)
        parent.add(f, text="Guest List")
        cols = ["Guest","Room","Check-in","Check-out","Amount"]
        t = make_table(f, cols, [150,80,100,100,100])
        for c in checkins:
            t.insert("", tk.END, values=(
                c["guest"], c["room_no"], c["cin"], c["cout"], f"RM {c['amount']}"))
        for h in history:
            t.insert("", tk.END, values=(
                h["guest"], h["room_no"], h["cin"], h["cout"], f"RM {h['total']}"))

    show_room_tab(nb)
    show_rev_tab(nb)
    show_guest_tab(nb)

# ===================== PROPERTY STATUS =====================
def show_property():
    clear()
    root.title("CHMS1 HOTEL - Property Status")
    topbar("Property Status", show_dashboard)

    body = tk.Frame(root, bg=BG_DASH)
    body.pack(fill=tk.BOTH, expand=True)
    section_title(body, "🏢  Property Status")

    # visual room grid
    tk.Label(body, text="Room Status Overview", bg=BG_DASH, fg=WHITE,
             font=("Arial", 12, "bold")).pack(anchor="w", padx=20, pady=(0,8))

    canvas_frame = tk.Frame(body, bg=BG_DASH)
    canvas_frame.pack(fill=tk.BOTH, expand=True, padx=20)

    STATUS_COLOR = {
        "Available":   "#27ae60",
        "Occupied":    "#e74c3c",
        "Cleaning":    "#f39c12",
        "Maintenance": "#7f8c8d",
    }

    # group by floor
    floors = sorted(set(r["floor"] for r in rooms), reverse=True)

    for floor in floors:
        row_frame = tk.Frame(canvas_frame, bg=BG_DASH)
        row_frame.pack(anchor="w", pady=4)
        tk.Label(row_frame, text=f"Floor {floor}", bg=BG_DASH, fg="#aaaaaa",
                 font=("Arial", 10), width=8).pack(side=tk.LEFT)
        for r in rooms:
            if r["floor"] != floor: continue
            color = STATUS_COLOR.get(r["status"], "#555")
            cell = tk.Frame(row_frame, bg=color, width=80, height=60, bd=1, relief=tk.RAISED)
            cell.pack(side=tk.LEFT, padx=3)
            cell.pack_propagate(False)
            tk.Label(cell, text=r["room_no"], bg=color, fg=WHITE,
                     font=("Arial", 10, "bold")).pack(expand=True)
            tk.Label(cell, text=r["type"][:3], bg=color, fg=WHITE,
                     font=("Arial", 8)).pack()

    # legend
    leg = tk.Frame(body, bg=BG_DASH)
    leg.pack(anchor="w", padx=20, pady=8)
    tk.Label(leg, text="Legend: ", bg=BG_DASH, fg=WHITE, font=("Arial", 10)).pack(side=tk.LEFT)
    for status, color in STATUS_COLOR.items():
        tk.Label(leg, text=f"  {status}  ", bg=color, fg=WHITE,
                 font=("Arial", 9)).pack(side=tk.LEFT, padx=3)

    # set maintenance
    ctrl = tk.Frame(body, bg=BG_DASH)
    ctrl.pack(anchor="w", padx=20, pady=8)
    tk.Label(ctrl, text="Set Room Maintenance:", bg=BG_DASH, fg=WHITE,
             font=("Arial", 10)).pack(side=tk.LEFT, padx=4)
    cb_room = ttk.Combobox(ctrl, values=[r["room_no"] for r in rooms],
                            font=("Arial", 10), width=8)
    cb_room.pack(side=tk.LEFT, padx=4)

    def set_maintenance():
        rno = cb_room.get()
        r = get_room(rno)
        if r:
            r["status"] = "Maintenance"
            messagebox.showinfo("Done", f"Room {rno} set to Maintenance.")
            show_property()

    tk.Button(ctrl, text="Set Maintenance", command=set_maintenance,
              bg=C_PROPERTY, fg=WHITE, font=("Arial", 10, "bold"),
              relief=tk.FLAT, padx=10, pady=4).pack(side=tk.LEFT, padx=4)

# ===================== HOUSE KEEPING =====================
def show_housekeeping():
    clear()
    root.title("CHMS1 HOTEL - House Keeping")
    topbar("House Keeping", show_dashboard)

    body = tk.Frame(root, bg=BG_DASH)
    body.pack(fill=tk.BOTH, expand=True)
    section_title(body, "🧹  House Keeping")

    # add task
    add = tk.Frame(body, bg="#1a1d2b")
    add.pack(fill=tk.X, padx=20, pady=4)

    def lbl2(t):
        tk.Label(add, text=t, bg="#1a1d2b", fg=WHITE, font=("Arial", 10)).pack(side=tk.LEFT, padx=4)

    lbl2("Room:")
    cb_room = ttk.Combobox(add, values=[r["room_no"] for r in rooms], width=6)
    cb_room.pack(side=tk.LEFT, padx=4)

    lbl2("Task:")
    cb_task = ttk.Combobox(add, values=["General Cleaning","Deep Cleaning",
                                         "Linen Change","Amenity Restock",
                                         "Post-checkout cleaning","Inspection"],
                            width=22)
    cb_task.pack(side=tk.LEFT, padx=4)

    lbl2("Assigned To:")
    e_staff = tk.Entry(add, font=("Arial", 10), width=18,
                       bg="#3d4261", fg=WHITE, insertbackground=WHITE,
                       relief=tk.FLAT, bd=3)
    e_staff.pack(side=tk.LEFT, padx=4)

    def add_task():
        rno   = cb_room.get()
        task  = cb_task.get()
        staff = e_staff.get().strip() or "Unassigned"
        if not all([rno, task]):
            messagebox.showwarning("Warning", "Select room and task."); return
        housekeeping_log.append({
            "room_no": rno, "task": task, "status": "Pending",
            "assigned": staff, "date": date.today().strftime("%d/%m/%Y")
        })
        refresh()
        cb_room.set(""); cb_task.set(""); e_staff.delete(0, tk.END)

    tk.Button(add, text="+ Add Task", command=add_task,
              bg=C_HOUSEKEEP, fg=WHITE, font=("Arial", 10, "bold"),
              relief=tk.FLAT, padx=10, pady=4).pack(side=tk.LEFT, padx=8)

    # table
    cols = ["#","Room","Task","Assigned","Date","Status"]
    tree = make_table(body, cols, [50,80,220,160,100,100])

    def refresh():
        tree.delete(*tree.get_children())
        for i, h in enumerate(housekeeping_log, 1):
            tree.insert("", tk.END, values=(
                i, h["room_no"], h["task"], h["assigned"], h["date"], h["status"]
            ))

    refresh()

    def mark_done():
        sel = tree.focus()
        if not sel:
            messagebox.showwarning("Warning", "Select a task."); return
        idx = int(tree.item(sel, "values")[0]) - 1
        housekeeping_log[idx]["status"] = "Completed"
        # if room was cleaning, set available
        rno = housekeeping_log[idx]["room_no"]
        r = get_room(rno)
        if r and r["status"] == "Cleaning":
            r["status"] = "Available"
        refresh()

    def mark_inprogress():
        sel = tree.focus()
        if not sel: return
        idx = int(tree.item(sel, "values")[0]) - 1
        housekeeping_log[idx]["status"] = "In Progress"
        refresh()

    btn_row = tk.Frame(body, bg=BG_DASH)
    btn_row.pack(anchor="w", padx=20, pady=6)
    action_btn(btn_row, "✔ Mark Done", C_NIGHTAUDIT, mark_done)
    action_btn(btn_row, "⚙ In Progress", C_PROPERTY, mark_inprogress)
    action_btn(btn_row, "🔄 Refresh", C_ROOMRACK, refresh)

# ===================== HISTORY =====================
def show_history():
    clear()
    root.title("CHMS1 HOTEL - History")
    topbar("History", show_dashboard)

    body = tk.Frame(root, bg=BG_DASH)
    body.pack(fill=tk.BOTH, expand=True)
    section_title(body, "📜  Guest History")

    # search
    srch = tk.Frame(body, bg=BG_DASH)
    srch.pack(fill=tk.X, padx=20, pady=4)
    tk.Label(srch, text="Search:", bg=BG_DASH, fg=WHITE, font=("Arial", 10)).pack(side=tk.LEFT)
    e_srch = tk.Entry(srch, font=("Arial", 10), width=24,
                      bg="#3d4261", fg=WHITE, insertbackground=WHITE,
                      relief=tk.FLAT, bd=3)
    e_srch.pack(side=tk.LEFT, padx=6)

    cols = ["Room","Guest","Phone","Check-in","Check-out","Nights","Room Amt","Extra","Total","Checkout Time"]
    tree = make_table(body, cols, [70,130,110,90,90,60,90,70,90,130])

    def refresh(q=""):
        tree.delete(*tree.get_children())
        for h in history:
            if q and q.lower() not in h["guest"].lower() and q not in h["room_no"]:
                continue
            tree.insert("", tk.END, values=(
                h["room_no"], h["guest"], h.get("phone",""),
                h["cin"], h["cout"], h["nights"],
                f"RM {h['amount']}", f"RM {h.get('extra',0)}",
                f"RM {h.get('total', h['amount'])}",
                h.get("checkout_time","")
            ))

    refresh()
    tk.Button(srch, text="🔍 Search", command=lambda: refresh(e_srch.get()),
              bg=C_ROOMRACK, fg=WHITE, font=("Arial", 10),
              relief=tk.FLAT, padx=8, pady=4).pack(side=tk.LEFT)
    tk.Button(srch, text="Clear", command=lambda: [e_srch.delete(0, tk.END), refresh()],
              bg="#555", fg=WHITE, font=("Arial", 10),
              relief=tk.FLAT, padx=8, pady=4).pack(side=tk.LEFT, padx=4)

    # stats
    total = sum(h.get("total", h["amount"]) for h in history)
    tk.Label(body, text=f"Total Checkouts: {len(history)}   |   Total Revenue from History: RM {total}",
             bg=BG_DASH, fg="#f39c12", font=("Arial", 11, "bold")).pack(anchor="w", padx=20)

# ===================== MEMBER =====================
def show_member():
    clear()
    root.title("CHMS1 HOTEL - Member")
    topbar("Member", show_dashboard)

    body = tk.Frame(root, bg=BG_DASH)
    body.pack(fill=tk.BOTH, expand=True)
    section_title(body, "👤  Member Management")

    pane = tk.Frame(body, bg=BG_DASH)
    pane.pack(fill=tk.BOTH, expand=True, padx=20)

    left = tk.Frame(pane, bg=BG_DASH)
    left.pack(side=tk.LEFT, fill=tk.Y, padx=(0,20))

    tk.Label(left, text="Add / Edit Member", bg=BG_DASH, fg=WHITE,
             font=("Arial", 12, "bold")).pack(anchor="w", pady=(0,8))

    def frow(label):
        tk.Label(left, text=label, bg=BG_DASH, fg=WHITE, font=("Arial", 10)).pack(anchor="w")
        e = tk.Entry(left, font=("Arial", 11), width=26, bg="#3d4261", fg=WHITE,
                     insertbackground=WHITE, relief=tk.FLAT, bd=4)
        e.pack(anchor="w", pady=2)
        return e

    e_name  = frow("Full Name:")
    e_phone = frow("Phone:")
    e_email = frow("Email:")
    e_ic    = frow("IC / Passport:")

    tk.Label(left, text="Tier:", bg=BG_DASH, fg=WHITE, font=("Arial", 10)).pack(anchor="w")
    cb_tier = ttk.Combobox(left, values=["Silver","Gold","Platinum"],
                            font=("Arial", 11), width=14)
    cb_tier.set("Silver"); cb_tier.pack(anchor="w", pady=2)

    right = tk.Frame(pane, bg=BG_DASH)
    right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    tk.Label(right, text="Member List", bg=BG_DASH, fg=WHITE,
             font=("Arial", 12, "bold")).pack(anchor="w", pady=(0,4))

    cols = ["Name","Phone","Email","Tier","Points","Stays","Joined"]
    tree = make_table(right, cols, [140,110,160,80,70,60,100])

    def refresh():
        tree.delete(*tree.get_children())
        for m in members:
            tree.insert("", tk.END, values=(
                m["name"], m["phone"], m.get("email",""),
                m.get("tier","Silver"), m.get("points",0),
                m.get("stays",0), m.get("joined","")
            ))

    refresh()

    def add_member():
        name = e_name.get().strip()
        phone= e_phone.get().strip()
        if not all([name, phone]):
            messagebox.showwarning("Warning", "Name and phone required."); return
        if get_member(name):
            messagebox.showwarning("Warning", "Member already exists."); return
        members.append({
            "name": name, "phone": phone, "email": e_email.get(),
            "ic": e_ic.get(), "tier": cb_tier.get(),
            "points": 0, "stays": 0,
            "joined": date.today().strftime("%d/%m/%Y")
        })
        refresh()
        e_name.delete(0, tk.END); e_phone.delete(0, tk.END)
        e_email.delete(0, tk.END); e_ic.delete(0, tk.END)
        messagebox.showinfo("Success", f"Member '{name}' added!")

    def delete_member():
        sel = tree.focus()
        if not sel:
            messagebox.showwarning("Warning", "Select a member."); return
        name = tree.item(sel, "values")[0]
        if messagebox.askyesno("Confirm", f"Delete member '{name}'?"):
            global members
            members = [m for m in members if m["name"] != name]
            refresh()

    btn_row = tk.Frame(left, bg=BG_DASH)
    btn_row.pack(anchor="w", pady=10)
    action_btn(btn_row, "➕ Add Member", C_MEMBER, add_member)

    btn_row2 = tk.Frame(right, bg=BG_DASH)
    btn_row2.pack(anchor="w")
    action_btn(btn_row2, "🗑 Delete", C_RESERVATION, delete_member)
    action_btn(btn_row2, "🔄 Refresh", C_ROOMRACK, refresh)

# ===================== CITY LEDGER =====================
def show_ledger():
    clear()
    root.title("CHMS1 HOTEL - City Ledger")
    topbar("City Ledger", show_dashboard)

    body = tk.Frame(root, bg=BG_DASH)
    body.pack(fill=tk.BOTH, expand=True)
    section_title(body, "🏦  City Ledger")

    # company accounts
    tk.Label(body, text="Corporate Accounts", bg=BG_DASH, fg=WHITE,
             font=("Arial", 12, "bold")).pack(anchor="w", padx=20, pady=(0,6))

    # Add account
    add = tk.Frame(body, bg="#1a1d2b")
    add.pack(fill=tk.X, padx=20, pady=4)

    def lbl2(t):
        tk.Label(add, text=t, bg="#1a1d2b", fg=WHITE, font=("Arial", 10)).pack(side=tk.LEFT, padx=4)

    lbl2("Company:"); e_co    = tk.Entry(add, width=20, bg="#3d4261", fg=WHITE, relief=tk.FLAT, bd=3)
    e_co.pack(side=tk.LEFT, padx=4)
    lbl2("Contact:"); e_cont  = tk.Entry(add, width=16, bg="#3d4261", fg=WHITE, relief=tk.FLAT, bd=3)
    e_cont.pack(side=tk.LEFT, padx=4)
    lbl2("Credit Limit (RM):"); e_lim = tk.Entry(add, width=10, bg="#3d4261", fg=WHITE, relief=tk.FLAT, bd=3)
    e_lim.pack(side=tk.LEFT, padx=4)

    ledger_accounts = []

    cols = ["Company","Contact","Credit Limit","Balance Used","Status"]
    tree = make_table(body, cols, [180,140,130,130,100])

    def refresh():
        tree.delete(*tree.get_children())
        for ac in ledger_accounts:
            tree.insert("", tk.END, values=(
                ac["company"], ac["contact"],
                f"RM {ac['limit']}", f"RM {ac['used']}", ac["status"]
            ))

    def add_account():
        co   = e_co.get().strip()
        cont = e_cont.get().strip()
        lim  = e_lim.get().strip()
        if not all([co, lim]):
            messagebox.showwarning("Warning", "Company and credit limit required."); return
        ledger_accounts.append({
            "company": co, "contact": cont,
            "limit": lim, "used": 0, "status": "Active"
        })
        refresh()
        e_co.delete(0, tk.END); e_cont.delete(0, tk.END); e_lim.delete(0, tk.END)

    tk.Button(add, text="+ Add Account", command=add_account,
              bg=C_LEDGER, fg=WHITE, font=("Arial", 10, "bold"),
              relief=tk.FLAT, padx=10, pady=4).pack(side=tk.LEFT, padx=8)

    refresh()

    tk.Label(body, text="City Ledger allows corporate guests to pay on account.\n"
             "Invoices are settled monthly by the company.",
             bg=BG_DASH, fg="#aaaaaa", font=("Arial", 10)).pack(anchor="w", padx=20, pady=6)

# ===================== MANAGEMENT (System Settings) =====================
def show_management():
    clear()
    root.title("CHMS1 HOTEL - Management")
    topbar("Management", show_dashboard)

    body = tk.Frame(root, bg=BG_DASH)
    body.pack(fill=tk.BOTH, expand=True)
    section_title(body, "⚙  System Management")

    nb = ttk.Notebook(body)
    nb.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    # --- User Management Tab ---
    f_users = tk.Frame(nb, bg=BG_DASH)
    nb.add(f_users, text="User Accounts")

    tk.Label(f_users, text="System Users", bg=BG_DASH, fg=WHITE,
             font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=8)

    cols_u = ["Username","Role"]
    tree_u = make_table(f_users, cols_u, [200,200])

    def refresh_users():
        tree_u.delete(*tree_u.get_children())
        for u in users:
            role = "Admin" if u == "admin" else "Manager" if u == "manager" else "Staff"
            tree_u.insert("", tk.END, values=(u, role))

    refresh_users()

    add_u = tk.Frame(f_users, bg=BG_DASH)
    add_u.pack(anchor="w", padx=10, pady=4)
    tk.Label(add_u, text="New User:", bg=BG_DASH, fg=WHITE, font=("Arial", 10)).pack(side=tk.LEFT)
    e_nu = tk.Entry(add_u, width=16, bg="#3d4261", fg=WHITE, relief=tk.FLAT, bd=3)
    e_nu.pack(side=tk.LEFT, padx=4)
    tk.Label(add_u, text="Password:", bg=BG_DASH, fg=WHITE, font=("Arial", 10)).pack(side=tk.LEFT)
    e_np = tk.Entry(add_u, width=14, bg="#3d4261", fg=WHITE, relief=tk.FLAT, bd=3, show="*")
    e_np.pack(side=tk.LEFT, padx=4)

    def add_user_mgmt():
        u, p = e_nu.get().strip(), e_np.get()
        if not u or not p:
            messagebox.showwarning("Warning", "Fill username and password."); return
        users[u] = p
        refresh_users()
        e_nu.delete(0, tk.END); e_np.delete(0, tk.END)
        messagebox.showinfo("Done", f"User '{u}' created.")

    def del_user_mgmt():
        sel = tree_u.focus()
        if not sel: return
        u = tree_u.item(sel, "values")[0]
        if u == current_user["name"]:
            messagebox.showerror("Error", "Cannot delete current user."); return
        del users[u]
        refresh_users()

    tk.Button(add_u, text="Add User", command=add_user_mgmt,
              bg=C_LEDGER, fg=WHITE, font=("Arial", 10),
              relief=tk.FLAT, padx=8).pack(side=tk.LEFT, padx=4)
    tk.Button(add_u, text="Delete Selected", command=del_user_mgmt,
              bg=C_RESERVATION, fg=WHITE, font=("Arial", 10),
              relief=tk.FLAT, padx=8).pack(side=tk.LEFT)

    # --- Room Types Tab ---
    f_types = tk.Frame(nb, bg=BG_DASH)
    nb.add(f_types, text="Room Types & Pricing")

    tk.Label(f_types, text="Room Pricing Reference", bg=BG_DASH, fg=WHITE,
             font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=8)

    price_data = [("Single","80"),("Double","120"),("Deluxe","200"),("Suite","350")]
    for rtype, price in price_data:
        row = tk.Frame(f_types, bg=BG_DASH)
        row.pack(anchor="w", padx=10, pady=3)
        tk.Label(row, text=f"{rtype:<12}", bg=BG_DASH, fg=WHITE,
                 font=("Arial", 11)).pack(side=tk.LEFT)
        tk.Label(row, text=f"RM {price} / night", bg=BG_DASH, fg="#f39c12",
                 font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=10)

    # --- Logout ---
    f_sys = tk.Frame(nb, bg=BG_DASH)
    nb.add(f_sys, text="System")

    tk.Label(f_sys, text=f"Logged in as: {current_user['name']}",
             bg=BG_DASH, fg=WHITE, font=("Arial", 13)).pack(anchor="w", padx=20, pady=20)
    tk.Label(f_sys, text=f"Session started: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
             bg=BG_DASH, fg="#aaaaaa", font=("Arial", 11)).pack(anchor="w", padx=20)

    def logout():
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            show_login()

    tk.Button(f_sys, text="🚪 Logout", command=logout,
              bg=C_RESERVATION, fg=WHITE, font=("Arial", 13, "bold"),
              relief=tk.FLAT, padx=20, pady=10).pack(anchor="w", padx=20, pady=20)

# ===================== BIG DATA / REVENUE MANAGEMENT =====================
def show_bigdata():
    clear()
    root.title("CHMS1 HOTEL - Big Data & Revenue Management")
    topbar("Big Data", show_dashboard)

    body = tk.Frame(root, bg=BG_DASH)
    body.pack(fill=tk.BOTH, expand=True)
    section_title(body, "📈  Big Data with Revenue Management")

    # KPI row
    cards = tk.Frame(body, bg=BG_DASH)
    cards.pack(fill=tk.X, padx=20, pady=8)

    total_rooms = len(rooms)
    occ = sum(1 for r in rooms if r["status"] == "Occupied")
    rev = sum(t["amount"] for t in transactions)
    adr = round(rev / max(len(history)+len(checkins), 1))
    revpar = round(rev / max(total_rooms, 1))

    metrics = [
        ("Total Revenue", f"RM {rev}", "#27ae60"),
        ("Occupancy %",   f"{round(occ/max(total_rooms,1)*100)}%", "#3498db"),
        ("ADR (Avg Daily Rate)", f"RM {adr}", "#f39c12"),
        ("RevPAR",        f"RM {revpar}", "#9b59b6"),
        ("Total Stays",   str(len(history)), "#e74c3c"),
        ("Active Guests", str(len(checkins)), "#1abc9c"),
    ]
    for title, val, color in metrics:
        c = tk.Frame(cards, bg=color, padx=16, pady=12)
        c.pack(side=tk.LEFT, padx=5)
        tk.Label(c, text=val, bg=color, fg=WHITE, font=("Arial", 15, "bold")).pack()
        tk.Label(c, text=title, bg=color, fg=WHITE, font=("Arial", 9)).pack()

    # ASCII bar chart
    tk.Label(body, text="Revenue by Room Type", bg=BG_DASH, fg=WHITE,
             font=("Arial", 12, "bold")).pack(anchor="w", padx=20, pady=(12,4))

    chart_frame = tk.Frame(body, bg=BG_DASH)
    chart_frame.pack(fill=tk.X, padx=30)

    type_rev = {}
    for h in history:
        r = get_room(h["room_no"])
        if r:
            type_rev[r["type"]] = type_rev.get(r["type"], 0) + h.get("total", h["amount"])
    for c in checkins:
        r = get_room(c["room_no"])
        if r:
            type_rev[r["type"]] = type_rev.get(r["type"], 0) + c["amount"]

    max_rev = max(type_rev.values()) if type_rev else 1
    BAR_W = 300

    for rtype, rev_val in sorted(type_rev.items(), key=lambda x: -x[1]):
        row = tk.Frame(chart_frame, bg=BG_DASH)
        row.pack(anchor="w", pady=3)
        tk.Label(row, text=f"{rtype:<10}", bg=BG_DASH, fg=WHITE,
                 font=("Arial", 10), width=10).pack(side=tk.LEFT)
        bar_len = int(rev_val / max_rev * BAR_W)
        tk.Frame(row, bg="#3498db", width=bar_len, height=20).pack(side=tk.LEFT)
        tk.Label(row, text=f"  RM {rev_val}", bg=BG_DASH, fg="#f39c12",
                 font=("Arial", 10, "bold")).pack(side=tk.LEFT)

    if not type_rev:
        tk.Label(chart_frame, text="No revenue data yet. Check in some guests!",
                 bg=BG_DASH, fg="#aaaaaa", font=("Arial", 11)).pack(anchor="w")

    # Recommendation
    tk.Label(body, text="💡 Revenue Recommendations", bg=BG_DASH, fg=WHITE,
             font=("Arial", 12, "bold")).pack(anchor="w", padx=20, pady=(14,4))

    occ_pct = occ / max(total_rooms, 1) * 100
    recs = []
    if occ_pct < 50:
        recs.append("• Low occupancy detected. Consider promotional rates or packages.")
    if occ_pct > 80:
        recs.append("• High demand! Consider dynamic pricing to increase ADR.")
    if len(history) == 0:
        recs.append("• No checkout history yet. Start checking in guests to gather data.")
    recs.append(f"• Current ADR: RM {adr}. Industry benchmark for mid-range hotels: RM 150-250.")
    recs.append(f"• RevPAR: RM {revpar}. Aim to improve through upselling and package deals.")

    for rec in recs:
        tk.Label(body, text=rec, bg=BG_DASH, fg="#c0d0ff",
                 font=("Arial", 10)).pack(anchor="w", padx=30, pady=1)

# ===================== FOLIO =====================
def show_folio():
    clear()
    root.title("CHMS1 HOTEL - Folio")
    topbar("Folio", show_dashboard)

    body = tk.Frame(root, bg=BG_DASH)
    body.pack(fill=tk.BOTH, expand=True)
    section_title(body, "🧾  Folio (Guest Bill)")

    pane = tk.Frame(body, bg=BG_DASH)
    pane.pack(fill=tk.BOTH, expand=True, padx=20)

    left = tk.Frame(pane, bg=BG_DASH)
    left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

    tk.Label(left, text="Add Charge to Room", bg=BG_DASH, fg=WHITE,
             font=("Arial", 12, "bold")).pack(anchor="w", pady=(0,8))

    tk.Label(left, text="Room No:", bg=BG_DASH, fg=WHITE, font=("Arial", 10)).pack(anchor="w")
    occupied_rooms = [c["room_no"] for c in checkins]
    cb_room = ttk.Combobox(left, values=occupied_rooms, width=10)
    cb_room.pack(anchor="w", pady=2)
    if occupied_rooms:
        cb_room.set(occupied_rooms[0])

    tk.Label(left, text="Charge Type:", bg=BG_DASH, fg=WHITE, font=("Arial", 10)).pack(anchor="w")
    cb_charge = ttk.Combobox(left, values=[
        "Room Service","Minibar","Laundry","Spa","Restaurant",
        "Parking","Phone","Pay-Per-View","Damage","Other"
    ], width=18)
    cb_charge.set("Room Service"); cb_charge.pack(anchor="w", pady=2)

    tk.Label(left, text="Description:", bg=BG_DASH, fg=WHITE, font=("Arial", 10)).pack(anchor="w")
    e_desc = tk.Entry(left, width=24, bg="#3d4261", fg=WHITE, relief=tk.FLAT, bd=3)
    e_desc.pack(anchor="w", pady=2)

    tk.Label(left, text="Amount (RM):", bg=BG_DASH, fg=WHITE, font=("Arial", 10)).pack(anchor="w")
    e_amt = tk.Entry(left, width=12, bg="#3d4261", fg=WHITE, relief=tk.FLAT, bd=3)
    e_amt.pack(anchor="w", pady=2)

    right = tk.Frame(pane, bg=BG_DASH)
    right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    tk.Label(right, text="Folio Items", bg=BG_DASH, fg=WHITE,
             font=("Arial", 12, "bold")).pack(anchor="w", pady=(0,4))

    cols = ["Room","Guest","Type","Description","Amount","Date"]
    tree = make_table(right, cols, [80,130,110,160,90,110])

    total_lbl = tk.Label(right, text="", bg=BG_DASH, fg="#f39c12", font=("Arial", 11, "bold"))
    total_lbl.pack(anchor="w", padx=6)

    def refresh(filter_room=None):
        tree.delete(*tree.get_children())
        total = 0
        for fi in folio_items:
            if filter_room and fi["room_no"] != filter_room: continue
            ci = get_checkin(fi["room_no"])
            guest = ci["guest"] if ci else fi.get("guest", "-")
            tree.insert("", tk.END, values=(
                fi["room_no"], guest, fi["type"],
                fi["desc"], f"RM {fi['amount']}", fi["date"]
            ))
            total += fi["amount"]
        total_lbl.config(text=f"Total Extra Charges: RM {total}")

    refresh()

    def add_charge():
        rno  = cb_room.get()
        typ  = cb_charge.get()
        desc = e_desc.get().strip()
        amt  = e_amt.get().strip()
        if not all([rno, typ, amt]):
            messagebox.showwarning("Warning", "Fill room, type and amount."); return
        try:
            amt_val = float(amt)
        except:
            messagebox.showerror("Error", "Invalid amount."); return

        ci = get_checkin(rno)
        folio_items.append({
            "room_no": rno, "type": typ, "desc": desc or typ,
            "amount": amt_val, "guest": ci["guest"] if ci else "",
            "date": datetime.now().strftime("%d/%m/%Y %H:%M")
        })
        add_transaction("Folio Charge", rno, ci["guest"] if ci else "", amt_val, typ)
        e_desc.delete(0, tk.END); e_amt.delete(0, tk.END)
        refresh()
        messagebox.showinfo("Charged", f"RM {amt_val:.2f} charged to Room {rno}.")

    def view_room_folio():
        rno = cb_room.get()
        if not rno:
            messagebox.showwarning("Warning", "Select a room."); return
        refresh(rno)

    btn_row = tk.Frame(left, bg=BG_DASH)
    btn_row.pack(anchor="w", pady=10)
    action_btn(btn_row, "💳 Add Charge", C_FOLIO, add_charge)

    btn_row2 = tk.Frame(right, bg=BG_DASH)
    btn_row2.pack(anchor="w")
    action_btn(btn_row2, "🔍 Filter Room", C_ROOMRACK, view_room_folio)
    action_btn(btn_row2, "🔄 Show All", "#555", lambda: refresh())

# ===================== TRANSACTION =====================
def show_transaction():
    clear()
    root.title("CHMS1 HOTEL - Transaction")
    topbar("Transaction", show_dashboard)

    body = tk.Frame(root, bg=BG_DASH)
    body.pack(fill=tk.BOTH, expand=True)
    section_title(body, "💰  Transaction Records")

    # summary
    total = sum(t["amount"] for t in transactions)
    checkin_rev = sum(t["amount"] for t in transactions if t["type"] == "Check-in")
    folio_rev   = sum(t["amount"] for t in transactions if t["type"] == "Folio Charge")

    cards = tk.Frame(body, bg=BG_DASH)
    cards.pack(fill=tk.X, padx=20, pady=8)
    for title, val, color in [
        ("Total Transactions", str(len(transactions)), "#3498db"),
        ("Total Revenue",     f"RM {total:.0f}", "#27ae60"),
        ("Room Revenue",      f"RM {checkin_rev}", "#f39c12"),
        ("Extra Charges",     f"RM {folio_rev:.0f}", "#9b59b6"),
    ]:
        c = tk.Frame(cards, bg=color, padx=16, pady=10)
        c.pack(side=tk.LEFT, padx=5)
        tk.Label(c, text=val, bg=color, fg=WHITE, font=("Arial", 14, "bold")).pack()
        tk.Label(c, text=title, bg=color, fg=WHITE, font=("Arial", 9)).pack()

    # filter
    flt = tk.Frame(body, bg=BG_DASH)
    flt.pack(fill=tk.X, padx=20, pady=4)
    tk.Label(flt, text="Filter by Type:", bg=BG_DASH, fg=WHITE, font=("Arial", 10)).pack(side=tk.LEFT)
    flt_var = tk.StringVar(value="All")
    for val in ["All","Check-in","Check-out","Folio Charge","Night Audit Post"]:
        tk.Radiobutton(flt, text=val, variable=flt_var, value=val,
                       bg=BG_DASH, fg=WHITE, selectcolor=BG_DASH,
                       font=("Arial", 9), command=lambda: refresh()
                       ).pack(side=tk.LEFT, padx=4)

    cols = ["Txn ID","Date","Type","Room","Guest","Amount","Description"]
    tree = make_table(body, cols, [90,130,130,70,140,90,160])

    def refresh():
        tree.delete(*tree.get_children())
        flt_val = flt_var.get()
        for t in reversed(transactions):
            if flt_val != "All" and t["type"] != flt_val: continue
            tree.insert("", tk.END, values=(
                t["id"], t["date"], t["type"], t["room_no"],
                t["guest"], f"RM {t['amount']:.0f}", t.get("desc","")
            ))

    refresh()

# ===================== ENTRY POINT =====================
show_login()
root.mainloop()
