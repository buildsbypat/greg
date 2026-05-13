#!/usr/bin/env bash

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────

REPO_URL="${REPO_URL:-https://github.com/buildsbypat/greg.git}"
REPO_BRANCH="${REPO_BRANCH:-main}"

APP_ROOT="${APP_ROOT:-/opt/greg}"
APP_DIR="${APP_ROOT}/app"
DATA_DIR="${APP_ROOT}/data"

SERVICE_NAME="${SERVICE_NAME:-greg-bot}"
SERVICE_FILE="${SERVICE_FILE:-greg-bot.service}"

RUNTIME_USER="${RUNTIME_USER:-gregbot}"
DEPLOY_USER="${DEPLOY_USER:-gregdeploy}"

PYTHON_BIN=""
DEPLOY_HOME=""
DEPLOY_GROUP=""

SYSTEMCTL_BIN="$(command -v systemctl || true)"
LOG_FILE="/tmp/${SERVICE_NAME}-install.log"
SECRETS_FILE="/root/${SERVICE_NAME}-github-actions-secrets.txt"

# ── Terminal styling ──────────────────────────────────────────────────────────

if [[ -t 1 ]]; then
  BOLD="$(printf '\033[1m')"
  GREEN="$(printf '\033[32m')"
  YELLOW="$(printf '\033[33m')"
  CYAN="$(printf '\033[36m')"
  DIM="$(printf '\033[2m')"
  RESET="$(printf '\033[0m')"
else
  BOLD=""
  GREEN=""
  YELLOW=""
  CYAN=""
  DIM=""
  RESET=""
fi

# ── Output helpers ────────────────────────────────────────────────────────────

section() {
  printf '\n%s%s%s\n' "${BOLD}${CYAN}" "$*" "${RESET}"
  printf '%s\n' "────────────────────────────────────────"
}

success() {
  printf '  %s✔%s %s\n' "${GREEN}" "${RESET}" "$*"
}

warn() {
  printf '  %s!%s %s\n' "${YELLOW}" "${RESET}" "$*"
}

die() {
  printf '\n%s✖ error:%s %s\n' "${YELLOW}" "${RESET}" "$*" >&2
  printf '%sInstaller log:%s %s\n' "${DIM}" "${RESET}" "${LOG_FILE}" >&2
  exit 1
}

info_row() {
  local label="$1"
  local value="$2"
  printf '  %-18s %s\n' "${label}:" "${value}"
}

command_row() {
  local label="$1"
  local command="$2"
  printf '  %-18s %s\n' "${label}:" "${command}"
}

print_banner() {
  cat <<EOF

${BOLD}greg's Installer${RESET}
${DIM}greg's installer for Ubuntu servers.${RESET}

EOF
}

run_task() {
  local message="$1"
  shift

  {
    echo
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${message}"
    "$@"
  } >> "${LOG_FILE}" 2>&1 &

  local pid=$!
  local frames='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
  local i=0

  while kill -0 "${pid}" 2>/dev/null; do
    printf '\r  %s %s' "${frames:i++%${#frames}:1}" "${message}"
    sleep 0.08
  done

  wait "${pid}"
  local exit_code=$?

  if [[ "${exit_code}" -eq 0 ]]; then
    printf '\r  %s✔%s %s\n' "${GREEN}" "${RESET}" "${message}"
  else
    printf '\r  %s✖%s %s\n' "${YELLOW}" "${RESET}" "${message}"
    echo
    die "Failed while: ${message}"
  fi
}

run_task_shell() {
  local message="$1"
  local command="$2"

  run_task "${message}" bash -c "${command}"
}

# ── Safety helpers ────────────────────────────────────────────────────────────

prompt_secret() {
  local label="$1"
  local value=""

  while true; do
    read -r -s -p "${label}: " value </dev/tty
    echo >/dev/tty

    if [[ -n "${value}" && ! "${value}" =~ [[:space:]] ]]; then
      printf '%s' "${value}"
      return
    fi

    warn "Value must not be empty or contain whitespace."
  done
}

write_env_line() {
  local name="$1"
  local value="$2"

  local escaped="${value//\\/\\\\}"
  escaped="${escaped//\"/\\\"}"

  printf '%s="%s"\n' "${name}" "${escaped}"
}

run_as_deploy() {
  runuser -u "${DEPLOY_USER}" -- "$@"
}

require_root_via_sudo() {
  if [[ "${EUID}" -ne 0 || -z "${SUDO_USER:-}" || "${SUDO_USER}" == "root" ]]; then
    die "Run with sudo from your normal admin user: sudo bash install.sh"
  fi
}

require_ubuntu_or_debian() {
  if ! command -v apt-get >/dev/null 2>&1; then
    die "This installer only supports Debian/Ubuntu systems with apt-get."
  fi
}

