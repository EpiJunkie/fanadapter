# Maintaining the STM32 / WeAct pin audit

[PIN-AUDIT.md](../PIN-AUDIT.md) answers both directions: firmware function to probe
location, and numbered WeAct header contact to MCU/board/firmware use. This is a
documentation snapshot of upstream `8c48cfe422bae50b96b04b9c8de813d434e0bd54`, not
a generated firmware configuration or a proposed reassignment.

## Maintained data and scope

JSON is the maintained source. Edit these files, then regenerate the Markdown:

| File | Authority / purpose |
| --- | --- |
| `audit.json` | Dataset filenames, physical scope, bench-evidence distinctions and pending V0 routing |
| `mcu.json` | ST CubeMX package/capability snapshot: 100 LQFP100 contacts, 82 logical GPIO identities, possible signals/AFs and special-pad restrictions |
| `weact-v1.2.json` | Revision-pinned WeAct drawing evidence: all 92 P1/P2/P3 contacts, rear silkscreen, onboard nets, solder bridges and other connectors |
| `breadboard-v1.json` | Named current wiring profile: 19 explicit application GPIO assignments plus PH0/PH1 HSE, non-GPIO roles, source ranges and coverage hashes |

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
Pin numbers follow the schematic and numbered mechanical drawing, with front/rear
orientation stated in the generated table. Never infer odd/even columns from a
mirrored rear view alone.

The first module's **1.2** marking was observed by its owner under the LCD, right
of the ribbon slot. This confirms that module's revision only. Individual contact
continuity, bridge/component population and the second module's revision remain
unverified. Dedicated handbrake testing has not occurred. The legacy carrier's F1
protection is still uncorrected in hardware and design; this audit does not qualify
a replacement or approve a powered test.

## Regenerate and verify

Python 3 standard library only; run from the repository root:

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
agreement. It also checks CubeMX reference hashes, target identity, label counts
and version agreement against the recorded reopen results. Tests deliberately remove/duplicate contacts, break references,
drop a firmware role and corrupt source evidence to ensure those errors fail.

The source hashes intentionally identify the audited implementation. A firmware
file change makes validation fail even if its pin behavior may be unchanged. Review
the new source, update the baseline/evidence and regenerate; do not blindly replace
hashes. These checks establish internal consistency and freshness, not the truth of
a transcribed schematic or physical continuity. Vendor HAL/startup defaults are not
an exhaustive part of the application-source audit, and the baseline leaves
PlatformIO framework/platform versions unpinned.

### Required forward and reverse examples

```sh
python3 firmware-stm32/pin-audit/generate.py --function handbrake-pwm
python3 firmware-stm32/pin-audit/generate.py --contact P1:30
# Additional MCU-centric lookup, including GPIOs with no expansion header:
python3 firmware-stm32/pin-audit/generate.py --gpio PH0
```

Both required queries resolve **P1 pin 30 (`C8`) → PC8 (LQFP100 pad 65)**,
firmware **TIM3_CH3 / AF2 handbrake PWM**, and WeAct **microSD D0** through R26
to U6 pin 7. ST lists TIM3_CH3 and SDMMC1_D0 as capabilities of PC8; the firmware
selects the former, while the board is wired to the latter. The JSON/source links
keep those three facts distinct. Lookup output includes the citations and pending
V0 decision, not just an uncited label.

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
  merely because a user peripheral is not connected.
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
