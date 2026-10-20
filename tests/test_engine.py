"""Enhedstests af motoren: tekstrens, pseudonymisering, lækagevagt, token-lager og emner. Alt er opdigtet."""
import tempfile
import unittest
from pathlib import Path

import _path  # noqa: F401
from pseudonymizer import (Pseudonymizer, TokenStore, find_identifiers, find_topics, html_to_text, scrub)


class ScrubTest(unittest.TestCase):
    def test_removes_identifiers(self):
        cases = {
            "Ring på 12345678": "[TELEFON]", "tlf 12 34 56 78": "[TELEFON]", "+45 87 65 43 21": "[TELEFON]",
            "0045 12345678": "[TELEFON]", "CPR 150312-5555": "[CPR]", "cpr 1503125555": "[CPR]",
            "mail a.b@example.invalid": "[EMAIL]", "se https://example.invalid/x?y=1": "[LINK]",
            "se www.example.invalid/x": "[LINK]", "Vi bor Egevej 12, 2. th, 2300 København S": "[ADRESSE]",
            "Skovvej 7": "[ADRESSE]", "2400 København NV": "[ADRESSE]",
            "ring 4040 4040": "[TELEFON]", "tlf 2030 4050": "[TELEFON]", "MobilePay 12345": "[KONTO]",
            "konto 1234567890": "[KONTO]", "find os på @navn_x": "[LINK]", "id 1234567890123": "[NUMMER]",
        }
        for text, mark in cases.items():
            out, _ = scrub(text)
            self.assertIn(mark, out, text)
            self.assertEqual(find_identifiers(out), [], out)

    def test_keeps_dates_times_and_numbers(self):
        for text in ["2026-10-19", "12.10.2026", "22/10-26", "kl. 15:30", "08.30 - 14.30", "uge 43", "side 14-15",
                     "38,5 i feber", "1000 kr.", "Mandag d. 12/10", "skoleåret 2026-2027", "2026 2027"]:
            out, _ = scrub(text)
            self.assertEqual(out, text, text)

    def test_html(self):
        self.assertEqual(html_to_text("Hej<br />Tak&nbsp;for &amp; i dag 🙂<p>Mvh X</p>"), "Hej\nTak for & i dag 🙂\nMvh X")


class PseudoTest(unittest.TestCase):
    def setUp(self):
        self.store = TokenStore()
        self.store.add_protected(["Mikkel", "Noah"])
        self.t_emma_a = self.store.token("Barn", "c:emma|rævene", ["Emma"])
        self.t_emma_b = self.store.token("Barn", "c:emma|sommerfuglene", ["Emma"])
        self.t_pernille = self.store.token("Forælder", "p:1", ["Pernille Lindholm"])
        self.t_sofie = self.store.token("Pædagog", "p:2", ["Sofie Dahl"])
        self.p = Pseudonymizer(self.store)

    def clean(self, text, **kw):
        return self.p.clean(text, **kw)

    def test_names_genitive_initials_case(self):
        out = self.clean("Pernille Lindholm og pernille og Pernilles mor. Sofie D. sagde, at SOFIE kommer.").text
        for gone in ("Pernille", "pernille", "Sofie"):
            self.assertNotIn(gone, out)
        self.assertIn(self.t_pernille + "'s", out)
        self.assertNotIn("D.", out)  # initial slugt med fornavnet

    def test_protected_names_kept_and_ambiguity(self):
        out = self.clean("Mikkel og Noah skal se Emma.").text
        self.assertIn("Mikkel", out)
        self.assertIn("Noah", out)
        self.assertIn("Barn-?", out)  # to børn hedder Emma: aldrig et gæt

    def test_word_boundaries(self):
        out = self.clean("Pernillevej og Sofiebogen og Anders Sofies").text
        self.assertIn("Pernillevej", out)
        self.assertIn(self.t_sofie + "'s", out)

    def test_two_letter_names_case_sensitive(self):
        self.store.token("Ansat", "p:9", ["Bo Winther"])
        out = Pseudonymizer(self.store).clean("Vi skal bo her. Bo kommer.").text
        self.assertIn("bo her", out)
        self.assertNotIn("Bo kommer", out)

    def test_trigger_words(self):
        out = self.clean("Mormor Birgit henter, og onkel Jens Hansen kommer").text
        self.assertEqual(out, "Mormor Person-? henter, og onkel Person-? kommer")

    def test_extra_words_flagged_by_user(self):
        out = Pseudonymizer(self.store, ["Zorro"]).clean("Zorros mor og zorro").text
        self.assertNotIn("orro", out)

    def test_unicode_tricks(self):
        out = self.clean("Pern​ille Lindholm og Sofi­e").text
        self.assertNotIn("Pernille", out)
        self.assertNotIn("Sofie", out)
        self.assertEqual(self.clean("Hej Réne").text, "Hej Person-?")  # NFD

    def test_fuzzy_typos_masked_as_known_name(self):
        for text in ("Sofi har ringet", "Hej Pernile", "Hej Villad og Emma"):
            out = self.clean(text).text
            for typo in ("Sofi", "Pernile", "Villad"):
                self.assertNotIn(typo + " ", out + " ")
        # ordet ligner et navn, men står i klientens tilladelsesliste: bevares
        self.assertEqual(self.clean("Sofia og Rævene", allowed={"Rævene", "Sofia"}).text, "Sofia og Rævene")

    def test_guard_catches_remaining_names(self):
        self.assertTrue(self.p.leaks("Hej Pernille"))
        self.assertTrue(self.p.leaks("ring 12345678"))
        self.assertTrue(self.p.leaks("tante Karen"))
        self.assertEqual(self.p.leaks("Hej Forælder-1 og Barn-2"), [])

    def test_mid_sentence_capitals_masked_level1(self):
        out = self.clean("Vi tager til Bakkehuset sammen med Oscar. Husk madpakke.", strict=1).text
        self.assertEqual(out, "Vi tager til Person-? sammen med Person-?. Husk madpakke.")

    def test_level2_masks_sentence_start_names(self):
        out = self.clean("Oscar har det fint. Lægen sagde Tak.", strict=2).text
        self.assertTrue(out.startswith("Person-? har det fint."))
        self.assertIn("Lægen", out)

    def test_tokens_acronyms_and_i_survive(self):
        out = self.clean("Hvis I kan, ring til Forælder-3 og PAU. Barn-?'s mor.", strict=1).text
        self.assertEqual(out, "Hvis I kan, ring til Forælder-3 og PAU. Barn-?'s mor.")

    def test_trace_records_what_was_masked(self):
        self.p.trace = []
        self.clean("Pernille og Bakkehuset")
        layers = {t[2] for t in self.p.trace}
        self.assertEqual(layers, {"navn", "ukendt stort ord"})

    def test_custom_layer_is_applied_and_protected_names_skipped(self):
        class Fake:
            name = "fake"

            def find_spans(self, text):
                i = text.find("Zacharias")
                j = text.find("Mikkel")
                return [(i, i + 9, "PERSON")] + ([(j, j + 6, "PERSON")] if j >= 0 else [])

        p = Pseudonymizer(self.store, layers=[Fake()])
        out = p.clean("Zacharias og Mikkel", strict=0).text
        self.assertEqual(out, "Person-? og Mikkel")


