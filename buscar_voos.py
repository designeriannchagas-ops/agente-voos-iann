"""
Agente de voos: pesquisa o Google Flights (via SerpApi) para todas as
combinações de datas do config.json e grava o resultado em dados/historico.json.

Uso (normalmente roda sozinho no GitHub Actions):
    SERPAPI_KEY=xxxx python buscar_voos.py

Não precisa instalar nada além do Python 3.
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from itertools import product
from pathlib import Path

RAIZ = Path(__file__).parent
CONFIG = RAIZ / "config.json"
HISTORICO = RAIZ / "dados" / "historico.json"
ALERTA = RAIZ / "alerta.md"
API_URL = "https://serpapi.com/search.json"
MAX_OFERTAS = 5  # quantas ofertas guardar por combinação de datas


def carregar_json(caminho, padrao):
    if caminho.exists():
        return json.loads(caminho.read_text(encoding="utf-8"))
    return padrao


def combinacoes_de_datas(cfg):
    """Todas as combinações ida x volta que respeitam a duração mínima."""
    combos = []
    for ida, volta in product(cfg["datas_ida"], cfg["datas_volta"]):
        dias = (date.fromisoformat(volta) - date.fromisoformat(ida)).days
        if dias >= cfg.get("dias_minimos", 1):
            combos.append((ida, volta, dias))
    return combos


def consultar_google_flights(cfg, ida, volta, chave):
    params = {
        "engine": "google_flights",
        "departure_id": cfg["origem"],
        "arrival_id": cfg["destinos"],
        "outbound_date": ida,
        "return_date": volta,
        "type": 1,  # ida e volta
        "adults": cfg.get("adultos", 1),
        "travel_class": cfg.get("classe", 1),
        "stops": cfg.get("paradas", 0),
        "currency": cfg.get("moeda", "BRL"),
        "hl": "pt-br",
        "gl": "br",
        "api_key": chave,
    }

    # Modo de teste: lê respostas salvas em disco em vez de chamar a API.
    pasta_mock = os.environ.get("MOCK_DIR")
    if pasta_mock:
        arquivo = Path(pasta_mock) / f"{ida}_{volta}.json"
        return json.loads(arquivo.read_text(encoding="utf-8"))

    url = API_URL + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def link_google_flights(cfg, ida, volta, resposta):
    url = resposta.get("search_metadata", {}).get("google_flights_url")
    if url:
        return url
    q = f"Voos de {cfg['origem']} para {cfg['destinos']} em {ida} volta {volta}"
    return "https://www.google.com/travel/flights?hl=pt-BR&curr=BRL&q=" + urllib.parse.quote(q)


def resumir_oferta(itin):
    trechos = itin.get("flights", [])
    if not trechos:
        return None
    companhias = []
    for t in trechos:
        if t.get("airline") and t["airline"] not in companhias:
            companhias.append(t["airline"])
    return {
        "preco": itin.get("price"),
        "companhias": companhias,
        "paradas": len(itin.get("layovers", [])),
        "escalas": [l.get("id") or l.get("name") for l in itin.get("layovers", [])],
        "duracao_min": itin.get("total_duration"),
        "partida": trechos[0]["departure_airport"].get("time"),
        "chegada": trechos[-1]["arrival_airport"].get("time"),
        "destino": trechos[-1]["arrival_airport"].get("id"),
        "voos": [t.get("flight_number") for t in trechos],
    }


def processar(cfg, ida, volta, dias, resposta):
    if resposta.get("error"):
        return {"ida": ida, "volta": volta, "dias": dias, "erro": resposta["error"]}

    itinerarios = resposta.get("best_flights", []) + resposta.get("other_flights", [])
    ofertas = [o for o in (resumir_oferta(i) for i in itinerarios) if o and o["preco"]]
    ofertas.sort(key=lambda o: o["preco"])

    insights = resposta.get("price_insights", {})
    return {
        "ida": ida,
        "volta": volta,
        "dias": dias,
        "menor_preco": ofertas[0]["preco"] if ofertas else insights.get("lowest_price"),
        "nivel_preco": insights.get("price_level"),
        "faixa_tipica": insights.get("typical_price_range"),
        "historico_google": insights.get("price_history", []),
        "ofertas": ofertas[:MAX_OFERTAS],
        "link": link_google_flights(cfg, ida, volta, resposta),
    }


def reais(v):
    return "R$ " + f"{v:,.0f}".replace(",", ".")


def data_br(iso):
    a, m, d = iso.split("-")
    return f"{d}/{m}/{a}"


def verificar_alerta(cfg, historico, coleta):
    """Cria alerta.md quando aparece um preço abaixo do alvo e menor que o último alerta."""
    validos = [r for r in coleta["resultados"] if r.get("menor_preco")]
    if not validos:
        return
    melhor = min(validos, key=lambda r: r["menor_preco"])
    alvo = cfg.get("preco_alvo")
    ultimo = historico.get("ultimo_alerta_preco")
    if alvo and melhor["menor_preco"] <= alvo and (ultimo is None or melhor["menor_preco"] < ultimo):
        historico["ultimo_alerta_preco"] = melhor["menor_preco"]
        o = melhor["ofertas"][0] if melhor["ofertas"] else {}
        ALERTA.write_text(
            f"Preço abaixo do seu alvo de {reais(alvo)}!\n\n"
            f"- **Preço:** {reais(melhor['menor_preco'])} (ida e volta, 1 adulto)\n"
            f"- **Datas:** {data_br(melhor['ida'])} a {data_br(melhor['volta'])} ({melhor['dias']} dias)\n"
            f"- **Companhia(s):** {', '.join(o.get('companhias', [])) or '-'}\n"
            f"- **Destino:** {o.get('destino', '-')}, paradas: {o.get('paradas', '-')}\n\n"
            f"[Ver no Google Flights]({melhor['link']})\n",
            encoding="utf-8",
        )
        print(f"ALERTA: R$ {melhor['menor_preco']} <= alvo R$ {alvo}")


def main():
    cfg = carregar_json(CONFIG, None)
    chave = os.environ.get("SERPAPI_KEY", "")
    if not chave and not os.environ.get("MOCK_DIR"):
        sys.exit("Erro: defina a variável SERPAPI_KEY com sua chave da SerpApi.")

    historico = carregar_json(HISTORICO, {"coletas": []})
    coleta = {"quando": datetime.now(timezone.utc).isoformat(timespec="seconds"), "resultados": []}

    for ida, volta, dias in combinacoes_de_datas(cfg):
        try:
            resposta = consultar_google_flights(cfg, ida, volta, chave)
            resultado = processar(cfg, ida, volta, dias, resposta)
        except Exception as e:  # uma data com problema não derruba as outras
            resultado = {"ida": ida, "volta": volta, "dias": dias, "erro": str(e)}
        coleta["resultados"].append(resultado)
        print(f"{ida} -> {volta}: {resultado.get('menor_preco', resultado.get('erro'))}")

    if not any(r.get("menor_preco") for r in coleta["resultados"]):
        print("Nenhum preço encontrado nesta coleta; histórico não alterado.")
        sys.exit(1)

    # Guarda o histórico do Google só na coleta mais recente (economiza espaço).
    for c in historico["coletas"]:
        for r in c["resultados"]:
            r.pop("historico_google", None)
    historico["coletas"].append(coleta)
    historico["config"] = cfg
    verificar_alerta(cfg, historico, coleta)

    HISTORICO.parent.mkdir(exist_ok=True)
    HISTORICO.write_text(json.dumps(historico, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Histórico salvo: {len(historico['coletas'])} coletas.")


if __name__ == "__main__":
    main()
