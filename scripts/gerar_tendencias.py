"""
scripts/gerar_tendencias.py
------------------------------
Roda automaticamente via GitHub Actions (veja .github/workflows/atualizar-tendencias.yml).

Lê o catálogo em data/produtos-catalogo.csv, monta os termos de busca
por produto (mesma lógica usada no site, em index.html), consulta o
Google Trends, e salva o resultado em trends.json — que o site (GitHub
Pages) lê diretamente, sem precisar de servidor.

Para não estourar o limite de consultas do Google Trends, o script
limita a análise aos N produtos de maior margem por categoria
(configurável abaixo).
"""

import json
import time
import re
import pandas as pd
from pytrends.request import TrendReq

ARQUIVO_CATALOGO = "data/produtos-catalogo.csv"
ARQUIVO_SAIDA = "trends.json"
MARKUP_PADRAO = 2.5          # mesmo valor padrão usado no site, só para ordenar por margem
TOP_POR_CATEGORIA = 40        # quantos produtos de cada categoria são analisados no Trends


def nome_para_busca(nome):
    """Mesma lógica usada em index.html (função nomeParaBusca) — precisa ficar igual
    para o site conseguir casar os termos com as chaves do trends.json."""
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


def buscar_tendencias_web(pytrends):
    """
    Busca as pesquisas em alta no Brasil AGORA, de forma totalmente genérica —
    sem nenhuma relação com o catálogo do usuário. É a tendência real da web.
    """
    try:
        df = pytrends.trending_searches(pn="brazil")
        termos = df[0].tolist()[:20]  # top 20 pesquisas em alta
        return termos
    except Exception as e:
        print(f"Aviso: falha ao buscar tendências gerais da web ({e})")
        return []


def main():
    print(f"Lendo {ARQUIVO_CATALOGO}...")
    df = pd.read_csv(ARQUIVO_CATALOGO)
    df.columns = [c.strip() for c in df.columns]

    termos = selecionar_termos(df)
    print(f"{len(termos)} termos únicos a consultar no Google Trends (baseados no catálogo).")

    scores = buscar_tendencias(termos)

    print("Buscando tendências gerais da web (independente do catálogo)...")
    pytrends_web = TrendReq(hl="pt-BR", tz=180)
    termos_web = buscar_tendencias_web(pytrends_web)
    print(f"{len(termos_web)} termos em alta na web encontrados.")

    saida = {
        "gerado_em": pd.Timestamp.utcnow().isoformat(),
        "scores": scores,
        "tendencias_web": termos_web,
    }

    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)

    print(f"Salvo em {ARQUIVO_SAIDA} com {len(scores)} termos do catálogo + {len(termos_web)} termos da web.")


if __name__ == "__main__":
    main()
