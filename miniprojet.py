"""LOCATION DE VÉHICULES - version simple (console + sauvegarde JSON).

Lancer :  python location_vehicules.py
Pour tester avec des données : copier donnees_demo.json et le renommer donnees.json.
"""

import json
import os
from datetime import date, datetime

FICHIER = "donnees.json"
DUREE_MAX = 30
CONFIRMEE = "confirmée"
EN_COURS = "en cours"
TERMINEE = "terminée"
ANNULEE = "annulée"


def lire_date_texte(texte):
    """'25/12/2026' -> '2026-12-25'. Renvoie "" si la date est invalide."""
    try:
        jour, mois, annee = texte.strip().split("/")
        return date(int(annee), int(mois), int(jour)).isoformat()
    except ValueError:
        return ""


def jours_entre(date1, date2):
    return (date.fromisoformat(date2) - date.fromisoformat(date1)).days


def nombre_de_jours(debut, fin):
    return jours_entre(debut, fin) + 1


def afficher_date(d):
    return d[8:10] + "/" + d[5:7] + "/" + d[0:4]


class Vehicule:
    def __init__(self, id_vehicule, marque, modele, tarif):
        self.__id = id_vehicule
        self.__marque = marque
        self.__modele = modele
        self.__tarif = tarif

    def get_id(self):
        return self.__id

    def get_marque(self):
        return self.__marque

    def get_nom(self):
        return self.__marque + " " + self.__modele

    def get_tarif(self):
        return self.__tarif

    def get_type(self):
        return "vehicule"

    def details(self):
        return ""

    def prix(self, nb_jours):
        return round(self.__tarif * nb_jours, 2)

    def prix_retard(self):
        """Prix d'un jour de retard."""
        return round(self.__tarif * 1.5, 2)

    def vers_dict(self):
        return {
            "type": self.get_type(),
            "id": self.__id,
            "marque": self.__marque,
            "modele": self.__modele,
            "tarif": self.__tarif,
        }


class Voiture(Vehicule):
    def __init__(self, id_vehicule, marque, modele, tarif, nb_portes):
        super().__init__(id_vehicule, marque, modele, tarif)
        self.__nb_portes = nb_portes

    def get_type(self):
        return "voiture"

    def details(self):
        return str(self.__nb_portes) + " portes"

    def prix(self, nb_jours):
        """Redéfinition : -10 % à partir de 7 jours."""
        total = self.get_tarif() * nb_jours
        if nb_jours >= 7:
            total = total * 0.90
        return round(total, 2)

    def vers_dict(self):
        donnees = super().vers_dict()
        donnees["nb_portes"] = self.__nb_portes
        return donnees


class Moto(Vehicule):
    def __init__(self, id_vehicule, marque, modele, tarif, cylindree):
        super().__init__(id_vehicule, marque, modele, tarif)
        self.__cylindree = cylindree

    def get_type(self):
        return "moto"

    def details(self):
        return str(self.__cylindree) + " cm3"

    def prix(self, nb_jours):
        """Redéfinition : +3 € par jour pour le casque."""
        return round((self.get_tarif() + 3) * nb_jours, 2)

    def prix_retard(self):
        """Redéfinition : le retard coûte 2 fois le tarif."""
        return round(self.get_tarif() * 2, 2)

    def vers_dict(self):
        donnees = super().vers_dict()
        donnees["cylindree"] = self.__cylindree
        return donnees


def cle_prix(vehicule):
    return vehicule.get_tarif()


def cle_marque(vehicule):
    return vehicule.get_marque().lower()


def cle_nombre(element):
    return element[1]


def montant_encaisse(r):
    """Ce que l'agence a vraiment encaissé pour une réservation (dictionnaire r)."""
    if r["statut"] == TERMINEE:
        return round(r["prix"] + r["frais_retard"], 2)
    if r["statut"] == ANNULEE:
        return r["frais_annulation"]
    return 0


