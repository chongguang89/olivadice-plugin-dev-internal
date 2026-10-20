#!/usr/bin/env python3
# coding=UTF-8
"""
把 opk 解包成插件文件夹，供修改后重新打包。

用法：
    python3 unpack_opk.py <插件.opk> [输出目录]

特性：
    - 只读原 opk，不修改；
    - 自动处理"包内多套了一层文件夹"的不规范包；
    - 跳过 __pycache__ / *.pyc / .DS_Store / *.bak；
    - 解包后打印文件清单与 app.json 关键字段，便于核对。
"""
import json
import os
import sys
import zipfile

SKIP_SUFFIX = (".pyc", ".pyo", ".bak")
SKIP_NAMES = {".DS_Store"}


def unpack(opk_path, out_dir=None):
    opk_path = os.path.abspath(opk_path)
    if not os.path.isfile(opk_path):
        print(f"[x] 文件不存在：{opk_path}")
        return 1

    name = os.path.splitext(os.path.basename(opk_path))[0]
    out_dir = os.path.abspath(out_dir) if out_dir else os.path.join(os.getcwd(), name)

    with zipfile.ZipFile(opk_path) as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]

        # 判断是否所有文件都在同一个顶层文件夹里（不合规的包）
        tops = {n.split("/")[0] for n in names}
        prefix = ""
        if len(tops) == 1 and all("/" in n for n in names):
            prefix = next(iter(tops)) + "/"
            print(f"[!] 这个包套了一层文件夹「{prefix[:-1]}/」，已自动展平")

        kept = []
        os.makedirs(out_dir, exist_ok=True)
        for n in names:
            rel = n[len(prefix):] if prefix and n.startswith(prefix) else n
            if not rel:
                continue
            base = os.path.basename(rel)
            if base in SKIP_NAMES or base.endswith(SKIP_SUFFIX) or "__pycache__" in rel.split("/"):
                print(f"[skip] {n}")
                continue
            target = os.path.join(out_dir, rel)
            os.makedirs(os.path.dirname(target), exist_ok=True) if os.path.dirname(target) else None
            with zf.open(n) as src, open(target, "wb") as dst:
                dst.write(src.read())
            kept.append(rel)

    print(f"[√] 已解包到 {out_dir}")
    print(f"    文件清单：{kept}")

    app_json = os.path.join(out_dir, "app.json")
    if os.path.isfile(app_json):
        try:
            with open(app_json, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            print(f"    name={cfg.get('name')}  namespace={cfg.get('namespace')}  "
                  f"version={cfg.get('version')}  author={cfg.get('author')}")
            if cfg.get("name") != cfg.get("namespace"):
                print("[!] name 与 namespace 不一致，加载可能异常（先别擅自改，问用户）")
        except Exception as e:
            print(f"[!] app.json 解析失败：{e}")
    else:
        print("[!] 包内没有 app.json")

    missing = [f for f in ("__init__.py", "main.py") if not os.path.isfile(os.path.join(out_dir, f))]
    if missing:
        print(f"[!] 缺少文件：{', '.join(missing)}，需要补齐后再打包")

    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    return unpack(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)


if __name__ == "__main__":
    sys.exit(main())
