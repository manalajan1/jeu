import tkinter as tk
from tkinter import ttk, messagebox
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime
import threading
import time

# Types partagés (identiques au client terminal)
class Role(Enum):
    LOUP = "loup"
    VILLAGEOIS = "villageois"

class PlayerStatus(Enum):
    ALIVE = "vivant"
    DEAD = "mort"

@dataclass
class Position:
    x: int
    y: int

class GameClientTk:
    def _init_(self, base_url: str = "http://localhost:5000/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
        self.player_id = None
        self.role = None
        self.position = None
        
        # Configuration du logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # Création de la fenêtre principale
        self.root = tk.Tk()
        self.root.title("Loup-Garou")
        self.root.geometry("800x600")
        
        self.setup_ui()
        self.update_thread = None
        self.running = False

    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        # Frame d'inscription
        self.login_frame = ttk.LabelFrame(self.root, text="Inscription", padding=10)
        self.login_frame.pack(padx=10, pady=10, fill="x")

        # Champs d'inscription
        ttk.Label(self.login_frame, text="Login:").grid(row=0, column=0, padx=5, pady=5)
        self.login_entry = ttk.Entry(self.login_frame)
        self.login_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.login_frame, text="Rôle:").grid(row=1, column=0, padx=5, pady=5)
        self.role_var = tk.StringVar(value="villageois")
        ttk.Radiobutton(self.login_frame, text="Villageois", variable=self.role_var,
                       value="villageois").grid(row=1, column=1)
        ttk.Radiobutton(self.login_frame, text="Loup", variable=self.role_var,
                       value="loup").grid(row=1, column=2)

        self.inscription_btn = ttk.Button(self.login_frame, text="S'inscrire",
                                        command=self.handle_inscription)
        self.inscription_btn.grid(row=2, column=1, pady=10)

        # Zone de jeu
        self.game_frame = ttk.LabelFrame(self.root, text="Jeu", padding=10)
        self.game_frame.pack(padx=10, pady=5, fill="both", expand=True)

        # Canvas pour la carte
        self.canvas = tk.Canvas(self.game_frame, width=400, height=400, bg='white')
        self.canvas.pack(pady=10)

        # Informations du jeu
        self.info_label = ttk.Label(self.game_frame, text="En attente d'inscription...")
        self.info_label.pack(pady=5)

        # Contrôles de déplacement
        self.controls_frame = ttk.Frame(self.game_frame)
        self.controls_frame.pack(pady=10)

        # Touches directionnelles
        ttk.Button(self.controls_frame, text="↑", command=lambda: self.move("z")).grid(row=0, column=1)
        ttk.Button(self.controls_frame, text="←", command=lambda: self.move("q")).grid(row=1, column=0)
        ttk.Button(self.controls_frame, text="↓", command=lambda: self.move("s")).grid(row=1, column=1)
        ttk.Button(self.controls_frame, text="→", command=lambda: self.move("d")).grid(row=1, column=2)

    def handle_inscription(self):
        """Gestion de l'inscription"""
        login = self.login_entry.get()
        role = Role(self.role_var.get())

        try:
            success, message = self.inscription(login, role)
            if success:
                messagebox.showinfo("Succès", "Inscription réussie!")
                self.login_frame.pack_forget()  # Cache le formulaire d'inscription
                self.start_game_updates()  # Démarre les mises à jour
            else:
                messagebox.showerror("Erreur", message)
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def inscription(self, login: str, role: Role) -> Tuple[bool, str]:
        """Inscription du joueur"""
        try:
            if not 3 <= len(login) <= 20 or not login.isalnum():
                return False, "Login invalide (3-20 caractères alphanumériques)"

            response = self.session.post(
                f"{self.base_url}/inscription",
                json={"login": login, "role": role.value}
            )

            if response.status_code == 200:
                data = response.json()
                self.player_id = data["player_id"]
                self.role = role
                self.position = Position(data["x"], data["y"])
                return True, "Inscription réussie"

            error_msg = response.json().get("error", "Erreur inconnue")
            return False, error_msg

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erreur réseau: {e}")
            return False, str(e)

    def move(self, direction: str):
        """Gestion des déplacements"""
        if not self.player_id:
            return

        delta = {"z": (0, -1), "s": (0, 1), "q": (-1, 0), "d": (1, 0)}[direction]
        nouvelle_pos = Position(
            self.position.x + delta[0],
            self.position.y + delta[1]
        )

        try:
            response = self.session.post(
                f"{self.base_url}/deplacement/{self.player_id}",
                json={
                    "x": nouvelle_pos.x,
                    "y": nouvelle_pos.y,
                    "tour": self.get_tour_actuel()
                }
            )

            if response.status_code == 200:
                self.position = nouvelle_pos
            else:
                messagebox.showwarning("Erreur", response.json().get("error", "Erreur de déplacement"))

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erreur réseau: {e}")

    def get_vision(self) -> Optional[Dict]:
        """Récupération de la vision du joueur"""
        if not self.player_id:
            return None

        try:
            response = self.session.get(f"{self.base_url}/vision/{self.player_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None

    def draw_map(self, vision: Dict):
        """Dessin de la carte"""
        if not vision:
            return

        self.canvas.delete("all")
        carte = vision["carte"]
        cell_size = min(400 // len(carte), 400 // len(carte[0]))

        colors = {
            ".": "white",    # Case vide
            "L": "red",      # Loup
            "V": "green",    # Villageois
            "?": "gray",     # Inconnu
            "X": "black"     # Obstacle
        }

        for i, row in enumerate(carte):
            for j, cell in enumerate(row):
                x1, y1 = j * cell_size, i * cell_size
                x2, y2 = x1 + cell_size, y1 + cell_size
                color = colors.get(cell, "white")
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")

        # Mise à jour des informations
        info_text = f"Tour: {vision['tour_actuel']} - "
        info_text += f"Temps: {vision['temps_restant']:.1f}s"
        if vision.get("elimine"):
            info_text += " - ÉLIMINÉ!"
        self.info_label.config(text=info_text)

    def update_game_state(self):
        """Mise à jour de l'état du jeu"""
        while self.running:
            vision = self.get_vision()
            if vision:
                self.root.after(0, self.draw_map, vision)
            time.sleep(0.1)  # Rafraîchissement toutes les 100ms

    def start_game_updates(self):
        """Démarrage du thread de mise à jour"""
        self.running = True
        self.update_thread = threading.Thread(target=self.update_game_state)
        self.update_thread.daemon = True
        self.update_thread.start()

    def get_tour_actuel(self) -> int:
        """Récupération du tour actuel"""
        try:
            response = self.session.get(f"{self.base_url}/tour")
            if response.status_code == 200:
                return response.json()["tour_actuel"]
            return 0
        except:
            return 0

    def run(self):
        """Lancement de l'application"""
        # Gestion de la fermeture
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        # Lancement de la boucle principale
        self.root.mainloop()

    def on_closing(self):
        """Gestion de la fermeture de l'application"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1.0)
        self.root.destroy()

if __name__ == "_main_":
    client = GameClientTk()
client.run()