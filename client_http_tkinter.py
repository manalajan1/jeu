import tkinter as tk 
from tkinter import messagebox
import requests

#Creation de la fenetre pricipale
root = tk.Tk()
root.title("Client HTTP Tkinter")  # Définir un titre
root.geometry("400x300")  # Définir la taille de la fenêtre

label_url = tk.Label(root, text="URL du Serveur: ")
label_url.pack()

#Champ de saisie pour l’URL
entry_url = tk.Entry(root, width=50)
entry_url.insert(0, "http://localhost:5000")  # URL par défaut
entry_url.pack()
#Un bouton : 
def send_request():
    url = entry_url.get()  # Récupère l’URL entrée par l’utilisateur
    try:
        response = requests.get(url)  # Envoie une requête GET au serveur
        messagebox.showinfo("Réponse du serveur", response.text)  # Affiche la réponse du serveur
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Erreur", str(e))  # Affiche un message d’erreur

btn_send = tk.Button(root, text="Envoyer GET", command=send_request)
btn_send.pack()


#Label pour les données à envoyer
label_data = tk.Label(root, text="Données à envoyer :")
label_data.pack()

#Champ de saisie des données
entry_data = tk.Entry(root, width=50)
entry_data.pack()

def send_post():
    url = entry_url.get()  # Récupérer l’URL
    data = entry_data.get()  # Récupérer les données entrées par l’utilisateur
    try:
        response = requests.post(url, json={"data": data})  # Envoyer une requête POST
        messagebox.showinfo("Réponse du serveur", response.text)  # Afficher la réponse
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Erreur", str(e))  # Afficher une erreur

btn_post = tk.Button(root, text="Envoyer POST", command=send_post)
btn_post.pack()


def send_delete():
    url = entry_url.get()
    try:
        response = requests.delete(url)  # Envoie une requête DELETE au serveur
        messagebox.showinfo("Réponse du serveur", response.text)  # Affiche la réponse
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Erreur", str(e))  # Affiche une erreur

btn_delete = tk.Button(root, text="Envoyer DELETE", command=send_delete)
btn_delete.pack()
root.mainloop()