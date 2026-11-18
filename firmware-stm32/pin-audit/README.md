# Maintaining the STM32 / WeAct pin audit

[PIN-AUDIT.md](../PIN-AUDIT.md) answers both directions: firmware function to probe
location, and numbered WeAct header contact to MCU/board/firmware use. This is a
documentation snapshot of upstream `8c48cfe422bae50b96b04b9c8de813d434e0bd54`, not
a generated firmware configuration or a proposed reassignment.

## Maintained data and scope

JSON is the maintained source. Edit these files, then regenerate the Markdown:

| File | Authority / purpose |
| --- | --- |
| `audit.json` | Dataset filenames, physical scope, bench conditions/tested-build provenance, earlier functional observations and pending V0 routing |
| `mcu.json` | ST CubeMX package/capability snapshot: 100 LQFP100 contacts, 82 logical GPIO identities, possible signals/AFs and special-pad restrictions |
| `weact-v1.2.json` | Revision-pinned WeAct drawing evidence: all 92 P1/P2/P3 contacts, rear silkscreen, onboard nets, bridges/connectors and observations attached to the specific measured segments |
| `breadboard-v1.json` | Named current wiring profile: 19 explicit application GPIO assignments plus PH0/PH1 HSE, non-GPIO roles, source ranges/hashes and scoped normal-heartbeat/reset observations |

`breadboard-v1` is a stable profile identity. Keep its history in Git; a future V0
decision can update the audit alongside the corresponding schematic and firmware.
This audit does not introduce a second firmware profile or build. Every planned
V0 routing cell remains pending; PC8 explicitly awaits a handbrake pin decision.

The join key is the logical STM32 GPIO name, **not** a header position or a
silkscreen abbreviation. `(header, pin)` uniquely identifies a physical contact.
Non-GPIO contacts have a null GPIO and explicit kind, net and MCU package-contact
references. The 5 V board rail is not a direct MCU supply pin. Preserve `PC2_C` and
`PC3_C` as physical package names even though the logical keys are PC2/PC3: their
internal analog switches matter when evaluating a new use.

P1 and P2 each have 44 contacts; P3 has four SWD contacts. Camera/TFT FPC connectors,
USB-C, microSD, buttons and other onboard connections are not additional numbered
expansion headers. They remain explicit connection targets in the board JSON.
The generated guide's [physical orientation](../PIN-AUDIT.md#physical-orientation)
identifies each header, pin 1 and the odd/even columns from either face, always
with USB-C at the bottom. Page 1 of the board PDF has hidden Altium pad identifiers,
not visible printed numbers: use the PDF viewer's exact text search for `PAP101`
(P1 pin 1), `PAP1030` (P1 pin 30), or `PAP301` (P3 pin 1). Square shape alone is
ambiguous because P2 pin 44 and P3 pin 4 are also square pads.

Keep the six offset rear labels: `G 5V` at P1 pins 1/2, `G 3V3` at P2 pins 1/2,
and `B13 B12` at P1 pins 43/44, read left to right from the rear. Matching white
dots connect each header row to its inboard legend. The JSON and generated guide
cite the rear drawing for markings and the schematic for their electrical nets.

The first module's **1.2** marking was observed by its owner under the LCD, right
of the ribbon slot. The owner identifies both modules as V1.2 and visually reports
SB3 alone appearing bridged on both; SB1, SB2, SB4, SB5 and SB6 appear open.
The guided bench review subsequently confirmed Board A's SB3 closure and C8-to-MCU
continuity. Board B's bridge evidence remains visual. The observations below and
their limits are retained in the maintained JSON. The legacy carrier's F1
protection is still uncorrected in hardware and design.

## Guided bench evidence (17 November 2026)

