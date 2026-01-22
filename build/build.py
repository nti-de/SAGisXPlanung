import ast
import re
import shutil
from pathlib import Path

SRC_NAME = "SAGisXPlanung"
SRC = Path("src") / SRC_NAME
TARGET_NAME = SRC_NAME + "_pro"
DST = Path("dist") / TARGET_NAME

class PluginRewriter(ast.NodeTransformer):
    ACTION_STRING_VARS = {
        "open_xplan_object_action_text",
    }

    def visit_Assign(self, node):
        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in self.ACTION_STRING_VARS
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            node.value.value = self._rewrite_action_string(node.value.value)

        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "RELEASE"
            and isinstance(node.value, ast.Constant)
            and node.value.value is False
        ):
            node.value = ast.Constant(value=True)

        return self.generic_visit(node)

    def _rewrite_action_string(self, text: str) -> str:
        return (
            text
            .replace(f"from {SRC_NAME}.", f"from {TARGET_NAME}.")
            .replace(f"import {SRC_NAME}", f"import {TARGET_NAME}")
            .replace(f"'{SRC_NAME}'", f"'{TARGET_NAME}'")
            .replace(f"plugins['{SRC_NAME}']", f"plugins['{TARGET_NAME}']")
        )

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name == SRC_NAME or alias.name.startswith(SRC_NAME + "."):
                alias.name = TARGET_NAME + alias.name[len(SRC_NAME):]
        return node

    def visit_ImportFrom(self, node):
        if node.module == SRC_NAME or (
            node.module and node.module.startswith(SRC_NAME + ".")
        ):
            node.module = TARGET_NAME + node.module[len(SRC_NAME):]
        return node

    def visit_Call(self, node):
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "reload"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "importlib"
            and node.args
        ):
            arg = node.args[0]
            if isinstance(arg, ast.Name) and arg.id == SRC_NAME:
                arg.id = TARGET_NAME

            elif (
                isinstance(arg, ast.Attribute)
                and self._is_myplugin_attr(arg)
            ):
                self._rewrite_attr(arg)

        return self.generic_visit(node)

    def _is_myplugin_attr(self, node):
        while isinstance(node, ast.Attribute):
            node = node.value
        return isinstance(node, ast.Name) and node.id == SRC_NAME

    def _rewrite_attr(self, node):
        # Walk down to the root Name node
        while isinstance(node.value, ast.Attribute):
            node = node.value
        if isinstance(node.value, ast.Name) and node.value.id == SRC_NAME:
            node.value.id = TARGET_NAME


if DST.exists():
    shutil.rmtree(DST)

shutil.copytree(SRC, DST)

for py in DST.rglob("*.py"):
    tree = ast.parse(py.read_text(encoding="utf-8"))
    tree = PluginRewriter().visit(tree)
    ast.fix_missing_locations(tree)
    py.write_text(ast.unparse(tree), encoding="utf-8")


metadata = DST / "metadata.txt"
text = metadata.read_text(encoding="utf-8")
text = re.sub(r'(?m)^\s*name\s*=.*$',f'name=SAGis XPlanung', text)
text = re.sub(r'(?m)^\s*icon\s*=.*$',f'icon=gui/resources/sagis_dev_icon.png', text)
metadata.write_text(text, encoding="utf-8")


def rewrite_ui_text(path, src, target):
    text = path.read_text(encoding="utf-8")
    if src not in text:
        return False

    path.write_text(text.replace(src, target), encoding="utf-8")
    return True

for ui in DST.rglob("*.ui"):
    rewrite_ui_text(ui, SRC_NAME, TARGET_NAME)