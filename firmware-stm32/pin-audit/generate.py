#!/usr/bin/env python3
"""Validate the maintained JSON and generate/query the source-pinned pin audit."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUTPUT = HERE.parent / 'PIN-AUDIT.md'


def load(directory=HERE):
    meta = json.loads((directory / 'audit.json').read_text())
    return (meta, *(json.loads((directory / meta[key]).read_text())
                    for key in ('mcu_file', 'board_file', 'profile_file')))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(data, root=ROOT):
    meta, mcu, board, profile = data
    require(meta['schema_version'] == 1, 'Unsupported audit schema')
    require(profile['profile_id'] == 'breadboard-v1', 'Unknown wiring profile')
    require(re.fullmatch(r'[0-9a-f]{40}', profile['coverage']['baseline_commit']), 'Invalid baseline')
    pads = {p['package_pin']: p for p in mcu['pins']}
    require(len(mcu['pins']) == len(pads) == 100 and set(pads) == set(range(1, 101)),
            'MCU must contain each LQFP100 package contact exactly once')
    gpios = {p['gpio']: p for p in mcu['pins'] if p['gpio']}
    require(len(gpios) == sum(bool(p['gpio']) for p in mcu['pins']) == 82,
            'Expected 82 distinct GPIO identities')
    require({h['id']: h['pin_count'] for h in board['headers']} == meta['expected_headers'],
            'Header inventory differs from audited physical scope')
    expected = {(h, pin) for h, count in meta['expected_headers'].items()
                for pin in range(1, count + 1)}
    keys = [(c['header'], c['pin']) for c in board['contacts']]
    require(len(keys) == len(set(keys)), 'Duplicate physical header contact')
    require(set(keys) == expected, 'Missing or unexpected physical header contact')
    for c in board['contacts']:
        require(type(c['pin']) is int and c['silkscreen'] and c['net'], 'Invalid contact identity')
        require(c['kind'] in ('gpio', 'power', 'ground', 'reset', 'analog_reference', 'backup_power'),
                f'Unknown contact kind: {c["kind"]}')
        require(all(p in pads for p in c['mcu_package_pins']), 'Unknown package contact reference')
        require((c['kind'] == 'gpio') == bool(c['gpio']), 'GPIO/contact kind mismatch')
        if c['gpio']:
            require(c['gpio'] in gpios, f'Unknown GPIO: {c["gpio"]}')
            require(c['mcu_package_pins'] == [gpios[c['gpio']]['package_pin']],
                    f'Package/contact mismatch: {c["header"]}:{c["pin"]}')
        require(c['sources'], 'Missing physical-contact evidence')
    require(set(board['gpio_onboard_connections']) <= set(gpios), 'Unresolved onboard GPIO')
    require(set(meta['v0_by_gpio']) <= set(gpios), 'Unresolved planned-routing GPIO')

    def board_refs(value):
        if isinstance(value, dict):
            if 'source' in value:
                require(value['source'] in board['sources'], 'Unresolved board source')
                require(1 <= value['page'] <= board['sources'][value['source']]['pages'],
                        'Invalid board source page')
            for item in value.values():
                board_refs(item)
        elif isinstance(value, list):
            for item in value:
                board_refs(item)
    board_refs(board)

    ids = [r['id'] for r in profile['records'] + profile['non_gpio_roles']]
    require(len(ids) == len(set(ids)), 'Duplicate firmware role ID')
    assigned = [r['gpio'] for r in profile['records']]
    expected_gpio = set(profile['coverage']['explicit_gpio_names']) | {'PH0', 'PH1'}
    require(len(assigned) == len(set(assigned)) and set(assigned) == expected_gpio,
            'Firmware GPIO inventory differs from reviewed coverage')
    require(set(assigned) <= set(gpios), 'Unresolved firmware GPIO')
    covered = {s['path']: s for s in profile['coverage']['audited_files']}
    actual = {str(p.relative_to(root)) for folder in ('src', 'include')
              for p in (root / 'firmware-stm32' / folder).rglob('*') if p.is_file()}
    actual |= {'firmware-stm32/platformio.ini', 'firmware-stm32/apply_tinyusb_patches.py'}
    require(actual == set(covered), 'Firmware file inventory changed; review audit coverage')
    for path, record in covered.items():
        require(hashlib.sha256((root / path).read_bytes()).hexdigest() == record['sha256'],
                f'Audited source changed: {path}; refresh the dated audit after reviewing it')
    for r in profile['records'] + profile['non_gpio_roles']:
        require(r['sources'], f'Missing firmware evidence: {r["id"]}')
        for source in r['sources']:
            require(source['path'] in covered, 'Firmware citation outside audited files')
            count = len((root / source['path']).read_text().splitlines())
            require(1 <= source['line_start'] <= source['line_end'] <= count,
                    f'Invalid firmware source lines: {r["id"]}')
    cubemx_dir = root / 'firmware-stm32/cubemx'
    provenance = json.loads((cubemx_dir / 'validation.json').read_text())
    require(provenance['cubemx_version'] == mcu['cubemx_version'] and
            provenance['database_version'] == mcu['cubemx_database_version'],
            'CubeMX and capability snapshot versions differ')
    for reference in provenance['references']:
        content = (cubemx_dir / reference['file']).read_bytes()
        require(hashlib.sha256(content).hexdigest() == reference['sha256'],
                f'CubeMX reference changed since recorded reopen: {reference["file"]}')
        entries = {key.replace('\\ ', ' '): value for key, value in
                   (line.split('=', 1) for line in content.decode().splitlines()
                    if '=' in line and not line.startswith('#'))}
        require(entries.get('Mcu.CPN') == mcu['mcu'] and entries.get('Mcu.Package') == mcu['package'],
                'CubeMX reference targets a different MCU/package')
        require(sum(k.endswith('.GPIO_Label') for k in entries) == reference['label_count'],
                'CubeMX annotation count differs from reopen record')
        if reference['label_count']:
            for contact in board['contacts']:
                if contact['gpio']:
                    pin = gpios[contact['gpio']]['package_name']
                    identity = f'{contact["header"]}_{contact["pin"]}_{contact["silkscreen"].replace(".", "_")}'
                    require(identity in entries.get(pin + '.GPIO_Label', ''),
                            f'CubeMX label disagrees with header contact: {identity}')
    return gpios


def cell(value):
    return str(value).replace('|', '&#124;').replace('\n', ' ')


def fw_sources(record, profile):
    base = f'{profile["repository"]}/blob/{profile["coverage"]["baseline_commit"]}'
    return ' '.join(f'[{s["symbol"]}]({base}/{s["path"]}#L{s["line_start"]}-L{s["line_end"]})'
                    for s in record['sources'])


def board_sources(refs, board):
    return ' '.join(f'[{"S" if "schematic" in s["source"] else "B"} p{s["page"]}: '
                    f'{s["block"]}]({board["sources"][s["source"]]["url"]}#page={s["page"]})'
                    for s in refs)


def connections(contact, board):
    return board['gpio_onboard_connections'].get(contact['gpio'], []) if contact['gpio'] else contact['onboard_connections']


def contact_label(contact):
    return f'{contact["header"]} pin {contact["pin"]} (`{contact["silkscreen"]}`)'


def wiring_text(items, board):
    return '<br>'.join(f'{cell(x["target"])}: {cell(x["net"])} — {cell(x["description"])} '
                      f'({cell(x["condition"])}). {board_sources(x["sources"], board)}' for x in items)


def contact_row(contact, data, gpios):
    meta, _, board, profile = data
    gpio = contact['gpio']
    if gpio:
        pad = gpios[gpio]
        pin_text = f'`{pad["package_name"]}` / pad {pad["package_pin"]}'
        if pad.get('note'):
            pin_text += f'<br>{cell(pad["note"])}'
    else:
        pin_text = f'{cell(contact["net"])} ({contact["kind"]}); pads ' + (', '.join(map(str, contact['mcu_package_pins'])) or 'none directly')
    uses = [r for r in profile['records'] if r['gpio'] == gpio]
    firmware = '<br>'.join(f'**{cell(r["function"])}**; {cell(r["mode"])}. {fw_sources(r, profile)}' for r in uses)
    if not firmware:
        firmware = 'No explicit application GPIO assignment' if gpio else 'Board supply/reference/reset; see non-GPIO roles'
    return '| ' + ' | '.join([contact_label(contact), pin_text,
        wiring_text(connections(contact, board), board) or 'No additional onboard connection identified in the cited drawing',
        firmware, cell(meta['v0_by_gpio'].get(gpio, meta['v0_default'])), board_sources(contact['sources'], board)]) + ' |'


def render(data):
    meta, mcu, board, profile = data
    gpios = {p['gpio']: p for p in mcu['pins'] if p['gpio']}
    lines = ['# STM32H743VIT6 / WeAct V1.2 pin audit', '',
        '<!-- Generated from pin-audit/*.json by pin-audit/generate.py; edit JSON, not this table. -->', '',
        f'Profile: **`{profile["profile_id"]}` — {profile["profile_name"]}**. '
        f'Audited firmware: [`{profile["coverage"]["baseline_commit"]}`]({profile["repository"]}/commit/{profile["coverage"]["baseline_commit"]}).', '',
        meta['scope'], '',
        'All contact mappings below are **drawing evidence, not individual bench confirmation**. '
        'Capability is not a selected firmware function, and an unconfigured GPIO is not necessarily electrically free. '
        'No GPIO is reassigned by this audit; V0 routing remains planned.', '',
        'See [maintenance, verification and findings](pin-audit/README.md) and '
        '[CubeMX reference provenance](cubemx/README.md).', '',
        '## Physical orientation', '']
    lines += [f'- **{h["id"]}** ({h["layout"]}, {h["pin_count"]} contacts): {h["orientation"]}' for h in board['headers']]
    lines += ['', 'S = WeAct schematic; B = WeAct board drawing. Links identify the vendor revision, page and block. '
              'Rear silkscreen is shown; front/rear views are mirrored.', '', '## Header contacts', '']
    for header in board['headers']:
        lines += [f'### {header["id"]}', '',
            '| WeAct header / contact (silkscreen) | STM32 pin / LQFP100 pad | Onboard connections | Firmware use: breadboard-v1 | V0 carrier use (planned) | Physical evidence |',
            '| --- | --- | --- | --- | --- | --- |']
        lines += [contact_row(c, data, gpios) for c in board['contacts'] if c['header'] == header['id']]
        lines.append('')
    lines += ['## Firmware function → probe contact', '',
              'This inventory includes startup, normal operation, non-fatal peripheral failures and diagnostics. '
              'HSE pins have no expansion-header contact; their MCU pads/crystal network identify the physical location, not a recommended powered probing method.', '',
              '| Function ID / use | GPIO | Header contacts / MCU pad | Mode and conditions | Source evidence |',
              '| --- | --- | --- | --- | --- |']
    for r in profile['records']:
        contacts = [contact_label(c) for c in board['contacts'] if c['gpio'] == r['gpio']]
        physical = ', '.join(contacts) or f'No P1/P2/P3 contact; MCU pad {gpios[r["gpio"]]["package_pin"]}'
        if not contacts:
            physical += '<br>' + wiring_text(board['gpio_onboard_connections'].get(r['gpio'], []), board)
        lines.append('| ' + ' | '.join([f'`{r["id"]}` — {cell(r["function"])}', r['gpio'], physical,
            cell(f'{r["mode"]}. {r["condition"]} {r["description"]}'), fw_sources(r, profile)]) + ' |')
    lines += ['', '### Non-GPIO firmware roles', '']
    for r in profile['non_gpio_roles']:
        lines += [f'- **{r["function"]}:** {r["description"]} Condition: {r["condition"]} {fw_sources(r, profile)}']
    lines += ['', '## MCU capabilities (not firmware selections)', '',
              f'ST CubeMX {mcu["cubemx_version"]}, database {mcu["cubemx_database_version"]}, '
              f'package {mcu["package"]}. {mcu["capabilities_scope"]}', '',
              'Function names/AF labels below are CubeMX database names; HAL aliases can differ. '
              'Empty AF lists mean a signal is not selected through an AF mux number. '
              'The complete JSON retains analog-switch settings and database conditions.', '',
              '<details>', '<summary>All 100 package contacts and capability signals</summary>', '',
              '| MCU pad | Package pin name | Logical GPIO | Capability signals / AF macros |',
              '| --- | --- | --- | --- |']
    for p in mcu['pins']:
        functions = '; '.join(f'{f["name"]}' + (f' ({", ".join(f["alternate_functions"])})' if f['alternate_functions'] else '') for f in p['functions'])
        lines.append(f'| {p["package_pin"]} | {p["package_name"]} | {p["gpio"] or "—"} | {cell(functions or p["type"])} |')
    lines += ['', '</details>', '', '## Source provenance', '']
    lines += [f'- [{s["title"]}]({s["url"]})' for s in mcu['documentation']]
    lines += [f'- [{key}]({s["url"]}); SHA-256 `{s["sha256"]}`.' for key, s in board['sources'].items()]
    lines += [f'- ST CubeMX `{s["relative_path"]}`; SHA-256 `{s["sha256"]}`.' for s in mcu['sources']]
    lines += ['', 'Firmware file hashes, source ranges, conditional-path coverage and exclusions are maintained in '
              '[breadboard-v1.json](pin-audit/breadboard-v1.json). Bench evidence is maintained in '
              '[audit.json](pin-audit/audit.json).', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true', help='validate sources and require up-to-date Markdown')
    group.add_argument('--function', help='firmware function ID, e.g. handbrake-pwm')
    group.add_argument('--contact', help='physical contact, e.g. P1:30')
    group.add_argument('--gpio', help='logical GPIO, e.g. PC8')
    args = parser.parse_args()
    try:
        data = load()
        gpios = validate(data)
        meta, mcu, board, profile = data
        if args.function or args.contact or args.gpio:
            if args.function:
                uses = [r for r in profile['records'] if r['id'] == args.function]
                require(uses, f'Unknown function: {args.function}')
                gpio = uses[0]['gpio']
                contacts = [c for c in board['contacts'] if c['gpio'] == gpio]
            elif args.contact:
                contacts = [c for c in board['contacts'] if f'{c["header"]}:{c["pin"]}' == args.contact]
                require(contacts, f'Unknown contact: {args.contact}')
                gpio = contacts[0]['gpio']
                uses = [r for r in profile['records'] if gpio and r['gpio'] == gpio]
            else:
                gpio = args.gpio
                require(gpio in gpios, f'Unknown GPIO: {gpio}')
                contacts = [c for c in board['contacts'] if c['gpio'] == gpio]
                uses = [r for r in profile['records'] if r['gpio'] == gpio]
            package_numbers = {p for c in contacts for p in c['mcu_package_pins']}
            if gpio:
                package_numbers.add(gpios[gpio]['package_pin'])
            onboard = board['gpio_onboard_connections'].get(gpio, []) if gpio else [
                item for c in contacts for item in connections(c, board)]
            print(json.dumps({'profile': profile['profile_id'], 'contacts': contacts,
                'mcu_package_contacts': [p for p in mcu['pins'] if p['package_pin'] in package_numbers],
                'onboard': onboard,
                'firmware': uses, 'v0_planned': meta['v0_by_gpio'].get(gpio, meta['v0_default'])}, indent=2))
        elif args.check:
            require(OUTPUT.exists() and OUTPUT.read_text() == render(data), 'PIN-AUDIT.md is stale; run generate.py')
            print(f'PASS: {len(board["contacts"])} unique header contacts; 100 MCU pads; '
                  f'{len(profile["records"])} firmware GPIO/oscillator roles; sources resolve; Markdown is current.')
        else:
            OUTPUT.write_text(render(data))
            print(f'Generated {OUTPUT.relative_to(ROOT)}')
    except (ValueError, KeyError, OSError) as error:
        print(f'Audit error: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
