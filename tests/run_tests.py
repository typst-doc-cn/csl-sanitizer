import tomllib
import xml.etree.ElementTree as ET
from collections.abc import Generator
from dataclasses import dataclass
from difflib import unified_diff
from pathlib import Path
from sys import argv
from typing import Self

from csl_sanitizer.csl import check_csl, dump_csl, load_csl
from csl_sanitizer.normalize import normalize_csl
from csl_sanitizer.util import get_bool_env, ns

ET.register_namespace("", ns["cs"])  # Required by `write_csl`

TEST_DIR = Path(__file__).parent


@dataclass
class TestCase:
    input_csl: str
    input_error: str
    normalizations: list[str]
    diff: str

    @classmethod
    def load(cls, file: Path, for_update=False) -> Self:
        raw = tomllib.loads(file.read_text(encoding="utf-8"))

        if not for_update:
            return cls(
                input_csl=raw["input_csl"],
                input_error=raw["input_error"],
                normalizations=raw["normalizations"],
                diff=raw["diff"],
            )
        else:
            return cls(
                input_csl=raw["input_csl"],
                input_error="",
                normalizations=[],
                diff="",
            )


def parse_args(args: list[str]) -> Generator[Path]:
    """Determine cases to be tested."""
    if "all" in args or not args:
        yield from TEST_DIR.glob("normalize/*.toml")
    else:
        yield from (Path(x) for x in args)


if __name__ == "__main__":
    update_test = get_bool_env("UPDATE_TEST")
    test_specs = parse_args(argv[1:])

    for test_spec in test_specs:
        if not update_test:
            print(f"📝 Testing {test_spec.stem}…")
        else:
            print(f"📝 Generating a test for {test_spec.stem}…")
        test = TestCase.load(test_spec, for_update=update_test)

        input_error = check_csl(test.input_csl)
        if not update_test:
            assert input_error == test.input_error, (
                f"Expected error before normalization: {test.input_error}, got: {input_error}"
            )
        else:
            assert input_error is not None, (
                "Expected an error before normalization, got none."
            )

        style = load_csl(test.input_csl)
        normalizations = [*normalize_csl(style)]
        if not update_test:
            assert normalizations == test.normalizations, (
                f"Expected normalizations: {test.normalizations}, got: {normalizations}"
            )
        output_csl = dump_csl(style)

        output_error = check_csl(output_csl)
        assert output_error is None, (
            f"Expected no error after normalization, got: {output_error}"
        )

        diff = "\n".join(
            unified_diff(
                test.input_csl.splitlines(),
                output_csl.splitlines(),
                "Original",
                "Sanitized",
            )
        )
        if not update_test:
            assert diff == test.diff, f"Expected diff:\n{test.diff}\nGot:\n{diff}"

        if update_test:
            print(f"""
input_error = {input_error!r}

normalizations = {normalizations!r}

diff = '''
{diff}'''
""")
