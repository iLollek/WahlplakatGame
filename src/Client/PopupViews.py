# Starry eyes tight as star-crossed lovers

from tkinter import Label, Entry, Button, messagebox
import tkinter as tk
import customtkinter as ctk
from typing import Optional
import logging
from PIL import Image

def show_info_box(title, body):
    """Shows a tkinter Info box with a Info Icon."""
    # Create a Tkinter window (optional if you already have a Tkinter window created)
    window = tk.Tk()
    window.withdraw()  # Hide the window to only show the message box

    # Show the message box with the given title and body
    messagebox.showinfo(title, body)

    # Destroy the Tkinter window (optional if you already have a Tkinter window created)
    window.destroy()

def show_error_box(title, body):
    """Shows a tkinter Info box with a Error Icon."""
    # Create a Tkinter window (optional if you already have a Tkinter window created)
    window = tk.Tk()
    window.withdraw()  # Hide the window to only show the message box

    # Show the message box with the given title and body
    messagebox.showerror(title, body)

    # Destroy the Tkinter window (optional if you already have a Tkinter window created)
    window.destroy()

def show_warning_box(title, body):
    """Shows a tkinter Info box with a Warning Icon."""
    # Create a Tkinter window (optional if you already have a Tkinter window created)
    window = tk.Tk()
    window.withdraw()  # Hide the window to only show the message box

    # Show the message box with the given title and body
    messagebox.showwarning(title, body)

    # Destroy the Tkinter window (optional if you already have a Tkinter window created)
    window.destroy()

def question_box(title: str, message: str, icon='info'):
    """Shows a tkinter Question Box with a Yes & No Answer. Returns the Answer. Icon can be set; defaults to info icon."""
    # Create a root window for the message box
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Show the message box and get the user's choice
    result = messagebox.askquestion(title, message, icon=icon, type=messagebox.YESNO, default=messagebox.YES)

    # Close the root window
    root.destroy()

    return result

def show_minibox_customtkinter(master, title: str, message: str, image: Optional[ctk.CTkImage | str] = None):
    """
    Zeigt ein kleines customtkinter-Popup-Fenster mit optionalem Bild.

    :param master: Das übergeordnete Fenster (z.B. CTk oder Tk).
    :type master: tk.Tk | ctk.CTk
    :param title: Fenstertitel.
    :type title: str
    :param message: Anzuzeigende Nachricht.
    :type message: str
    :param image: Optionales Bild als Pfad oder CTkImage.
    :type image: Optional[ctk.CTkImage | str]
    """
    popup = ctk.CTkToplevel(master)
    popup.title(title)
    popup.geometry("600x200")
    popup.resizable(False, False)
    popup.grab_set()  # Macht das Fenster modal

    frame = ctk.CTkFrame(popup)
    frame.pack(expand=True, fill="both", padx=20, pady=20)

    if image:
        # Falls ein Pfad übergeben wurde, lade es als CTkImage
        if isinstance(image, str):
            try:
                tk_img = Image.open(image)
                image = ctk.CTkImage(light_image=tk_img, size=(100, 50))
            except Exception as e:
                logging.error(f"Fehler beim Laden des Bildes: {e}")
                image = None

    if image:
        img_label = ctk.CTkLabel(frame, image=image, text="")
        img_label.pack(pady=(0, 10))

    msg_label = ctk.CTkLabel(frame, text=message, wraplength=260, justify="center")
    msg_label.pack(pady=(0, 15))

    ok_button = ctk.CTkButton(frame, text="OK", command=popup.destroy, width=100)
    ok_button.pack()