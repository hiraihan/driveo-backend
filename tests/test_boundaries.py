import ast, pathlib

def test_no_cross_module_model_imports():
    root = pathlib.Path("app/modules")
    for f in root.rglob("*.py"):
        mod = f.relative_to(root).parts[0]
        for node in ast.walk(ast.parse(f.read_text())):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app.modules."):
                parts = node.module.split(".")
                if len(parts) >= 4 and parts[2] != mod and parts[3] in {"models", "checklist_models", "routers"}:
                    raise AssertionError(f"{f} imports {node.module}")

def test_mocks_not_used_in_app():
    for f in pathlib.Path("app").rglob("*.py"):
        if "mocks" not in f.parts:
            assert "app.mocks" not in f.read_text(), f
