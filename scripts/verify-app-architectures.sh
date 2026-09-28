#!/bin/zsh
# Every shipped Mach-O file, including Sparkle's helpers, must run on both CPUs.
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <app>" >&2
  exit 64
fi

app_path=${1:A}
main_binary="$app_path/Contents/MacOS/Cida"
if [[ ! -x "$main_binary" ]] || ! /usr/bin/lipo "$main_binary" -verify_arch arm64 x86_64; then
  echo "Missing universal executable: $main_binary (requires arm64 and x86_64)" >&2
  exit 66
fi

while IFS= read -r -d '' binary; do
  if [[ "$(/usr/bin/file -b "$binary")" != *Mach-O* ]]; then
    continue
  fi
  if ! /usr/bin/lipo "$binary" -verify_arch arm64 x86_64; then
    echo "Missing arm64 or x86_64 architecture: $binary" >&2
    exit 1
  fi
done < <(/usr/bin/find "$app_path/Contents" -type f -print0)
