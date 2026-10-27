"""Migration Arc -> Google Chrome (macOS).

Reprend, pour chaque espace Arc : favoris, onglets épinglés (avec leurs dossiers),
onglets ouverts, historique de navigation et liste des extensions.
Arc n'est jamais modifié ; les fichiers Chrome sont sauvegardés avant écriture.

Lancé par migrer-arc-vers-chrome.sh (qui vérifie qu'Arc et Chrome sont fermés).
Bibliothèque standard uniquement, compatible Python 3.9+.

Variables d'environnement (tests) : ARC_DIR, CHROME_DIR, KIT_DIR, AUTO_YES, NO_OPEN, MODE, PROFIL.
"""

import datetime
import html
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import uuid

__version__ = "1.0.0"

USAGE = """Usage : bash migrer-arc-vers-chrome.sh [options]

Options :
  --mode espaces       un profil Chrome par espace Arc (profils nommés comme les espaces)
  --mode unique        tous les espaces dans un seul profil Chrome
  --profil "Nom"       profil Chrome cible en mode unique
  --remplacer          vider l'historique et les favoris des profils Chrome ciblés
                       avant d'y mettre le contenu d'Arc (sauvegarde faite avant)
  --forcer             refaire une migration déjà faite
  --oui                répondre oui à toutes les questions
  --version            afficher la version
  --aide               afficher cette aide

Mode d'emploi complet : LISEZMOI.txt"""

HOME = os.path.expanduser("~")
ARC = os.environ.get("ARC_DIR", os.path.join(HOME, "Library/Application Support/Arc"))
ARC_UD = os.path.join(ARC, "User Data")
CHROME = os.environ.get("CHROME_DIR", os.path.join(HOME, "Library/Application Support/Google/Chrome"))
KIT = os.environ.get("KIT_DIR") or os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(KIT, "resultat-migration")
STATE_FILE = os.path.join(OUT, ".etat-migration.json")
BACKUP = os.path.join(OUT, "sauvegardes-chrome", datetime.datetime.now().strftime("%Y-%m-%d_%Hh%Mm%S"))
ARGS = sys.argv[1:]


def arg(name):
    if name in ARGS:
        i = ARGS.index(name)
        return ARGS[i + 1] if i + 1 < len(ARGS) else ""
    return None


FORCE = "--forcer" in ARGS
REPLACE = "--remplacer" in ARGS
YES = "--oui" in ARGS or os.environ.get("AUTO_YES") == "1"
NO_OPEN = os.environ.get("NO_OPEN") == "1"
MODE = arg("--mode") or os.environ.get("MODE")  # espaces | unique
TARGET = arg("--profil") or os.environ.get("PROFIL")  # profil Chrome cible (mode unique)
FAV_FOLDER = "Arc – favoris"
PINNED_FOLDER = "Arc – onglets épinglés"
OPEN_FOLDER = "Arc – onglets ouverts"

LOG = []


def out(m=""):
    print(m)
    LOG.append(m)


def ok(m):
    out("  ✓ " + m)


def warn(m):
    out("  ⚠ " + m)


def head(m):
    print("\n\033[1m" + m + "\033[0m")
    LOG.append("\n" + m)


def save_log():
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "resume.txt"), "w", encoding="utf-8") as f:
        f.write("Migration du %s\n%s\n" % (datetime.datetime.now().strftime("%d/%m/%Y %H:%M"), "\n".join(LOG)))


def ask(prompt, default=""):
    if YES:
        return default
    try:
        return input(prompt).strip()
    except EOFError:
        return default


def confirm(prompt):
    return ask(prompt + " (o/n) ", "o").lower() in ("o", "oui", "y", "yes")


def now_str():
    return datetime.datetime.now().strftime("%d/%m/%Y %H:%M")


def read_json(path, encoding="utf-8"):
    with open(path, encoding=encoding) as f:
        return json.load(f)


def write_json(path, data, indent=None):
    """Écriture atomique : fichier temporaire puis remplacement."""
    tmp = path + ".arc-tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
    os.replace(tmp, path)


def load_state():
    try:
        return read_json(STATE_FILE)
    except Exception:
        return {}


