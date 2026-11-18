#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p ~/.local/share/applications

cat << EOT > ~/.local/share/applications/cosmos-fable.desktop
[Desktop Entry]
Name=Cosmos Fable
Comment=Tracker for nutrition, workouts, and study notes
Exec=python3 $PROJECT_DIR/main.py
Path=$PROJECT_DIR
Icon=$PROJECT_DIR/assets/icon.png
Terminal=false
Type=Application
Categories=Utility;
EOT

chmod +x ~/.local/share/applications/cosmos-fable.desktop
update-desktop-database ~/.local/share/applications 2>/dev/null || true
echo "Ярлык Cosmos Fable успешно добавлен в меню приложений!"