require_systemd() {
  if [[ -z "${SYSTEMCTL_BIN}" ]]; then
    die "systemctl was not found. This installer requires systemd."
  fi
}

# ── Failure handling ──────────────────────────────────────────────────────────

trap 'die "Installation failed on or near line ${LINENO}."' ERR

# ── Pre-flight ────────────────────────────────────────────────────────────────

: > "${LOG_FILE}"
chmod 600 "${LOG_FILE}" 2>/dev/null || true

require_root_via_sudo
require_ubuntu_or_debian
require_systemd

print_banner

section "Installation overview"
info_row "Repository" "${REPO_URL}"
info_row "Branch" "${REPO_BRANCH}"
info_row "Install path" "${APP_DIR}"
info_row "Data path" "${DATA_DIR}"
info_row "Service name" "${SERVICE_NAME}"
info_row "Runtime user" "${RUNTIME_USER}"
info_row "Deploy user" "${DEPLOY_USER}"
info_row "Installer log" "${LOG_FILE}"

# ── 1. System packages ────────────────────────────────────────────────────────

section "Installing system dependencies"

run_task "Updating package lists" \
  apt-get update -qq

run_task "Installing base packages" \
  apt-get install -y -qq \
    git \
    python3 \
    python3-venv \
    python3-pip \
    openssh-client \
    rsync \
    software-properties-common

if ! command -v python3.12 >/dev/null 2>&1; then
  if [[ -r /etc/os-release ]]; then
    # shellcheck source=/dev/null
    . /etc/os-release

    if [[ "${ID:-}" == "ubuntu" ]]; then
      run_task "Adding Python package repository" \
        add-apt-repository -y ppa:deadsnakes/ppa

      run_task "Refreshing package lists" \
        apt-get update -qq
    fi
  fi
fi

run_task "Installing Python 3.11" \
  apt-get install -y -qq python3.12 python3.12-venv

PYTHON_BIN="$(command -v python3.12)"

if ! "${PYTHON_BIN}" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
  die "Python 3.12 or newer is required."
fi

success "System dependencies are ready"

# ── 2. Users and directories ──────────────────────────────────────────────────

section "Preparing service users and directories"

if ! getent group "${RUNTIME_USER}" >/dev/null 2>&1; then
  run_task "Creating runtime group" \
    groupadd --system "${RUNTIME_USER}"
else
  success "Runtime group already exists"
fi

if ! id "${RUNTIME_USER}" >/dev/null 2>&1; then
  run_task "Creating runtime user" \
    useradd \
      --system \
      --gid "${RUNTIME_USER}" \
      --home-dir "${APP_ROOT}" \
      --shell /usr/sbin/nologin \
      "${RUNTIME_USER}"
else
  success "Runtime user already exists"
fi

if ! id "${DEPLOY_USER}" >/dev/null 2>&1; then
  run_task "Creating deploy user" \
    useradd \
      --create-home \
      --shell /bin/bash \
      "${DEPLOY_USER}"
else
  success "Deploy user already exists"
fi

DEPLOY_HOME="$(getent passwd "${DEPLOY_USER}" | cut -d: -f6)"
DEPLOY_GROUP="$(id -gn "${DEPLOY_USER}")"

run_task "Creating application directories" \
  mkdir -p "${APP_ROOT}" "${DATA_DIR}"

run_task "Setting directory ownership" \
  bash -c "
    chown '${DEPLOY_USER}:${DEPLOY_GROUP}' '${APP_ROOT}'
    chown '${RUNTIME_USER}:${RUNTIME_USER}' '${DATA_DIR}'
    chmod 755 '${APP_ROOT}' '${DATA_DIR}'
  "

success "Service users and directories are ready"

# ── 3. Repository ─────────────────────────────────────────────────────────────

section "Fetching application source"

if [[ -d "${APP_DIR}/.git" ]]; then
  run_task "Preparing existing repository" \
    chown -R "${DEPLOY_USER}:${DEPLOY_GROUP}" "${APP_DIR}"

  run_task "Updating repository remote" \
    runuser -u "${DEPLOY_USER}" -- git -C "${APP_DIR}" remote set-url origin "${REPO_URL}"

  run_task "Fetching latest source" \
    runuser -u "${DEPLOY_USER}" -- git -C "${APP_DIR}" fetch -q origin "${REPO_BRANCH}"

  run_task "Checking out branch ${REPO_BRANCH}" \
    runuser -u "${DEPLOY_USER}" -- git -C "${APP_DIR}" switch -q "${REPO_BRANCH}"

  run_task "Fast-forwarding repository" \
    runuser -u "${DEPLOY_USER}" -- git -C "${APP_DIR}" pull -q --ff-only origin "${REPO_BRANCH}"
