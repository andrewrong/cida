import pathlib
import shutil
import subprocess
import tempfile
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
VERIFY = PROJECT_ROOT / "scripts/verify-app-architectures.sh"


class UniversalAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.root = pathlib.Path(cls.directory.name)
        source = cls.root / "main.c"
        source.write_text("int main(void) { return 0; }\n")
        for arch in ("arm64", "x86_64"):
            subprocess.run(
                ["xcrun", "clang", "-arch", arch, "-mmacosx-version-min=15.0",
                 str(source), "-o", str(cls.root / arch)],
                check=True, capture_output=True,
            )
        subprocess.run(
            ["lipo", "-create", str(cls.root / "arm64"), str(cls.root / "x86_64"),
             "-output", str(cls.root / "universal")],
            check=True, capture_output=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def verify(self, main_arch, helper_arch="universal"):
        with tempfile.TemporaryDirectory() as directory:
            app = pathlib.Path(directory) / "App With Spaces.app"
            main = app / "Contents/MacOS/Cida"
            helper = app / "Contents/Frameworks/Sparkle.framework/Versions/B/Autoupdate"
            for destination, arch in ((main, main_arch), (helper, helper_arch)):
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.root / arch, destination)
            (app / "Contents/Info.plist").write_text("Not executable code\n")
            return subprocess.run(
                ["zsh", str(VERIFY), str(app)], capture_output=True, text=True,
            )

    def test_rejects_the_arm_only_release(self):
        result = self.verify("arm64")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Contents/MacOS/Cida", result.stderr)

    def test_accepts_both_architectures(self):
        result = self.verify("universal")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_a_thin_nested_helper(self):
        for arch in ("arm64", "x86_64"):
            with self.subTest(arch=arch):
                result = self.verify("universal", arch)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Autoupdate", result.stderr)

    def test_rejects_a_missing_app(self):
        result = subprocess.run(
            ["zsh", str(VERIFY), str(self.root / "missing.app")],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 66)


if __name__ == "__main__":
    unittest.main()
