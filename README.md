# fanadapter

USB HID → Fanatec wheelbase adapter — on an STM32H743 — combined with a browser-based WebSerial configuration UI and a SimHub plugin.

An open-source adapter that lets arbitrary USB HID sim racing peripherals (H-pattern shifters, sequential shifters, handbrakes, and USB pedals — plus gamepads, D-pad/Hat controllers, and keyboards) connect to a Fanatec wheelbase as if they were native Fanatec gear. This is particularly valuable on game consoles (PS4/PS5/Xbox Series X|S) where third-party USB peripherals cannot be plugged directly into the console.

From the perspective of the wheelbase, the adapter looks like genuine Fanatec hardware (supporting a digital UART pedal stream and analog/digital shifter and handbrake signals).

---

## Architecture Block Diagram

```
USB H-pattern shifter ─┐
USB sequential shifter ┼──► [Powered USB Hub] ──► [STM32H743] ──► RJ12 ──► Fanatec Wheelbase
USB handbrake ─────────┤                                         RJ12        (up to 3 ports)
USB pedals ────────────┘                                         RJ12
```

Configure the adapter with the [live web configurator](https://gugic.github.io/fanadapter/) or the SimHub plugin. The browser also provides firmware updates over WebUSB/DFU.

---

## Compatibility

### Wheelbase Bases
* **Verified:** Fanatec ClubSport DD+ (15 Nm)
* **Expected to work** (same RJ12 protocols across generations, but untested here):
  * CSL Elite 1.1 / V2
  * Podium DD1 / DD2
  * ClubSport DD
  * CSL DD
  * CSW V2.5
* **Likely Incompatible:**
  * CSR Elite and older bases predating the current Shifter 1/2 RJ12 layout.
  * Bases without dedicated handbrake ports (Pre-DD generation may share the handbrake with the pedal port).

### USB Hubs (Important)
A **powered USB 2.0 hub** connects multiple peripherals to the STM32's USB host on **PB14/PB15**. Feed the hub's upstream VBUS from the board's 5 V rail so it detects the host. The on-board USB-C connects to the PC for power, configuration and firmware updates; it cannot host a hub.

If devices stop responding, replug the affected device at the hub. See the [STM32 troubleshooting guide](firmware-stm32/README.md#7-troubleshooting) for polling gaps and USB diagnostics.

---

## Repository Layout

The project is structured into four main directories:

1. **[`firmware-stm32/`](firmware-stm32/README.md)**
   Firmware for the **STM32H743** core board (WeAct MiniSTM32H743VITX), written in C with PlatformIO, STM32Cube HAL and TinyUSB. Hardware-validated on a real wheelbase, with DAC H-pattern outputs, sequential shifts, handbrake, pedal-port UART, PC direct output, DFU updates and USB diagnostics. The [protocol and calibration reference](firmware-stm32/PROTOCOL.md) documents its shared contracts with both clients.

2. **[`webconfig/`](webconfig/README.md)**
   A React 19 + TypeScript + Tailwind + shadcn/ui interface for desktop Chromium browsers. Captures bindings, calibrates axes, tests outputs, and updates firmware over WebUSB/DFU. [Open the configurator](https://gugic.github.io/fanadapter/).

3. **[`simhub-plugin/`](simhub-plugin/README.md)**
   A [SimHub](https://www.simhubdash.com/) plugin (C# / .NET Framework 4.8 / WPF). PC-attached controllers drive the wheelbase through direct-output commands; devices on the adapter's hub are configured through a mirror of webconfig. Includes firmware updates over WinUSB and live dashboard properties.

4. **[`schematics/`](schematics/README.md)**
   RJ12 pinouts, port protocols, wiring diagrams, a bill of materials, assembly instructions and multimeter checks for the STM32 hardware.

---

## Project Roadmap

The following features and improvements are planned for future updates:

* **Analog Pedal Fallback** — Supporting older bases predating CSL Elite V2 by implementing a 4-channel analog DAC output stage (MCP4728) on the pedal RJ12.
* **Software-Controlled Handbrake Detect** — Controlling Shifter 1 / Handbrake port detection via an STM32 GPIO rather than hardwired ground, allowing the adapter to show or hide ports dynamically.
* **Custom PCB Design** — A small, custom-routed KiCad PCB to replace the breadboard.
* **3D-Printed Enclosure** — A robust case with panel-mounted RJ12 jacks and a secure powered USB hub integration.
* **OLED Display & Buttons** — On-board configuration interface for status reports, calibration, and profile-switching without a computer.
* ~~**SimHub Integration**~~ — **Done:** the [`simhub-plugin/`](simhub-plugin/README.md) drives the same JSON protocol from SimHub, so a shifter or pedal set attached to the PC can command the wheelbase through the adapter, and the adapter's own mapping can be configured without leaving SimHub.
* **0-5V Handbrake Scaler** — Incorporating an op-amp scaling stage (MCP6001 with ~1.52 gain) for native 0-5V analog voltage swing.
* **Mode Switching on Shifter 1** — Software toggle between H-pattern and sequential modes on a single physical RJ12 port.
* **Built-in USB Hub** — Designing a USB hub circuit directly onto the project's custom PCB to ensure maximum stability and compatibility.

---

## References and Acknowledgments

This project relies on the incredible reverse-engineering efforts of the sim racing DIY community:

* **[Universal Shifter Interface for Fanatec Wheelbase](https://www.diy-sim.com/guides/projects/item/universal-fanatec-shifter-interface)** by DIY-Sim — H-pattern resistor ladder voltages and column/row maps.
* **[Fanashifter](https://github.com/juanmcasillas/Fanashifter)** by Juan M. Casillas — Sequential shifter RJ12 pinout and pull-up behaviors.
* **[Fanatec ClubSport Shifter SQ V1.5 USB Adapter DIY](https://hackaday.io/project/171155-fanatec-clubsport-shifter-sq-v15-usb-adapter-diy)** by Yin Zhong — Shifter protocol structures.
* **[Conversion of a Logitech Shifter for Fanatec Wheelbase Compatibility](https://www.gtplanet.net/forum/threads/conversion-of-a-logitech-shifter-for-fanatec-wheelbase-compatibility-enabling-7th-gear-other-mods.384099/)** by B-spec / Bob — 7th gear logic and mappings.
* **[Guide to convert third-party (Hall sensor) handbrake to Fanatec base compatible](https://www.oakheartcustombuilds.com/handleidingen/GuideThirdPartyHandbrakeToFanatec_v1.0.pdf)** by Oakheart Custom Builds — Handbrake signal and pinout references.
* **[fanatec-pedal-emulator](https://github.com/GeekyDeaks/fanatec-pedal-emulator)** by GeekyDeaks — UART framing, CSL Elite V2 emulation state machines, and CRC-8 tables.

---

## License

`fanadapter` is **dual-licensed**, and both licenses are deliberately permissive: the software (firmware + webconfig) under **Apache 2.0**, the hardware design under **CERN-OHL-P v2**. They were chosen to make building on, modifying, and *commercializing* this project as frictionless as possible — attribution is the only obligation and no copyleft applies. Full terms, SPDX identifiers, and the build-from-scratch provenance note are in **[LICENSE.md](LICENSE.md)**.

### Manufacturing and commercial reuse — explicitly welcome

If you have the capacity to turn this into a polished product — a small enclosed unit with an integrated powered USB hub, panel-mount RJ12 jacks, a clean PCB instead of the breadboard build, proper EMI considerations, and decent QC — **please do**. The permissive licenses are chosen precisely to make this easy.

The sim racing community has a real gap for affordable, well-built USB-HID-to-Fanatec adapters. The few existing commercial products are either expensive, awkward to use, or limited to specific peripheral brands. A polished version of this design — even at a reasonable markup for the work involved — would be a genuinely useful product.

If you take this to market, attribution to this repository and the prior reverse-engineering work cited in [References and Acknowledgments](#references-and-acknowledgments) is the only ask. Pull requests improving the design upstream are appreciated but not required.

---

**Maintainer:** [Gugic](https://github.com/Gugic)  
**Issues / contributions welcome:** [https://github.com/Gugic/fanadapter/issues](https://github.com/Gugic/fanadapter/issues)