class Agence:
    def __init__(self):
        self.__vehicules = []
        self.__clients = []
        self.__reservations = []
        self.__maintenances = []
        self.__historique = []
        self.__prochain_id = {"vehicule": 1, "client": 1, "reservation": 1, "maintenance": 1}

    def get_vehicules(self):
        return list(self.__vehicules)

    def get_clients(self):
        return list(self.__clients)

    def get_reservations(self):
        return list(self.__reservations)

    def get_maintenances(self):
        return list(self.__maintenances)

    def get_historique(self):
        return list(self.__historique)

    def __nouvel_id(self, nom):
        numero = self.__prochain_id[nom]
        self.__prochain_id[nom] = numero + 1
        return numero

    def __noter(self, texte):
        self.__historique.append(datetime.now().strftime("%Y-%m-%d %H:%M") + " | " + texte)

    def __trouver(self, liste, numero):
        for element in liste:
            if element["id"] == numero:
                return element
        return None

    def trouver_vehicule(self, numero):
        for v in self.__vehicules:
            if v.get_id() == numero:
                return v
        return None

    def ajouter_vehicule(self, type_v, marque, modele, tarif, special):
        """special = nombre de portes (voiture) ou cylindrée (moto)."""
        if marque.strip() == "" or modele.strip() == "":
            return False, "La marque et le modèle sont obligatoires."
        if tarif <= 0:
            return False, "Le tarif doit être supérieur à 0."
        if type_v == "voiture":
            if special < 2 or special > 5:
                return False, "Le nombre de portes doit être entre 2 et 5."
            v = Voiture(self.__nouvel_id("vehicule"), marque.strip(), modele.strip(), tarif, special)
        else:
            if special < 50 or special > 2000:
                return False, "La cylindrée doit être entre 50 et 2000 cm3."
            v = Moto(self.__nouvel_id("vehicule"), marque.strip(), modele.strip(), tarif, special)
        self.__vehicules.append(v)
        self.__noter("Ajout véhicule n°" + str(v.get_id()) + " " + v.get_nom())
        return True, "Véhicule n°" + str(v.get_id()) + " ajouté."

    def ajouter_client(self, nom, telephone):
        telephone = telephone.replace(" ", "")
        if nom.strip() == "":
            return False, "Le nom est obligatoire."
        if not telephone.isdigit() or len(telephone) < 8 or len(telephone) > 15:
            return False, "Téléphone invalide (8 à 15 chiffres)."
        client = {"id": self.__nouvel_id("client"), "nom": nom.strip(), "telephone": telephone}
        self.__clients.append(client)
        self.__noter("Ajout client n°" + str(client["id"]) + " " + client["nom"])
        return True, "Client n°" + str(client["id"]) + " ajouté."

    def verifier_libre(self, id_vehicule, debut, fin, ignorer):
        """Renvoie "" si le véhicule est libre, sinon l'explication du problème."""
        for r in self.__reservations:
            if r["vehicule"] == id_vehicule and r["id"] != ignorer:
                if r["statut"] == CONFIRMEE or r["statut"] == EN_COURS:
                    if debut <= r["fin"] and r["debut"] <= fin:
                        return "déjà réservé du " + afficher_date(r["debut"]) + " au " + afficher_date(r["fin"])
        for m in self.__maintenances:
            if m["vehicule"] == id_vehicule and debut <= m["fin"] and m["debut"] <= fin:
                return "en maintenance du " + afficher_date(m["debut"]) + " au " + afficher_date(m["fin"])
        return ""

    def rechercher(self, type_v, prix_max, marque, debut, fin, tri):
        """Recherche avec plusieurs critères. Si debut = "", on ne regarde pas les dates."""
        resultat = []
        for v in self.__vehicules:
            if type_v != "" and v.get_type() != type_v:
                continue
            if prix_max > 0 and v.get_tarif() > prix_max:
                continue
            if marque.strip() != "" and marque.strip().lower() not in v.get_marque().lower():
                continue
            if debut != "" and self.verifier_libre(v.get_id(), debut, fin, 0) != "":
                continue
            resultat.append(v)
        if tri == "prix":
            resultat.sort(key=cle_prix)
        elif tri == "marque":
            resultat.sort(key=cle_marque)
        return resultat

    def reserver(self, id_client, id_vehicule, debut, fin, aujourdhui):
        if self.__trouver(self.__clients, id_client) is None:
            return False, "Client introuvable."
        vehicule = self.trouver_vehicule(id_vehicule)
        if vehicule is None:
            return False, "Véhicule introuvable."
        if fin < debut:
            return False, "La date de fin est avant la date de début."
        if debut < aujourdhui:
            return False, "On ne peut pas réserver dans le passé."
        n = nombre_de_jours(debut, fin)
        if n > DUREE_MAX:
            return False, "Durée maximale : " + str(DUREE_MAX) + " jours."
        probleme = self.verifier_libre(id_vehicule, debut, fin, 0)
        if probleme != "":
            return False, "Véhicule indisponible : " + probleme + "."

        r = {
            "id": self.__nouvel_id("reservation"),
            "client": id_client,
            "vehicule": id_vehicule,
            "debut": debut,
            "fin": fin,
            "prix": vehicule.prix(n),
            "statut": CONFIRMEE,
            "depart": "",
            "retour": "",
            "retard": 0,
            "frais_retard": 0,
            "frais_annulation": 0,
        }
        self.__reservations.append(r)
        self.__noter(
            "Réservation n°"
            + str(r["id"])
            + " : "
            + vehicule.get_nom()
            + " du "
            + afficher_date(debut)
            + " au "
            + afficher_date(fin)
            + " = "
            + str(r["prix"])
            + " €"
        )
        return (
            True,
            "Réservation n°" + str(r["id"]) + " créée : " + str(n) + " jour(s), " + str(r["prix"]) + " €.",
        )

    def annuler(self, id_reservation, aujourdhui):
        """7 jours ou plus avant : gratuit / 2 à 6 jours : 20 % / 0 à 1 jour : 50% / après le début : impossible."""
        r = self.__trouver(self.__reservations, id_reservation)
        if r is None:
            return False, "Réservation introuvable."
        if r["statut"] != CONFIRMEE:
            return False, "Annulation impossible : la réservation est " + r["statut"] + "."
        jours_avant = jours_entre(aujourdhui, r["debut"])
        if jours_avant < 0:
            return False, "Annulation impossible : la location a déjà commencé."
        if jours_avant >= 7:
            taux = 0
        elif jours_avant >= 2:
            taux = 0.20
        else:
            taux = 0.50
        r["statut"] = ANNULEE
        r["frais_annulation"] = round(r["prix"] * taux, 2)
        self.__noter("Annulation réservation n°" + str(r["id"]) + ", frais " + str(r["frais_annulation"]) + " €")
        return True, "Réservation annulée. Frais : " + str(r["frais_annulation"]) + " €."

    def depart(self, id_reservation, date_depart):
        r = self.__trouver(self.__reservations, id_reservation)
        if r is None:
            return False, "Réservation introuvable."
        if r["statut"] != CONFIRMEE:
            return False, "Départ impossible : la réservation est " + r["statut"] + "."
        if date_depart < r["debut"]:
            return False, "Trop tôt : la location commence le " + afficher_date(r["debut"]) + "."
        if date_depart > r["fin"]:
            return False, "La période de réservation est dépassée."
        for autre in self.__reservations:
            if autre["vehicule"] == r["vehicule"] and autre["statut"] == EN_COURS:
                return False, "Le véhicule n'est pas encore rentré (réservation n°" + str(autre["id"]) + ")."
        r["statut"] = EN_COURS
        r["depart"] = date_depart
        self.__noter("Départ réservation n°" + str(r["id"]))
        return True, "Départ enregistré."

    def retour(self, id_reservation, date_retour):
        r = self.__trouver(self.__reservations, id_reservation)
        if r is None:
            return False, "Réservation introuvable."
        if r["statut"] != EN_COURS:
            return False, "Retour impossible : la réservation est " + r["statut"] + "."
        if date_retour < r["depart"]:
            return False, "La date de retour est avant la date de départ."
        retard = jours_entre(r["fin"], date_retour)
        if retard < 0:
            retard = 0
        frais = round(retard * self.trouver_vehicule(r["vehicule"]).prix_retard(), 2)
        r["statut"] = TERMINEE
        r["retour"] = date_retour
        r["retard"] = retard
        r["frais_retard"] = frais
        self.__noter("Retour réservation n°" + str(r["id"]) + ", total " + str(montant_encaisse(r)) + " €")
        return (
            True,
            (
                "Retour enregistré. Prix prévu : "
                + str(r["prix"])
                + " €, retard : "
                + str(retard)
                + " jour(s) = "
                + str(frais)
                + " €. TOTAL À PAYER : "
                + str(montant_encaisse(r))
                + " €."
            ),
        )

    def planifier_maintenance(self, id_vehicule, debut, fin, motif, aujourdhui):
        vehicule = self.trouver_vehicule(id_vehicule)
        if vehicule is None:
            return False, "Véhicule introuvable."
        if motif.strip() == "":
            return False, "Le motif est obligatoire."
        if fin < debut:
            return False, "La date de fin est avant la date de début."
        if fin < aujourdhui:
            return False, "Cette période est dans le passé."
        probleme = self.verifier_libre(id_vehicule, debut, fin, 0)
        if probleme != "":
            return False, "Maintenance impossible : véhicule " + probleme + "."
        m = {
            "id": self.__nouvel_id("maintenance"),
            "vehicule": id_vehicule,
            "debut": debut,
            "fin": fin,
            "motif": motif.strip(),
        }
        self.__maintenances.append(m)
        self.__noter("Maintenance n°" + str(m["id"]) + " : " + vehicule.get_nom() + " (" + m["motif"] + ")")
        return True, "Maintenance n°" + str(m["id"]) + " planifiée."

    def indicateurs(self):
        revenus = 0
        revenus_par_type = {}
        retards = []
        nb_locations = {}
        for r in self.__reservations:
            revenus = revenus + montant_encaisse(r)
            if r["statut"] == TERMINEE:
                type_v = self.trouver_vehicule(r["vehicule"]).get_type()
                revenus_par_type[type_v] = revenus_par_type.get(type_v, 0) + montant_encaisse(r)
                if r["retard"] > 0:
                    retards.append(r)
            if r["statut"] == TERMINEE or r["statut"] == EN_COURS:
                nom = self.trouver_vehicule(r["vehicule"]).get_nom()
                nb_locations[nom] = nb_locations.get(nom, 0) + 1
        classement = sorted(nb_locations.items(), key=cle_nombre, reverse=True)
        return {
            "revenus": round(revenus, 2),
            "par_type": revenus_par_type,
            "retards": retards,
            "plus_loues": classement[:3],
        }

    def sauvegarder(self, fichier):
        liste_vehicules = []
        for v in self.__vehicules:
            liste_vehicules.append(v.vers_dict())
        donnees = {
            "prochain_id": self.__prochain_id,
            "vehicules": liste_vehicules,
            "clients": self.__clients,
            "reservations": self.__reservations,
            "maintenances": self.__maintenances,
            "historique": self.__historique,
        }
        temporaire = fichier + ".tmp"
        with open(temporaire, "w", encoding="utf-8") as f:
            json.dump(donnees, f, ensure_ascii=False, indent=2)
        os.replace(temporaire, fichier)

    def remplir(self, donnees):
        """Remplit l'agence avec le contenu du fichier. Lève ValueError si le fichier est incohérent."""
        for d in donnees["vehicules"]:
            if d["type"] == "voiture":
                v = Voiture(d["id"], d["marque"], d["modele"], d["tarif"], d["nb_portes"])
            elif d["type"] == "moto":
                v = Moto(d["id"], d["marque"], d["modele"], d["tarif"], d["cylindree"])
            else:
                raise ValueError("type de véhicule inconnu")
            self.__vehicules.append(v)
        self.__clients = donnees["clients"]
        self.__reservations = donnees["reservations"]
        self.__maintenances = donnees["maintenances"]
        self.__historique = donnees["historique"]

        for r in self.__reservations:
            if self.__trouver(self.__clients, r["client"]) is None or self.trouver_vehicule(r["vehicule"]) is None:
                raise ValueError("réservation n°" + str(r["id"]) + " : client ou véhicule inexistant")

        plus_grand = {"vehicule": 0, "client": 0, "reservation": 0, "maintenance": 0}
        for v in self.__vehicules:
            plus_grand["vehicule"] = max(plus_grand["vehicule"], v.get_id())
        for c in self.__clients:
            plus_grand["client"] = max(plus_grand["client"], c["id"])
        for r in self.__reservations:
            plus_grand["reservation"] = max(plus_grand["reservation"], r["id"])
        for m in self.__maintenances:
            plus_grand["maintenance"] = max(plus_grand["maintenance"], m["id"])
        for nom in plus_grand:
            self.__prochain_id[nom] = max(donnees["prochain_id"][nom], plus_grand[nom] + 1)


