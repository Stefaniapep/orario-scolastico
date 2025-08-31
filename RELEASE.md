# Release Process Documentation

Questo documento descrive il processo di release automatizzato per GeneraOrarioApp.

## 🎯 Panoramica

Il sistema di release automatizzato permette di:

- ✅ Gestire il versioning semantico automaticamente
- ✅ **Trigger automatico**: Commit su `version.py` → GitHub Actions build → Tag automatico
- ✅ Creare build Windows con PyInstaller via GitHub Actions
- ✅ Pubblicare automaticamente release su GitHub
- ✅ Generare artifact scaricabili
- ✅ Supportare build locali per testing

## Workflow Semplificato

### **Flusso Automatico:**

1. **Developer** aggiorna versione in `version.py` e fa commit
2. **GitHub Actions** rileva la modifica e inizia la build
3. **Se build OK** → Crea automaticamente tag `v{version}` + Release GitHub
4. **Se build FAIL** → Nessun tag creato

### **Vantaggi:**

- 🚀 **Un solo comando** per release completa
- 🛡️ **Sicurezza**: Tag solo se build successful
- 📝 **Tracciabilità**: Ogni release legata a commit specifico
- ⚡ **Velocità**: No step manuali dopo il commit

## Prerequisiti

### Per Release Automatiche (GitHub Actions)

- Repository con accesso GitHub Actions abilitato
- Commit su file `version.py` (righe `__version__`, `__app_name__`, `__description__`, `__author__`)

### Per Build Locali

- Python 3.11+
- Dipendenze installate: `pip install -r requirements.txt`
- PyInstaller: `pip install pyinstaller`
- Git configurato

## 🚀 Processo di Release

### 1. Release Automatica (Consigliata) 🌟

```bash
# 1. Aggiorna la versione in version.py
# Modifica __version__ = "1.2.0"

# 2. Commit delle modifiche
git add version.py
git commit -m "Release v1.2.0 - Update version info"

# 3. Push per triggerare GitHub Actions
git push origin main

# 🎉 GitHub Actions fa il resto automaticamente!
```

### 2. Build Locale (Per Testing)

```bash
# Con script helper
.\release.ps1 -BuildOnly

# Manuale
pyinstaller --clean --name "GeneraOrarioApp" --onefile --console \
    --add-data "app.py;." \
    --add-data "config.json;." \
    --add-data "version.py;." \
    --collect-all streamlit \
    --collect-all ortools \
    --noconfirm streamlit_wrapper.py
```

### 3. Release Manuale da GitHub UI

1. Vai su **Actions** → **Build and Release GeneraOrarioApp**
2. Clicca **Run workflow**
3. Inserisci versione (es. `1.2.0`)
4. Clicca **Run workflow**

## Output della Pipeline

### **Artifact Generato:**

```
GeneraOrarioApp-v1.2.0-windows-x64.zip
├── GeneraOrarioApp.exe      # Eseguibile ottimizzato
├── config-template.json     # Template configurazione
├── BUILD_INFO.txt          # Info build e versione
├── README.md               # Documentazione
└── LICENSE                 # Licenza
```

### **GitHub Release Automatica:**

- ✅ **Release Notes** generati automaticamente
- ✅ **Download link** per l'eseguibile
- ✅ **Tag automatico** creato dopo build successful
- ✅ **Metadata completi** (commit, data, size)

## 🔧 Configurazione GitHub Actions

### File: `.github/workflows/build-release.yml`

**Nuovi Trigger Events:**

- ✅ **Push su `main`** con modifiche a `version.py` → Release automatica
- ✅ **Trigger manuale** → Build di test

**Trigger Intelligente:**

```yaml
on:
  push:
    branches: [ main ]
    paths: 
      - 'version.py'  # Solo quando cambia version.py
```

**Fasi di Build:**

