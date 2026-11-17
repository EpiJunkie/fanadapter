"""Cross-check CubeMX net annotations against independently maintained board JSON."""

import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import generate


class OnboardLabelTests(unittest.TestCase):
    def test_every_documented_net_annotation_rejects_json_disagreement(self):
        data = generate.load()
        checked = 0
        for gpio, connections in data[2]['gpio_onboard_connections'].items():
            for index, connection in enumerate(connections):
                # GPIO-named nets use descriptive LED/button/clock labels instead.
                if connection['net'] == gpio:
                    continue
                with self.subTest(gpio=gpio, net=connection['net']):
                    changed = copy.deepcopy(data)
                    changed[2]['gpio_onboard_connections'][gpio][index]['net'] += '_WRONG'
                    with self.assertRaisesRegex(ValueError,
                                                'CubeMX label disagrees with onboard net'):
                        generate.validate(changed)
                    checked += 1
        self.assertEqual(checked, 41)

    def test_pd13_json_mutation_fails_after_markdown_regeneration_and_restores(self):
        with tempfile.TemporaryDirectory(prefix='pin-audit-onboard-') as temporary:
            root = Path(temporary)
            firmware = root / 'firmware-stm32'
            firmware.mkdir()
            for name in ('src', 'include', 'pin-audit', 'cubemx'):
                shutil.copytree(generate.ROOT / 'firmware-stm32' / name,
                                firmware / name, ignore=shutil.ignore_patterns('__pycache__'))
            for name in ('platformio.ini', 'apply_tinyusb_patches.py', 'PIN-AUDIT.md'):
                shutil.copy2(generate.ROOT / 'firmware-stm32' / name, firmware / name)
            audit = firmware / 'pin-audit'

            def check():
                return subprocess.run([sys.executable, str(audit / 'generate.py'), '--check'],
                                      capture_output=True, text=True, encoding='utf-8')

            baseline = check()
            self.assertEqual(baseline.returncode, 0, baseline.stderr)
            board_path = audit / 'weact-v1.2.json'
            original = board_path.read_bytes()
            board = json.loads(original)
            self.assertEqual(board['gpio_onboard_connections']['PD13'][0]['net'],
                             'QSPI_BK1_IO3')
            board['gpio_onboard_connections']['PD13'][0]['net'] = 'QSPI_BK1_IO2'
            board_path.write_text(json.dumps(board, indent=2) + '\n', encoding='utf-8')
            # Deliberately render directly, bypassing validation, to prove that a
            # freshly regenerated table cannot conceal the cross-source mismatch.
            document = firmware / 'PIN-AUDIT.md'
            document.write_text(generate.render(generate.load(audit)), encoding='utf-8')
            rejected = check()
            self.assertEqual(rejected.returncode, 1)
            self.assertIn('CubeMX label disagrees with onboard net: PD13', rejected.stderr)
            self.assertIn('QSPI_BK1_IO3', rejected.stderr)
            self.assertIn('QSPI_BK1_IO2', rejected.stderr)
            self.assertNotIn('PIN-AUDIT.md is stale', rejected.stderr)

            board_path.write_bytes(original)
            document.write_text(generate.render(generate.load(audit)), encoding='utf-8')
            restored = check()
            self.assertEqual(restored.returncode, 0, restored.stderr)


if __name__ == '__main__':
    unittest.main()
