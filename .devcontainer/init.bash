#!/bin/bash
export DEBIAN_FRONTEND=noninteractive

sudo apt-get update && sudo apt-get install -y --no-install-recommends \
    entr \
    vim-nox

# "break-system-packages" is a lazy workaround for newer Python versions. A
# better solution is to create a venv. But this would make this script
# increasingly complex (when we consider ensuring that the bin folder is on the
# path). For now, this will do.
pip install --user --break-system-packages pipx
pipx install pre-commit

[ -d env ] || python3 -m venv env
./env/bin/pip install -e ".[dev]"

[ -f .devcontainer/init-personal.bash ] && \
  bash .devcontainer/init-personal.bash || \
  echo ".devcontainer/init-personal.bash not present. Skipping."
