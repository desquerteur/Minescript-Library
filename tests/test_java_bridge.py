"""Optional integration test using the installed Pyjinn interpreter and a JDK."""

import ast
import os
import shutil
import subprocess
from pathlib import Path

import pytest


def test_shipped_surface_lookup_with_real_pyjinn(tmp_path):
    classpath = os.environ.get("MINESCRIPT_TEST_CLASSPATH")
    if not classpath:
        pytest.skip("Set MINESCRIPT_TEST_CLASSPATH to the Pyjinn and Gson jars")
    java = os.environ.get("MINESCRIPT_TEST_JAVA") or shutil.which("java")
    if not java:
        pytest.fail("The real Pyjinn bridge test requires a JDK")
    root = Path(__file__).resolve().parents[1]
    module = ast.parse((root / "travel_elytra.py").read_text(encoding="utf-8"))
    native_source = next(
        ast.literal_eval(node.value)
        for node in module.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "NATIVE_FLIGHT" for target in node.targets
        )
    )
    function = next(
        node
        for node in ast.parse(native_source).body
        if isinstance(node, ast.FunctionDef) and node.name == "surfaces"
    )
    source = tmp_path / "shipped-surfaces.pyj"
    source.write_text(ast.get_source_segment(native_source, function) + "\n", encoding="utf-8")
    # Local JDK, fixed arguments, no shell. No game access or downloaded code.
    result = subprocess.run(  # noqa: S603
        [
            java,
            "--class-path",
            classpath,
            str(root / "tests" / "fixtures" / "NativeSurfaceProbe.java"),
            str(source),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        cwd=tmp_path,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Real Pyjinn surface lookup: PASS" in result.stdout
