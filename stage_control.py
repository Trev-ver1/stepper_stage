import serial
import time
import sys

# ── Hardware geometry — EDIT THESE TO MATCH YOUR SETUP ───────────────────────

STEPS_PER_REV = 200     # 1.8° motor = 200 full steps per revolution
MICROSTEPS    = 8       # Must match DM542T DIP switch setting
LEAD_PITCH_MM = 8.0     # mm of travel per motor revolution

# Derived — don't edit:
STEPS_PER_MM = (STEPS_PER_REV * MICROSTEPS) / LEAD_PITCH_MM

# ── Safety limits ─────────────────────────────────────────────────────────────

MAX_SPEED_MM_S = 50.0   # Hard ceiling on speed (mm/s)
DEFAULT_SPEED  = 10.0   # Speed when script starts (mm/s)

# ── Serial settings ───────────────────────────────────────────────────────────

BAUD_RATE    = 115200   # Must match Serial.begin() in firmware
CONNECT_WAIT = 2.0      # Seconds to wait for ESP32 to boot after connecting

def connect(port: str) -> serial.Serial:
    """Open the serial port and wait for the ESP32 READY message."""
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=5)
    except serial.SerialException as e:
        sys.exit(
            f"\n✗  Cannot open {port}: {e}\n"
            f"   Run:  ls /dev/ttyUSB*  to find your device.\n"
            f"   You may also need:  sudo usermod -aG dialout $USER\n"
        )
    print("  Waiting for ESP32...")
    time.sleep(2.0)
    ser.reset_input_buffer()
    ser.write(b"PING\n")
    response = ser.readline().decode(errors="replace").strip()
    if response != "READY":
        ser.close()
        sys.exit(f"✗  Expected 'READY' from ESP32, got: {response!r}")
    print(f"✓  Connected on {port}   ({STEPS_PER_MM:.2f} steps/mm)")
    return ser

def send(ser: serial.Serial, cmd: str) -> str:
    """Send a single command and return the response."""
    ser.write((cmd + "\n").encode())
    return ser.readline().decode(errors="replace").strip()


def move(ser: serial.Serial, distance_mm: float, speed_mm_s: float) -> None:
    """Convert mm to steps and command a move, blocking until complete."""
    steps         = round(distance_mm * STEPS_PER_MM)
    steps_per_sec = abs(speed_mm_s) * STEPS_PER_MM

    if steps == 0:
        print("  (no move — distance rounds to 0 steps)")
        return

    print(f"  {distance_mm:+.3f} mm  @  {speed_mm_s:.2f} mm/s"
          f"   [{steps:+d} steps  ×  {steps_per_sec:.0f} steps/s]")

    ser.write(f"MOVE {steps} {steps_per_sec:.1f}\n".encode())

    while True:
        resp = ser.readline().decode(errors="replace").strip()
        if resp == "DONE":
            break
        if resp == "STOPPED":
            print("  (motion stopped)")
            break
        if resp.startswith("ERROR"):
            print(f"  ESP32: {resp}")
            break
        if resp:
            print(f"  (ESP32: {resp})")

def show_help() -> None:
    print("""
  Commands:
    <mm>           Move ±mm in X   examples:  10    -5.5    +0.1
    s <speed>      Set speed (mm/s)            s 20    s 2.5
    stop           Decelerate to a halt
    zero           Set current position as origin
    status         Query ESP32 state
    config         Show geometry configuration
    help           Show this message
    q / quit       Exit
""")


def show_config() -> None:
    print(f"""
  Geometry:
    Motor steps/rev  {STEPS_PER_REV}
    Microsteps       {MICROSTEPS}×
    Lead pitch       {LEAD_PITCH_MM} mm/rev
    ──────────────────────────────────
    Steps / mm       {STEPS_PER_MM:.4f}
    Max speed        {MAX_SPEED_MM_S} mm/s
    Max step rate    {MAX_SPEED_MM_S * STEPS_PER_MM:.0f} steps/s
""")
    
def main() -> None:
    port  = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
    ser   = connect(port)
    speed = DEFAULT_SPEED

    print(f"  Speed: {speed} mm/s   |   type 'help' for commands\n")

    try:
        while True:
            try:
                raw = input("stage > ").strip()
            except EOFError:
                break

            if not raw:
                continue

            lo = raw.lower()

            if lo in ("q", "quit", "exit"):
                break

            elif lo == "help":
                show_help()

            elif lo == "config":
                show_config()

            elif lo == "stop":
                print(f"  {send(ser, 'STOP')}")

            elif lo == "zero":
                print(f"  {send(ser, 'ZERO')}")

            elif lo == "status":
                print(f"  {send(ser, 'STATUS')}")

            elif lo.startswith(("s ", "speed ")):
                parts = raw.split(maxsplit=1)
                try:
                    new_speed = float(parts[1])
                    if new_speed <= 0:
                        print("  Speed must be positive.")
                    else:
                        speed = min(new_speed, MAX_SPEED_MM_S)
                        if new_speed > MAX_SPEED_MM_S:
                            print(f"  Clamped to max {MAX_SPEED_MM_S} mm/s")
                        print(f"  Speed → {speed} mm/s")
                except (IndexError, ValueError):
                    print("  Usage:  s <value>   e.g.  s 10  or  s 0.5")

            else:
                try:
                    distance = float(raw)
                    move(ser, distance, speed)
                except ValueError:
                    print(f"  Unknown command: {raw!r}   (type 'help')")

    except KeyboardInterrupt:
        pass

    finally:
        try:
            send(ser, "STOP")
        except Exception:
            pass
        ser.close()
        print("\n  Disconnected.")


if __name__ == "__main__":
    main()