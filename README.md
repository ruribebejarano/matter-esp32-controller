# Matter Light Controller — ESP32 + WSL + Python

Control de una luz ESP32 Matter desde Python usando chip-tool en WSL.

## Requisitos

- Windows 10/11 con WSL2 Ubuntu
- ESP32 con firmware `esp-matter` (on_off_light)
- chip-tool compilado en WSL
- Python 3.8+

## Instalación rápida

### 1. Clonar el repositorio
```bash
git clone <url_del_repo>
cd matter_automation
```

### 2. Instalar dependencias Python
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Compilar chip-tool (solo primera vez)
```bash
cd ~/esp/esp-matter/connectedhomeip/connectedhomeip
source scripts/activate.sh
ninja -C out/linux-x64-chip-tool chip-tool -j2
```

### 4. Parche WSL obligatorio (solo primera vez)
chip-tool ignora interfaces que no sean WiFi. Aplicar este parche:

```bash
FILE=~/esp/esp-matter/connectedhomeip/connectedhomeip/src/platform/Linux/PlatformManagerImpl.cpp

# Backup
cp $FILE $FILE.bak

# Parche
sed -i 's|const char \* wifiIfName = ConnectivityMgrImpl().GetWiFiIfName();|const char * wifiIfName = "eth0"; // WSL patch|' $FILE

# Recompilar
cd ~/esp/esp-matter/connectedhomeip/connectedhomeip
ninja -C out/linux-x64-chip-tool chip-tool -j2
```

### 5. Configurar red WSL
```bash
# Ejecutar cada vez que abres WSL
./scripts/setup_network.sh
```

### 6. Comisionar el ESP32
```bash
# Asegúrate que el ESP32 esté en modo commissioning
./scripts/commission.sh
# O con parámetros personalizados:
./scripts/commission.sh 20202021 3840 1
```

### 7. Ejecutar el controlador
```bash
source venv/bin/activate
python3 matter.py
```

## Uso
## Automatizaciones programadas

Editá `matter.py` en la función `iniciar_scheduler()`:

```python
schedule.every().day.at("07:00").do(luz_encender)   # Encender a las 7am
schedule.every().day.at("23:00").do(luz_apagar)      # Apagar a las 11pm
schedule.every().day.at("18:30").do(encender_si_apagada)
```

## Arquitectura
WSL (Ubuntu)
├── Python (matter.py)
│   └── subprocess → chip-tool
│                       └── Matter over WiFi
│                               └── ESP32 (GPIO 2 = LED)
└── scripts/
├── setup_network.sh   ← fix interfaz eth0
└── commission.sh      ← pairing inicial
## Solución de problemas

| Problema | Solución |
|---|---|
| `mDNS timeout` | Ejecutar `setup_network.sh` |
| `Ignoring IP update` | Aplicar parche PlatformManagerImpl.cpp |
| ESP32 no responde | Verificar WiFi estable, reiniciar ESP32 |
| chip-tool no encontrado | Agregar al PATH: `export PATH=$PATH:~/esp/esp-matter/connectedhomeip/connectedhomeip/out/linux-x64-chip-tool` |

## Firmware ESP32

El firmware usado está en `firmware/`. Basado en el ejemplo
`esp-matter/examples/light` con estas modificaciones:
- Multi-Admin habilitado (Alexa + chip-tool)
- LED en GPIO 2
- WiFi Power Save deshabilitado

## Valores por defecto del firmware

| Parámetro | Valor |
|---|---|
| Passcode | 20202021 |
| Discriminator | 3840 |
| Node ID asignado | 1 |
| Endpoint luz | 1 |
| GPIO LED | 2 |
