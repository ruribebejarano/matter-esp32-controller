import subprocess
import re
import time
import schedule
import threading
from datetime import datetime

CHIP_TOOL = "chip-tool"
NODE_ID = 1
ENDPOINT_ID = 1

def run_chip_tool(*args, timeout=20):
    cmd = [CHIP_TOOL] + list(args)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] >> {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        output = result.stdout + result.stderr
        success = result.returncode in (0, 1) and "CHIP Error" not in output
        return success, output
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)

def luz_encender():
    ok, _ = run_chip_tool("onoff", "on", str(NODE_ID), str(ENDPOINT_ID))
    print("✅ ON" if ok else "❌ Error encendiendo")
    return ok

def luz_apagar():
    ok, _ = run_chip_tool("onoff", "off", str(NODE_ID), str(ENDPOINT_ID))
    print("✅ OFF" if ok else "❌ Error apagando")
    return ok

def luz_toggle():
    ok, _ = run_chip_tool("onoff", "toggle", str(NODE_ID), str(ENDPOINT_ID))
    print("✅ Toggle" if ok else "❌ Error en toggle")
    return ok

def luz_estado():
    ok, out = run_chip_tool("onoff", "read", "on-off", str(NODE_ID), str(ENDPOINT_ID))
    if ok:
        match = re.search(r"OnOff.*?value:\s*(TRUE|FALSE|true|false|1|0)", out, re.IGNORECASE)
        if match:
            estado = match.group(1).lower() in ("true", "1")
            print(f"💡 Estado: {'ON' if estado else 'OFF'}")
            return estado
    print("❌ No se pudo leer estado")
    return None

def parpadear(veces=3, intervalo=0.5):
    print(f"🔦 Parpadeando {veces} veces...")
    for _ in range(veces):
        luz_encender(); time.sleep(intervalo)
        luz_apagar();   time.sleep(intervalo)

def encender_si_apagada():
    estado = luz_estado()
    if not estado:
        luz_encender()

def iniciar_scheduler():
    schedule.every().day.at("07:00").do(luz_encender)
    schedule.every().day.at("23:00").do(luz_apagar)
    schedule.every().day.at("18:30").do(encender_si_apagada)
    print("\n📅 Scheduler activo:")
    for job in schedule.jobs:
        print(f"   {job}")
    def loop():
        while True:
            schedule.run_pending()
            time.sleep(1)
    threading.Thread(target=loop, daemon=True).start()
    print("⏰ Scheduler corriendo en segundo plano\n")

def menu():
    iniciar_scheduler()
    opciones = {
        "1": ("Encender",          luz_encender),
        "2": ("Apagar",            luz_apagar),
        "3": ("Toggle",            luz_toggle),
        "4": ("Ver estado",        luz_estado),
        "5": ("Parpadear 3 veces", lambda: parpadear(3, 0.5)),
        "0": ("Salir",             None),
    }
    while True:
        print("\n" + "="*30)
        print("   Matter Light Controller")
        print("="*30)
        for k, (desc, _) in opciones.items():
            print(f"  {k}) {desc}")
        eleccion = input("\nOpción: ").strip()
        if eleccion == "0":
            break
        elif eleccion in opciones:
            opciones[eleccion][1]()

if __name__ == "__main__":
    menu()
