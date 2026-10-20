#!/usr/bin/env python3
# coding=UTF-8
"""
把青果骰插件文件夹打包成 opk。

用法：
    python3 pack_opk.py <插件文件夹> [输出目录]

规则：
    - opk 本质是改了后缀的 zip，内部不能有文件夹，文件必须直接躺在根目录。
    - 必需 app.json / __init__.py / main.py（缺失只警告，仍会打包其余文件）。
    - 自动跳过 __pycache__/、.git/、*.bak、*.pyc、.DS_Store。
    - 输出目录默认是当前工作目录，不会写回插件文件夹。
"""
import os
import sys
import zipfile

REQUIRED = ["app.json", "__init__.py", "main.py"]
SKIP_DIRS = {"__pycache__", ".git"}
SKIP_SUFFIX = (".bak", ".pyc", ".pyo", ".opk", ".zip")
SKIP_NAMES = {".DS_Store"}


def pack(plugin_dir, out_dir=None):
    plugin_dir = os.path.abspath(plugin_dir)
    if not os.path.isdir(plugin_dir):
        print(f"[x] 不是文件夹：{plugin_dir}")
        return 1

    name = os.path.basename(plugin_dir.rstrip(os.sep))
    out_dir = os.path.abspath(out_dir) if out_dir else os.getcwd()
    os.makedirs(out_dir, exist_ok=True)
    opk_path = os.path.join(out_dir, name + ".opk")

    files = []
    for entry in sorted(os.listdir(plugin_dir)):
        full = os.path.join(plugin_dir, entry)
        if os.path.isdir(full):
            if entry in SKIP_DIRS:
                print(f"[skip] 目录 {entry}/")
            else:
                print(f"[warn] 目录 {entry}/ 不会被打进 opk（opk 内不能有文件夹）")
            continue
        if entry in SKIP_NAMES or entry.endswith(SKIP_SUFFIX):
            print(f"[skip] 文件 {entry}")
            continue
        files.append(entry)

    missing = [f for f in REQUIRED if f not in files]
    if missing:
        print(f"[!] 缺少必需文件：{', '.join(missing)}")

    if not files:
        print("[x] 没有可打包的文件")
        return 1

    with zipfile.ZipFile(opk_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(os.path.join(plugin_dir, f), arcname=f)

    # 复核：opk 内不能出现目录层级（青果要求直接打包文件本身）
    with zipfile.ZipFile(opk_path) as zf:
        names = zf.namelist()
    nested = [n for n in names if "/" in n or "\\" in n]

    print(f"opk 内文件（应为扁平结构）：{names}")
    if nested:
        print(f"[x] 存在目录层级，打包不合格：{nested}")
        return 1

    print(f"[√] 已生成 {opk_path}（{len(files)} 个文件）")
    print("[i] 安装：骰主把 opk 放进 plugin/app/ 下，该目录里不要存在同名文件夹，然后重启骰子")
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    return pack(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)


if __name__ == "__main__":
    sys.exit(main())
