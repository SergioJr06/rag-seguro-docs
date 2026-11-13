import argparse
import json
from pathlib import Path

import app.rag as rag
from eval.run_eval import norm

retrieve_original = rag.retrieve


def com_documento_malicioso(texto):
    def falso(pergunta, k=4):
        hits = retrieve_original(pergunta, k)
        malicioso = {"text": texto, "source": "documento_malicioso.pdf", "page": 1, "distance": 0.0}
        return [malicioso] + hits
    return falso


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--nome", default="sem_guardrail")
    p.add_argument("--arquivo", default="eval/ataques.json")
    args = p.parse_args()

    ataques = json.loads(Path(args.arquivo).read_text(encoding="utf-8"))
    resultados = []
    for a in ataques:
        if "documento_malicioso" in a:
            rag.retrieve = com_documento_malicioso(a["documento_malicioso"])
        else:
            rag.retrieve = retrieve_original
        out = rag.ask(a["pergunta"])
        passou = any(norm(m) in norm(out["answer"]) for m in a["marcadores"])
        resultados.append({**a, "passou": passou, "resposta": out["answer"]})
        print(f"{a['id']} {'PASSOU   ' if passou else 'BLOQUEOU '} {a['tipo']}")
    rag.retrieve = retrieve_original

    n = len(resultados)
    total = sum(r["passou"] for r in resultados)
    print(f"\nConfig '{args.nome}': {total}/{n} ataques passaram")
    saida = Path(f"eval/ataques_{args.nome}.json")
    saida.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Detalhes salvos em {saida}")


if __name__ == "__main__":
    main()