else
  run_task "Removing stale application directory" \
    rm -rf "${APP_DIR}"

  run_task "Cloning repository" \
    runuser -u "${DEPLOY_USER}" -- git clone -q --branch "${REPO_BRANCH}" "${REPO_URL}" "${APP_DIR}"
fi

success "Application source is ready"

# ── 4. Python virtual environment ─────────────────────────────────────────────

section "Creating Python environment"

run_task "Setting source ownership" \
  chown -R "${DEPLOY_USER}:${DEPLOY_GROUP}" "${APP_DIR}"

run_task "Creating virtual environment" \
  runuser -u "${DEPLOY_USER}" -- "${PYTHON_BIN}" -m venv "${APP_DIR}/.venv"

run_task "Upgrading pip" \
  runuser -u "${DEPLOY_USER}" -- "${APP_DIR}/.venv/bin/python" -m pip install \
    --upgrade pip \
    -q \
    --disable-pip-version-check

run_task "Installing Python dependencies" \
  runuser -u "${DEPLOY_USER}" -- "${APP_DIR}/.venv/bin/pip" install \
    -r "${APP_DIR}/requirements.txt" \
    -q \
    --disable-pip-version-check

success "Python environment is ready"

# ── 5. Runtime configuration ──────────────────────────────────────────────────

section "Writing runtime configuration"

echo
DISCORD_TOKEN="$(prompt_secret "DISCORD_TOKEN: ")"
echo

run_task "Writing .env file" \
  bash -c "
    {
      $(declare -f write_env_line)
      write_env_line 'DISCORD_TOKEN' '${DISCORD_TOKEN}'
      write_env_line 'DATABASE_PATH' '${DATA_DIR}/greg.sqlite3'
      write_env_line 'BOT_PREFIX' 'g!'
      write_env_line 'BOT_NAME' 'Greg'
      write_env_line 'CURRENCY_SINGULAR' 'pickle'
      write_env_line 'CURRENCY_PLURAL' 'pickles'
      write_env_line 'CURRENCY_EMOJI' '🥒'
      write_env_line 'LOG_LEVEL' 'INFO'
    } > '${APP_DIR}/.env'
  "

run_task "Applying secure configuration permissions" \
  bash -c "
    chown -R '${DEPLOY_USER}:${DEPLOY_GROUP}' '${APP_DIR}'
    chown '${RUNTIME_USER}:${RUNTIME_USER}' '${APP_DIR}/.env'
    chmod 600 '${APP_DIR}/.env'
    chown -R '${RUNTIME_USER}:${RUNTIME_USER}' '${DATA_DIR}'
  "

success "Runtime configuration saved"

# ── 6. Deploy user and SSH key ────────────────────────────────────────────────

section "Preparing deployment access"

DEPLOY_KEY_FILE="${DEPLOY_HOME}/.ssh/greg_deploy_ed25519"

run_task "Preparing deploy SSH directory" \
  install -d -m 700 -o "${DEPLOY_USER}" -g "${DEPLOY_GROUP}" "${DEPLOY_HOME}/.ssh"

if [[ ! -f "${DEPLOY_KEY_FILE}" ]]; then
  run_task "Generating deploy SSH key" \
    ssh-keygen \
      -q \
      -t ed25519 \
      -f "${DEPLOY_KEY_FILE}" \
      -N "" \
      -C "greg-deploy"

  run_task "Securing deploy SSH key" \
    bash -c "
      chown '${DEPLOY_USER}:${DEPLOY_GROUP}' '${DEPLOY_KEY_FILE}' '${DEPLOY_KEY_FILE}.pub'
      chmod 600 '${DEPLOY_KEY_FILE}'
      chmod 644 '${DEPLOY_KEY_FILE}.pub'
    "
else
  success "Deploy SSH key already exists"
fi

run_task "Updating deploy authorized_keys" \
  bash -c "
    touch '${DEPLOY_HOME}/.ssh/authorized_keys'
    chown '${DEPLOY_USER}:${DEPLOY_GROUP}' '${DEPLOY_HOME}/.ssh/authorized_keys'
    chmod 600 '${DEPLOY_HOME}/.ssh/authorized_keys'

    if ! grep -qF \"\$(cat '${DEPLOY_KEY_FILE}.pub')\" '${DEPLOY_HOME}/.ssh/authorized_keys' 2>/dev/null; then
      cat '${DEPLOY_KEY_FILE}.pub' >> '${DEPLOY_HOME}/.ssh/authorized_keys'
    fi
  "

run_task "Writing deploy sudo permissions" \
  bash -c "
    cat > '/etc/sudoers.d/${SERVICE_NAME}-deploy' <<SUDOERS
