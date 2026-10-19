"""Moteur du jeu de cartes : la logique, sans aucun affichage.

Ce fichier est utilisé deux fois, sans changement :
- par jeu.py, la version console ;
- par index.html, la version web (Python tourne dans le navigateur via Pyodide).
"""
import json
import random

# ----------------------------------------------------------------------
# RÉGLAGES : c'est ici que tu joues avec l'équilibrage
# ----------------------------------------------------------------------
# Poids de chaque rareté (plus c'est grand, plus c'est fréquent)
RARETES = {
    "commune": 60,
    "peu commune": 25,
    "rare": 10,
    "ultra rare": 4,
    "légendaire": 1,
}
ORDRE = list(RARETES)              # de la plus commune à la plus rare
TAILLE_BOOSTER = 5                 # nombre de cartes par booster
GARANTIE_DERNIERE = "peu commune"  # la dernière carte est au moins de cette rareté
PITIE_APRES = 10                   # après N boosters sans "rare" ou mieux, le suivant en contient un


# ----------------------------------------------------------------------
# Logique de tirage
# ----------------------------------------------------------------------
def etat_initial():
    # collection : {id de la carte (texte): nombre d'exemplaires}
    return {"collection": {}, "boosters_ouverts": 0, "sans_rare": 0}


def tirer_carte(cartes, rarete_min=None):
    """Tire une carte au hasard, avec les probabilités de RARETES."""
    debut = ORDRE.index(rarete_min) if rarete_min else 0
    # on ne garde que les raretés qui ont au moins une carte
    possibles = [r for r in ORDRE[debut:] if any(c["rarete"] == r for c in cartes)]
    rarete = random.choices(possibles, weights=[RARETES[r] for r in possibles])[0]
    return random.choice([c for c in cartes if c["rarete"] == rarete])


def ouvrir_booster(cartes, etat):
    """Ouvre un booster et met l'état à jour.

    Renvoie (liste de cartes, pitie_declenchee). Chaque carte est une copie
    avec une clé en plus, "nouvelle" : True si le joueur ne l'avait pas encore.
    """
    tirage = [tirer_carte(cartes) for _ in range(TAILLE_BOOSTER - 1)]

    # dernière carte : rareté minimale garantie
    derniere = tirer_carte(cartes, GARANTIE_DERNIERE)

    # système de pitié : une carte rare ou mieux est forcée
    pitie = etat["sans_rare"] >= PITIE_APRES
    if pitie:
        derniere = tirer_carte(cartes, "rare")
    tirage.append(derniere)

    # on trie de la plus commune à la plus rare, pour le suspense
    tirage.sort(key=lambda c: ORDRE.index(c["rarete"]))

    # quelles cartes sont nouvelles ? (un doublon dans le même booster ne l'est pas)
    deja = set(etat["collection"])
    resultat = []
    for c in tirage:
        cle = str(c["id"])
        resultat.append({**c, "nouvelle": cle not in deja})
        deja.add(cle)

    # mise à jour de l'état
    if any(ORDRE.index(c["rarete"]) >= ORDRE.index("rare") for c in tirage):
        etat["sans_rare"] = 0
    else:
        etat["sans_rare"] += 1
    etat["boosters_ouverts"] += 1
    for c in tirage:
        cle = str(c["id"])
        etat["collection"][cle] = etat["collection"].get(cle, 0) + 1
    return resultat, pitie


# ----------------------------------------------------------------------
# Passerelle pour la page web (JavaScript <-> Python, en texte JSON)
# ----------------------------------------------------------------------
def reglages_web():
    return json.dumps({
        "ordre": ORDRE,
        "taille_booster": TAILLE_BOOSTER,
        "pitie_apres": PITIE_APRES,
        "etat_initial": etat_initial(),
    }, ensure_ascii=False)


def ouvrir_booster_web(cartes_json, etat_json):
    cartes = json.loads(cartes_json)
    etat = json.loads(etat_json)
    tirage, pitie = ouvrir_booster(cartes, etat)
    return json.dumps({"cartes": tirage, "pitie": pitie, "etat": etat}, ensure_ascii=False)
