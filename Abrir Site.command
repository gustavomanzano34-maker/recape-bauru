#!/bin/bash
# Abre o Painel de Obras Recape Bauru no navegador.
# Basta dar 2 cliques neste arquivo.
cd "$(dirname "$0")"

PORT=""
for p in 8137 8138 8139 8080 8000; do
  if ! lsof -i :$p >/dev/null 2>&1; then PORT=$p; break; fi
done
[ -z "$PORT" ] && PORT=8137

echo "======================================================"
echo "  Painel de Obras - Recape Bauru"
echo "  Site rodando em: http://localhost:$PORT"
echo "  >> NAO feche esta janela enquanto estiver usando <<"
echo "  Para encerrar: feche esta janela (Cmd+Q)."
echo "======================================================"

python3 -m http.server $PORT >/dev/null 2>&1 &
SERVER=$!
sleep 1
open "http://localhost:$PORT/index.html"
wait $SERVER
