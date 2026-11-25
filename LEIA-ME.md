# Agente de voos: Fortaleza → Europa (maio de 2027)

Este agente pesquisa o Google Flights **todo dia às 06:43 (horário de Fortaleza)**, guarda o histórico de preços e atualiza um painel web com gráficos. Se o preço cair abaixo do seu alvo, você recebe um aviso por e-mail.

Tudo roda de graça na nuvem do GitHub. Você não precisa instalar nada no computador.

---

## O que vem nesta pasta

| Arquivo | Para que serve |
|---|---|
| `config.json` | **O único arquivo que você vai editar.** Datas, destinos e preço alvo. |
| `buscar_voos.py` | Faz a pesquisa no Google Flights. |
| `gerar_painel.py` e `painel_modelo.html` | Montam o painel web. |
| `docs/index.html` | O painel em si (publicado na internet). |
| `workflow-buscar-voos.yml` | A "agenda" que faz tudo rodar sozinho todo dia. |

---

## Configuração (uma vez só, cerca de 20 minutos)

### Passo 1: crie a conta na SerpApi (a fonte dos preços)
1. Acesse **serpapi.com** e clique em **Register**. O plano **Free** dá 250 buscas por mês, mais do que o agente usa (veja "Custos" abaixo).
2. Depois de entrar, vá em **Api Key** (no menu da sua conta) e copie a chave, um código longo de letras e números. Guarde-a para o Passo 5.

### Passo 2: crie a conta e o repositório no GitHub
1. Acesse **github.com** e crie uma conta gratuita (se ainda não tiver).
2. Clique no **+** no canto superior direito → **New repository**.
3. Em *Repository name*, escreva `agente-voos`.
4. Marque **Public**. O plano gratuito só publica painéis de repositórios públicos. Sua chave da SerpApi **não** fica visível (ela vai num cofre, no Passo 5); o que fica público são só os preços pesquisados.
5. Clique em **Create repository**.

### Passo 3: envie os arquivos
1. Na página do repositório recém-criado, clique no link **uploading an existing file**.
2. Arraste para a página: `config.json`, `buscar_voos.py`, `gerar_painel.py`, `painel_modelo.html`, `LEIA-ME.md` **e a pasta `docs`** inteira.
3. Clique em **Commit changes** (botão verde).

### Passo 4: crie a agenda diária
1. No repositório, clique em **Add file** → **Create new file**.
2. No campo do nome, digite exatamente: `.github/workflows/buscar-voos.yml`. As barras criam as pastas sozinhas.
3. Abra o arquivo `workflow-buscar-voos.yml` desta pasta com o Bloco de Notas (ou TextEdit), copie **todo** o conteúdo e cole na área de texto do GitHub.
4. Clique em **Commit changes** → **Commit changes**.

### Passo 5: guarde a chave da SerpApi no cofre do GitHub
1. No repositório, vá em **Settings** → no menu da esquerda **Secrets and variables** → **Actions**.
2. Clique em **New repository secret**.
3. *Name*: `SERPAPI_KEY` (exatamente assim). *Secret*: cole a chave do Passo 1.
4. Clique em **Add secret**.

### Passo 6: publique o painel
1. Em **Settings** → **Pages** (menu da esquerda).
2. Em *Source* escolha **Deploy from a branch**. Em *Branch* escolha **main** e a pasta **/docs**. Clique em **Save**.
3. Em 1 ou 2 minutos aparece o endereço do seu painel, no formato
   `https://SEU-USUARIO.github.io/agente-voos/`. Salve nos favoritos (no celular também).

### Passo 7: rode a primeira busca agora
1. Clique na aba **Actions** do repositório. Se aparecer um botão pedindo para habilitar os workflows, clique nele.
2. À esquerda, clique em **Buscar voos** → botão **Run workflow** → **Run workflow**.
3. Espere 1 a 3 minutos até aparecer o ✅ verde. Atualize o painel: os primeiros preços estarão lá.

A partir daí, ele roda sozinho todo dia.

---

## Como ajustar a busca (`config.json`)

No GitHub, clique em `config.json` → ícone de **lápis** (Edit) → altere → **Commit changes**.

```json
{
  "origem": "FOR",
  "destinos": "LIS,OPO,MAD",
  "datas_ida": ["2027-05-10", "2027-05-11", "2027-05-12"],
  "datas_volta": ["2027-05-25", "2027-05-26"],
  "dias_minimos": 14,
  "adultos": 1,
  "classe": 1,
  "paradas": 0,
  "moeda": "BRL",
  "preco_alvo": 3700
}
```

- **destinos**: códigos de aeroportos separados por vírgula. LIS = Lisboa, OPO = Porto, MAD = Madri, CDG = Paris, FCO = Roma, BCN = Barcelona. Cada busca considera todos ao mesmo tempo e traz o mais barato.
- **datas_ida / datas_volta**: o agente testa todas as combinações (ano-mês-dia), descartando as viagens mais curtas que `dias_minimos`. Com a configuração acima são **5 combinações por dia**, incluindo a sua de 11 a 25 de maio.
- **paradas**: 0 = qualquer número, 1 = só voo direto, 2 = no máximo 1 parada.
- **classe**: 1 = econômica, 2 = premium economy, 3 = executiva.
- **preco_alvo**: **ajuste este valor!** Está em R$ 3.700. Depois de uma semana de coletas, olhe a "faixa típica" que o Google mostra no painel e escolha um alvo realista. Quando o melhor preço ficar igual ou abaixo dele, o GitHub te manda um **e-mail** (e um aviso no app do GitHub). Você só é avisado de novo se o preço cair ainda mais.

---

## Custos

- **GitHub**: grátis.
- **SerpApi**: cada combinação de datas = 1 busca por dia. Com 5 combinações ≈ **150 buscas/mês**, dentro do plano gratuito (250/mês).
  - Cada combinação nova que você adicionar soma ~30 buscas/mês. Até 8 combinações ainda cabem no plano grátis.
  - Se quiser mais, o plano Starter da SerpApi custa US$ 25/mês e dá 1.000 buscas.

---

## Como ler o painel

- **Melhor preço agora**: o menor ida e volta da última coleta, com as datas e a companhia.
- **Desde a coleta anterior**: quanto subiu ou caiu desde ontem.
- **Avaliação do Google**: se o Google considera o preço Baixo, Típico ou Alto para a rota.
- **Evolução do preço**: o histórico que o seu agente vem montando. Use o seletor "Datas" para ver uma combinação específica.
- **Histórico do Google Flights**: os últimos ~60 dias registrados pelo próprio Google. Já é útil desde o primeiro dia.
- **Melhores ofertas agora**: tabela com o link "Abrir" para ir direto ao Google Flights e comprar.

> Os preços vêm do Google Flights e podem mudar a qualquer momento. Confirme sempre no site antes de comprar.

---

## Se algo der errado

- **Ícone ❌ vermelho na aba Actions**: clique na execução para ver a mensagem. Causas mais comuns:
  - "defina a variável SERPAPI_KEY": o segredo do Passo 5 está faltando ou com outro nome.
  - Erro 401 / "Invalid API key": a chave foi colada errada.
  - Erro ao fazer `git push`: em **Settings → Actions → General → Workflow permissions**, marque **Read and write permissions** e salve.
- **O painel não atualiza**: espere alguns minutos e recarregue a página (o GitHub Pages leva um tempinho).
- **E-mail do GitHub dizendo que o workflow foi desativado**: entre na aba Actions e clique em **Enable workflow**.
- **Quer pausar o agente**: aba Actions → Buscar voos → botão **···** → **Disable workflow**.
