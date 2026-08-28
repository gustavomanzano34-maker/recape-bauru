#!/bin/bash
# Regenera o traçado das ruas do site a partir dos arquivos KMZ.
# Use depois de adicionar/alterar ruas no "RECAPE PM BAURU.kmz".
cd "$(dirname "$0")"
echo "======================================================"
echo "  Atualizando o mapa a partir dos KMZ..."
echo "======================================================"
python3 gerar_mapa.py
echo ""
echo "Pronto. Pode fechar esta janela."
echo "No site, clique em  ↻ Atualizar  para ver as mudanças."
read -n 1 -s -r -p "Pressione qualquer tecla para sair..."
