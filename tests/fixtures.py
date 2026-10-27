"""Données factices pour les tests : un faux Arc et un faux Chrome dans un dossier temporaire.

Rien ici ne lit ni n'écrit dans les vrais navigateurs : le script est lancé avec
ARC_DIR, CHROME_DIR et KIT_DIR pointant vers ces dossiers.
"""

import json
import os
import sqlite3
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "migrer_arc_chrome.py")
EXTENSION_ID = "abcdefghijklmnopabcdefghijklmnop"


def tab(item_id, title, url):
    return {
        "id": item_id,
        "title": title,
        "childrenIds": [],
        "createdAt": 700000000,
        "data": {"tab": {"savedURL": url}},
    }


def container(item_id, children):
    return {"id": item_id, "childrenIds": children, "data": {"itemContainer": {}}}


def space(space_id, title, profile):
    pinned, unpinned = "pin-" + space_id, "unp-" + space_id
    return {
        "id": space_id,
        "title": title,
        "profile": profile,
        "newContainerIDs": [{"pinned": {}}, pinned, {"unpinned": {}}, unpinned],
    }


DEFAULT = {"default": True}
PROFILE_1 = {"custom": {"_0": {"directoryBasename": "Profile 1", "machineID": "M1"}}}


def sidebar():
    """Trois espaces : « Clients » (profil Arc par défaut), « Perso » (Profile 1) et « Ancien » (à ignorer)."""
    items = [
        # Favoris (icônes du haut) de chaque profil Arc
        container("top-default", ["fav-mail"]),
        tab("fav-mail", "Messagerie", "https://mail.example.com/"),
        container("top-p1", ["fav-banque"]),
        tab("fav-banque", "Banque", "https://banque.example.com/"),
        # Espace Clients : un onglet épinglé, un dossier épinglé, un onglet ouvert
        container("pin-s1", ["doc", "outils"]),
        tab("doc", "Documentation", "https://doc.example.com/"),
        {"id": "outils", "title": "Outils", "childrenIds": ["crm"], "data": {"list": {}}},
        tab("crm", "CRM", "https://crm.example.com/"),
        container("unp-s1", ["ouvert"]),
        tab("ouvert", "Article ouvert", "https://article.example.com/"),
        # Espace Perso
        container("pin-s2", ["recette"]),
        tab("recette", "Recettes", "https://recettes.example.com/"),
        container("unp-s2", []),
        # Espace Ancien
        container("pin-s3", ["vieux"]),
        tab("vieux", "Vieux site", "https://vieux.example.com/"),
        container("unp-s3", []),
    ]
    spaces = [space("s1", "Clients", DEFAULT), space("s2", "Perso", PROFILE_1), space("s3", "Ancien", DEFAULT)]
    top = [DEFAULT, "top-default", PROFILE_1, "top-p1"]
    return {"sidebar": {"containers": [{"global": {}}, {"spaces": spaces, "items": items, "topAppsContainerIDs": top}]}}


