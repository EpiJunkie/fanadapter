"""Meaningful completeness/reference and bidirectional-lookup regression checks."""

import copy
import json
import subprocess
import sys
import unittest

import generate


class PinAuditTests(unittest.TestCase):
    def setUp(self):
        self.data = generate.load()

    def test_audit_and_generated_document_agree(self):
        generate.validate(self.data)
        self.assertEqual(generate.OUTPUT.read_text(), generate.render(self.data))

    def test_both_directions_identify_handbrake_and_sd_d0(self):
        _, mcu, board, profile = self.data
        function = next(r for r in profile['records'] if r['id'] == 'handbrake-pwm')
        forward = [c for c in board['contacts'] if c['gpio'] == function['gpio']]
        self.assertEqual([(c['header'], c['pin'], c['silkscreen']) for c in forward],
                         [('P1', 30, 'C8')])
        reverse = next(c for c in board['contacts'] if (c['header'], c['pin']) == ('P1', 30))
        self.assertEqual(reverse['gpio'], 'PC8')
        self.assertIn('TIM3', function['function'])
        self.assertEqual(board['gpio_onboard_connections']['PC8'][0]['net'], 'MicroSD_D0')
        self.assertIn('SDMMC1 D0', board['gpio_onboard_connections']['PC8'][0]['description'])
        capabilities = next(p for p in mcu['pins'] if p['gpio'] == 'PC8')
        self.assertEqual(capabilities['package_pin'], 65)
        signals = {f['name']: f['alternate_functions'] for f in capabilities['functions']}
        self.assertEqual(signals['TIM3_CH3'], ['GPIO_AF2_TIM3'])
        self.assertIn('SDMMC1_D0', signals)

    def test_missing_or_duplicated_contact_fails(self):
        for mutation in ('missing', 'duplicate'):
            data = copy.deepcopy(self.data)
            contacts = data[2]['contacts']
            if mutation == 'missing':
                contacts.pop()
            else:
                contacts[-1] = copy.deepcopy(contacts[0])
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                generate.validate(data)

    def test_dangling_gpio_and_source_fail(self):
        for key, value in [('gpio', 'PZ99'), ('sources', [{'source': 'missing', 'page': 1}])]:
            data = copy.deepcopy(self.data)
            data[2]['contacts'][2][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                generate.validate(data)

    def test_missing_firmware_role_fails(self):
        data = copy.deepcopy(self.data)
        data[3]['records'].pop()
        with self.assertRaisesRegex(ValueError, 'Firmware GPIO inventory'):
            generate.validate(data)

    def test_stale_source_hash_or_line_range_fails(self):
        data = copy.deepcopy(self.data)
        data[3]['coverage']['audited_files'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Audited source changed'):
            generate.validate(data)
        data = copy.deepcopy(self.data)
        data[3]['records'][0]['sources'][0]['line_end'] = 100000
        with self.assertRaisesRegex(ValueError, 'Invalid firmware source lines'):
            generate.validate(data)

    def test_diagnostic_pins_and_c_pad_identity_are_preserved(self):
        _, mcu, board, profile = self.data
        heartbeat = {r['gpio'] for r in profile['records'] if r['id'].startswith('heartbeat-')}
        self.assertEqual(heartbeat, {'PE3', 'PB7', 'PB0', 'PB1', 'PE1', 'PD13'})
        self.assertIn('QSPI', str(board['gpio_onboard_connections']['PD13']))
        for gpio in ('PC2', 'PC3'):
            pad = next(p for p in mcu['pins'] if p['gpio'] == gpio)
            self.assertEqual(pad['package_name'], gpio + '_C')
            self.assertIn('SYSCFG', str(pad['configuration_parameters']))

    def test_cli_lookups_preserve_physical_and_non_gpio_connections(self):
        def lookup(*args):
            return json.loads(subprocess.check_output(
                [sys.executable, str(generate.HERE / 'generate.py'), *args], text=True))
        forward = lookup('--function', 'handbrake-pwm')
        reverse = lookup('--contact', 'P1:30')
        self.assertEqual(forward, reverse)
        self.assertEqual(reverse['mcu_package_contacts'][0]['package_name'], 'PC8')
        reference = lookup('--contact', 'P2:16')
        self.assertEqual(reference['contacts'][0]['silkscreen'], 'V+')
        self.assertEqual(reference['mcu_package_contacts'][0]['package_pin'], 20)
        self.assertIn('R9', str(reference['onboard']))
        self.assertEqual(reference['firmware'], [])


if __name__ == '__main__':
    unittest.main()
