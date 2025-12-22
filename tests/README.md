# Tests

Tests in this directory track changes in hayagriva, making sure the normalization is not too zealous.

Run all tests:

```shell
uv run tests/run_tests.py
```

Add a test:

1. Create `tests/normalize/⟨test-name⟩.toml` and write `input_csl`.
2. Execute `UPDATE_TEST=1 uv run tests/run_tests.py tests/normalize/⟨test-name⟩.toml`.
3. Copy the stdout and continue editing the file.
