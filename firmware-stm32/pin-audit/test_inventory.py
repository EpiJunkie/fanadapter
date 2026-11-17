"""Ignore incidental checkout files while retaining firmware coverage checks."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import generate


class FirmwareInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='pin-audit-inventory-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.firmware = self.root / 'firmware-stm32'
        shutil.copytree(generate.ROOT / 'firmware-stm32', self.firmware,
                        ignore=shutil.ignore_patterns('.pio', '__pycache__', '.DS_Store', 'Thumbs.db'))
        shutil.copy2(generate.ROOT / '.gitignore', self.root / '.gitignore')
        subprocess.run(['git', 'init', '-q'], cwd=self.root, check=True)
        subprocess.run(['git', 'add', '--', '.gitignore', 'firmware-stm32'],
                       cwd=self.root, check=True, capture_output=True)

    def check(self):
        return subprocess.run(
            [sys.executable, str(self.firmware / 'pin-audit/generate.py'), '--check'],
            cwd=self.root, capture_output=True, encoding='utf-8')

    def test_ignored_finder_file_passes_check(self):
        (self.firmware / 'src/.DS_Store').write_bytes(b'Finder metadata')
        ignored = subprocess.run(
            ['git', 'check-ignore', '--', 'firmware-stm32/src/.DS_Store'],
            cwd=self.root, capture_output=True, encoding='utf-8')
        self.assertEqual(ignored.returncode, 0, ignored.stderr)
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_new_unignored_source_fails_inventory(self):
        (self.firmware / 'src/new_driver.c').write_text('void new_driver(void) {}\n',
                                                       encoding='utf-8')
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn('Firmware file inventory changed', result.stderr)

    def test_substantive_audited_source_edit_still_fails(self):
        source = self.firmware / 'src/main.c'
        source.write_bytes(source.read_bytes() + b'\n#error Inventory regression edit\n')
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn('Audited source changed: firmware-stm32/src/main.c', result.stderr)

    def test_ignore_rule_does_not_hide_a_tracked_source_edit(self):
        with (self.root / '.gitignore').open('a', encoding='utf-8') as ignores:
            ignores.write('\nfirmware-stm32/src/main.c\n')
        source = self.firmware / 'src/main.c'
        source.write_bytes(source.read_bytes() + b'\n#error Tracked source remains audited\n')
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn('Audited source changed: firmware-stm32/src/main.c', result.stderr)

    def test_deleted_tracked_source_still_fails(self):
        (self.firmware / 'src/main.c').unlink()
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn('Audit error:', result.stderr)
        self.assertIn('main.c', result.stderr)


if __name__ == '__main__':
    unittest.main()
