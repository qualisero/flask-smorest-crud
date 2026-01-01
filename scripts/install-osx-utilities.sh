#!/usr/bin/env bash
set -euo pipefail

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required but not found. Install it from https://brew.sh/."
  exit 1
fi

PACKAGES=(
  ripgrep
  fd
  fzf
  bat
  jq
  yq
  sd
  tidy-html5
  htmlq
  htop
  btop
  glances
  watchman
  fswatch
  mas
  httpie
  mitmproxy
  nmap
  iperf3
  asdf
  direnv
  chezmoi
  gdu
  zoxide
  eza
  lsd
  tmux
  git-delta
)

# Keep Homebrew metadata fresh before installing.
echo "Updating Homebrew..."
brew update

echo "Installing utilities..."
for pkg in "${PACKAGES[@]}"; do
  if brew list "$pkg" >/dev/null 2>&1; then
    echo "✓ $pkg is already installed"
  else
    echo "→ Installing $pkg"
    brew install "$pkg"
  fi
  echo
  # Short delay to keep output readable when installing many packages.
  sleep 0.2
done

echo "All requested utilities have been processed."
echo
if [ -d "$(brew --prefix)/opt/fzf" ]; then
  brew_prefix="$(brew --prefix)"
  cat <<EOF
To enable fzf shell integrations, run:
  $brew_prefix/opt/fzf/install --key-bindings --completion --update-rc
EOF
fi
