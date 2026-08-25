import pytest
from ape.intelligence.execution.policy import translate_sandbox_path

def test_translate_sandbox_path_basic_file():
    assert translate_sandbox_path("/workspace/foo.py") == "foo.py"
    assert translate_sandbox_path("\\workspace\\foo.py") == "foo.py"

def test_translate_sandbox_path_nested_file():
    assert translate_sandbox_path("/workspace/src/foo.py") == "src/foo.py"

def test_translate_sandbox_path_traversal():
    assert translate_sandbox_path("/workspace/../outside.py") == "../outside.py"

def test_translate_sandbox_path_deep_traversal():
    assert translate_sandbox_path("/workspace/../../outside.py") == "../../outside.py"

def test_translate_sandbox_path_windows_traversal():
    assert translate_sandbox_path("/workspace/..\\..\\outside.py") == "..\\..\\outside.py"

def test_translate_sandbox_path_normal_relative():
    # Regression: shouldn't touch normal relative paths
    assert translate_sandbox_path("src/foo.py") == "src/foo.py"
    assert translate_sandbox_path("../foo.py") == "../foo.py"

def test_translate_sandbox_path_absolute_windows():
    assert translate_sandbox_path("C:\\Windows\\System32\\cmd.exe") == "C:\\Windows\\System32\\cmd.exe"
    assert translate_sandbox_path("C:/workspace/foo.py") == "C:/workspace/foo.py"

def test_translate_sandbox_path_unc_path():
    assert translate_sandbox_path("\\\\server\\share\\test.py") == "\\\\server\\share\\test.py"

def test_translate_sandbox_path_exact_match():
    assert translate_sandbox_path("/workspace") == "."
    assert translate_sandbox_path("\\workspace") == "."

def test_docker_namespace_preservation_after_translation():
    """
    Proves that translating /workspace/foo.py to foo.py still writes to
    /workspace/foo.py inside Docker because of cwd='/workspace'.
    """
    original_agent_intent = "/workspace/foo.py"
    translated_path = translate_sandbox_path(original_agent_intent)

    # In DockerSandboxExecutor:
    docker_cwd = "/workspace"
    import pathlib
    # Inside docker, writing to translated_path relative to docker_cwd
    docker_effective_path = pathlib.PurePosixPath(docker_cwd) / translated_path

    assert str(docker_effective_path) == "/workspace/foo.py"