def history_db(path, urls):
    """Base History minimale (schéma Chrome simplifié) avec une visite par adresse."""
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, value LONGVARCHAR);
        CREATE TABLE urls(id INTEGER PRIMARY KEY AUTOINCREMENT, url LONGVARCHAR, title LONGVARCHAR,
            visit_count INTEGER DEFAULT 0 NOT NULL, typed_count INTEGER DEFAULT 0 NOT NULL,
            last_visit_time INTEGER NOT NULL, hidden INTEGER DEFAULT 0 NOT NULL);
        CREATE TABLE visits(id INTEGER PRIMARY KEY AUTOINCREMENT, url INTEGER NOT NULL, visit_time INTEGER NOT NULL,
            from_visit INTEGER, transition INTEGER DEFAULT 0 NOT NULL, segment_id INTEGER,
            visit_duration INTEGER DEFAULT 0 NOT NULL);
        INSERT INTO meta VALUES ('version', '60');
        """
    )
    for i, url in enumerate(urls, 1):
        t = 13300000000000000 + i
        con.execute("INSERT INTO urls (url, title, visit_count, last_visit_time) VALUES (?, ?, 1, ?)", (url, url, t))
        con.execute("INSERT INTO visits (url, visit_time, transition) VALUES (?, ?, 0)", (i, t))
    con.commit()
    con.close()


def bookmarks(bar_children, other_children=(), synced_children=()):
    def root(node_id, name, children):
        return {"children": list(children), "id": str(node_id), "name": name, "type": "folder", "date_added": "0"}

    return {
        "roots": {
            "bookmark_bar": root(1, "Barre de favoris", bar_children),
            "other": root(2, "Autres favoris", other_children),
            "synced": root(3, "Favoris sur mobile", synced_children),
        },
        "version": 1,
    }


OLD_FOLDER = {
    "type": "folder",
    "name": "Ancien dossier Chrome",
    "id": "10",
    "date_added": "0",
    "children": [{"type": "url", "name": "Ancien lien", "url": "https://ancien.example.com/", "id": "11"}],
}
ACCOUNT_FOLDER = {
    "type": "folder",
    "name": "Dossier du compte",
    "id": "20",
    "children": [{"type": "url", "name": "Lien du compte", "url": "https://compte.example.com/", "id": "21"}],
}


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def build(root):
    """Crée root/arc, root/chrome et root/kit. Profils Chrome : « Clients » (Profile 5) et « Perso » (Profile 6)."""
    arc, chrome, kit = (os.path.join(root, d) for d in ("arc", "chrome", "kit"))
    for d in (arc, chrome, kit):
        os.makedirs(d)
    write_json(os.path.join(arc, "StorableSidebar.json"), sidebar())
    ud = os.path.join(arc, "User Data")
    os.makedirs(os.path.join(ud, "Default"))
    os.makedirs(os.path.join(ud, "Profile 1"))
    history_db(os.path.join(ud, "Default", "History"), ["https://doc.example.com/", "https://crm.example.com/"])
    ext = os.path.join(ud, "Default", "Extensions", EXTENSION_ID, "1.0")
    os.makedirs(ext)
    write_json(
        os.path.join(ext, "manifest.json"),
        {"name": "Extension de test", "update_url": "https://clients2.google.com/service/update2/crx"},
    )

    write_json(
        os.path.join(chrome, "Local State"),
        {"profile": {"info_cache": {"Profile 5": {"name": "Clients"}, "Profile 6": {"name": "Perso"}}}},
    )
    for d in ("Profile 5", "Profile 6"):
        p = os.path.join(chrome, d)
        os.makedirs(p)
        write_json(os.path.join(p, "Bookmarks"), bookmarks([OLD_FOLDER]))
        with open(os.path.join(p, "EncryptedBookmarks2"), "wb") as f:
            f.write(b"copie chiffree factice")
        history_db(os.path.join(p, "History"), ["https://deja-vu.example.com/"])
    # Le profil « Perso » est connecté à un compte Google qui a ses propres favoris
    write_json(os.path.join(chrome, "Profile 6", "Preferences"), {"account_info": [{"gaia": "factice"}]})
    write_json(os.path.join(chrome, "Profile 6", "AccountBookmarks"), bookmarks([ACCOUNT_FOLDER]))

    with open(os.path.join(kit, "correspondance.txt"), "w", encoding="utf-8") as f:
        f.write("# test\nAncien = ignorer   # commentaire en fin de ligne\n")
    return {"arc": arc, "chrome": chrome, "kit": kit}


def run(root, *args, yes=True):
    """Lance le script sur les données factices, sans ouvrir Chrome.

    Avec yes=True, répond oui à tout ; sinon, le script tourne sans terminal ni réponse possible,
    comme lorsqu'un assistant le lance sans --oui."""
    env = dict(os.environ)
    env.pop("AUTO_YES", None)
    env.update(
        ARC_DIR=os.path.join(root, "arc"),
        CHROME_DIR=os.path.join(root, "chrome"),
        KIT_DIR=os.path.join(root, "kit"),
        NO_OPEN="1",
    )
    if yes:
        env["AUTO_YES"] = "1"
    return subprocess.run(
        [sys.executable, "-B", SCRIPT, *args],
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )


def read_bookmarks(root, profile):
    with open(os.path.join(root, "chrome", profile, "Bookmarks"), encoding="utf-8") as f:
        return json.load(f)


def bar(root, profile):
    """Liste (type, nom) des éléments du premier niveau de la barre de favoris."""
    return [(n["type"], n["name"]) for n in read_bookmarks(root, profile)["roots"]["bookmark_bar"]["children"]]
