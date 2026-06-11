#!/bin/bash
# Comisiona el ESP32 con chip-tool
# Uso: ./commission.sh [passcode] [discriminator] [node_id]

PASSCODE=${1:-20202021}
DISCRIMINATOR=${2:-3840}
NODE_ID=${3:-1}

echo "[*] Limpiando estado previo de chip-tool..."
rm -rf /tmp/chip_tool_kvs /tmp/chip_factory.ini \
       /tmp/chip_config.ini /tmp/chip_counters.ini

echo "[*] Comisionando ESP32..."
echo "    Passcode:      $PASSCODE"
echo "    Discriminator: $DISCRIMINATOR"
echo "    Node ID:       $NODE_ID"
echo ""

chip-tool pairing onnetwork-long "$NODE_ID" "$PASSCODE" "$DISCRIMINATOR" \
    --bypass-attestation-verifier 1

if [ $? -eq 0 ]; then
    echo ""
    echo "[OK] Commissioning exitoso. Node ID: $NODE_ID"
else
    echo ""
    echo "[ERROR] Commissioning falló. Verifica:"
    echo "  1. ESP32 en modo commissioning (LED parpadeando)"
    echo "  2. Red configurada: ./setup_network.sh"
    echo "  3. Misma subred que el ESP32"
fi
