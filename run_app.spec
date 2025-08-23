# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# --- Inizio Modifiche Cruciali ---
# Raccogliamo TUTTI i file di dati di Streamlit, inclusi i metadati
# Questo è il metodo più robusto per risolvere 'PackageNotFoundError'
streamlit_datas = collect_data_files('streamlit')

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app.py', '.'),
        ('genera_orario_engine.py', '.'),
        ('default_data.py', '.')
    ] + streamlit_datas,  # Aggiungiamo i file di Streamlit qui
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GeneratoreOrario',  # Nome del nostro eseguibile
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # Equivalente a --windowed
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GeneratoreOrario',
)