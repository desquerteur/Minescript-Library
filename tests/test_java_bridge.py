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


def test_shipped_walk_lease_with_real_pyjinn(tmp_path):
    classpath = os.environ.get("MINESCRIPT_TEST_CLASSPATH")
    if not classpath:
        pytest.skip("Set MINESCRIPT_TEST_CLASSPATH to the Pyjinn and Gson jars")
    java = os.environ.get("MINESCRIPT_TEST_JAVA") or shutil.which("java")
    if not java:
        pytest.fail("The real Pyjinn bridge test requires a JDK")
    root = Path(__file__).resolve().parents[1]
    module = ast.parse((root / "travel.py").read_text(encoding="utf-8"))
    native = next(
        ast.literal_eval(node.value)
        for node in module.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "NATIVE_WALK_LEASE" for t in node.targets)
    )
    # Inject a Java API double while executing the shipped globals/functions.
    # Event registration belongs to Minescript and is not available standalone.
    pieces = ["key_listener, tick_listener = 1, 2"]
    for node in ast.parse(native).body:
        if isinstance(node, ast.Import):
            continue
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id in {"key_listener", "tick_listener"}
            for t in node.targets
        ):
            continue
        pieces.append(ast.get_source_segment(native, node))
    source = tmp_path / "shipped-walk-lease.pyj"
    source.write_text("\n\n".join(pieces) + "\n", encoding="utf-8")
    result = subprocess.run(  # noqa: S603
        [
            java,
            "--class-path",
            classpath,
            str(root / "tests" / "fixtures" / "NativeWalkLeaseProbe.java"),
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
    assert "Real Pyjinn walk lease: PASS" in result.stdout


def test_shipped_collision_snapshot_with_real_pyjinn(tmp_path):
    classpath = os.environ.get("MINESCRIPT_TEST_CLASSPATH")
    if not classpath:
        pytest.skip("Set MINESCRIPT_TEST_CLASSPATH to the Pyjinn and Gson jars")
    java = os.environ.get("MINESCRIPT_TEST_JAVA") or shutil.which("java")
    if not java:
        pytest.fail("The real Pyjinn bridge test requires a JDK")
    root = Path(__file__).resolve().parents[1]
    module = ast.parse((root / "travel.py").read_text(encoding="utf-8"))
    native = next(
        ast.literal_eval(node.value)
        for node in module.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "NATIVE_TERRAIN"
            for target in node.targets
        )
    )
    probe = next(
        node
        for node in ast.parse(native).body
        if isinstance(node, ast.FunctionDef) and node.name == "probe"
    )
    source = tmp_path / "shipped-terrain.pyj"
    source.write_text(ast.get_source_segment(native, probe) + "\n", encoding="utf-8")
    javac = Path(java).with_name("javac.exe" if os.name == "nt" else "javac")
    compilation = subprocess.run(  # noqa: S603
        [
            str(javac),
            "-classpath",
            classpath,
            "-d",
            str(tmp_path),
            str(root / "tests/fixtures/NativeTerrainProbe.java"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        cwd=tmp_path,
        check=False,
    )
    assert compilation.returncode == 0, compilation.stdout + compilation.stderr
    result = subprocess.run(  # noqa: S603
        [
            java,
            "--class-path",
            str(tmp_path) + os.pathsep + classpath,
            "NativeTerrainProbe",
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
    assert "Real Pyjinn terrain lookup: PASS" in result.stdout
