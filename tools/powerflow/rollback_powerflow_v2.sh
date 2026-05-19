#!/usr/bin/env bash
set -e

cd "$HOME/energy-brain/energy-brain-addon"

cp backups/powerflow/responsive.py.1779210162.bak    energy_brain/ui/components/responsive.py

cp backups/powerflow/tesla_fusion.py.1779210162.bak    energy_brain/ui/themes/tesla_fusion.py

pkill -9 -f "energy_brain.web_ui" || true
sleep 2

nohup python3 -m energy_brain.web_ui >/tmp/energy_brain.log 2>&1 &

echo
echo "ROLLBACK COMPLETE"
