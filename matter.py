import subprocess
import threading
import queue
import re
import time
import schedule
from datetime import datetime


CHIP_TOOL = "chip-tool"
NODE_ID   = 1
ENDPOINT  = 1


class MatterController:
    """
    Mantiene chip-tool en modo interactivo para reutilizar
    la sesión CASE y evitar el handshake en cada comando.
    """

    def __init__(self):
        self._proc       = None
        self._lock       = threading.Lock()
        self._output_q   = queue.Queue()
        self._reader     = None
        self._start()

    # ── Ciclo de vida ─────────────────────────────────────────

    def _start(self):
        print("[Matter] Iniciando chip-tool interactivo...")
        self._proc = subprocess.Popen(
            [CHIP_TOOL, "interactive", "start"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self._reader = threading.Thread(target=self._read_output, daemon=True)
        self._reader.start()
        time.sleep(2)          # esperar que el stack Matter arranque
        print("[Matter] Listo.")

    def _read_output(self):
        for line in self._proc.stdout:
            self._output_q.put(line.rstrip())

    def _restart(self):
        print("[Matter] Reiniciando chip-tool...")
        try:
            self._proc.terminate()
            self._proc.wait(timeout=3)
        except Exception:
            pass
        self._start()

    def close(self):
        if self._proc:
            self._proc.terminate()

    # ── Envío de comandos ─────────────────────────────────────

    def send(self, command: str, timeout: float = 8.0) -> tuple[bool, str]:
        """Envía un comando al shell interactivo y espera la respuesta."""
        with self._lock:
            if self._proc.poll() is not None:
                self._restart()

            # Vaciar cola antes de enviar
            while not self._output_q.empty():
                self._output_q.get_nowait()

            ts = datetime.now().strftime("%H:%M:%S")
            print(f"[{ts}] >> {command}")

            self._proc.stdin.write(command + "\n")
            self._proc.stdin.flush()

            return self._wait_response(timeout)

    def _wait_response(self, timeout: float) -> tuple[bool, str]:
        """Acumula líneas hasta detectar éxito o error."""
        lines   = []
        deadline = time.time() + timeout

        while time.time() < deadline:
            try:
                line = self._output_q.get(timeout=0.2)
                lines.append(line)

                if any(k in line for k in ("CHIP Error", "Run command failure")):
                    return False, "\n".join(lines)

                # Éxito detectado
                if any(k in line for k in (
                    "Attribute Value", "OnOff", "CommandSuccessResponse",
                    "DefaultSuccess", "Received Command Response",
                )):
                    time.sleep(0.1)   # drenar líneas restantes
                    while not self._output_q.empty():
                        lines.append(self._output_q.get_nowait())
                    return True, "\n".join(lines)

            except queue.Empty:
                continue

        return False, "\n".join(lines)


# ── Instancia global ──────────────────────────────────────────

_ctrl: MatterController | None = None

def get_controller() -> MatterController:
    global _ctrl
    if _ctrl is None:
        _ctrl = MatterController()
    return _ctrl


# ── Comandos de luz ───────────────────────────────────────────

def luz_encender():
    ok, _ = get_controller().send(f"onoff on {NODE_ID} {ENDPOINT}")
    print("✅ ON" if ok else "❌ Error encendiendo")
    return ok

def luz_apagar():
    ok, _ = get_controller().send(f"onoff off {NODE_ID} {ENDPOINT}")
    print("✅ OFF" if ok else "❌ Error apagando")
    return ok

def luz_toggle():
    ok, _ = get_controller().send(f"onoff toggle {NODE_ID} {ENDPOINT}")
    print("✅ Toggle" if ok else "❌ Error en toggle")
    return ok

def luz_estado() -> bool | None:
    ok, out = get_controller().send(f"onoff read on-off {NODE_ID} {ENDPOINT}")
    if ok:
        match = re.search(r"value:\s*(TRUE|FALSE|true|false|1|0)", out, re.IGNORECASE)
        if match:
            estado = match.group(1).lower() in ("true", "1")
            print(f"💡 Estado: {'ON' if estado else 'OFF'}")
            return estado
    print("❌ No se pudo leer estado")
    return None


# ── Automatizaciones ─────────────────────────────────────────

def parpadear(veces: int = 5, intervalo: float = 0.3):
    """Parpadeo rápido — se nota la diferencia con modo interactivo."""
    print(f"🔦 Parpadeando {veces} veces (intervalo {intervalo}s)...")
    for i in range(veces):
        luz_encender()
        time.sleep(intervalo)
        luz_apagar()
        time.sleep(intervalo)
    print("✅ Parpadeo terminado")

def encender_si_apagada():
    if not luz_estado():
        luz_encender()

def apagar_si_encendida():
    if luz_estado():
        luz_apagar()


# ── Scheduler ────────────────────────────────────────────────

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


# ── Menú ─────────────────────────────────────────────────────

def menu():
    iniciar_scheduler()

    opciones = {
        "1": ("Encender",              luz_encender),
        "2": ("Apagar",                luz_apagar),
        "3": ("Toggle",                luz_toggle),
        "4": ("Ver estado",            luz_estado),
        "5": ("Parpadear 5 veces",     lambda: parpadear(5, 0.3)),
        "6": ("Parpadear rápido x10",  lambda: parpadear(10, 0.1)),
        "0": ("Salir",                 None),
    }

    while True:
        print("\n" + "="*32)
        print("   Matter Light Controller v2")
        print("="*32)
        for k, (desc, _) in opciones.items():
            print(f"  {k}) {desc}")

        eleccion = input("\nOpción: ").strip()

        if eleccion == "0":
            get_controller().close()
            break
        elif eleccion in opciones:
            opciones[eleccion][1]()
        else:
            print("Opción inválida")


if __name__ == "__main__":
    menu()