def charger(fichier):
    """Renvoie (agence, erreur). Fichier absent = agence vide. Fichier invalide = erreur (jamais écrasé)."""
    agence = Agence()
    if not os.path.exists(fichier):
        return agence, ""
    try:
        with open(fichier, "r", encoding="utf-8") as f:
            donnees = json.load(f)
        agence.remplir(donnees)
    except (ValueError, KeyError, TypeError, OSError) as e:
        return None, str(e)
    return agence, ""


def saisir_entier(message):
    while True:
        try:
            return int(input(message + " : "))
        except ValueError:
            print("  -> Entrez un nombre entier.")


def saisir_nombre(message):
    while True:
        try:
            return float(input(message + " : ").replace(",", "."))
        except ValueError:
            print("  -> Entrez un nombre (ex : 45.5).")


def saisir_date(message, defaut=""):
    while True:
        texte = input(message + " (JJ/MM/AAAA) : ")
        if texte.strip() == "" and defaut != "":
            return defaut
        resultat = lire_date_texte(texte)
        if resultat != "":
            return resultat
        print("  -> Date invalide.")


def resultat(agence, ok, message):
    """Affiche le résultat ; si l'opération a réussi, on sauvegarde dans le JSON."""
    if ok:
        print("[OK] " + message)
        agence.sauvegarder(FICHIER)
    else:
        print("[REFUSÉ] " + message)


