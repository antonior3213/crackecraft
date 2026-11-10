# CrackeCraft APK Launcher

Launcher de escritorio para instalar y abrir una APK de Minecraft en un entorno Android. Funciona en Windows mediante ADB y en Linux mediante Waydroid o ADB. **No ejecuta una APK directamente en Windows/Linux ni incluye un emulador**: abre un emulador Android ya instalado en Windows, o Waydroid/otro Android con ADB en Linux.

## Usar en Windows

1. Instala y abre un emulador Android que permita ADB, por ejemplo el emulador de Android Studio o uno de terceros.
2. Habilita ADB/depuración en el emulador y acepta el aviso de autorización si aparece.
3. Ejecuta `dist\CrackeCraft.exe`.
4. Pulsa **Buscar dispositivos**. Si CrackeCraft no encuentra ADB, ve a Ajustes → **Buscar…** y selecciona `adb.exe` (Android SDK Platform-Tools o el ADB incluido con tu emulador).
5. Selecciona el archivo `.apk`. Para Bedrock, el identificador predeterminado es `com.mojang.minecraftpe`.
6. Selecciona el emulador conectado y pulsa **Instalar y jugar**.

Una conexión ADB correcta aparece como `device` al ejecutar `adb devices`. Si aparecen varios destinos, escoge el emulador correcto en la lista. Una instalación nueva puede tardar. La guía oficial de Android documenta `adb devices` y `adb install` para emuladores y dispositivos conectados ([ADB](https://developer.android.com/tools/adb)).

### Opción rápida en Windows: BlueStacks

BlueStacks incluye el emulador Android, así que no hace falta crear un dispositivo virtual con Android Studio.

1. Descarga e instala [BlueStacks 5](https://www.bluestacks.com/es/index.html) desde su sitio oficial.
2. Abre BlueStacks y, desde su barra lateral, pulsa **Instalar APK**. Elige tu archivo `.apk` (también puedes arrastrarlo a la ventana). Esto instala y abre el juego directamente en BlueStacks; no necesitas ADB ni CrackeCraft para esta opción.
3. Para instalar desde CrackeCraft: en BlueStacks abre **Ajustes → Avanzado** y activa **Android Debug Bridge (ADB)**. En CrackeCraft, abre **Ajustes**, selecciona `C:\Program Files\BlueStacks_nxt\HD-Adb.exe` (si BlueStacks se instaló en otra carpeta, localiza ahí `HD-Adb.exe`), guarda y pulsa **Buscar de nuevo** en **Dispositivo Android**. Cuando aparezca el dispositivo, selecciona la APK y pulsa **Instalar y jugar**.

La ruta de ADB indicada es la habitual de BlueStacks 5 y puede variar según dónde se instaló. Consulta las instrucciones oficiales para [instalar BlueStacks](https://support.bluestacks.com/hc/es/articles/360061525271-C%C3%B3mo-descargar-e-instalar-BlueStacks-5) y [activar ADB](https://support.bluestacks.com/hc/es/articles/23925869130381-C%C3%B3mo-habilitar-Android-Debug-Bridge-en-BlueStacks-5).

## Usar en Linux

- **Waydroid:** instala, inicializa e inicia Waydroid. En modo automático CrackeCraft lo usa si encuentra el comando `waydroid`.
- **Otro emulador/ADB:** instala Android SDK Platform-Tools, inicia el emulador con ADB habilitado y selecciona ADB en Ajustes si hace falta.

Selecciona la APK y el destino Android, y pulsa **Instalar y jugar**. Waydroid documenta los comandos `waydroid app install` y `waydroid app launch`, además de que algunas APK solo incluyen bibliotecas ARM y no funcionan en contenedores x86_64 ([instalar y ejecutar apps](https://docs.waydro.id/usage/install-and-run-android-applications)).

## Ejecutar desde el código

Se requiere Python 3.10+ y una sesión de escritorio compatible con Qt.

### Windows PowerShell

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -e .
.
run-windows.bat
```

### Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
chmod +x run-linux.sh
./run-linux.sh
```

## Compilar

Compila en el sistema operativo de destino.

- **Windows:** ejecuta `build-windows.ps1`. Genera el ejecutable de un archivo `dist\CrackeCraft.exe`. Si Inno Setup 6 está instalado, también genera `dist\installer\CrackeCraft-Setup.exe` usando `installer.iss`.
- **Linux:** `./build-linux.sh` genera `dist/CrackeCraft/`. Instala `appimagetool` y ejecuta `./build-appimage.sh` para crear un AppImage.

El emulador Android debe instalarse por separado. No se distribuye Minecraft ni se elude el inicio de sesión del juego; la APK inicia su propio flujo de cuenta.

## Pruebas

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Arquitectura

```text
src/crackecraft/
  config.py              Preferencias Android/ADB
  services/apk.py        Validación APK, descubrimiento ADB, instalación y lanzamiento
  ui/main_window.py      Interfaz CrackeCraft
  workers.py             Tareas de instalación fuera del hilo visual
  assets/hero.svg        Ilustración local
```
