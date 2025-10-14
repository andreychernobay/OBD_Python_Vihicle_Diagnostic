# OBD_Python_Vihicle_Diagnostic

Python based utilities for interacting with an OBD-II adapter. The current
command line interface supports:

- Checking Diagnostic Trouble Codes (DTCs)
- Clearing stored DTCs
- Reading live sensor data from all available Mode 1 and Mode 2 commands

## Requirements

- Python 3.8 or newer
- [`python-obd`](https://github.com/brendan-w/python-OBD) package
- An ELM327-compatible OBD-II adapter connected to your computer

Install the dependency with:

```bash
pip install python-obd
```

## Usage

The `obd_diagnostic.py` script provides a CLI for the supported actions. The
adapter port is detected automatically when possible, but you can override it
with the `--port` argument.

## How the tool connects to your vehicle

The diagnostic flow relies on a **vehicle communication interface (VCI)** that
speaks the ELM327 command set. The high-level architecture looks like this:

```
┌──────────────────────┐      ┌─────────────────────────────┐      ┌─────────────────────────────┐
│  Vehicle ECUs (CAN,  │ CAN  │   OBD-II 16-pin connector    │ ELM  │  ELM327-compatible adapter  │ USB/Bluetooth/Wi-Fi
│   ISO9141, J1850…)   │◀────▶│   (SAE J1962 female socket)  │◀────▶│  (VCI / OBD-II dongle)      │◀────────────────────┐
└──────────────────────┘      └─────────────────────────────┘      └─────────────────────────────┘                     │
                                                                                                        Serial port / IP │
                                                                                                                         ▼
                                                                                                ┌───────────────────────────┐
                                                                                                │ Host computer running the │
                                                                                                │ `obd_diagnostic.py` CLI   │
                                                                                                └───────────┬───────────────┘
                                                                                                            │
                                                                                                            ▼
                                                                                               `python-obd` library & CLI
```

Any adapter that presents itself as an ELM327-style interface is supported,
including common USB sticks, Bluetooth LE dongles, and Wi-Fi bridges. Popular
choices include the OBDLink CX/MX+, Veepeak BLE/BLE+, and budget ELM327 USB
interfaces. When connected, the operating system exposes a serial or network
port (e.g., `/dev/ttyUSB0`, `COM3`, or an IP address) that you provide to the
CLI.

### Connecting over Bluetooth

Bluetooth adapters work exactly the same as wired ones from the CLI's
perspective—the key difference is pairing the dongle with your computer ahead
of time so the OS exposes a virtual serial port:

1. Put the adapter in pairing mode (often by plugging it into the vehicle).
2. Pair it with your computer using the system Bluetooth settings.
3. Identify the virtual serial port that was created. Common defaults are
   `/dev/rfcomm0` on Linux, a new `COM` port on Windows (visible in Device
   Manager), or `/dev/tty.*` entries on macOS.
4. Use that port with the CLI, for example:

   ```bash
   python obd_diagnostic.py live --port /dev/rfcomm0
   ```

`python-obd` handles the protocol negotiation once the port is open, so no
extra Bluetooth-specific configuration is needed within the script.

If your adapter requires a custom baud rate or pairing step, complete that at
the OS level first and then re-run the CLI with the detected port. The
`python-obd` library automatically negotiates the protocol (CAN, ISO9141-2,
SAE J1850, etc.) through the VCI so no additional configuration is necessary in
the script.

### Check DTCs

```bash
python obd_diagnostic.py check --port /dev/ttyUSB0
```

### Clear DTCs

```bash
python obd_diagnostic.py erase --port /dev/ttyUSB0
```

### Read live data

```bash
python obd_diagnostic.py live --port /dev/ttyUSB0 --interval 2 --iterations 5
```

- `--interval` controls how often the sensor values are refreshed.
- `--iterations` can be set to `0` for continuous streaming until interrupted.

