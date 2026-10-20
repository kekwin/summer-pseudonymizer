"""Navnelisten (data/fornavne_da.txt, efternavne_da.txt) og opslaget i motoren. Alt er opdigtet eller offentlig statistik."""
import time
import unittest

import _path  # noqa: F401
from pseudonymizer import Pseudonymizer, TokenStore, names_da


class ListTest(unittest.TestCase):
    def test_list_is_large_and_monotone_in_threshold(self):
        sizes = [len(names_da.first_names(t)) for t in (0, 1, 5, 20, 100, 10**9)]
        self.assertGreater(sizes[0], 100_000)
        self.assertEqual(sizes, sorted(sizes, reverse=True))
        self.assertGreaterEqual(sizes[-1], 1000)  # de 1000 mest frekvente er altid med

    def test_common_words_are_not_names(self):
        names = names_da.first_names(0)
        for w in "hans per bo august mark tom maj liv rune bent sol rose max karry hej tak mor far barn dag mandag maj".split():
            self.assertFalse(w in names, w)
        # almindelige ord fra børnehavens hverdag
        for w in "bleer sut bamse madpakke regntøj frugt mælk legetøj skov strand feber hoste fødselsdag velkommen".split():
            self.assertFalse(w in names, w)

    def test_common_names_are_in(self):
        names = names_da.first_names(0)
        for w in "peter anne emma camilla oline torvald hjalte ingvild mathilde line mia ebbe".split():
            self.assertTrue(w in names, w)

    def test_threshold_removes_rare_names_only(self):
        rare = "torvald"  # registreret, men ingen forekomster i nyhedskorpusset
        self.assertIn(rare, names_da.first_names(0))
        self.assertNotIn(rare, names_da.first_names(1))
        self.assertIn("peter", names_da.first_names(10**9))

    def test_surnames_off_by_default(self):
        self.assertEqual(names_da.surnames(0), frozenset())
        self.assertIn("andersen", names_da.surnames(1000))
        self.assertNotIn("møller", names_da.surnames(5000))  # også et almindeligt ord


class LookupTest(unittest.TestCase):
    def mask(self, text, **kw):
        return Pseudonymizer(TokenStore(), **kw).clean(text, strict=1).text

    def test_rare_names_in_lowercase_and_at_sentence_start(self):
        self.assertEqual(self.mask("ring til oline og gudrun, de ved besked"), "ring til Person-? og Person-?, de ved besked")
        self.assertEqual(self.mask("Torvald har det fint."), "Person-? har det fint.")
        self.assertEqual(self.mask("RING TIL OLINE"), "RING TIL Person-?")

    def test_genitive_apostrophe_initial_and_double_names(self):
        self.assertEqual(self.mask("oline's mor og torvalds far"), "Person-?'s mor og Person-?'s far")
        self.assertEqual(self.mask("Det er Oline K. der kommer"), "Det er Person-? der kommer")
        self.assertEqual(self.mask("anne-mette og Lise-Lotte"), "Person-? og Person-?")

    def test_whole_words_only(self):
        self.assertEqual(self.mask("olinesque og hjaltemose"), "olinesque og hjaltemose")

    def test_ordinary_text_survives(self):
        text = "Vi skal tage på tur, og børnene har en sten i skoen. Det koster 5 mia. kr.."
        self.assertEqual(self.mask(text), text)

    def test_threshold_is_per_instance(self):
        text = "ring til torvald og peter"
        self.assertEqual(self.mask(text, min_count=0), "ring til Person-? og Person-?")
        self.assertEqual(self.mask(text, min_count=1), "ring til torvald og Person-?")

    def test_surname_rank(self):
        self.assertEqual(self.mask("ring til andersen"), "ring til andersen")
        self.assertIn("Person-?", self.mask("ring til andersen", surname_rank=100))

    def test_protected_and_allowed_names_are_kept(self):
        store = TokenStore()
        store.add_protected(["Oline"])
        p = Pseudonymizer(store)
        self.assertEqual(p.clean("oline og torvald", strict=1, allowed={"torvald"}).text, "oline og torvald")

    def test_speed_on_a_long_text(self):
        p = Pseudonymizer(TokenStore())
        p.clean("opvarmning")
        text = ("Hej, ring til oline eller gudrun, og husk madpakke og regntøj til turen i morgen kl. 9. " * 40)[:3000]
        t0 = time.perf_counter()
        for _ in range(20):
            p.clean(text, strict=1)
        per_text_ms = (time.perf_counter() - t0) / 20 * 1000
        self.assertLess(per_text_ms, 50, f"{per_text_ms:.1f} ms pr. tekst")  # typisk ca. 2-3 ms; grænsen er løs, så langsomme maskiner ikke fejler


if __name__ == "__main__":
    unittest.main()
