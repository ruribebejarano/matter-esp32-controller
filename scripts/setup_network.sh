#!/bin/bash
# Configura la red WSL para que chip-tool use la interfaz correcta
# Necesario ejecutar cada vez que se abre WSL

echo "[*] Configurando red para Matter..."

# Detectar interfaz con acceso a la red local
REAL_IF=$(ip route show default | awk '{print $5}' | head -1)

if [ "$REAL_IF" = "eth0" ]; then
    echo "[OK] eth0 ya es la interfaz correcta"
else
    echo "[*] Renombrando $REAL_IF -> eth0"
    sudo ip link set eth0 down 2>/dev/null
    sudo ip link set eth0 name eth0_bak 2>/dev/null
    sudo ip link set "$REAL_IF" name eth0 2>/dev/null
    sudo ip link set eth0 up 2>/dev/null
    echo "[OK] Interfaz configurada"
fi

# Verificar conectividad
echo "[*] IP de WSL: $(ip addr show eth0 | grep 'inet ' | awk '{print $2}')"
echo "[*] Ruta por defecto: $(ip route show default)"
