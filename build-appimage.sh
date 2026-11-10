#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
command -v appimagetool >/dev/null || { echo "Instala appimagetool y vuelve a ejecutar este script." >&2; exit 1; }
[[ -x dist/CrackeCraft/CrackeCraft ]] || { echo "Primero ejecuta ./build-linux.sh" >&2; exit 1; }
rm -rf AppDir
mkdir -p AppDir/opt/crackecraft AppDir/usr/bin AppDir/usr/share/applications
cp -a dist/CrackeCraft/. AppDir/opt/crackecraft/
ln -s ../../opt/crackecraft/CrackeCraft AppDir/usr/bin/crackecraft
cp packaging/crackecraft.desktop AppDir/crackecraft.desktop
cp packaging/crackecraft.desktop AppDir/usr/share/applications/crackecraft.desktop
cp packaging/crackecraft.svg AppDir/crackecraft.svg
cat > AppDir/AppRun <<'EOF'
#!/usr/bin/env sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/opt/crackecraft/CrackeCraft" "$@"
EOF
chmod +x AppDir/AppRun
ARCH="$(uname -m)" appimagetool AppDir CrackeCraft-x86_64.AppImage
