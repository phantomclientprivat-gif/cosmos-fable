#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE}")" && pwd)"
cd "$PROJECT_DIR"

echo "1. Создаем виртуальное окружение Python..."
python3 -m venv venv

echo "2. Устанавливаем зависимости из requirements.txt..."
"$PROJECT_DIR/venv/bin/pip" install --upgrade pip
"$PROJECT_DIR/venv/bin/pip" install -r requirements.txt

echo "3. Создаем ярлык приложения в меню..."
mkdir -p ~/.local/share/applications
cat << EOT > ~/.local/share/applications/cosmos-fable.desktop
[Desktop Entry]
Name=Cosmos Fable
Comment=Tracker for nutrition, workouts, and study notes
Exec=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/main.py
Path=$PROJECT_DIR
Icon=$PROJECT_DIR/assets/icon.png
Terminal=false
Type=Application
Categories=Utility;
EOT

chmod +x ~/.local/share/applications/cosmos-fable.desktop
update-desktop-database ~/.local/share/applications 2>/dev/null || true
kbuildsycoca6 --noincremental 2>/dev/null || true

echo "Готово! Ярлык создан, запускаем Cosmos Fable..."
"$PROJECT_DIR/venv/bin/python" "$PROJECT_DIR/main.py" &
