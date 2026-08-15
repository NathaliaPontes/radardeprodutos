"""
scripts/gerar_tendencias.py
------------------------------
Roda automaticamente via GitHub Actions (veja .github/workflows/atualizar-tendencias.yml).

Lê o catálogo em data/produtos-catalogo.csv, monta os termos de busca
por produto (mesma lógica usada no site, em index.html), consulta o
Google Trends, e salva o resultado em trends.json — que o site (GitHub
Pages) lê diretamente, sem precisar de servidor.
"""

import json
import time
import pandas as pd
from pytrends.request import TrendReq

ARQUIVO_CATALOGO = "data/produtos-catalogo.csv"
ARQUIVO_SAIDA = "trends.json"
MARKUP_PADRAO = 2.5
TOP_POR_CATEGORIA = 40


def nome_para_busca(nome):
    ignorar = {"com", "de", "para", "cm", "kg", "un", "unid", "-"}
    palavras = [p for p in str(nome).split() if p.lower() not in ignorar]
    return " ".join(palavras[:4])


def parse_preco(v):
    if pd.isna(v):
        return 0.0
    s = str(v).replace("R$", "").strip()
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def selecionar_termos(df):
    df = df.copy()
    df["_preco"] = df["Preço"].apply(parse_preco)
    df["_margem"] = df["_preco"] * (MARKUP_PADRAO - 1)
    df["_termo"] = df["Nome do Produto"].apply(nome_para_busca)

    selecionados = []
    for categoria, grupo in df.groupby("Categoria"):
        top = grupo.sort_values("_margem", ascending=False).head(TOP_POR_CATEGORIA)
        selecionados.extend(top["_termo"].tolist())

    return sorted(set(t for t in selecionados if t.strip()))


def buscar_tendencias(termos):
    pytrends = TrendReq(hl="pt-BR", tz=180)
    scores = {}
    lote = 5
    total = (len(termos) - 1) // lote + 1

    for i in range(0, len(termos), lote):
        grupo = termos[i:i + lote]
        n = i // lote + 1
        print(f"Consultando lote {n}/{total}: {grupo}")
        try:
            pytrends.build_payload(grupo, timeframe="now 7-d", geo="BR")
            dados = pytrends.interest_over_time()
            for termo in grupo:
                scores[termo] = round(float(dados[termo].mean()), 1) if (not dados.empty and termo in dados.columns) else 0
            time.sleep(3)
        except Exception as e:
            print(f"Aviso: falha no lote {n} ({e}) - marcando como 0")
            for termo in grupo:
                scores[termo] = 0

    return scores


def main():
    print(f"Lendo {ARQUIVO_CATALOGO}...")
    df = pd.read_csv(ARQUIVO_CATALOGO)
    df.columns = [c.strip() for c in df.columns]

    termos = selecionar_termos(df)
    print(f"{len(termos)} termos únicos a consultar no Google Trends.")

    scores = buscar_tendencias(termos)

    saida = {
        "gerado_em": pd.Timestamp.utcnow().isoformat(),
        "scores": scores,
    }

    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)

    print(f"Salvo em {ARQUIVO_SAIDA} com {len(scores)} termos.")


if __name__ == "__main__":
    main()
