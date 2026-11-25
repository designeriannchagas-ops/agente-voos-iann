"""
Gera o painel web (docs/index.html) a partir de dados/historico.json.
O GitHub Pages publica a pasta docs/ automaticamente.
"""

import json
from pathlib import Path

RAIZ = Path(__file__).parent
HISTORICO = RAIZ / "dados" / "historico.json"
SAIDA = RAIZ / "docs" / "index.html"
MODELO = RAIZ / "painel_modelo.html"


def main():
    historico = json.loads(HISTORICO.read_text(encoding="utf-8")) if HISTORICO.exists() else {"coletas": []}
    dados = json.dumps(historico, ensure_ascii=False).replace("</", "<\\/")
    html = MODELO.read_text(encoding="utf-8").replace("/*__DADOS__*/null", dados)
    SAIDA.parent.mkdir(exist_ok=True)
    SAIDA.write_text(html, encoding="utf-8")
    print(f"Painel gerado em {SAIDA}")


if __name__ == "__main__":
    main()
