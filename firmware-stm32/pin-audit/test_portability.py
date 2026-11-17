"""Checkout line endings and native path syntax must not invalidate evidence."""

from pathlib import Path, PurePosixPath, PureWindowsPath
import shutil
import subprocess
import sys
import tempfile
import unittest

import generate


class CheckoutPortabilityTests(unittest.TestCase):
    def test_native_paths_match_json_inventory_and_resolve(self):
        json_path = 'firmware-stm32/src/main.c'
        for root, native in (
            (PurePosixPath('/checkout'), PurePosixPath('/checkout/firmware-stm32/src/main.c')),
            (PureWindowsPath(r'C:\checkout'), PureWindowsPath(r'C:\checkout\firmware-stm32\src\main.c')),
        ):
            with self.subTest(platform=type(root).__name__):
                self.assertEqual(generate.repository_path(native, root), json_path)
                self.assertEqual(root / json_path, native)

    def test_checkout_normalization_preserves_other_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.c'
            # Lone CR, whitespace, UTF-8 BOM and non-ASCII bytes are not discarded.
            content = b'\xef\xbb\xbf// caf\xc3\xa9\r\nvalue = 1; \r\n\r'
            path.write_bytes(content)
            self.assertEqual(generate.checkout_text_bytes(path),
                             b'\xef\xbb\xbf// caf\xc3\xa9\nvalue = 1; \n\r')

    def test_lf_and_crlf_fixtures_pass_but_source_edit_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(generate.ROOT / 'firmware-stm32', root / 'firmware-stm32',
                            ignore=shutil.ignore_patterns('.pio', '__pycache__', '.DS_Store', 'Thumbs.db'))
            script = root / 'firmware-stm32/pin-audit/generate.py'
            output = root / 'firmware-stm32/PIN-AUDIT.md'
            source = root / 'firmware-stm32/src/main.c'

            def run(*args):
                return subprocess.run([sys.executable, str(script), *args],
                                      capture_output=True, encoding='utf-8')

            for newline in (b'\n', b'\r\n'):
                with self.subTest(newline=newline):
                    # Include scripts, JSON, Markdown, firmware sources and .ioc files.
                    for path in root.rglob('*'):
                        if path.is_file():
                            path.write_bytes(path.read_bytes().replace(b'\r\n', b'\n')
                                             .replace(b'\n', newline))
                    self.assertIn(newline, source.read_bytes())
                    result = run('--check')
                    self.assertEqual(result.returncode, 0, result.stderr)

                    # A real C edit still fails, even with the correct line endings.
                    original = source.read_bytes()
                    source.write_bytes(original + newline + b'#error Audit regression edit' + newline)
                    result = run('--check')
                    self.assertEqual(result.returncode, 1)
                    self.assertIn('Audited source changed: firmware-stm32/src/main.c', result.stderr)
                    source.write_bytes(original)

                    expected = output.read_bytes()
                    result = run()
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(output.read_bytes(), expected)

                    # A newly generated file is UTF-8/LF; an unchanged checkout
                    # above keeps its exact bytes, including Git's CRLF choice.
                    output.unlink()
                    result = run()
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(output.read_bytes(), expected.replace(b'\r\n', b'\n'))
                    self.assertNotIn(b'\r\n', output.read_bytes())
                    result = run('--check')
                    self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
