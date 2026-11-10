# CrackeCraft

Launcher de escritorio para **Minecraft: Java Edition** en Windows 10/11 y Linux. La implementación usa las APIs de lanzamiento de `minecraft-launcher-lib` para leer el catálogo Mojang, descargar/verificar Vanilla y construir el comando de juego. CrackeCraft no contiene archivos del juego.

## Funciones implementadas

- Interfaz oscura adaptable con Inicio, Versiones, Instalaciones, Mods, Ajustes y Cuenta.
- Catálogo Mojang con lanzamientos estables y snapshots; instalación y reparación de archivos.
- Perfiles separados: cada perfil conserva su directorio propio de mundos, ajustes y carpeta `mods`; bibliotecas y assets compartidos se guardan una sola vez.
- Inicio de sesión Microsoft mediante navegador del sistema, OAuth con PKCE y comprobación de titularidad Minecraft. No hay modo offline/cracked.
- Renovación de sesión. Los tokens se guardan en Windows Credential Manager o el almacén seguro del escritorio Linux mediante `keyring`; las contraseñas nunca se solicitan ni guardan.
- Memoria, Java opcional, argumentos JVM, consola y registro local con filtrado de tokens.
- Detección de Java del sistema; las versiones modernas de Minecraft incluyen la selección/descarga de runtime gestionada por `minecraft-launcher-lib`.
- La sección Mods abre la carpeta de mods del perfil. Fabric y Forge no están habilitados en esta versión, por lo que no se presentan como funcionalidad operativa.

## Requisitos de inicio de sesión

Registra una aplicación propia en Microsoft Entra:

1. Habilita cuentas personales Microsoft en los tipos de cuenta compatibles.
2. Añade la plataforma **Mobile and desktop applications** con redirect URI `http://localhost`.
3. Habilita el flujo de cliente público y no crees/uses un client secret.
4. Copia el Application (client) ID a **Ajustes → Microsoft App Client ID**.

Microsoft documenta el redirect localhost para clientes de escritorio. El launcher usa un puerto local efímero, `state` y PKCE. El servicio Microsoft/Minecraft también debe aceptar el registro de aplicación; si la API de Minecraft rechaza el cliente, la autenticación mostrará el error del servicio. Para jugar se necesita una cuenta con Minecraft: Java Edition.

## Ejecutar desde el código

Se requiere Python 3.10 o posterior. Desde la carpeta del proyecto:

### Windows PowerShell

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e .
.
run-windows.bat
```

### Ubuntu/Debian/Fedora

Instala Python, `venv` y los paquetes de Qt que requiera tu distribución (por ejemplo `python3-venv` en Debian/Ubuntu):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
chmod +x run-linux.sh
./run-linux.sh
```

En Linux se necesita una sesión de escritorio con Qt. Para guardar sesiones, `keyring` necesita el servicio de llaves de la sesión (Secret Service/libsecret o KWallet). Si no hay un almacén seguro, CrackeCraft no persiste el token y explica el problema.

## Compilar

Los paquetes deben compilarse en el sistema operativo de destino.

### Windows y Setup.exe

Ejecuta `build-windows.ps1` en PowerShell. Crea `dist/CrackeCraft/`. Para generar el instalador de Windows, instala **Inno Setup 6** y compila `installer.iss`; el resultado se guarda en `dist/installer/CrackeCraft-Setup.exe`.

### Linux portable y AppImage

Ejecuta `./build-linux.sh` para producir `dist/CrackeCraft/`. Para AppImage, instala `appimagetool` en esa máquina y ejecuta `./build-appimage.sh`; genera `CrackeCraft-x86_64.AppImage`. PyInstaller/AppImage no pueden producir el ejecutable de Windows desde Linux ni viceversa.

## Estructura

```text
src/crackecraft/
  app.py                 Inicio y configuración de Qt
  config.py              Preferencias de aplicación
  services/
    auth.py              OAuth Microsoft y renovación
    credential_store.py  Almacén seguro del sistema
    minecraft.py         Catálogo, instalación y lanzamiento Vanilla
  ui/main_window.py      Interfaz y navegación
  workers.py             Tareas de red/instalación fuera del hilo visual
  assets/hero.svg        Arte vectorial local
packaging/               Icono y entrada de escritorio Linux
tests/                   Pruebas de servicios
```

## Límites de esta versión

Es un launcher Vanilla funcional de Minecraft Java. No instala Fabric, Forge ni mods por sí mismo; la carpeta Mods está separada por perfil para evitar mezclar datos. No se han generado binarios en este entorno Windows: AppImage debe generarse en Linux y el Setup.exe mediante PyInstaller/Inno Setup en Windows. La autenticación real requiere el Client ID configurado y aprobación del servicio Microsoft/Minecraft.
