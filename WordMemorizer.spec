# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['/Users/wangyuyang/Projects/Languages/Python/Demos/ui/main.py'],
    pathex=[],
    binaries=[],
    datas=[('/Users/wangyuyang/Projects/Languages/Python/Demos/data', 'data')],
    hiddenimports=['tkinter', 'matplotlib', 'PIL', 'pygame', 'sounddevice', 'edge_tts', 'pydub', 'sqlite3', 'scipy', 'scipy.io', 'scipy.io.wavfile', 'scipy._cyutility', 'scipy.sparse.csgraph._validation', 'scipy.sparse._matrix', 'scipy.sparse._csparsetools', 'numpy', 'numpy.core._methods', 'numpy.lib.format'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='WordMemorizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
app = BUNDLE(
    exe,
    name='WordMemorizer.app',
    icon=None,
    bundle_identifier=None,
)