def save_state(s):
    write_json(STATE_FILE, s, indent=1)


def fda_help(path):
    out("\n  ✗ macOS empêche Terminal de lire : " + path)
    out("  → Réglages Système › Confidentialité et sécurité › Accès complet au disque : active « Terminal »")
    out("    (bouton + s'il n'est pas dans la liste : Applications › Utilitaires › Terminal).")
    out("  → Quitte Terminal (Cmd+Q), rouvre-le, puis relance la commande.")


def now_chrome():
    return str(int((time.time() + 11644473600) * 1000000))


def arc_time(t):  # Arc : secondes depuis 2001 -> Chrome : microsecondes depuis 1601
    try:
        return str(int((float(t) + 978307200 + 11644473600) * 1000000))
    except Exception:
        return now_chrome()


def norm(s):
    return re.sub(r"\s+", " ", s or "").strip().casefold()


def count(nodes):
    return sum(1 if n["type"] == "url" else count(n["children"]) for n in nodes)


def folder(name, children):
    return [{"type": "folder", "name": name, "children": children}] if children else []


# ------------------------------------------------------------------ Arc
def prof_of(desc):
    if not isinstance(desc, dict):
        return None, None
    if "default" in desc:
        return "Default", None
    c = (desc.get("custom") or {}).get("_0") or {}
    return c.get("directoryBasename"), c.get("machineID")


def load_sidebar():
    d = read_json(os.path.join(ARC, "StorableSidebar.json"))
    spaces, items, top, names, untitled = [], {}, [], set(), 0
    for c in d["sidebar"]["containers"]:
        if not isinstance(c, dict) or "spaces" not in c:
            continue
        for x in c.get("items", []):
            if isinstance(x, dict) and "id" in x:
                items[x["id"]] = x
        top += c.get("topAppsContainerIDs", []) or []
        for s in c.get("spaces", []):
            if not isinstance(s, dict):
                continue
            s = dict(s)
            if not s.get("title"):
                untitled += 1
                s["title"] = "Espace sans nom %d" % untitled
                s["_untitled"] = True
            base, k = s["title"], 2
            while norm(s["title"]) in names:
                s["title"] = "%s (%d)" % (base, k)
                k += 1
            names.add(norm(s["title"]))
            spaces.append(s)
    return spaces, items, top


def space_containers(s):
    res, nc = {}, s.get("newContainerIDs") or []
    for i, x in enumerate(nc[:-1]):
        if isinstance(x, dict) and "pinned" in x:
            res["pinned"] = nc[i + 1]
        elif isinstance(x, dict) and "unpinned" in x:
            res["unpinned"] = nc[i + 1]
    if not res:
        ci = s.get("containerIDs") or []
        for i, x in enumerate(ci[:-1]):
            if x in ("pinned", "unpinned"):
                res[x] = ci[i + 1]
    return res


def to_nodes(item_id, items, seen=None):
    seen = seen if seen is not None else set()
    res, x = [], items.get(item_id)
    if not x or item_id in seen:
        return res
    seen.add(item_id)
    for cid in x.get("childrenIds", []) or []:
        c = items.get(cid)
        if not c:
            continue
        data = c.get("data") or {}
        if "tab" in data:
            t = data["tab"] or {}
            url = t.get("savedURL")
            if url and re.match(r"^(https?|file|ftp)://", url):
                res.append(
                    {
                        "type": "url",
                        "name": c.get("title") or t.get("savedTitle") or url,
                        "url": url,
                        "created": c.get("createdAt"),
                    }
                )
        elif "list" in data:
            kids = to_nodes(cid, items, seen)
            if kids:
                res.append(
                    {
                        "type": "folder",
                        "name": c.get("title") or "Dossier",
                        "children": kids,
                        "created": c.get("createdAt"),
                    }
                )
        else:  # vue partagée, etc. : on aplatit
            res.extend(to_nodes(cid, items, seen))
    return res


def favorites_for(prof, machine, top, items):
    cands = [(prof_of(top[i])[1], top[i + 1]) for i in range(0, len(top) - 1, 2) if prof_of(top[i])[0] == prof]
    for m, cid in cands:
        if m == machine:
            return to_nodes(cid, items)
    for m, cid in cands:
        if m is None:
            return to_nodes(cid, items)
    return to_nodes(cands[0][1], items) if len(cands) == 1 else []


