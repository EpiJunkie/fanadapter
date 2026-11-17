"""Header identity must match exactly, independently of the recorded IOC hash."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import generate


class HeaderIdentityTests(unittest.TestCase):
    def test_exact_header_identity_after_ioc_hash_refresh(self):
        with tempfile.TemporaryDirectory(prefix='pin-audit-header-') as temporary:
            root = Path(temporary)
            firmware = root / 'firmware-stm32'
            shutil.copytree(generate.ROOT / 'firmware-stm32', firmware,
                            ignore=shutil.ignore_patterns('.pio', '__pycache__', '.DS_Store', 'Thumbs.db'))
            reference = firmware / 'cubemx/STM32H743VIT6.weact-v1.2.ioc'
            provenance_path = firmware / 'cubemx/validation.json'
            original = generate.checkout_text_bytes(reference)
            provenance = json.loads(provenance_path.read_text(encoding='utf-8'))

            def check():
                return subprocess.run(
                    [sys.executable, str(firmware / 'pin-audit/generate.py'), '--check'],
                    capture_output=True, encoding='utf-8')

            baseline = check()
            self.assertEqual(baseline.returncode, 0, baseline.stderr)
            for incorrect in ('P2_28_B10', 'XP2_28_B1_PB1'):
                with self.subTest(label=incorrect):
                    changed = original.replace(b'PB1.GPIO_Label=P2_28_B1\n',
                                               f'PB1.GPIO_Label={incorrect}\n'.encode())
                    self.assertNotEqual(changed, original)
                    reference.write_bytes(changed)
                    for record in provenance['references']:
                        if record['file'] == reference.name:
                            record['sha256'] = hashlib.sha256(changed).hexdigest()
                    provenance_path.write_text(json.dumps(provenance), encoding='utf-8')
                    rejected = check()
                    self.assertEqual(rejected.returncode, 1)
                    self.assertIn('CubeMX label disagrees with header contact: P2_28_B1',
                                  rejected.stderr)
                    self.assertNotIn('CubeMX reference changed', rejected.stderr)

            reference.write_bytes(original)
            for record in provenance['references']:
                if record['file'] == reference.name:
                    record['sha256'] = hashlib.sha256(original).hexdigest()
            provenance_path.write_text(json.dumps(provenance), encoding='utf-8')
            restored = check()
            self.assertEqual(restored.returncode, 0, restored.stderr)

    def test_documented_net_and_bridge_suffixes_keep_exact_identity(self):
        reference = (generate.ROOT / 'firmware-stm32/cubemx/STM32H743VIT6.weact-v1.2.ioc')
        text = reference.read_text(encoding='utf-8')
        self.assertIn('PC8.GPIO_Label=P1_30_C8__MicroSD_D0\n', text)
        self.assertIn('PD6.GPIO_Label=P1_13_D6__SPI_Flash_CS_VIA_SB3\n', text)
        generate.validate(generate.load())


if __name__ == '__main__':
    unittest.main()
