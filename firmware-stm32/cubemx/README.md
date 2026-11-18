# CubeMX pin-audit references

These files are reference views for the [pin audit](../PIN-AUDIT.md). They are
not inputs to the PlatformIO firmware build. Do not generate or flash firmware
from them.

- `STM32H743VIT6.stock.ioc` is the unchanged output of selecting the bare MCU
  with `load STM32H743VITx` and saving the new configuration. CubeMX records
  `Mcu.CPN=STM32H743VIT6` and `Mcu.Package=LQFP100`. Its defaults select only
  the SysTick and MemoryMap virtual pins, with no physical GPIO selected.
- `STM32H743VIT6.weact-v1.2.ioc` starts from that stock file and adds physical
  header/net labels from the WeAct V1.2 drawing and schematic. It labels all
  82 package GPIOs, including the four oscillator pins that are not on the
  expansion headers. It does not apply Fanadapter's peripheral assignments.

## Annotation limits

**The WeAct reference uses `GPIO_Analog` placeholders solely to retain labels
in CubeMX.** CubeMX 6.18.1 discarded labels on unassigned pins in a load/save
experiment, including pins listed without a signal. Selecting an analog mode
retained the labels. These placeholder modes are neither the MCU reset state
nor the intended operating configuration of the board or Fanadapter. In
particular, the reference does not enable USB, SWD, oscillators, SDMMC, QSPI,
camera, TFT, or the handbrake timer. The audit JSON contains their actual roles
and possible functions.

Labels put header/contact/silkscreen first, then the onboard net where present.
For example, `P1_30_C8__MicroSD_D0` is PC8, and
`P1_35_D13__QSPI_BK1_IO3` is PD13. A `_VIA_SB1`, `_VIA_SB2`, or `_VIA_SB3`
suffix identifies a schematic solder-bridge path; it does not confirm that the
bridge is closed on the assembled board. Supply, ground, reset, series
components, bridge states, and shared-connection details are modeled in the
JSON because one CubeMX pin selection cannot represent those circuits.

The audit validator compares each represented net suffix with the GPIO's onboard
net in JSON, removing only the `_VIA_SB<n>` routing suffix. The `USER_LED`,
`SW2_USER_BUTTON` and oscillator labels describe roles rather than literal net
names; the full JSON wiring remains authoritative for those annotations.
Header identities before `__` must match exactly; a label such as `P2_28_B10`
does not match `P2_28_B1`, even if the reference's recorded hash is refreshed.

The stock project's toolchain and clock values remain CubeMX defaults. Its
EWARM setting is not a Fanadapter toolchain recommendation. CubeMX derives the
internal project name from the filename before its first dot, so the two
reference files have the same internal project name; open them separately.

## Recorded tool and database versions

| Item | Recorded value |
| --- | --- |
| Validation date | 2026-11-17 |
| Native application | macOS ARM64 STM32CubeMX |
| CubeMX serialized version | `6.18.1` (`MxCube.Version`; application bundle reports `6.18`) |
| MCU database | `DB.6.0.181` |
| MCU file / schema | `db/mcu/STM32H743VITx.xml` / `V3.0` |
| GPIO modes database | `db/mcu/IP/GPIO-STM32H747_gpio_v1_0_Modes.xml` |
| Selected firmware-package metadata | `STM32Cube FW_H7 V1.13.0` |

No firmware package was installed for this audit and no code was generated.
The selected package version is CubeMX project metadata, separate from the
MCU database version. Source-file hashes and final reference hashes are in
[`validation.json`](validation.json).

The original reference files used LF line endings. Audit validation normalizes
Git checkout CRLF to LF before comparing these text-file hashes. This tolerates
`core.autocrlf=true` without changing the recorded hashes or implying a new native
CubeMX round trip. The byte-identical reopen results below describe the original
files and saved copies, not every possible checkout's raw bytes.

## Reproduce the stock reference

Use the same CubeMX/database versions when comparing defaults. Work in a
temporary directory so the checked-in stock snapshot remains unchanged:

```sh
audit_tmp=$(mktemp -d)
cat > "$audit_tmp/create.mxscript" <<EOF
load STM32H743VITx
config saveas $audit_tmp/STM32H743VIT6.stock.ioc
exit
EOF
/Applications/STMicroelectronics/STM32CubeMX.app/Contents/MacOS/STM32CubeMX \
  -q "$audit_tmp/create.mxscript"
```

The CLI target is the database name ending in `x`. `load STM32H743VIT6` is not
accepted by this CLI, even though `STM32H743VIT6` is the resulting orderable
part number. Check command responses and output files: CubeMX can exit with
code zero after a command reports `KO`.

## Reopen the references

From the repository root, set `audit_repo` to its absolute path. Use a temporary
output directory and load/save each checked-in file:

```sh
audit_repo=$(pwd)
audit_tmp=$(mktemp -d)
cat > "$audit_tmp/reopen.mxscript" <<EOF
config load $audit_repo/firmware-stm32/cubemx/STM32H743VIT6.stock.ioc
config saveas $audit_tmp/STM32H743VIT6.stock.ioc
config load $audit_repo/firmware-stm32/cubemx/STM32H743VIT6.weact-v1.2.ioc
config saveas $audit_tmp/STM32H743VIT6.weact-v1.2.ioc
exit
EOF
/Applications/STMicroelectronics/STM32CubeMX.app/Contents/MacOS/STM32CubeMX \
  -q "$audit_tmp/reopen.mxscript"
```

The recorded check reopened both files through the installed CubeMX quiet CLI
and saved staged copies. All commands returned `OK`. Parsed configuration
entries, selected pins, and all 82 labels were checked after the round trip.
This reference-file round trip did not include interactive GUI inspection or
electrical measurements. The later [guided bench evidence](../pin-audit/README.md#guided-bench-evidence-17-november-2026)
records Board A's C8-to-MCU continuity, SB3 closure and D6-to-SB3 connection,
plus external NR button/reboot captures and representative normal heartbeat
observations. Board B's SB3 evidence remains visual. R26/microSD and R30/QSPI
branches, fitted component identity/values, `dfu` and downstream TFT/camera reset
behavior are not verified by those measurements. These evidence distinctions are
maintained in the audit JSON; the CubeMX labels remain drawing annotations.

WeAct source: [V1.2 schematic](https://github.com/WeActStudio/MiniSTM32H7xx/blob/ff1e3d67589293ed734df6b17e751b4668077f90/Hardware/STM32H7xx%20SchDoc%20V12.pdf)
and [V1.2 board drawing](https://github.com/WeActStudio/MiniSTM32H7xx/blob/ff1e3d67589293ed734df6b17e751b4668077f90/Hardware/STM32H7xx_BoardShape%20Board%20Shape%20%E5%A4%96%E5%BD%A2%20V12.pdf).