def arc_extensions(prof):
    res, d = {}, os.path.join(ARC_UD, prof, "Extensions")
    if not os.path.isdir(d):
        return res
    for e in os.listdir(d):
        if not re.fullmatch(r"[a-p]{32}", e):
            continue
        try:
            vers = [v for v in os.listdir(os.path.join(d, e)) if os.path.isfile(os.path.join(d, e, v, "manifest.json"))]
            if not vers:
                continue
            v = max(vers, key=lambda v: os.path.getmtime(os.path.join(d, e, v)))
            m = read_json(os.path.join(d, e, v, "manifest.json"), "utf-8-sig")
        except Exception:
            continue
        if "google" not in (m.get("update_url") or ""):
            continue  # hors Chrome Web Store
        name = m.get("name", e)
        if name.startswith("__MSG_"):
            key = name[6:-2].lower()
            for loc in (m.get("default_locale", "en"), "fr", "en", "en_US"):
                try:
                    p = os.path.join(d, e, v, "_locales", loc, "messages.json")
                    msgs = {k.lower(): val for k, val in read_json(p, "utf-8-sig").items()}
                    if key in msgs:
                        name = msgs[key]["message"]
                        break
                except Exception:
                    pass
        res[e] = name
    return res


def html_export(p):
    L = [
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
        "<TITLE>Bookmarks</TITLE>",
        "<H1>Bookmarks</H1>",
        "<DL><p>",
    ]

    def emit(nodes, ind):
        for n in nodes:
            if n["type"] == "url":
                L.append('%s<DT><A HREF="%s">%s</A>' % (ind, html.escape(n["url"], True), html.escape(n["name"])))
            else:
                L.append("%s<DT><H3>%s</H3>" % (ind, html.escape(n["name"])))
                L.append(ind + "<DL><p>")
                emit(n["children"], ind + "    ")
                L.append(ind + "</DL><p>")

    tree = list(p["favs"]) + folder(PINNED_FOLDER, p["pinned"]) + folder(OPEN_FOLDER, p["unpinned"])
    emit(folder("Arc – " + p["title"], tree), "    ")
    L.append("</DL><p>")
    os.makedirs(os.path.join(OUT, "favoris-html"), exist_ok=True)
    safe = re.sub(r"[^\w\- ]", "_", p["title"]).strip() or "espace"
    with open(os.path.join(OUT, "favoris-html", safe + ".html"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


# ------------------------------------------------------------------ Chrome
def chrome_profiles():
    ls = read_json(os.path.join(CHROME, "Local State"))
    ic = (ls.get("profile") or {}).get("info_cache") or {}
    return {d: (i.get("name") or d) for d, i in ic.items() if os.path.isdir(os.path.join(CHROME, d))}


def load_overrides():
    res, p = {}, os.path.join(KIT, "correspondance.txt")
    if os.path.exists(p):
        with open(p, encoding="utf-8-sig") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    a, b = line.split("=", 1)
                    res[norm(a)] = b.strip()
    return res


def match(title, profs, overrides):
    target = overrides.get(norm(title), title)
    if target in profs:
        return target
    hits = [d for d, n in profs.items() if norm(n) == norm(target)]
    return hits[0] if len(hits) == 1 else None


def backup(cdir, name):
    dst = os.path.join(BACKUP, cdir, name)
    if os.path.exists(dst):
        return dst
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    src = os.path.join(CHROME, cdir, name)
    if name == "History":
        sqlite_copy(src, dst)
    else:
        shutil.copy2(src, dst)
    return dst


BAR, OTHER, SYNCED = (
    "0bc5d13f-2cba-5d74-951f-3f233fe6c908",
    "82b081ec-3dd3-529c-8475-ab6c344590dd",
    "4cf2e351-0e85-532b-bb37-df045d8f8d0f",
)


def root_folder(node_id, guid, name, created):
    return {
        "children": [],
        "date_added": created,
        "date_last_used": "0",
        "date_modified": "0",
        "guid": guid,
        "id": str(node_id),
        "name": name,
        "type": "folder",
    }


def empty_bookmarks():
    t = now_chrome()
    return {
        "roots": {
            "bookmark_bar": root_folder(1, BAR, "Barre de favoris", t),
            "other": root_folder(2, OTHER, "Autres favoris", t),
            "synced": root_folder(3, SYNCED, "Favoris sur mobile", t),
        },
        "version": 1,
    }


def max_id(n):
    m = int(n["id"]) if str(n.get("id", "")).isdigit() else 0
    for c in n.get("children", []) or []:
        m = max(m, max_id(c))
    return m


def build(nodes, counter):
    res = []
    for n in nodes:
        counter[0] += 1
        b = {
            "date_added": arc_time(n.get("created")) if n.get("created") else now_chrome(),
            "date_last_used": "0",
            "guid": str(uuid.uuid4()),
            "id": str(counter[0]),
            "name": n["name"],
        }
        if n["type"] == "url":
            b.update(type="url", url=n["url"])
        else:
            b.update(type="folder", date_modified=now_chrome(), children=build(n["children"], counter))
        res.append(b)
    return res


def write_bookmarks(cdir, nodes):
    path = os.path.join(CHROME, cdir, "Bookmarks")
    if os.path.exists(path):
        data = read_json(path)
        backup(cdir, "Bookmarks")
    else:
        data = empty_bookmarks()
    bar = data["roots"]["bookmark_bar"]
    counter = [max(max_id(r) for r in data["roots"].values() if isinstance(r, dict))]
    bar.setdefault("children", []).extend(build(nodes, counter))
    bar["date_modified"] = now_chrome()
    data.pop("checksum", None)  # Chrome recalcule la somme de contrôle au démarrage
    write_json(path, data, indent=3)


def clear_bookmarks(cdir):
    """Mode --remplacer : vide la barre de favoris, « Autres favoris » et « Favoris sur mobile »."""
    path = os.path.join(CHROME, cdir, "Bookmarks")
    if not os.path.exists(path):
        return 0
    data = read_json(path)
    backup(cdir, "Bookmarks")
    removed = 0
    for root in data["roots"].values():
        if isinstance(root, dict):
            removed += sum(1 for n in root.get("children", []) for _ in walk_urls(n))
            root["children"] = []
            root["date_modified"] = now_chrome()
    data.pop("checksum", None)
    data.pop("sync_metadata", None)  # état de synchronisation devenu faux : Chrome le reconstruit
    write_json(path, data, indent=3)
    return removed


def walk_urls(node):
    if node.get("type") == "url":
        yield node
    for c in node.get("children", []) or []:
        yield from walk_urls(c)


def account_bookmarks(cdir):
    """Nombre de favoris enregistrés dans le compte Google (fichier AccountBookmarks des Chrome récents).
    Ils sont stockés chez Google : seul Chrome peut les supprimer (sinon il les retélécharge)."""
    path = os.path.join(CHROME, cdir, "AccountBookmarks")
    try:
        data = read_json(path)
    except Exception:
        return 0
    roots = [r for r in (data.get("roots") or {}).values() if isinstance(r, dict)]
    return sum(1 for r in roots for n in r.get("children", []) for _ in walk_urls(n))


STATEMENTS = [
    """CREATE TEMP TABLE arc_u AS SELECT url, MAX(title) AS title, SUM(visit_count) AS vc, SUM(typed_count) AS tc,
   MAX(last_visit_time) AS lvt, MIN(hidden) AS hidden FROM arc.urls
   WHERE url LIKE 'http://%' OR url LIKE 'https://%' GROUP BY url""",
    "CREATE INDEX temp.arc_u_url ON arc_u(url)",
    """UPDATE main.urls SET
   visit_count = visit_count + (SELECT vc FROM arc_u WHERE arc_u.url = main.urls.url),
   typed_count = typed_count + (SELECT tc FROM arc_u WHERE arc_u.url = main.urls.url),
   last_visit_time = MAX(last_visit_time, (SELECT lvt FROM arc_u WHERE arc_u.url = main.urls.url))
   WHERE url IN (SELECT url FROM arc_u)""",
    """INSERT INTO main.urls (url, title, visit_count, typed_count, last_visit_time, hidden)
   SELECT url, title, vc, tc, lvt, hidden FROM arc_u
   WHERE url NOT IN (SELECT url FROM main.urls WHERE url IS NOT NULL)""",
    """INSERT INTO main.visits (url, visit_time, from_visit, transition, segment_id, visit_duration)
   SELECT (SELECT MIN(m.id) FROM main.urls m WHERE m.url = au.url), v.visit_time, 0, v.transition, 0, v.visit_duration
   FROM arc.visits v JOIN arc.urls au ON au.id = v.url
   WHERE (au.url LIKE 'http://%' OR au.url LIKE 'https://%')
     AND NOT EXISTS (SELECT 1 FROM main.visits mv WHERE mv.visit_time = v.visit_time
                     AND mv.url = (SELECT MIN(m.id) FROM main.urls m WHERE m.url = au.url))""",
    "DROP TABLE temp.arc_u",
]


def sqlite_copy(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src.replace("%", "%25").replace("?", "%3f").replace("#", "%23"), uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def merge_history(aprof, cdir):
    src, dst = os.path.join(ARC_UD, aprof, "History"), os.path.join(CHROME, cdir, "History")
    if not os.path.exists(src):
        return "pas d'historique côté Arc"
    if not os.path.exists(dst):
        return "profil Chrome jamais ouvert (ouvre-le une fois, quitte Chrome et relance)"
    bak = backup(cdir, "History")
    tmpd = tempfile.mkdtemp()
    arc_copy = os.path.join(tmpd, "arc.sqlite")
    con = None
    try:
        sqlite_copy(src, arc_copy)
        con = sqlite3.connect(dst, isolation_level=None)
        bu, bv = [con.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0] for t in ("urls", "visits")]
        con.execute("ATTACH DATABASE ? AS arc", (arc_copy,))
        con.execute("BEGIN")
        for st in STATEMENTS:
            con.execute(st)
        con.execute("COMMIT")
        con.execute("DETACH DATABASE arc")
        chk = con.execute("PRAGMA quick_check").fetchone()[0]
        if chk != "ok":
            raise RuntimeError("contrôle d'intégrité : " + chk)
        au, av = [con.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0] for t in ("urls", "visits")]
        con.close()
        con = None
        cache = os.path.join(CHROME, cdir, "History Provider Cache")
        if os.path.exists(cache):
            shutil.move(cache, os.path.join(os.path.dirname(bak), "History Provider Cache"))
        return "ok:%d adresses et %d visites ajoutées" % (au - bu, av - bv)
    except Exception as e:
        if con is not None:
            try:
                con.execute("ROLLBACK")
            except Exception:
                pass
            con.close()
        b = sqlite3.connect(bak)
        d = sqlite3.connect(dst)
        b.backup(d)
        d.close()
        b.close()
        return "échec (%s) — historique Chrome remis tel qu'avant" % e
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)


