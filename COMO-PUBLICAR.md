# Ranking Ao Vico — usando só GitHub (Pages + Actions)

Tudo roda dentro do GitHub, sem Netlify e sem servidor separado:
- **GitHub Pages** hospeda o site (`index.html`) de graça
- **GitHub Actions** roda 1x por dia, consulta o Google Trends e salva o resultado em `trends.json`
- O site lê esse `trends.json` direto — instantâneo, sem espera

## Estrutura de arquivos

```
.github/workflows/atualizar-tendencias.yml   → o "robô" que roda todo dia
scripts/gerar_tendencias.py                  → o script que consulta o Google Trends
data/produtos-catalogo.csv                   → SEU catálogo (troque pelo export real da WeDrop)
index.html                                   → o site
trends.json                                  → gerado automaticamente (não precisa criar)
```

## Passo 1 — Criar o repositório

1. Crie uma conta gratuita em https://github.com (se ainda não tiver).
2. Clique em **"New repository"**. Nome sugerido: `ranking-wedrop`. Pode deixar **Public** (necessário pro GitHub Pages gratuito) ou Private (também funciona, mas exige conta paga pra Pages — recomendo Public).
3. Clique em **"uploading an existing file"** e suba TODOS os arquivos deste pacote, mantendo as pastas (`.github/workflows/...`, `scripts/...`, `data/...`).

## Passo 2 — Trocar o catálogo de exemplo pelo seu

1. Dentro do repositório no GitHub, abra a pasta `data/`.
2. Apague o `produtos-catalogo.csv` de exemplo e suba o CSV real exportado da WeDrop, com esse mesmo nome (`produtos-catalogo.csv`).
3. Sempre que quiser atualizar o catálogo, é só repetir esse passo — o robô do dia seguinte já usa o novo arquivo.

## Passo 3 — Ativar o GitHub Pages

1. No repositório, vá em **Settings → Pages**.
2. Em "Source", escolha **Deploy from a branch**, branch `main`, pasta `/ (root)`.
3. Salve. Em 1-2 minutos, o GitHub te dá um link tipo `https://seu-usuario.github.io/ranking-wedrop/`.

## Passo 4 — Rodar a primeira atualização de tendências manualmente

Por padrão, o robô roda sozinho todo dia às 6h (horário de Brasília), mas você pode rodar agora mesmo, sem esperar:

1. Vá na aba **Actions** do repositório.
2. Clique no workflow **"Atualizar tendências"** na lista à esquerda.
3. Clique no botão **"Run workflow"** → **"Run workflow"** de novo pra confirmar.
4. Espere 1-3 minutos. Quando terminar, um arquivo `trends.json` aparece automaticamente na raiz do repositório.

## Pronto!

Acesse o link do Passo 3 — o site carrega normalmente, com a tendência já disponível (lida do `trends.json`), sem nenhuma espera nem chamada externa no momento do uso.

## Notas importantes

- O robô roda automaticamente **a cada 15 minutos**, consultando o Google Trends e atualizando o `trends.json`. Isso deixa os dados quase em tempo real, sem precisar de servidor externo.
- O robô analisa até 40 produtos por categoria (os de maior margem), pra não sobrecarregar o Google Trends. Se quiser mudar esse número, é só editar a linha `TOP_POR_CATEGORIA = 40` no arquivo `scripts/gerar_tendencias.py`.
- O GitHub não garante o horário exato de execuções agendadas (pode atrasar alguns minutos em horários de pico), mas na prática costuma rodar bem próximo do intervalo configurado.
- Se o Google Trends bloquear temporariamente as consultas (acontece de vez em quando com ferramentas não-oficiais), o script simplesmente marca os produtos daquele lote com pontuação 0, sem quebrar o robô — na próxima rodada (15 min depois) ele tenta de novo.
- Repositórios **Public** têm GitHub Actions gratuito ilimitado, então rodar a cada 15 minutos não gera custo.
