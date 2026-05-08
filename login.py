#!/bin/perl

import tkinter as tk
from tkinter import messagebox
import bcrypt
import requests
import data
import home  # <--- WE IMPORT HOME HERE



def login_user(username, password):
    try:
        response = requests.post(f"{data.SERVER_URL}/login", json={"username": username}, timeout=10)
        if response.status_code == 200:
            stored_hash = response.json().get("password")
            if isinstance(stored_hash, str): stored_hash = stored_hash.encode('utf-8')
            if bcrypt.checkpw(password.encode("utf-8"), stored_hash): return True
        return False
    except Exception as e:
        messagebox.showerror("Error", f"Server Unreachable: {e}")
        return False

def open_login_window():
    root = tk.Tk()
    root.title("Coreton")
    root.geometry("300x230")
    root.config(bg="black")

    tk.Label(root, text="Username:", bg="black", fg="green", font=("Pixelify Sans", 9, "bold")).grid(row=0, column=0, padx=5, pady=5)
    u_entry = tk.Entry(root, bg="black", fg="green")
    u_entry.grid(row=0, column=1)

    tk.Label(root, text="Password:", bg="black", fg="green", font=("Pixelify Sans", 9, "bold")).grid(row=1, column=0, padx=5, pady=5)
    p_entry = tk.Entry(root, show="*", bg="black", fg="green")
    p_entry.grid(row=1, column=1)

    def on_login():
        u = u_entry.get().strip()
        if login_user(u, p_entry.get().strip()):
            root.destroy() # Closes the login box
            home.open_home_window(u)
        else: 
            messagebox.showerror("Error", "Invalid Login")

    tk.Button(root, text="Login", width=20, command=on_login, bg="black", fg="green").grid(row=2, column=0, columnspan=2, pady=10)
    tk.Button(root, text="Register", width=20, command=lambda: [root.destroy(), data.open_registration_window()], bg="black", fg="#ff80ff").grid(row=3, column=0, columnspan=2)
    root.mainloop()

if __name__ == "__main__":
    open_login_window()