def afficher_vehicules(liste):
    if len(liste) == 0:
        print("Aucun véhicule.")
    for v in liste:
        print(
            str(v.get_id())
            + " | "
            + v.get_type()
            + " | "
            + v.get_nom()
            + " | "
            + str(v.get_tarif())
            + " €/jour | "
            + v.details()
        )


def main():
    agence, erreur = charger(FICHIER)
    if agence is None:
        print("ERREUR : donnees.json est invalide (" + erreur + ").")
        print("Le fichier n'a PAS été modifié. Corrigez-le ou renommez-le, puis relancez.")
        return

    aujourdhui = date.today().isoformat()
    while True:
        print("\n===== LOCATION DE VÉHICULES (date : " + afficher_date(aujourdhui) + ") =====")
        print(" 1. Ajouter un véhicule        8. Enregistrer un départ")
        print(" 2. Chercher / trier véhicules 9. Enregistrer un retour")
        print(" 3. Ajouter un client         10. Planifier une maintenance")
        print(" 4. Lister les clients        11. Indicateurs")
        print(" 5. Réserver                  12. Historique")
        print(" 6. Annuler une réservation   13. Changer la date du jour")
        print(" 7. Lister réservations / maintenances        0. Quitter")
        choix = input("Votre choix : ").strip()

        if choix == "0":
            print("Au revoir !")
            break

        elif choix == "1":
            type_v = input("Type (1 = voiture, 2 = moto) : ")
            marque = input("Marque : ")
            modele = input("Modèle : ")
            tarif = saisir_nombre("Tarif par jour (€)")
            if type_v == "1":
                ok, message = agence.ajouter_vehicule(
                    "voiture", marque, modele, tarif, saisir_entier("Nombre de portes")
                )
            else:
                ok, message = agence.ajouter_vehicule(
                    "moto", marque, modele, tarif, saisir_entier("Cylindrée (cm3)")
                )
            resultat(agence, ok, message)

        elif choix == "2":
            type_v = input("Type (v = voiture, m = moto, Entrée = tous) : ").strip().lower()
            type_v = {"v": "voiture", "m": "moto"}.get(type_v, "")
            prix_max = saisir_nombre("Prix max par jour (0 = pas de limite)")
            marque = input("Marque (Entrée = toutes) : ")
            debut = ""
            fin = ""
            if input("Seulement les véhicules disponibles sur une période ? (o/n) : ").lower() == "o":
                debut = saisir_date("Date de début")
                fin = saisir_date("Date de fin")
                if fin < debut:
                    print("[REFUSÉ] La date de fin est avant la date de début.")
                    continue
            tri = {"1": "prix", "2": "marque"}.get(input("Trier par (1 = prix, 2 = marque, Entrée = numéro) : "), "id")
            liste = agence.rechercher(type_v, prix_max, marque, debut, fin, tri)
            afficher_vehicules(liste)
            if debut != "":
                n = nombre_de_jours(debut, fin)
                for v in liste:
                    print("  " + v.get_nom() + " : " + str(v.prix(n)) + " € pour " + str(n) + " jour(s)")

        elif choix == "3":
            ok, message = agence.ajouter_client(input("Nom : "), input("Téléphone : "))
            resultat(agence, ok, message)

        elif choix == "4":
            for c in agence.get_clients():
                print(str(c["id"]) + " | " + c["nom"] + " | " + c["telephone"])

        elif choix == "5":
            id_client = saisir_entier("N° du client")
            id_vehicule = saisir_entier("N° du véhicule")
            debut = saisir_date("Date de début", aujourdhui)
            fin = saisir_date("Date de fin")
            resultat(agence, *agence.reserver(id_client, id_vehicule, debut, fin, aujourdhui))

        elif choix == "6":
            resultat(agence, *agence.annuler(saisir_entier("N° de la réservation"), aujourdhui))

        elif choix == "7":
            for r in agence.get_reservations():
                print(
                    "Réservation n°"
                    + str(r["id"])
                    + " | client "
                    + str(r["client"])
                    + " | véhicule "
                    + str(r["vehicule"])
                    + " | "
                    + afficher_date(r["debut"])
                    + " -> "
                    + afficher_date(r["fin"])
                    + " | "
                    + r["statut"]
                    + " | "
                    + str(r["prix"])
                    + " €"
                )
            for m in agence.get_maintenances():
                print(
                    "Maintenance n°"
                    + str(m["id"])
                    + " | véhicule "
                    + str(m["vehicule"])
                    + " | "
                    + afficher_date(m["debut"])
                    + " -> "
                    + afficher_date(m["fin"])
                    + " | "
                    + m["motif"]
                )

        elif choix == "8":
            resultat(
                agence, *agence.depart(saisir_entier("N° de la réservation"), saisir_date("Date de départ", aujourdhui))
            )

        elif choix == "9":
            resultat(
                agence, *agence.retour(saisir_entier("N° de la réservation"), saisir_date("Date de retour", aujourdhui))
            )

        elif choix == "10":
            id_vehicule = saisir_entier("N° du véhicule")
            debut = saisir_date("Date de début", aujourdhui)
            fin = saisir_date("Date de fin")
            motif = input("Motif : ")
            resultat(agence, *agence.planifier_maintenance(id_vehicule, debut, fin, motif, aujourdhui))

        elif choix == "11":
            ind = agence.indicateurs()
            print("REVENUS TOTAUX : " + str(ind["revenus"]) + " €")
            for type_v in ind["par_type"]:
                print("  " + type_v + " : " + str(ind["par_type"][type_v]) + " €")
            print("Locations rendues en retard : " + str(len(ind["retards"])))
            for r in ind["retards"]:
                print("  réservation n°" + str(r["id"]) + " : " + str(r["retard"]) + " jour(s) de retard")
            print("Véhicules les plus loués :")
            for nom, nombre in ind["plus_loues"]:
                print("  " + nom + " : " + str(nombre) + " location(s)")

        elif choix == "12":
            for ligne in agence.get_historique():
                print(ligne)

        elif choix == "13":
            aujourdhui = saisir_date("Nouvelle date du jour (simulation)")

        else:
            print("Choix invalide.")


if __name__ == "__main__":
    main()