import re
import unicodedata


def _norm(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in sem_acento if not unicodedata.combining(c))


# Pedidos suspeitos na pergunta do usuário
PADROES_ENTRADA = [
    r"\b(ignore|ignora|ignorar|disregard|forget|esqueca|desconsidere)\b.{0,40}\b(instruc\w*|instruction\w*|regras|rules|prompt\w*|anterior\w*|previous|prior)\b",
    r"\b(repita|repeat|print|reveal|revele|mostre|show|imprima|display|exiba)\b.{0,60}\b(system prompt|prompt do sistema|instrucoes do sistema|system instructions|your instructions|suas instrucoes)\b",
    r"\b(sem|nao tem|nao tera|no|without|have no)\s+(nenhuma\s+)?(restric\w*|restrictions|limitac\w*|limits)\b",
]

# Frases com cara de instrução escondidas nos trechos recuperados
PADROES_CONTEXTO = [
    r"\b(ignore|ignora|ignorar|disregard|forget|esqueca|desconsidere)\b.{0,40}\b(instruc\w*|instruction\w*|regras|rules|prompt\w*|anterior\w*|previous|prior)\b",
    r"\b(system note|nota do sistema|nota do administrador|admin note)\b",
    r"\b(inclua|include|insira|adicione|add|escreva|write|diga|say|termine|end)\b.{0,50}\b(a frase|the (exact )?phrase|a palavra|the word)\b",
    r"\b(reply only with|answer only with|responda apenas com|responda somente com)\b",
]


def entrada_suspeita(pergunta: str) -> bool:
    t = _norm(pergunta)
    return any(re.search(p, t) for p in PADROES_ENTRADA)


def limpar_contexto(texto: str) -> str:
    """Remove as frases do trecho que parecem instruções; mantém o resto."""
    frases = re.split(r"(?<=[.!?])\s+", texto)
    mantidas = [f for f in frases if not any(re.search(p, _norm(f)) for p in PADROES_CONTEXTO)]
    return " ".join(mantidas)


def _palavras(texto: str, ignorar: tuple) -> list[str]:
    t = re.sub(r"[^\w\s]", " ", _norm(texto))
    t = " ".join(t.split())
    for frase in ignorar:
        t = t.replace(frase, " ")
    return t.split()


def saida_vaza_prompt(resposta: str, prompt: str, janela: int = 6,
                      ignorar: tuple = ("nao sei com base nos documentos",)) -> bool:
    """True se a resposta repete uma sequência de 6 palavras do prompt do sistema."""
    p, r = _palavras(prompt, ignorar), " ".join(_palavras(resposta, ignorar))
    return any(" ".join(p[i:i + janela]) in r for i in range(len(p) - janela + 1))