1. **Version Change Detection** - Verifica se righe importanti sono cambiate
2. **Setup Environment** - Python 3.11, cache dipendenze
3. **Build Verification** - Test import e funzionalità
4. **PyInstaller Build** - Creazione eseguibile Windows
5. **Package Creation** - ZIP con documentazione
6. **Artifact Upload** - Upload su GitHub
7. **🆕 Tag Creation** - Tag automatico dopo build successful
8. **Release Creation** - Release automatica con artifact

## 📊 Versioning Strategy

### Formato Versioni

- **Semantic Versioning**: `MAJOR.MINOR.PATCH` (es. `1.2.0`)
- **Tag Git**: `v{version}` (es. `v1.2.0`) - **Creato automaticamente**

### Incrementi di Versione

- **MAJOR** (`1.0.0` → `2.0.0`): Breaking changes, incompatibilità
- **MINOR** (`1.0.0` → `1.1.0`): Nuove funzionalità, backward compatible
- **PATCH** (`1.0.0` → `1.0.1`): Bug fix, hotfix

### Gestione Automatica

```python
# version.py - TRIGGER FILE
__version__ = "1.0.0"  # ← Modifica qui triggera GitHub Actions
__app_name__ = "GeneraOrarioApp"
__description__ = "Generatore di Orari Scolastici"  
__author__ = "Stefania Pepe"
```

## 🐛 Troubleshooting

### Build Fallisce con Errori di Import

```bash
# Verifica dipendenze localmente
python -c "import streamlit, ortools, pandas, openpyxl; print('OK')"

# Reinstalla dipendenze
pip install -r requirements.txt --force-reinstall
```

### GitHub Actions Non Si Attivano

- ✅ Verifica che sia stata modificata una delle righe trigger in `version.py`
- ✅ Controlla che il commit sia su branch `main`
- ✅ Verifica che il repository abbia Actions abilitati
- ✅ Controlla syntax del file YAML

### Eseguibile Non Funziona

```bash
# Test locale dell'eseguibile
dist/GeneraOrarioApp.exe --help

# Controlla log di PyInstaller
cat build/GeneraOrarioApp/warn-GeneraOrarioApp.txt
```

### Tag Non Creato Dopo Build Successful

- ✅ Controlla i log di GitHub Actions step "Create Git Tag"
- ✅ Verifica permessi del token GitHub
- ✅ Controlla che non esista già un tag con la stessa versione

## 📋 Checklist di Release

### Pre-Release

- [ ] Codice testato e funzionante
- [ ] Documentazione aggiornata
- [ ] Dipendenze in `requirements.txt` aggiornate
- [ ] Versione incrementata correttamente in `version.py`

### Durante Release

- [ ] Commit pushato su `main`
- [ ] GitHub Actions avviate automaticamente
- [ ] Build completata con successo
- [ ] Tag creato automaticamente

### Post-Release

- [ ] Artifact scaricabile e funzionante
- [ ] Release notes verificate
- [ ] Eseguibile testato su sistemi di destinazione

## 🎮 Comandi Rapidi

```bash
# Stato corrente
python -c "from version import get_version; print(f'Current: {get_version()}')"

# Release completa (nuovo workflow)
.\release.ps1 1.2.0

# Build di test rapido
.\release.ps1 -BuildOnly

# Monitora GitHub Actions
# https://github.com/Stefaniapep/orario-scolastico/actions

# Lista release disponibili
git tag -l "v*"
```

## 🔍 Monitoring & Debug

### GitHub Actions Status

```bash
# URL diretta per monitorare le Actions
https://github.com/Stefaniapep/orario-scolastico/actions
```

### Log Debugging

- **Setup Step**: Verifica dipendenze e environment
- **Version Detection**: Controlla parsing della versione
- **Build Step**: Output di PyInstaller
- **Tag Creation**: Conferma creazione tag automatico

## 📞 Supporto

Per problemi con il processo di release:

1. Controlla i log di GitHub Actions
2. Verifica la configurazione locale
3. Consulta la sezione Troubleshooting
4. Apri un issue nel repository
