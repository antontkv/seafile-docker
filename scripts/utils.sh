need_sudo_or_not() {
  if [[ -v SUDO_OR_NOT ]]; then
    return 0
  fi
  set +o pipefail
  if docker ps 2>&1 | grep -c "permission denied" > /dev/null; then
    SUDO_OR_NOT=sudo
  else
    SUDO_OR_NOT=
  fi
  set -o pipefail
}