# Fichiers dérivés de l'historique (suggestions, sites fréquents, liens visités) : Chrome les recrée.
HISTORY_CACHES = [
    "History Provider Cache",
    "Visited Links",
    "Top Sites",
    "Top Sites-journal",
    "Shortcuts",
    "Shortcuts-journal",
    "Network Action Predictor",
    "Network Action Predictor-journal",
]


def clear_history(cdir):
    """Mode --remplacer : vide toutes les tables de l'historique Chrome (sauf « meta »), après sauvegarde."""
    dst = os.path.join(CHROME, cdir, "History")
    if not os.path.exists(dst):
        return "ok:aucun historique"
    bak = backup(cdir, "History")
    con = sqlite3.connect(dst, isolation_level=None)
    try:
        rows = con.execute("SELECT name, sql FROM sqlite_master WHERE type = 'table'").fetchall()
        virtual = [n for n, sql in rows if (sql or "").upper().startswith("CREATE VIRTUAL TABLE")]
        tables = [
            n
            for n, _sql in rows
            if not n.startswith("sqlite_") and n != "meta" and not any(n.startswith(v + "_") for v in virtual)
        ]
        visits = con.execute("SELECT COUNT(*) FROM visits").fetchone()[0]
        con.execute("BEGIN")
        for t in tables:
            con.execute('DELETE FROM "%s"' % t.replace('"', '""'))
        con.execute("COMMIT")
        con.execute("VACUUM")
        con.close()
    except Exception as e:
        try:
            con.execute("ROLLBACK")
        except Exception:
            pass
        con.close()
        b, d = sqlite3.connect(bak), sqlite3.connect(dst)
        b.backup(d)
        d.close()
        b.close()
        return "échec (%s) — historique Chrome remis tel qu'avant" % e
    for name in HISTORY_CACHES:
        src = os.path.join(CHROME, cdir, name)
        if os.path.exists(src):
            shutil.move(src, os.path.join(os.path.dirname(bak), name))
    return "ok:%d visites effacées" % visits