The owner used a **Rigol MHO984** and **Fluke 115**, primarily with a bare WeAct
module connected to macOS over USB-C. The tested upstream firmware was **v0.6.2**,
reference build [`6faeb9e`](https://github.com/Gugic/fanadapter/commit/6faeb9ee03a28f27387533552000376cd07580bb).
The audited source baseline remains `8c48cfe`; the
[intervening changes](https://github.com/Gugic/fanadapter/compare/6faeb9ee03a28f27387533552000376cd07580bb...8c48cfe422bae50b96b04b9c8de813d434e0bd54)
affected only the SimHub plugin. These are owner-reported measurements, not a new
test of every contact or onboard branch.

| Contact or function | Bench result and its scope |
| --- | --- |
| **PC8 / P1:30 (`C8`)** | Board A measured approximately **0.1 Ω** from the header to MCU pad 65. Only that segment has measured continuity. The separate R26-to-microSD D0 path remains schematic evidence; readings at an unidentified resistor location do not verify R26. |
| **PD13 / P1:35 (`D13`)** | Board A read **9.29 MΩ** to presumed pad 60 with uncertain probe contact. This is inconclusive, not evidence of an open trace. The header mapping and R30-to-QSPI IO3 path remain drawing evidence. |
| **PD6 / P1:13 (`D6`) / SB3** | Board A: shorted leads **0.1 Ω**, SB3 pad-to-pad **0.2 Ω**, and D6 to the probed SB3 pad **0.3 Ω**. SB3 is electrically closed on Board A and D6 reaches it. Board B's closure is visually observed only. Fitted part identity/value and the remainder of the path to U8 chip select are unverified. |
| **Reset / P2:10 (`NR`)** | The physical button press and software `reboot` were captured at the external contact. `reboot` spent approximately **26 µs near zero** there. That interval does not measure the internal MCU reset duration. `dfu` and downstream TFT/camera reset lines remain unmeasured. |
| **Heartbeat** | The PE3 blue LED pulsed visibly; PB7 (P1:7) and PB0 (P2:27) showed about **one second high and one second low** (approximately 0.5 Hz full cycle). PB1, PE1 and PD13 remain source-confirmed outputs. All six retain their normal-heartbeat and fatal-error assignments; the scope observations cover normal heartbeat only. |

The [bench report](https://github.com/EpiJunkie/fanadapter/wiki/STM32H743VIT6-and-WeAct-V1.2-Pin-Audit#guided-bench-validation)
also records earlier functional observations: H-pattern and sequential shifting,
pedal UART operation, handbrake PWM activity, and a Web Config handbrake command
registering in the Fanatec Windows application. Those observations support
functional signaling but do not identify the route of that command or establish
full dedicated-handbrake-port coverage. They are distinct from the pin-specific
measurements above.

Routine bench testing for this mapping audit is complete. The 92-contact map
retains drawing evidence alongside the measured segments; remaining component
identification and electrical questions can be revisited when a specific design
depends on them. Future pin allocation and assembly-label changes are separate
work.

## Regenerate and verify

Python 3 standard library plus Git in a Git checkout; no Python packages to install.
Run from the repository root:

```sh
python3 firmware-stm32/pin-audit/generate.py
python3 firmware-stm32/pin-audit/generate.py --check
python3 -m unittest discover -s firmware-stm32/pin-audit -p 'test_*.py'
git diff --exit-code -- firmware-stm32/PIN-AUDIT.md
```

The last command is the clean-regeneration check after the initial generated file
has been committed. `--check` validates the expected 92 unique contacts, all 100
package positions, GPIO/package joins, board citations/pages, firmware role/source
references, complete application source-file inventory/hashes, and exact Markdown
agreement. It also checks CubeMX reference hashes, target identity, label counts,
exact header identities, represented onboard nets and version agreement against the
recorded reopen results. Tests deliberately remove/duplicate contacts, break
references, drop a firmware role and corrupt source evidence to ensure those errors
fail. A PD13 regression changes only its JSON net from `QSPI_BK1_IO3` to
`QSPI_BK1_IO2` in a disposable copy, renders fresh Markdown, and checks that the
unchanged CubeMX label still rejects it. Restoring IO3 passes. Net comparisons cover
all 41 net-bearing annotations; LED/button/clock role labels are not net names.
Header identity is the entire label before `__`: `P2_28_B10` cannot stand in for
`P2_28_B1`. Tests refresh the deliberately changed `.ioc` hash before checking
this mismatch; valid net and `_VIA_SB<n>` suffixes still pass.

Text is read as UTF-8; new or changed Markdown is written as UTF-8 with LF line
endings. Regenerating an already-current document preserves its checkout bytes,
including CRLF, to avoid spurious Git modifications. Firmware
and `.ioc` checkout hashes normalize **only CRLF to LF** so Git's
`core.autocrlf=true` conversion does not invalidate the recorded LF hashes. Other
bytes, whitespace and substantive edits remain significant. File inventory paths
use repository-relative forward slashes on every host. External XML/PDF provenance
hashes and the historical CubeMX byte-identical reopen record are unchanged.

In a Git checkout, the firmware inventory includes tracked files and unignored
untracked files using `git ls-files --cached --others --exclude-standard`. Finder's
ignored `src/.DS_Store` does not trigger a coverage failure. New unignored sources,
substantive edits and missing tracked sources still fail; an ignore rule cannot
hide an edit to an already-tracked source. Git inventory errors fail validation.
Source archives without `.git` use a strict filesystem inventory instead; without
Git metadata, ignore rules are not interpreted and extra files remain significant.

The source hashes intentionally identify the audited implementation. A substantive
firmware file change makes validation fail even if its pin behavior may be unchanged. Review
the new source, update the baseline/evidence and regenerate; do not blindly replace
hashes. These checks establish internal consistency and freshness, not the truth of
a transcribed schematic or physical continuity. Vendor HAL/startup defaults are not
an exhaustive part of the application-source audit, and the baseline leaves
PlatformIO framework/platform versions unpinned.

### Checkout portability validation at `d1c891b` (17 November 2026)

The Copilot follow-up commit [`d1c891b`](https://github.com/EpiJunkie/fanadapter/commit/d1c891b217c60711574fbd51893440e17526bc32)
was tested on **macOS 26.7.1 ARM64**, Python **3.15.2**, Git
**2.50.1 (Apple Git-155)**. The full 22-test suite and `--check` pass in clean local
clones with `core.autocrlf=false` / `core.eol=lf` and with `core.autocrlf=true`.
Actual LF/CRLF bytes were checked in firmware sources, JSON, Markdown and both
`.ioc` files. Two successive regenerations leave a clean Git diff and status in
both clones. The suite and `--check` also pass with an ignored `src/.DS_Store` in
each checkout; a new unignored source and a substantive `src/main.c` edit fail.
Removing the new source and restoring the original source makes validation pass.

The suite also checks Windows drive/backslash paths with `PureWindowsPath`, both
when matching the JSON inventory and when resolving its slash-separated paths.
**Native Windows and Linux execution were not performed in that IDE validation.**
Windows path semantics and CRLF checkouts on macOS are not a substitute for a
native Windows run. That code-validation step did not perform a new CubeMX reopen,
GUI inspection or hardware test. The later guided bench observations are recorded
separately above; the `.ioc` contents and electrical mappings are unchanged.

### Required forward and reverse examples

```sh
python3 firmware-stm32/pin-audit/generate.py --function handbrake-pwm
python3 firmware-stm32/pin-audit/generate.py --contact P1:30
# Additional MCU-centric lookup, including GPIOs with no expansion header:
python3 firmware-stm32/pin-audit/generate.py --gpio PH0
# A declared firmware role without an assigned GPIO:
python3 firmware-stm32/pin-audit/generate.py --function reset-and-rom-entry
```

Both required queries resolve **P1 pin 30 (`C8`) → PC8 (LQFP100 pad 65)**,
firmware **TIM3_CH3 / AF2 handbrake PWM**, and WeAct **microSD D0** through R26
to U6 pin 7. ST lists TIM3_CH3 and SDMMC1_D0 as capabilities of PC8; the firmware
selects the former, while the board is wired to the latter. The JSON/source links
keep those three facts distinct. Lookup output includes the citations and pending
V0 decision, not just an uncited label.

Non-GPIO function lookups return the declared role with its source evidence and
empty contact, package-contact and onboard lists. They do not invent a mapping to
NRST or BOOT0 from a software reset/ROM-entry role. Unknown function IDs remain
errors.

That empty list does not imply NRST stays high. The reset role and P2:10 (`NR`)
entry cite RM0433 §8.4.2, Figure 43 and the board schematic: the reset controller
is expected to pulse NRST on `reboot`/`dfu`, with the connected `SYS_RESET` line
feeding the camera/TFT reset inputs. The owner captured a physical button press
and software `reboot` at `NR`; the approximately 26 µs near-zero interval belongs
to that external contact waveform. It does not establish internal MCU reset
duration. `dfu`, downstream reset waveforms and TFT/camera response remain
unmeasured. The current ST reference is Rev 8 p. 329;
Copilot's Rev 7 citation used p. 327 for the same section/figure.

## Findings at the audited baseline

- **Handbrake sharing:** `outputs_init()` configures PC8 for TIM3_CH3 even if the
  dedicated handbrake connector is unused. PWM start can fail non-fatally; the pin
  is still assigned. The WeAct microSD data connection remains present. This is a
  source/drawing overlap; no SD malfunction was observed or tested here.
- **Heartbeat:** the intended PE3 LED and five extra bring-up pins (PB7, PB0, PB1,
  PE1, PD13) are all push-pull outputs, initialized early and toggled together in
  normal and fatal-error paths. PE3 controls the transistor-driven LED. PD13 also
  connects to QSPI flash IO3; PB7/PE1 connect to camera VSYNC/D3. PB0/PB1 have no
  additional onboard connection identified in the drawing. None is a spare pin
  merely because a user peripheral is not connected. Visible PE3 activity and
  scoped PB7/PB0 waveforms confirm representative normal heartbeat behavior;
  PB1, PE1, PD13 and the fatal-error path remain source-confirmed.
- **Other camera overlaps:** PA4 DAC X shares camera HSYNC, and PC6/PC7 sequential
  outputs share camera D0/D1. The camera/TFT/SD/flash peripherals are not initialized
  by this application; their physical wiring nevertheless remains relevant.
- **USB identity and console:** PA11/PA12 are the FS device port, while PB14/PB15
  use the HS controller's embedded FS PHY as host. WeAct's `USB1_DN/DP` net names
  are not STM32 controller indices. Some source comments reverse the roles;
  actual macros/initialization establish the audit. PA9/PA10 remain USART1 AF7
  while USB is mounted; buffering policy changes do not release those pins.
- **Clocks and special contacts:** PH0/PH1 serve the HSE crystal used for USB PLL3;
  SYSCLK uses internal HSI. PC14/PC15 are wired to the LSE crystal but not selected
  by the application. SWD reset defaults, power/ground, NRST, BOOT0, VBAT and VREF+
  are not ordinary free GPIO assignments. SB1–SB6 and R9 conditions are in the JSON.

No replacement PWM pin, firmware-compatibility mechanism, corrected V0 routing,
`schematics/` reorganization or webconfig pin explorer is implemented here. Those
decisions require follow-up work. These findings establish shared connections,
not a diagnosed electrical fault or a measured performance effect.

## Evidence and CubeMX references

The JSON preserves immutable firmware/vendor revisions, PDF hashes and source
locations. ST DS12110 supplies package/pin capabilities; the installed ST CubeMX
database provides the machine-readable capability snapshot and its exact hashes.
RM0433 remains the reference for peripheral and analog-switch behavior. Downloaded
vendor PDFs and SDKs are not vendored into this documentation branch.

The two [CubeMX references](../cubemx/README.md) document bare-MCU defaults and
WeAct drawing annotations. They are deliberately separate from `breadboard-v1` and
must not be used to regenerate the hand-written firmware. Their provenance records
the tool/database/firmware-package metadata, reopen checks and any limitations.
