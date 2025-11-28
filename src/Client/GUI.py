from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox
from NetworkClient import NetworkClient
from PopupViews import *
import logging
import os
import signal

def closing_protocol():
    """Closes WahlplakatGame and executes some last saving lines of Code."""
    logging.info(f'Closing WahlplakatGame')
    os.kill(os.getpid(), signal.SIGTERM) # This is the last line that gets executed.


class AuthenticationPage(ctk.CTkFrame):
    """
    Authentifizierungs-Seite mit Login und Registrierung als Tabs.
    Ähnlich dem DokumenteUebersichtPopup mit Tabview-Navigation.
    """
    
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        
        self.setup_ui()

        self.NetClient = NetworkClient.get_instance()
    
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche mit Tabview."""
        # Grid-Konfiguration für die Page selbst
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Hauptframe
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Grid-Konfiguration für main_frame
        main_frame.grid_rowconfigure(1, weight=1)  # Tabview soll sich ausdehnen
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Titel
        title_label = ctk.CTkLabel(
            main_frame,
            text="WahlplakatGame",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(10, 30), sticky="n")
        
        # Tabview für Login/Register
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Tabs erstellen
        self.tabview.add("Anmelden")
        self.tabview.add("Registrieren")
        
        # Login Tab einrichten
        self._setup_login_tab()
        
        # Register Tab einrichten
        self._setup_register_tab()
    
    def _setup_login_tab(self):
        """Erstellt den Login-Tab."""
        login_frame = self.tabview.tab("Anmelden")
        
        # Grid-Konfiguration für login_frame
        login_frame.grid_rowconfigure(0, weight=1)  # Oberer Spacer
        login_frame.grid_rowconfigure(1, weight=0)  # Content
        login_frame.grid_rowconfigure(2, weight=1)  # Unterer Spacer
        login_frame.grid_columnconfigure(0, weight=1)
        
        # Zentrierter Content-Frame
        content_frame = ctk.CTkFrame(login_frame, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="n")
        
        # Überschrift
        ctk.CTkLabel(
            content_frame,
            text="Willkommen zurück!",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(0, 30))
        
        # Username
        ctk.CTkLabel(
            content_frame,
            text="Benutzername:",
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.login_username_entry = ctk.CTkEntry(
            content_frame,
            placeholder_text="Benutzername eingeben",
            width=300,
            height=40
        )
        self.login_username_entry.pack(padx=20, pady=(0, 15))
        
        # Passwort
        ctk.CTkLabel(
            content_frame,
            text="Passwort:",
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.login_password_entry = ctk.CTkEntry(
            content_frame,
            placeholder_text="Passwort eingeben",
            show="•",
            width=300,
            height=40
        )
        self.login_password_entry.pack(padx=20, pady=(0, 30))
        
        # Enter-Taste bindet an Login
        self.login_username_entry.bind('<Return>', lambda e: self._handle_login())
        self.login_password_entry.bind('<Return>', lambda e: self._handle_login())
        
        # Login Button
        self.login_button = ctk.CTkButton(
            content_frame,
            text="Anmelden",
            command=self._handle_login,
            width=300,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#1f538d",
            hover_color="#164270"
        )
        self.login_button.pack(padx=20, pady=(0, 10))
        
        # Info-Text
        ctk.CTkLabel(
            content_frame,
            text="Noch kein Konto? → Wechsle zum Registrieren-Tab",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(pady=(20, 0))
    
    def _setup_register_tab(self):
        """Erstellt den Registrierungs-Tab."""
        register_frame = self.tabview.tab("Registrieren")
        
        # Grid-Konfiguration für register_frame
        register_frame.grid_rowconfigure(0, weight=1)  # Oberer Spacer
        register_frame.grid_rowconfigure(1, weight=0)  # Content
        register_frame.grid_rowconfigure(2, weight=1)  # Unterer Spacer
        register_frame.grid_columnconfigure(0, weight=1)
        
        # Zentrierter Content-Frame
        content_frame = ctk.CTkFrame(register_frame, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="n")
        
        # Überschrift
        ctk.CTkLabel(
            content_frame,
            text="Neues Konto erstellen",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(0, 30))
        
        # Username mit Verfügbarkeits-Check
        username_label_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        username_label_frame.pack(fill="x", padx=20, pady=(10, 5))
        
        ctk.CTkLabel(
            username_label_frame,
            text="Benutzername:",
            font=ctk.CTkFont(size=14)
        ).pack(side="left")
        
        username_input_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        username_input_frame.pack(fill="x", padx=20, pady=(0, 5))
        
        self.register_username_entry = ctk.CTkEntry(
            username_input_frame,
            placeholder_text="Benutzername (max. 18 Zeichen)",
            width=200,
            height=40
        )
        self.register_username_entry.pack(side="left", padx=(0, 10))
        
        self.check_username_button = ctk.CTkButton(
            username_input_frame,
            text="Verfügbarkeit prüfen",
            command=self._check_username_availability,
            width=140,
            height=40,
            font=ctk.CTkFont(size=12)
        )
        self.check_username_button.pack(side="left")
        
        # Verfügbarkeits-Status Label
        self.username_status_label = ctk.CTkLabel(
            content_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.username_status_label.pack(padx=20, pady=(0, 10))
        
        # Passwort
        ctk.CTkLabel(
            content_frame,
            text="Passwort:",
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.register_password_entry = ctk.CTkEntry(
            content_frame,
            placeholder_text="Passwort (min. 6 Zeichen)",
            show="•",
            width=300,
            height=40
        )
        self.register_password_entry.pack(padx=20, pady=(0, 15))
        
        # Passwort wiederholen
        ctk.CTkLabel(
            content_frame,
            text="Passwort wiederholen:",
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.register_password_repeat_entry = ctk.CTkEntry(
            content_frame,
            placeholder_text="Passwort erneut eingeben",
            show="•",
            width=300,
            height=40
        )
        self.register_password_repeat_entry.pack(padx=20, pady=(0, 30))
        
        # Enter-Taste bindet an Register
        self.register_username_entry.bind('<Return>', lambda e: self._handle_register())
        self.register_password_entry.bind('<Return>', lambda e: self._handle_register())
        self.register_password_repeat_entry.bind('<Return>', lambda e: self._handle_register())
        
        # Registrieren Button
        self.register_button = ctk.CTkButton(
            content_frame,
            text="Konto erstellen",
            command=self._handle_register,
            width=300,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#1f8d54",
            hover_color="#166d41"
        )
        self.register_button.pack(padx=20, pady=(0, 10))
        
        # Info-Text
        ctk.CTkLabel(
            content_frame,
            text="Bereits ein Konto? → Wechsle zum Anmelden-Tab",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(pady=(20, 0))
    
    def _handle_login(self):
        """Behandelt den Login-Vorgang."""
        username = self.login_username_entry.get().strip()
        password = self.login_password_entry.get()
        
        # Validierung
        if not username:
            messagebox.showerror("Fehler", "Bitte geben Sie einen Benutzernamen ein.")
            return
        
        if not password:
            messagebox.showerror("Fehler", "Bitte geben Sie ein Passwort ein.")
            return

        self.login_button.configure(require_redraw=True, text="Anmeldung läuft...")
        self.update()
        
        response = self.NetClient.login(username, password)

        if response["success"]:
            last_login = response["last_login_time"]
            if last_login != None:
                last_login_str = last_login.value  # Gibt z.B. "20251128T08:31:52"
                dt = datetime.strptime(last_login_str, "%Y%m%dT%H:%M:%S")
                last_login_formatted = dt.strftime('%d.%m.%Y %H:%M:%S')
            else:
                last_login_formatted = "(UNBEKANNT!)"
            show_info_box(
                f'Anmeldung erfolgreich!', 
                f'Willkommen zurück, {response["nickname"]}! (Punkte: {response["points"]})\n\n'
                f'Die letzte erfolgreiche Anmeldung erfolgte am {last_login_formatted} von der IP-Adresse {response["last_login_ip"]}'
            )
            self.controller.my_user = response
            self.controller.show_page("GamePage")
            # Größe setzen
            self.controller.geometry("1600x900")

            # Mindestgröße ändern
            self.controller.minsize(1600, 900)

            # Maximale Größe setzen
            self.controller.maxsize(1920, 1080)

            # Fenster zentrieren (optional)
            self.controller.update_idletasks()
            width = 1600
            height = 900
            x = (self.controller.winfo_screenwidth() // 2) - (width // 2)
            y = (self.controller.winfo_screenheight() // 2) - (height // 2)
            self.controller.geometry(f'{width}x{height}+{x}+{y}')
        else:
            self.login_button.configure(require_redraw=True, text="Anmelden")
            show_warning_box(f'Anmeldung fehlgeschlagen!', f'Die Anmeldung am WahlplakatGame-Server ist fehlgeschlagen. Grund: {response["message"]} (Vielleicht hast du dein Passwort falsch eingetippt?)')
    
    def _handle_register(self):
        """Behandelt den Registrierungs-Vorgang."""
        username = self.register_username_entry.get().strip()
        password = self.register_password_entry.get()
        password_repeat = self.register_password_repeat_entry.get()
        
        # Validierung
        if not username:
            messagebox.showerror("Fehler", "Bitte geben Sie einen Benutzernamen ein.")
            return
        
        if len(username) > 18:
            messagebox.showerror("Fehler", "Benutzername darf maximal 18 Zeichen lang sein.")
            return
        
        if not password:
            messagebox.showerror("Fehler", "Bitte geben Sie ein Passwort ein.")
            return
        
        if len(password) < 6:
            messagebox.showerror("Fehler", "Passwort muss mindestens 6 Zeichen lang sein.")
            return
        
        if password != password_repeat:
            messagebox.showerror("Fehler", "Die Passwörter stimmen nicht überein.")
            return
        
        response = self.NetClient.register_account(username, password)

        if response["success"]:
            show_info_box(f'Konto erfolgreich erstellt!', f'Ihr WahlplakatGame-Konto wurde erstellt. Bitte starte WahlplakatGame nach schließen dieses Dialogs neu. Viel Spaß beim spielen, {username}!')
            closing_protocol()
        else:
            show_error_box(f'Konto nicht erstellt!', f'Das Konto konnte nicht erstellt werden: {response["message"]} (Bitte versuche es erneut!)')
    
    def _check_username_availability(self):
        """Prüft ob der Benutzername verfügbar ist."""
        username = self.register_username_entry.get().strip()
        
        if not username:
            messagebox.showwarning("Hinweis", "Bitte geben Sie zuerst einen Benutzernamen ein.")
            return
        
        if len(username) > 18:
            self.username_status_label.configure(
                text="❌ Benutzername zu lang (max. 18 Zeichen)",
                text_color="red"
            )
            return
        
        response = self.NetClient.check_username_available(username)

        if response["available"]:
            self.username_status_label.configure(
                text="✓ Benutzername verfügbar!",
                text_color="green"
            )
        else:
            self.username_status_label.configure(
                text="❌ Benutzername bereits vergeben",
                text_color="red"
            )


class GamePage(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        self.NetClient = NetworkClient.get_instance()
        self.setup_ui()

    def setup_ui(self):
        """Erstellt die statische UI-Struktur"""
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        



    def insert_into_textbox(self, text: str, color: str = None):
        self.main_game_box.configure(state="normal")
        self.main_game_box.see("end")  # Scrollt zum Ende
        self.main_game_box.configure(state="disabled")
        
    
    def on_show(self):
        """Wird aufgerufen wenn die Page angezeigt wird"""
        # Jetzt haben wir die User-Daten
        if self.controller.my_user:
            nickname = self.controller.my_user["nickname"]
            points = self.controller.my_user["points"]
            self.parteien = self.NetClient.get_alle_parteien(self.controller.my_user["token"])
            print(self.parteien)
            print(f"User eingeloggt: {self.controller.my_user}")

        else:
            print("ne")

        self.main_game_box = ctk.CTkTextbox(
            self,
            state="disabled"
        )
        self.main_game_box.grid(row=0, column=0, rowspan=1, columnspan=1, sticky="nsew")

        self.my_user_label = ctk.CTkLabel(
            self,
            text=f"Name: {self.controller.my_user['nickname']}\nPunkte: {self.controller.my_user['points']}",
            font=ctk.CTkFont(size=16)
        )
        self.my_user_label.grid(row=0, column=2, sticky="new", pady=10, padx=10)






# -------------------------
#   MAIN GUI + NAVIGATOR
# -------------------------
class MainGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WahlplakatGame")
        self.geometry("800x700")
        self.minsize(600, 500)  # Mindestgröße setzen
        
        # Grid-Konfiguration für das Hauptfenster
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Container für alle Seiten
        self.container = ctk.CTkFrame(self)
        self.container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # Grid-Konfiguration für den Container
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        # dict für Page-Objekte
        self.pages = {}

        self.my_user = None
        
        # Seiten erstellen
        for PageClass in (AuthenticationPage, GamePage):
            page_name = PageClass.__name__
            frame = PageClass(self.container, self)
            self.pages[page_name] = frame
            # Alle Seiten übereinander legen mit sticky für Responsiveness
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_page("AuthenticationPage")
    
    def show_page(self, page_name):
        """Zeigt die gewünschte Page an"""
        frame = self.pages[page_name]
        frame.tkraise()  # bringt Frame nach vorne
        # Rufe on_show auf, falls die Methode existiert
        if hasattr(frame, 'on_show'):
            frame.on_show()


# -------------------------
#   START
# -------------------------
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app = MainGUI()
    app.mainloop()