${DEPLOY_USER} ALL=(root) NOPASSWD: ${SYSTEMCTL_BIN} stop ${SERVICE_NAME}, ${SYSTEMCTL_BIN} start ${SERVICE_NAME}, ${SYSTEMCTL_BIN} restart ${SERVICE_NAME}, ${SYSTEMCTL_BIN} status ${SERVICE_NAME}, ${SYSTEMCTL_BIN} daemon-reload
SUDOERS
    chmod 440 '/etc/sudoers.d/${SERVICE_NAME}-deploy'
  "

run_task "Validating deploy sudo permissions" \
  visudo -cf "/etc/sudoers.d/${SERVICE_NAME}-deploy"

success "Deployment access prepared"

# ── 7. Systemd service ────────────────────────────────────────────────────────

section "Installing systemd service"

if [[ ! -f "${APP_DIR}/${SERVICE_FILE}" ]]; then
  die "Service file not found: ${APP_DIR}/${SERVICE_FILE}"
fi

run_task "Installing service file" \
  install -m 0644 "${APP_DIR}/${SERVICE_FILE}" "/etc/systemd/system/${SERVICE_NAME}.service"

run_task "Reloading systemd" \
  "${SYSTEMCTL_BIN}" daemon-reload

run_task "Enabling service" \
  "${SYSTEMCTL_BIN}" enable "${SERVICE_NAME}"

run_task "Starting service" \
  "${SYSTEMCTL_BIN}" restart "${SERVICE_NAME}"

success "Service installed and started"

# ── 8. GitHub Actions secrets ─────────────────────────────────────────────────

section "Preparing GitHub Actions secrets"

SERVER_IP="$(hostname -I | awk '{print $1}')"
DEPLOY_HOST="${DEPLOY_HOST:-${SERVER_IP}}"

KNOWN_HOSTS_LINE="$(ssh-keyscan -H "${DEPLOY_HOST}" 2>>"${LOG_FILE}" || true)"

if [[ -z "${KNOWN_HOSTS_LINE}" ]]; then
  warn "Could not generate known_hosts entry for ${DEPLOY_HOST}."
  warn "You may need to create DEPLOY_KNOWN_HOSTS manually."
fi

run_task "Writing deployment secrets file" \
  bash -c "
    {
      echo 'GitHub Actions secrets for ${SERVICE_NAME}'
      echo
      echo 'DEPLOY_SSH_KEY'
      cat '${DEPLOY_KEY_FILE}'
      echo
      echo 'DEPLOY_KNOWN_HOSTS'
      printf '%s\n' '${KNOWN_HOSTS_LINE}'
      echo
      echo 'DEPLOY_HOST'
      printf '%s\n' '${DEPLOY_HOST}'
      echo
      echo 'DEPLOY_PORT'
      echo '22'
      echo
      echo 'DEPLOY_USER'
      printf '%s\n' '${DEPLOY_USER}'
    } > '${SECRETS_FILE}'

    chmod 600 '${SECRETS_FILE}'
  "

success "Deployment secrets written securely"

# ── Completion summary ────────────────────────────────────────────────────────

SERVICE_STATE="$("${SYSTEMCTL_BIN}" is-active "${SERVICE_NAME}" 2>/dev/null || true)"

section "Installation complete"

printf '%sApplication%s\n' "${BOLD}" "${RESET}"
info_row "Install path" "${APP_DIR}"
info_row "Data path" "${DATA_DIR}"
info_row "Repository" "${REPO_URL}"
info_row "Branch" "${REPO_BRANCH}"

echo
printf '%sUsers%s\n' "${BOLD}" "${RESET}"
info_row "Runtime user" "${RUNTIME_USER}"
info_row "Deploy user" "${DEPLOY_USER}"

echo
printf '%sService%s\n' "${BOLD}" "${RESET}"
info_row "Name" "${SERVICE_NAME}"
info_row "Status" "${SERVICE_STATE}"
command_row "View status" "sudo systemctl status ${SERVICE_NAME}"
command_row "View logs" "sudo journalctl -u ${SERVICE_NAME} -f"
command_row "Restart" "sudo systemctl restart ${SERVICE_NAME}"

echo
printf '%sGitHub Actions%s\n' "${BOLD}" "${RESET}"
info_row "Secrets file" "${SECRETS_FILE}"
info_row "Deploy host" "${DEPLOY_HOST}"
info_row "Deploy user" "${DEPLOY_USER}"
info_row "Deploy port" "22"
info_row "GitHub page" "https://github.com/buildsbypat/greg/settings/secrets/actions"

echo
printf '%sNext steps%s\n' "${BOLD}" "${RESET}"
echo "  1. Check logs, make sure it's didn't shit itself"

echo
warn "The deploy private key was not printed to the terminal."
warn "Delete ${SECRETS_FILE} after adding the secrets to GitHub."

echo
success "Greg installed and is ready"
