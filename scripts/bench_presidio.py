"""Måler Presidio-lagets indlæsningstid, tid pr. tekst og hukommelse. Kør i en container med begrænsede ressourcer
for at ligne en lille server, fx:  docker run --cpus=2 --memory=2g ... python scripts/bench_presidio.py da_core_news_md
"""
import json
import resource
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from pseudonymizer.evaluation import build, evaluate  # noqa: E402
from pseudonymizer.presidio_layer import PresidioLayer  # noqa: E402

model = sys.argv[1] if len(sys.argv) > 1 else "da_core_news_md"
corpus = json.loads((Path(__file__).resolve().parent.parent / "corpus" / "da_synthetic.json").read_text(encoding="utf-8"))
t0 = time.time()
layer = PresidioLayer(model=model)
load = time.time() - t0
layer.find_spans("Opvarmning med Sofie")
texts = [d["text"] for d in corpus["docs"]]
t0 = time.time()
for _ in range(3):
    for t in texts:
        layer.find_spans(t)
per = (time.time() - t0) / (3 * len(texts)) * 1000
r = evaluate(corpus, (layer,))
rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
ukendt = r["recall"].get("navn-ukendt-satsstart", {})
print(f"{model}: indlæsning {load:.1f} s, {per:.0f} ms pr. tekst, spids-RAM {rss:.0f} MB, "
      f"sætningsstart-navne {ukendt.get('fjernet')}/{ukendt.get('i_alt')}, "
      f"overmaskering {r['overmaskering']['andel']:.1%}, lækager {len(r['lækager'])}")