class StoreTest(unittest.TestCase):
    def test_tokens_stable_and_never_reused(self):
        s = TokenStore()
        a = s.token("Forælder", "p:1", ["Anna Hansen"])
        self.assertEqual(a, s.token("Forælder", "p:1", ["Anna Hansen"]))
        self.assertNotEqual(a, s.token("Forælder", "p:2", ["Bo Jensen"]))

    def test_same_full_name_other_key_reuses_token(self):
        s = TokenStore()
        a = s.token("Lærer", "p:5", ["Lone Mortensen"])
        self.assertEqual(a, s.token("Ansat", "n:lone", ["Lone Mortensen"]))
        self.assertEqual(a, s.token("Person", "n:lone2", ["Lone Mortensen"]))

    def test_persists_and_keeps_meta(self):
        path = Path(tempfile.mkdtemp()) / "store.json"
        s = TokenStore(path)
        t = s.token("Barn", "c:x|", ["Xander"])
        s.add_protected(["Ejer"])
        s.meta["klient"] = {"x": 1}
        s.save()
        s2 = TokenStore(path)
        self.assertEqual(s2.token("Barn", "c:x|", ["Xander"]), t)
        self.assertIn("Ejer", s2.protected)
        self.assertEqual(s2.meta["klient"], {"x": 1})

    def test_corrupt_or_wrong_version_fails_closed(self):
        path = Path(tempfile.mkdtemp()) / "store.json"
        path.write_text('{"version": 2, "entries": [', encoding="utf-8")
        with self.assertRaises(RuntimeError):
            TokenStore(path)
        path.write_text('{"version": 1}', encoding="utf-8")
        with self.assertRaises(RuntimeError):
            TokenStore(path)

    def test_prefix_must_be_letters(self):
        with self.assertRaises(ValueError):
            TokenStore().token("Be-1", "k", ["x"])


class TopicsTest(unittest.TestCase):
    def test_topics(self):
        self.assertIn("sygdom", find_topics("Barnet har skoldkopper og feber"))
        self.assertIn("sygdom", find_topics("hånd-fod-mundsyge"))
        self.assertIn("helbred-medicin", find_topics("husk medicin og allergi"))
        self.assertIn("familie", find_topics("efter skilsmissen"))
        self.assertEqual(find_topics("Madplan uge 42: boller i karry"), set())


if __name__ == "__main__":
    unittest.main()
