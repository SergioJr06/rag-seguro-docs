import json
import sys
import unicodedata
from pathlib import Path


def norm(texto):
    sem = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in sem if not unicodedata.combining(c))


def resposta_ok(resposta, grupos):
    t = norm(resposta)
    return all(any(norm(a) in t for a in g) for g in grupos)


perguntas = {q["id"]: q for q in json.loads(Path("eval/perguntas.json").read_text(encoding="utf-8"))}
for nome in sys.argv[1:]:
    res = json.loads(Path(f"eval/resultados_{nome}.json").read_text(encoding="utf-8"))
    ok = sum(resposta_ok(r["resposta"], perguntas[r["id"]]["contem"]) for r in res)
    print(f"{nome:<16} resposta ok: {ok}/{len(res)} = {100 * ok / len(res):.0f}%")