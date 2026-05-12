set -euo pipefail

REPO="https://github.com/buildsbypat/paul.git"
APP_ROOT="/opt/paul"
APP_DIR="${APP_ROOT}/app"
DATA_DIR="${APP_ROOT}/data"
SERVICE_NAME="paul-bot"
SERVICE_FILE="paul-bot.service"
RUNTIME_USER="paul"
DEPLOY_USER="paul-deploy"
PYTHON_BIN=""
DEPLOY_HOME=""
DEPLOY_GROUP=""
SYSTEMCTL_BIN="(command -v systemctl)"

if [[ -t 1 ]]; then
