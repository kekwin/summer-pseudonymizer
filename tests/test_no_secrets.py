"""Dette repo er offentligt. Ingen hemmeligheder, rigtige data eller personoplysninger må ligge her."""
import re
import subprocess
import unittest

import _path

REGEXES = [r"gh[pousr]_[A-Za-z0-9]{20,}", r"sk-[A-Za-z0-9]{20,}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"AULA_MCP_KEY\s*="]
SUBSTRINGS = ["C:" + chr(92) + "Users", "Athena", "Olivia", "Sommer Pedersen", "3177502", "3177503", "kewi0194", "@gmail.com",
              "tailcc94cc", "ts.net", "G18932", "PILETR"]
FORBIDDEN = REGEXES
OWNER = "Kewin Sommer Pedersen"  # copyright-linjen i LICENSE
# Opdigtede eksempler må stå: e-mails og links på example.invalid, og de falske CPR-numre i korpusset.
EMAIL = re.compile(r"[\w.+-]+@(?!example\.invalid)[\w-]+(?:\.[\w-]+)+")
URL = re.compile(r"https?://(?!example\.invalid|github\.com|presidio|spacy|microsoft\.github\.io|explosion\.ai|pypi\.org|docs\.python\.org|sprogtek-ressources\.digst\.govcloud\.dk|sprogteknologi\.dk|downloads\.wortschatz-leipzig\.de|wortschatz\.uni-leipzig\.de|www\.dst\.dk|creativecommons\.org)[^\s\"')]+")


def tracked_files():
    out = subprocess.run(["git", "ls-files"], cwd=_path.ROOT, capture_output=True, text=True).stdout.split("\n")
    return [_path.ROOT / f for f in out if f and not f.endswith((".png", ".jpg"))]


class NoSecretsTest(unittest.TestCase):
    def test_no_secrets_or_personal_data_in_tracked_files(self):
        problems = []
        for f in tracked_files():
            if f.name == "test_no_secrets.py" or not f.exists():
                continue
            try:
                text = f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                problems.append(f"{f.name}: binær fil")
                continue
            for pat in REGEXES:
                if re.search(pat, text):
                    problems.append(f"{f.relative_to(_path.ROOT)}: {pat}")
            # Ejerens navn står med vilje i LICENSE (og nævnes i CLAUDE.md); andre former af navnet fanges stadig.
            checked = text.replace(OWNER, "")
            for sub in SUBSTRINGS:
                if sub in checked:
                    problems.append(f"{f.relative_to(_path.ROOT)}: {sub}")
            for rx in (EMAIL, URL):
                m = rx.search(text)
                if m:
                    problems.append(f"{f.relative_to(_path.ROOT)}: {m.group(0)[:40]}")
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