def installed(cdir):
    d = os.path.join(CHROME, cdir, "Extensions")
    return set(os.listdir(d)) if os.path.isdir(d) else set()


# ------------------------------------------------------------------ programme
KNOWN_FLAGS = {"--forcer", "--remplacer", "--oui", "--mode", "--profil", "--version", "--aide", "-h", "--help"}


def check_args():
    """Retourne un code de sortie si le programme doit s'arrêter (aide, version, option inconnue)."""
    if any(a in ARGS for a in ("--aide", "-h", "--help")):
        print(USAGE)
        return 0
    if "--version" in ARGS:
        print("migrer-arc-vers-chrome " + __version__)
        return 0
    skip = False
    for a in ARGS:
        if skip:
            skip = False
            continue
        if a in ("--mode", "--profil"):
            skip = True
            continue
        if a not in KNOWN_FLAGS:
            print("Option inconnue : %s\n\n%s" % (a, USAGE))
            return 2
    if MODE is not None and MODE not in ("espaces", "unique"):
        print("--mode doit valoir « espaces » ou « unique ».")
        return 2
    return None


def main():
    os.makedirs(OUT, exist_ok=True)
    head("Migration Arc → Google Chrome (v%s)" % __version__)
    try:
        spaces, items, top = load_sidebar()
    except PermissionError:
        fda_help(ARC)
        save_log()
        return
    except FileNotFoundError:
        out("  ✗ Arc introuvable sur ce Mac (%s)." % ARC)
        save_log()
        return
    except Exception as e:
        out("  ✗ Impossible de lire les espaces Arc (%s)." % e)
        save_log()
        return
    overrides = load_overrides()
    machines = [prof_of(s.get("profile"))[1] for s in spaces if prof_of(s.get("profile"))[1]]
    machine = max(set(machines), key=machines.count) if machines else None

    head("Espaces Arc")
    plan = []
    for s in spaces:
        t = s["title"]
        if overrides.get(norm(t), "").casefold() in ("-", "ignorer"):
            out("  • %-24s ignoré (correspondance.txt)" % t)
            continue
        aprof = prof_of(s.get("profile"))[0] or "Default"
        c = space_containers(s)
        p = dict(
            title=t,
            aprof=aprof,
            pinned=to_nodes(c["pinned"], items) if c.get("pinned") else [],
            unpinned=to_nodes(c["unpinned"], items) if c.get("unpinned") else [],
            favs=favorites_for(aprof, machine, top, items),
        )
        if s.get("_untitled") and not p["pinned"]:
            continue
        html_export(p)
        out(
            "  • %-24s %3d favoris · %3d épinglés · %3d ouverts"
            % (t, count(p["favs"]), count(p["pinned"]), count(p["unpinned"]))
        )
        plan.append(p)
    if not plan:
        out("  Aucun espace à migrer.")
        save_log()
        return
    ok("Copie de secours des favoris (fichiers HTML) : resultat-migration/favoris-html")

    try:
        profs = chrome_profiles()
    except PermissionError:
        fda_help(CHROME)
        out("  Plan B sans accès : importe les fichiers HTML à la main (voir LISEZMOI.txt).")
        save_log()
        return
    except FileNotFoundError:
        out("  ✗ Chrome introuvable : installe Google Chrome, ouvre-le une fois, quitte-le, puis relance.")
        save_log()
        return
    if not profs:
        out("  ✗ Aucun profil Chrome trouvé : ouvre Chrome une fois, quitte-le, puis relance.")
        save_log()
        return
    head("Profils Chrome")
    plist = sorted(profs.items(), key=lambda x: x[1].casefold())
    for i, (_d, n) in enumerate(plist, 1):
        out("  %d) %s" % (i, n))
    for p in plan:
        p["match"] = match(p["title"], profs, overrides)
    nm = sum(1 for p in plan if p["match"])

    mode = MODE if MODE in ("espaces", "unique") else None
    if not mode:
        head("Organisation dans Chrome")
        out(
            "  1) Un profil Chrome par espace Arc (%d espace(s) sur %d ont déjà un profil Chrome du même nom)"
            % (nm, len(plan))
        )
        out("  2) Tout dans un seul profil Chrome")
        mode = {"1": "espaces", "2": "unique"}.get(ask("Ton choix (1, 2 ou q pour quitter) : ", "1" if nm else "2"))
        if not mode:
            out("Rien n'a été modifié.")
            save_log()
            return

    if mode == "espaces":
        head("Correspondance espaces Arc → profils Chrome")
        used = set()
        for p in plan:
            cd = p["match"] if p["match"] not in used else None
            if cd:
                used.add(cd)
            p["cdir"] = cd
            out("  %-24s → %s" % (p["title"], profs[cd] if cd else "✗ aucun profil Chrome de ce nom : ignoré"))
        miss = [p["title"] for p in plan if not p["cdir"]]
        if miss:
            out("\n  Pour migrer aussi %s : crée un profil Chrome portant exactement ce nom" % ", ".join(miss))
            out("  (ou indique la correspondance dans correspondance.txt), puis relance le script.")
    else:
        cd = None
        if TARGET:
            cd = TARGET if TARGET in profs else next((d for d, n in profs.items() if norm(n) == norm(TARGET)), None)
        if not cd and len(plist) == 1:
            cd = plist[0][0]
        while not cd:
            r = ask("Numéro du profil Chrome qui reçoit tout : ", "q")
            if r.lower() == "q":
                out("Rien n'a été modifié.")
                save_log()
                return
            if r.isdigit() and 1 <= int(r) <= len(plist):
                cd = plist[int(r) - 1][0]
        for p in plan:
            p["cdir"] = cd
        out("\n  Tous les espaces vont dans le profil Chrome « %s »." % profs[cd])

    todo = [p for p in plan if p["cdir"]]
    if not todo:
        save_log()
        return
    by_profile = {}
    for p in todo:
        by_profile.setdefault(p["cdir"], []).append(p)
    if REPLACE:
        out("\n  ⚠ Mode --remplacer : l'historique et les favoris actuels de ces profils Chrome seront effacés")
        out("    avant d'y mettre le contenu d'Arc : %s." % ", ".join(profs[cd] for cd in by_profile))
        out("    Une sauvegarde est faite avant (resultat-migration/sauvegardes-chrome).")
    if not confirm("\nOn lance la migration ?"):
        out("Rien n'a été modifié.")
        save_log()
        return

    state = load_state()
    force = FORCE or REPLACE
    if REPLACE:
        head("Remise à zéro des profils Chrome")
        for cd in by_profile:
            try:
                n = clear_bookmarks(cd)
                ok("%s : %d favoris effacés" % (profs[cd], n))
            except Exception as e:
                warn("%s : favoris non effacés (%s)" % (profs[cd], e))
            r = clear_history(cd)
            (ok if r.startswith("ok:") else warn)(
                "%s : historique %s" % (profs[cd], r[3:] if r.startswith("ok:") else r)
            )
            n_account = account_bookmarks(cd)
            if n_account:
                warn(
                    "%s : %d favoris sont enregistrés dans ton compte Google et resteront visibles. "
                    "Supprime-les dans Chrome (chrome://bookmarks) : ils disparaîtront aussi du compte."
                    % (profs[cd], n_account)
                )
            for k in [k for k in state if k.split("|")[-1] == cd or k.split("|")[1:2] == [cd]]:
                del state[k]
        save_state(state)
        out("  Si la synchronisation Chrome est activée sur ces profils, efface aussi les données du compte Google")
        out("  (chrome.google.com/sync › Supprimer les données) : sinon Chrome peut faire revenir l'ancien contenu.")

    head("Favoris")
    for cd, ps in by_profile.items():
        nodes, keys = [], []
        if mode == "espaces":
            p = ps[0]
            key = "favoris|%s|%s" % (cd, p["title"])
            if not state.get(key) or force:
                nodes = list(p["favs"]) + folder(PINNED_FOLDER, p["pinned"]) + folder(OPEN_FOLDER, p["unpinned"])
                keys.append(key)
        else:
            fkey = "favoris|%s|__favoris__" % cd
            if not state.get(fkey) or force:
                favs, seen_p, seen_u = [], set(), set()
                for p in ps:
                    if p["aprof"] in seen_p:
                        continue
                    seen_p.add(p["aprof"])
                    for n in p["favs"]:
                        k = n.get("url") or n["name"] + json.dumps(n.get("children"), default=str)
                        if k not in seen_u:
                            seen_u.add(k)
                            favs.append(n)
                nodes += folder(FAV_FOLDER, favs)
                keys.append(fkey)
            for p in ps:
                key = "favoris|%s|%s" % (cd, p["title"])
                if state.get(key) and not force:
                    continue
                nodes += folder("Arc – " + p["title"], list(p["pinned"]) + folder("Onglets ouverts", p["unpinned"]))
                keys.append(key)
        if not keys:
            warn("%s : déjà migrés (option --forcer pour refaire)" % profs[cd])
            continue
        try:
            if nodes:
                write_bookmarks(cd, nodes)
            for k in keys:
                state[k] = now_str()
            save_state(state)
            ok("%s : %d favoris ajoutés" % (profs[cd], count(nodes)))
        except Exception as e:
            warn("%s : favoris non écrits (%s) — utilise les fichiers HTML de secours" % (profs[cd], e))

    head("Historique")
    pairs = []
    for p in todo:
        if (p["aprof"], p["cdir"]) not in pairs:
            pairs.append((p["aprof"], p["cdir"]))
    for ap, cd in pairs:
        key = "historique|%s|%s" % (ap, cd)
        label = "%s → %s" % (", ".join(p["title"] for p in todo if p["aprof"] == ap and p["cdir"] == cd), profs[cd])
        if state.get(key) and not force:
            warn("%s : déjà fusionné le %s" % (label, state[key]))
            continue
        r = merge_history(ap, cd)
        if r.startswith("ok:"):
            ok("%s : %s" % (label, r[3:]))
            state[key] = now_str()
            save_state(state)
        else:
            warn("%s : %s" % (label, r))

    head("Extensions")
    to_open = []
    for cd, ps in by_profile.items():
        have, need = installed(cd), {}
        for ap in sorted({p["aprof"] for p in ps}):
            for i, n in arc_extensions(ap).items():
                if i not in have:
                    need[i] = n
        if need:
            ok("%s : %s" % (profs[cd], ", ".join(sorted(need.values(), key=str.casefold))))
            to_open.append((cd, need))
        else:
            ok("%s : rien à installer" % profs[cd])

    if os.path.isdir(BACKUP):
        out("\n  Fichiers Chrome d'origine sauvegardés dans : resultat-migration/sauvegardes-chrome")
    save_log()
    if to_open and not NO_OPEN and confirm("\nOuvrir Chrome sur les extensions à réinstaller, profil par profil ?"):
        for cd, need in to_open:
            urls = ["https://chromewebstore.google.com/detail/" + i for i in sorted(need)]
            subprocess.run(["open", "-na", "Google Chrome", "--args", "--profile-directory=" + cd] + urls)
            time.sleep(3)
        out("  Clique sur « Ajouter à Chrome » dans chaque onglet.")
    head("Terminé ✅")
    out("  • Dans Chrome, affiche la barre de favoris avec Cmd+Maj+B.")
    out("  • Mots de passe : suis l'étape 6 du LISEZMOI.txt.")
    out("  • Résumé, favoris HTML et sauvegardes : dossier resultat-migration.")
    save_log()


if __name__ == "__main__":
    code = check_args()
    if code is not None:
        sys.exit(code)
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrompu.")
