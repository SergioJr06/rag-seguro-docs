import argparse
import json
import unicodedata
from pathlib import Path

from app.rag import ask


def norm(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in sem_acento if not unicodedata.combining(c))


def resposta_ok(resposta: str, grupos: list[list[str]]) -> bool:
    t = norm(resposta)
    return all(any(norm(alt) in t for alt in grupo) for grupo in grupos)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--k", type=int, default=4)
    p.add_argument("--nome", default="base")
    args = p.parse_args()

    perguntas = json.loads(Path("eval/perguntas.json").read_text(encoding="utf-8"))
    resultados = []
    for q in perguntas:
        out = ask(q["pergunta"], args.k)
        fonte_ok = any(s["document"] == q["fonte"] for s in out["sources"])
        resp_ok = resposta_ok(out["answer"], q["contem"])
        resultados.append({**q, "fonte_ok": fonte_ok, "resp_ok": resp_ok,
                           "resposta": out["answer"], "fontes": out["sources"]})
        print(f"{q['id']:>2} fonte={'OK' if fonte_ok else '--'} "
              f"resposta={'OK' if resp_ok else '--'}  {q['pergunta'][:55]}")

    n = len(resultados)
    f = sum(r["fonte_ok"] for r in resultados)
    a = sum(r["resp_ok"] for r in resultados)
    print(f"\nConfig '{args.nome}' (k={args.k})")
    print(f"Fonte correta entre os trechos: {f}/{n} = {100 * f / n:.0f}%")
    print(f"Resposta com a informação esperada: {a}/{n} = {100 * a / n:.0f}%")

    saida = Path(f"eval/resultados_{args.nome}.json")
    saida.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Detalhes salvos em {saida}")


if __name__ == "__main__":
    main()