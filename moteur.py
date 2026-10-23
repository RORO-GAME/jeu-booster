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
# Poids de chaque rareté (plus c'est grand, plus c'est fréquent).
# Sur 100 cartes tirées : environ 52 communes, 28 rares, 13 super rares,
# 5 ultra rares, 1 légendaire, et une secrète toutes les 1000 cartes.
RARETES = {
    "commune": 52,
    "rare": 28,
    "super rare": 13,
    "ultra rare": 5.5,
    "légendaire": 1.4,
    "secrète": 0.1,
}
ORDRE = list(RARETES)  # de la plus commune à la plus rare

# Le petit code affiché dans le coin de chaque carte
CODES = {
    "commune": "C",
    "rare": "R",
    "super rare": "SR",
    "ultra rare": "UR",
    "légendaire": "L",
    "secrète": "S",
}

TAILLE_BOOSTER = 5            # nombre de cartes par booster
GARANTIE_DERNIERE = "rare"    # la dernière carte du booster est au moins de cette rareté
PITIE_APRES = 8               # après N boosters sans carte "PITIE_RARETE" ou mieux...
PITIE_RARETE = "super rare"   # ...le booster suivant en contient une

# Finitions : chance qu'une carte tirée soit brillante ou arc-en-ciel,
# quelle que soit sa rareté (0.06 = 6 %).
CHANCE_BRILLANTE = 0.06
CHANCE_ARC_EN_CIEL = 0.015


# ----------------------------------------------------------------------
# Logique de tirage
# ----------------------------------------------------------------------
def etat_initial():
    # collection : {id de la carte (texte): nombre d'exemplaires}
    # finitions  : {id de la carte (texte): {"brillante": n, "arc-en-ciel": n}}
    return {"collection": {}, "finitions": {}, "boosters_ouverts": 0, "sans_rare": 0}


def tirer_carte(cartes, rarete_min=None):
    """Tire une carte au hasard, avec les probabilités de RARETES."""
    debut = ORDRE.index(rarete_min) if rarete_min else 0
    # on ne garde que les raretés qui ont au moins une carte
    possibles = [r for r in ORDRE[debut:] if any(c["rarete"] == r for c in cartes)]
    if not possibles:  # aucune carte assez rare : on se rabat sur toutes celles qui existent
        possibles = [r for r in ORDRE if any(c["rarete"] == r for c in cartes)]
    rarete = random.choices(possibles, weights=[RARETES[r] for r in possibles])[0]
    return random.choice([c for c in cartes if c["rarete"] == rarete])


def tirer_finition():
    x = random.random()
    if x < CHANCE_ARC_EN_CIEL:
        return "arc-en-ciel"
    if x < CHANCE_ARC_EN_CIEL + CHANCE_BRILLANTE:
        return "brillante"
    return "normale"


def ouvrir_booster(cartes, etat):
    """Ouvre un booster et met l'état à jour.

    Renvoie (liste de cartes, pitie_declenchee). Chaque carte est une copie
    avec des clés en plus :
    - "finition" : "normale", "brillante" ou "arc-en-ciel"
    - "nouvelle" : True si le joueur ne possédait pas encore cette carte
    - "nouvelle_finition" : True si la carte est déjà possédée mais pas dans cette finition
    """
    etat.setdefault("finitions", {})

    tirage = [tirer_carte(cartes) for _ in range(TAILLE_BOOSTER - 1)]
    tirage.append(tirer_carte(cartes, GARANTIE_DERNIERE))  # dernière carte : rareté minimale

    # système de pitié : on force une carte assez rare, seulement si le booster n'en a pas déjà une
    seuil = ORDRE.index(PITIE_RARETE)

    def a_une_belle_carte(liste):
        return any(ORDRE.index(c["rarete"]) >= seuil for c in liste)

    pitie = False
    if etat["sans_rare"] >= PITIE_APRES and not a_une_belle_carte(tirage):
        tirage[-1] = tirer_carte(cartes, PITIE_RARETE)
        pitie = True

    # on trie de la plus commune à la plus rare, pour le suspense
    tirage.sort(key=lambda c: ORDRE.index(c["rarete"]))

    # finitions, et quelles cartes sont nouvelles (un doublon dans le même booster ne l'est pas)
    deja = set(etat["collection"])
    finitions_vues = {cle: set(v) for cle, v in etat["finitions"].items()}
    resultat = []
    for c in tirage:
        cle = str(c["id"])
        fin = tirer_finition()
        nouvelle = cle not in deja
        nouvelle_fin = (not nouvelle) and fin != "normale" and fin not in finitions_vues.get(cle, set())
        resultat.append({**c, "finition": fin, "nouvelle": nouvelle, "nouvelle_finition": nouvelle_fin})
        deja.add(cle)
        if fin != "normale":
            finitions_vues.setdefault(cle, set()).add(fin)

    # mise à jour de l'état
    if a_une_belle_carte(tirage):
        etat["sans_rare"] = 0
    else:
        etat["sans_rare"] += 1
    etat["boosters_ouverts"] += 1
    for c in resultat:
        cle = str(c["id"])
        etat["collection"][cle] = etat["collection"].get(cle, 0) + 1
        if c["finition"] != "normale":
            f = etat["finitions"].setdefault(cle, {})
            f[c["finition"]] = f.get(c["finition"], 0) + 1
    return resultat, pitie


# ----------------------------------------------------------------------
# Passerelle pour la page web (JavaScript <-> Python, en texte JSON)
# ----------------------------------------------------------------------
def reglages_web():
    return json.dumps({
        "ordre": ORDRE,
        "codes": [CODES[r] for r in ORDRE],
        "taille_booster": TAILLE_BOOSTER,
        "pitie_apres": PITIE_APRES,
        "pitie_rarete": PITIE_RARETE,
        "etat_initial": etat_initial(),
    }, ensure_ascii=False)


def ouvrir_booster_web(cartes_json, etat_json):
    cartes = json.loads(cartes_json)
    etat = json.loads(etat_json)
    tirage, pitie = ouvrir_booster(cartes, etat)
    return json.dumps({"cartes": tirage, "pitie": pitie, "etat": etat}, ensure_ascii=False)
