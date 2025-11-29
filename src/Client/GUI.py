from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox
from NetworkClient import NetworkClient
from PopupViews import *
import logging
import os
import signal
from CTkListbox import CTkListbox
import webbrowser
from GameClient import GameClient
import random
import pygame
from ResourceFetcher import ResourceFetcher



RF = ResourceFetcher()



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
            self.login_button.configure(require_redraw=True, text="Anmelden")
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
        self.GameClient = GameClient.get_instance()
        
        self.current_quelle = None
        self.has_answered = False
        self.available_parteien = []
        
        self.setup_ui()
        self.setup_game_callbacks()

    def setup_ui(self):
        """Erstellt die statische UI-Struktur"""
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

        # In der __init__ oder setup_ui von GamePage:
        pygame.mixer.init()

        # Sounds laden (einmalig, z.B. in on_show):
        self.sound_correct = pygame.mixer.Sound(RF.get_resource("correct_answer.mp3"))
        self.sound_incorrect = pygame.mixer.Sound(RF.get_resource("incorrect_answer.mp3"))
        self.sound_join = pygame.mixer.Sound(RF.get_resource("player_join.mp3"))
        self.sound_leave = pygame.mixer.Sound(RF.get_resource("player_leave.mp3"))
        self.sound_lock = pygame.mixer.Sound(RF.get_resource("lock_answer.mp3"))
        
    def setup_game_callbacks(self):
        """Registriert WebSocket Event Callbacks"""
        self.GameClient.on('new_round', self.on_new_round)
        self.GameClient.on('player_answered', self.on_player_answered)
        self.GameClient.on('round_end', self.on_round_end)
        self.GameClient.on('player_joined', self.on_player_joined)
        self.GameClient.on('player_left', self.on_player_left)
        self.GameClient.on('player_list_update', self.on_player_list_update)
        self.GameClient.on('answer_accepted', self.on_answer_accepted)
        self.GameClient.on('leaderboard_update', self.on_leaderboard_update)
        self.GameClient.on('error', self.on_error)
        
    def insert_into_textbox(self, text: str, color: str = None):
        """
        Fügt Text in die Textbox ein und scrollt zum Ende.
        """
        self.main_game_box.configure(state='normal')

        if color != "default":
            tag_hash = random.getrandbits(32)
            self.main_game_box.insert("end", text + "\n", tags=tag_hash)
            self.main_game_box.tag_config(tag_hash, foreground=color)
        else:
            self.main_game_box.insert("end", text + "\n")

        self.main_game_box.yview_moveto(1)
        self.main_game_box.configure(state='disabled')
    
    def on_show(self):
        """Wird aufgerufen wenn die Page angezeigt wird"""
        if not self.controller.my_user:
            return

        nickname = self.controller.my_user["nickname"]
        points = self.controller.my_user["points"]
        token = self.controller.my_user["token"]
        
        # Hole Parteien
        self.available_parteien = self.NetClient.get_alle_parteien(token)
        
        # Erstelle UI Elemente
        self.main_game_box = ctk.CTkTextbox(
            self,
            state="disabled",
            wrap="word",
            font=ctk.CTkFont(size=14)
        )
        self.main_game_box.grid(row=0, column=0, rowspan=3, columnspan=2, sticky="nsew", padx=10, pady=10)

        self.my_user_label = ctk.CTkLabel(
            self,
            text=f"Spieler: {nickname}\nPunkte: {points}",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.my_user_label.grid(row=0, column=2, sticky="new", pady=10, padx=10)

        self.current_lobby_players = CTkListbox(
            self,
            height=250
        )
        self.current_lobby_players.grid(row=1, column=2, sticky="nsew", pady=10, padx=10)

        self.leaderboard = CTkListbox(
            self,
            height=250
        )
        self.leaderboard.grid(row=2, column=2, sticky="nsew", pady=10, padx=10)
        self.leaderboard.insert(0, "🏆 Top-Spieler")

        # Partei-Auswahl Dropdown
        if self.available_parteien:
            self.partei_auswahl_dropdown = ctk.CTkOptionMenu(
                self,
                values=self.available_parteien,
                font=ctk.CTkFont(size=14)
            )
            self.partei_auswahl_dropdown.grid(row=3, column=0, sticky="ew", pady=10, padx=10)
            self.partei_auswahl_dropdown.set(self.available_parteien[0])

        # Antwort-Button
        self.antwort_button = ctk.CTkButton(
            self,
            text="Antwort senden",
            command=self.send_answer,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1f8d54",
            hover_color="#166d41"
        )
        self.antwort_button.grid(row=3, column=1, sticky="ew", pady=10, padx=10)

        # Button Frame für Quellen und Verlassen
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=3, column=2, sticky="ew", pady=10, padx=10)
        
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        # Quellen-Button (initial disabled)
        self.source_button = ctk.CTkButton(
            button_frame,
            text="Quelle anzeigen",
            command=self.show_source,
            font=ctk.CTkFont(size=12),
            state="disabled"
        )
        self.source_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        # Verlassen-Button
        self.leave_button = ctk.CTkButton(
            button_frame,
            text="Spiel verlassen",
            command=self.leave_game,
            font=ctk.CTkFont(size=12),
            fg_color="#8d1f1f",
            hover_color="#701616"
        )
        self.leave_button.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # Verbinde mit GameService und tritt bei
        self.insert_into_textbox("🔌 Verbinde mit Server...\n")
        
        if self.GameClient.connect():
            self.insert_into_textbox("✅ Verbunden! Trete Lobby bei...\n", "#00FF00")
            self.GameClient.join_game(token)
        else:
            self.insert_into_textbox("❌ Verbindung fehlgeschlagen!\n", "#FF0000")
        
        # Leaderboard anfordern
        self.GameClient.request_leaderboard()
    
    # ==================== GAME EVENT HANDLERS ====================
    
    def on_new_round(self, data):
        """Neue Runde beginnt"""
        self.has_answered = False
        self.current_quelle = None
        self.source_button.configure(state="disabled")
        self.antwort_button.configure(state="normal")
        
        round_num = data.get('round_number', '?')
        wahlspruch = data.get('wahlspruch', '')
        
        self.insert_into_textbox(f"\n{'='*60}\n", "#FFFF00")
        self.insert_into_textbox(f"🎮 RUNDE #{round_num}\n", "#FFFF00")
        self.insert_into_textbox(f"{'='*60}\n\n", "#FFFF00")
        self.insert_into_textbox(f'"{wahlspruch}"\n\n', "#FFFFFF")
        self.insert_into_textbox("⏱️ 15 Sekunden Zeit zum Antworten!\n")
    
    def on_player_answered(self, data):
        """Ein Spieler hat geantwortet"""
        nickname = data.get('nickname', 'Jemand')
        self.insert_into_textbox(f"✓ {nickname} hat geantwortet\n", "#00FFFF")
    
    def on_round_end(self, data):
        """Runde ist zu Ende"""
        correct_partei = data.get('correct_partei', '')
        results = data.get('results', [])
        quelle = data.get('quelle', None)
        
        self.current_quelle = quelle
        
        self.insert_into_textbox(f"\n{'='*60}\n", "#FF00FF")
        self.insert_into_textbox(f"🏁 RUNDENENDE\n", "#FF00FF")
        self.insert_into_textbox(f"{'='*60}\n\n", "#FF00FF")
        self.insert_into_textbox(f"Richtige Antwort: {correct_partei}\n\n", "#00FF00")
        
        # Prüfe ob der eigene Spieler richtig oder falsch geantwortet hat
        my_result = None
        for result in results:
            if result['nickname'] == self.controller.my_user['nickname']:
                my_result = result
                break
        
        # Spiele Sound für eigene Antwort
        if my_result:
            if my_result.get('correct') == True:
                self.sound_correct.play()
            elif my_result.get('correct') == False:
                self.sound_incorrect.play()
        
        # Zeige Ergebnisse
        for result in results:
            nickname = result['nickname']
            answered = result.get('answered', 'Keine Antwort')
            correct = result.get('correct')
            points_earned = result.get('points_earned', 0)
            total_points = result.get('total_points', 0)
            could_answer = result.get('could_answer', True)
            
            if not could_answer:
                self.insert_into_textbox(f"  {nickname}: (während Runde beigetreten)\n", "#808080")
            elif correct is None:
                self.insert_into_textbox(f"  {nickname}: Keine Antwort\n", "#808080")
            elif correct:
                self.insert_into_textbox(f"  ✓ {nickname}: {answered} [+{points_earned} Punkt] (Gesamt: {total_points})\n", "#00FF00")
            else:
                self.insert_into_textbox(f"  ✗ {nickname}: {answered} (Gesamt: {total_points})\n", "#FF0000")
        
        self.insert_into_textbox(f"\n⏳ Nächste Runde in 5 Sekunden...\n\n")
        
        # Update eigene Punkte
        for result in results:
            if result['nickname'] == self.controller.my_user['nickname']:
                self.controller.my_user['points'] = result['total_points']
                self.my_user_label.configure(
                    text=f"Spieler: {self.controller.my_user['nickname']}\nPunkte: {result['total_points']}"
                )
                break
    
    def on_player_joined(self, data):
        """Neuer Spieler ist beigetreten"""
        nickname = data.get('nickname', 'Jemand')
        self.insert_into_textbox(f"👋 {nickname} ist beigetreten\n", "#FFFF00")
        self.sound_join.play()
    
    def on_player_left(self, data):
        """Spieler hat verlassen"""
        nickname = data.get('nickname', 'Jemand')
        reason = data.get('reason', '')
        
        if reason == 'disconnect':
            self.insert_into_textbox(f"👋 {nickname} hat die Lobby verlassen (Verbindung getrennt)\n", "#FFA500")
        elif reason == 'request':
            self.insert_into_textbox(f"👋 {nickname} hat die Lobby verlassen\n", "#FFA500")
        else:
            self.insert_into_textbox(f"👋 {nickname} hat die Lobby verlassen\n", "#FFA500")

        self.sound_leave.play()
    
    def on_player_list_update(self, data):
        """Spielerliste wurde aktualisiert"""
        players = data.get('players', [])
        
        # Update Current Players Liste
        self.current_lobby_players.delete(0, "end")
        self.current_lobby_players.insert(0, "👥 Aktuelle Spieler:")
        
        for i, player in enumerate(players, 1):
            nickname = player['nickname']
            points = player['points']
            answered = player.get('answered', False)
            can_answer = player.get('can_answer', True)
            
            status = "✓" if answered else "⏳"
            if not can_answer:
                status = "⊘"  # Kann nicht antworten
            
            self.current_lobby_players.insert("end", f"{status} {nickname} ({points})")
    
    def on_answer_accepted(self, data):
        """Eigene Antwort wurde akzeptiert"""
        self.has_answered = True
        self.antwort_button.configure(state="disabled")
        
        if self.current_quelle:
            self.source_button.configure(state="normal")
        
        partei = data.get('partei', '')
        self.insert_into_textbox(f"✅ Deine Antwort wurde registriert: {partei}\n", "#00FF00")

        self.sound_lock.play()
    
    def on_leaderboard_update(self, data):
        """Leaderboard wurde aktualisiert"""
        leaderboard = data.get('leaderboard', [])
        
        self.leaderboard.delete(0, "end")
        self.leaderboard.insert(0, "🏆 Top-Spieler")
        
        for entry in leaderboard:
            rank = entry['rank']
            nickname = entry['nickname']
            points = entry['points']
            
            medal = ""
            if rank == 1:
                medal = "🥇"
            elif rank == 2:
                medal = "🥈"
            elif rank == 3:
                medal = "🥉"
            else:
                medal = f"{rank}."
            
            self.leaderboard.insert("end", f"{medal} {nickname}: {points}")
    
    def on_error(self, data):
        """Fehler vom Server"""
        message = data.get('message', 'Unbekannter Fehler')
        self.insert_into_textbox(f"❌ Fehler: {message}\n", "#FF0000")
    
    # ==================== UI ACTIONS ====================
    
    def send_answer(self):
        """Sendet die gewählte Antwort"""
        if self.has_answered:
            show_warning_box("Hinweis", "Du hast bereits geantwortet!")
            return
        
        if not hasattr(self, 'partei_auswahl_dropdown'):
            return
        
        selected_partei = self.partei_auswahl_dropdown.get()
        
        if not selected_partei:
            show_warning_box("Fehler", "Bitte wähle eine Partei aus!")
            return
        
        self.GameClient.submit_answer(selected_partei)
    
    def show_source(self):
        """Zeigt die Quelle an"""
        if self.current_quelle:
            if self.current_quelle.startswith('http'):
                # Öffne URL im Browser
                webbrowser.open(self.current_quelle)
            else:
                # Zeige Text-Quelle
                show_info_box("Quelle", self.current_quelle if self.current_quelle else "Keine Quelle verfügbar")
        else:
            show_warning_box("Quelle", "Keine Quelle verfügbar für diesen Wahlspruch.")
    
    def leave_game(self):
        """Verlässt das Spiel und kehrt zum Login zurück"""
        result = question_box(
            "Spiel verlassen",
            "Möchtest du das Spiel wirklich verlassen?",
            icon='warning'
        )
        
        if result == 'yes':
            self.insert_into_textbox("👋 Verlasse Spiel...\n", "#FFA500")
            
            # Verlasse GameService
            self.GameClient.leave_game()
            
            # Kurze Verzögerung für sauberes Disconnect
            self.after(500, self._complete_leave)
    
    def _complete_leave(self):
        """Komplettiert das Verlassen des Spiels"""
        # Zurück zum Login
        self.controller.show_page("AuthenticationPage")
        
        # Fenster zurücksetzen
        self.controller.geometry("800x700")
        self.controller.minsize(600, 500)
        self.controller.maxsize(1920, 1080)
        
        # Zentriere Fenster
        self.controller.update_idletasks()
        width = 800
        height = 700
        x = (self.controller.winfo_screenwidth() // 2) - (width // 2)
        y = (self.controller.winfo_screenheight() // 2) - (height // 2)
        self.controller.geometry(f'{width}x{height}+{x}+{y}')



# -------------------------
#   MAIN GUI + NAVIGATOR
# -------------------------
class MainGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WahlplakatGame")
        self.geometry("800x700")
        self.minsize(600, 500)  # Mindestgröße setzen
        self.iconbitmap(RF.get_resource('icon.ico'))
        
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
        
        # Cleanup beim Schließen
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.show_page("AuthenticationPage")
    
    def show_page(self, page_name):
        """Zeigt die gewünschte Page an"""
        frame = self.pages[page_name]
        frame.tkraise()  # bringt Frame nach vorne
        # Rufe on_show auf, falls die Methode existiert
        if hasattr(frame, 'on_show'):
            frame.on_show()
    
    def on_closing(self):
        """Wird beim Schließen des Fensters aufgerufen"""
        logging.info("Fenster wird geschlossen - führe Cleanup durch")
        
        # Disconnect GameClient falls verbunden
        game_client = GameClient.get_instance()
        if game_client.is_connected():
            logging.info("Trenne GameClient...")
            game_client.disconnect()
        
        # Logout über NetClient falls angemeldet
        net_client = NetworkClient.get_instance()
        if net_client.is_authenticated():
            logging.info("Melde vom Server ab...")
            net_client.logout()
        
        # Schließe Fenster
        self.destroy()
        
        # Beende Programm sauber
        closing_protocol()


# -------------------------
#   START
# -------------------------
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app = MainGUI()
    app.mainloop()