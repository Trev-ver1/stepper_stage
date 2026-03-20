# Stepper Stage Reference

## Hardware
- ESP32 DevKit → DM542T → Stepper motor (4-wire bipolar, ~4Ω/coil)
- Power supply: 24V, 1.25A current limit

## Wiring (common cathode)
- PUL+ → GPIO 27
- PUL− → GND
- DIR+ → GPIO 14
- DIR− → GND
- ENA− → GND
- A+ → Red, A− → Blue, B+ → Black, B− → Green

## DM542T DIP switches
- SW1 ON, SW2 ON, SW3 ON → 1.00A peak current
- SW4 ON → half current at standstill
- SW5 OFF, SW6 OFF, SW7 ON, SW8 ON → 16× microsteps (3200 steps/rev)

## Software
- Firmware: PlatformIO, Arduino framework, AccelStepper
- Project: ~/code/projects/work/stepper_stage
- Run: source .venv/bin/activate → python3 stage_control.py /dev/ttyUSB0

## Calibration (TODO)
- STEPS_PER_REV = 200
- MICROSTEPS = 16
- LEAD_PITCH_MM = 8.0 ← needs verification with calipers

## Commands
- <mm>             Move ±mm
- set_speed <val>  Set speed (mm/s)
- speed            Show current speed
- stop             Emergency stop
- zero             Set home position
- status           Query ESP32 state
- config           Show geometry config
- q                Quit
