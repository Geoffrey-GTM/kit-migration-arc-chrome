"""Tests de bout en bout du kit, sur des données factices (voir fixtures.py)."""

import hashlib
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

import fixtures

ARC_FOLDERS = ("Arc – onglets épinglés", "Arc – onglets ouverts")


def digest(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def visits(root, profile):
    con = sqlite3.connect(os.path.join(root, "chrome", profile, "History"))
    try:
        return con.execute("SELECT COUNT(*) FROM visits").fetchone()[0]
    finally:
        con.close()


class MigrationTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="kit-arc-")
        fixtures.build(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def run_ok(self, *args):
        r = fixtures.run(self.root, *args)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout

    # --------------------------------------------------------------- favoris
    def test_un_profil_par_espace_a_plat(self):
        self.run_ok("--mode", "espaces")
        bar = fixtures.bar(self.root, "Profile 5")
        names = [n for _t, n in bar]
        # Ancien contenu conservé, puis favoris, onglets épinglés (avec leur dossier) et ouverts, à plat
        self.assertEqual(names, ["Ancien dossier Chrome", "Messagerie", "Documentation", "Outils", "Article ouvert"])
        self.assertIn(("folder", "Outils"), bar)
        for folder in ARC_FOLDERS:
            self.assertNotIn(folder, names)
        self.assertEqual([n for _t, n in fixtures.bar(self.root, "Profile 6")][1:], ["Banque", "Recettes"])

    def test_option_dossiers(self):
        self.run_ok("--mode", "espaces", "--dossiers")
        names = [n for _t, n in fixtures.bar(self.root, "Profile 5")]
        self.assertEqual(names, ["Ancien dossier Chrome", "Messagerie", *ARC_FOLDERS])

    def test_relance_sans_doublon(self):
        self.run_ok("--mode", "espaces")
        first = fixtures.bar(self.root, "Profile 5")
        out = self.run_ok("--mode", "espaces")
        self.assertIn("déjà migrés", out)
        self.assertEqual(fixtures.bar(self.root, "Profile 5"), first)

    def test_espace_ignore(self):
        out = self.run_ok("--mode", "espaces")
        self.assertIn("ignoré (fichier de correspondance)", out)
        self.assertNotIn("Vieux site", str(fixtures.read_bookmarks(self.root, "Profile 5")))

    def test_un_seul_profil(self):
        self.run_ok("--mode", "unique", "--profil", "Clients")
        names = [n for _t, n in fixtures.bar(self.root, "Profile 5")]
        self.assertEqual(names, ["Ancien dossier Chrome", "Arc – favoris", "Arc – Clients", "Arc – Perso"])

    def test_copie_html_de_secours(self):
        self.run_ok("--mode", "espaces")
        html_dir = os.path.join(self.root, "kit", "resultat-migration", "favoris-html")
        self.assertEqual(sorted(os.listdir(html_dir)), ["Clients.html", "Perso.html"])

    def test_correspondance_locale(self):
        with open(os.path.join(self.root, "kit", "correspondance.local.txt"), "w", encoding="utf-8") as f:
            f.write("Perso = ignorer  # espace perso, pas dans Chrome\n")
        out = self.run_ok("--mode", "espaces")
        self.assertIn("Perso", out)
        self.assertEqual([n for _t, n in fixtures.bar(self.root, "Profile 6")], ["Ancien dossier Chrome"])
        self.assertIn("Messagerie", [n for _t, n in fixtures.bar(self.root, "Profile 5")])

    # --------------------------------------------------------------- simulation et confirmation
    def chrome_digests(self):
        names = ("Bookmarks", "History")
        return {
            (p, n): digest(os.path.join(self.root, "chrome", p, n)) for p in ("Profile 5", "Profile 6") for n in names
        }

    def test_plan_ne_modifie_rien(self):
        before = self.chrome_digests()
        out = self.run_ok("--plan", "--mode", "espaces", "--remplacer")
        self.assertEqual(self.chrome_digests(), before)
        self.assertIn("Simulation terminée", out)
        self.assertIn("Clients                  → Clients", out)
        self.assertTrue(os.path.exists(os.path.join(self.root, "kit", "resultat-migration", "plan.txt")))

    def test_sans_terminal_ni_oui_rien_n_est_modifie(self):
        before = self.chrome_digests()
        r = fixtures.run(self.root, "--mode", "espaces", "--remplacer", yes=False)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.chrome_digests(), before)
        self.assertIn("Rien n'a été modifié", r.stdout)
        self.assertIn("ajoute --oui", r.stdout)

    # --------------------------------------------------------------- remplacer et compte Google
    def test_remplacer_vide_puis_importe(self):
        account = os.path.join(self.root, "chrome", "Profile 6", "AccountBookmarks")
        before = digest(account)
        out = self.run_ok("--mode", "espaces", "--remplacer")
        names = [n for _t, n in fixtures.bar(self.root, "Profile 5")]
        self.assertEqual(names, ["Messagerie", "Documentation", "Outils", "Article ouvert"])
        # Les favoris du compte Google ne sont jamais modifiés, mais ils sont signalés
        self.assertEqual(digest(account), before)
        self.assertIn("Perso : 1 favoris enregistrés dans le compte Google — dossiers : Dossier du compte", out)
        self.assertNotIn("Supprimer les données", out)
        # Sauvegarde du fichier Bookmarks et de sa copie chiffrée
        backups = os.path.join(self.root, "kit", "resultat-migration", "sauvegardes-chrome")
        (stamp,) = os.listdir(backups)
        saved = sorted(os.listdir(os.path.join(backups, stamp, "Profile 5")))
        self.assertIn("Bookmarks", saved)
        self.assertIn("EncryptedBookmarks2", saved)

    def test_avertissement_compte_google_sans_remplacer(self):
        out = self.run_ok("--mode", "espaces")
        self.assertIn("Favoris de ton compte Google", out)
        self.assertIn("Favoris du compte Google encore affichés dans : Perso", out)

    # --------------------------------------------------------------- historique
    def test_historique_fusionne_sans_doublon(self):
        self.assertEqual(visits(self.root, "Profile 5"), 1)
        self.run_ok("--mode", "espaces")
        self.assertEqual(visits(self.root, "Profile 5"), 3)
        self.run_ok("--mode", "espaces", "--forcer")
        self.assertEqual(visits(self.root, "Profile 5"), 3)

    def test_remplacer_vide_l_historique_avant_fusion(self):
        self.run_ok("--mode", "espaces", "--remplacer")
        self.assertEqual(visits(self.root, "Profile 5"), 2)

    # --------------------------------------------------------------- extensions
    def test_extensions_a_reinstaller(self):
        out = self.run_ok("--mode", "espaces")
        self.assertIn("Clients : Extension de test", out)

    # --------------------------------------------------------------- diagnostic
    def test_diagnostic_lecture_seule(self):
        files = [os.path.join(self.root, "chrome", p, "Bookmarks") for p in ("Profile 5", "Profile 6")]
        before = [digest(f) for f in files]
        out = self.run_ok("--diagnostic")
        self.assertEqual([digest(f) for f in files], before)
        self.assertIn("Perso (Profile 6) — connecté à un compte Google : oui", out)
        self.assertIn("Dossier du compte", out)
        self.assertIn("Favoris du compte Google affichés en plus dans : Perso.", out)
        self.assertTrue(os.path.exists(os.path.join(self.root, "kit", "resultat-migration", "diagnostic.txt")))

    # --------------------------------------------------------------- ligne de commande
    def test_version(self):
        out = self.run_ok("--version")
        self.assertRegex(out, r"^migrer-arc-vers-chrome \d+\.\d+\.\d+")

    def test_option_inconnue(self):
        r = fixtures.run(self.root, "--inconnue")
        self.assertEqual(r.returncode, 2)
        self.assertIn("Option inconnue", r.stdout)

    def test_mode_invalide(self):
        r = fixtures.run(self.root, "--mode", "nimporte")
        self.assertEqual(r.returncode, 2)


@unittest.skipUnless(sys.platform == "darwin", "le lanceur bash ne fonctionne que sur macOS")
class LanceurTest(unittest.TestCase):
    def test_version_via_lanceur(self):
        r = subprocess.run(
            ["bash", os.path.join(fixtures.ROOT, "migrer-arc-vers-chrome.sh"), "--version"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("migrer-arc-vers-chrome", r.stdout)


if __name__ == "__main__":
    unittest.main()
