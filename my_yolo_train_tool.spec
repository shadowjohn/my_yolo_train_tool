# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['my_yolo_train_tool.py'],
    pathex=[],
    binaries=[],
    datas=[('www', 'www')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['_ssl', '_bz2', '_lzma', 'pyconfig', 'pytorch', 'torch', 'sqlite3', 'pandas', 'IPython', 'scipy', 'pygments', 'pyinstaller', 'tensorflow', 'unittest', 'doctest', 'pillow', 'av', 'setuptools', 'PIL'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='my_yolo_train_tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='metadata.txt',
    icon=['pic\\icon.ico'],
)
