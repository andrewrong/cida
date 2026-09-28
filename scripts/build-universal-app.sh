#!/bin/zsh
# Builds both slices with SwiftPM's native layout so assemble-app.sh can find the
# resource bundle and Sparkle.framework. Merge before signing, without changing
# either architecture's cached build product.
set -euo pipefail

if (( $# < 1 || $# > 2 )); then
  echo "usage: $0 <new app path> [configuration]" >&2
  exit 64
fi

script_dir=${0:A:h}
project_dir=${script_dir:h}
app_path=${1:A}
configuration=${2:-release}
if [[ -e "$app_path" ]]; then
  echo "Refusing to replace an existing app: $app_path" >&2
  exit 73
fi

binary_paths=()
for architecture in arm64 x86_64; do
  swift build \
    --package-path "$project_dir" \
    --configuration "$configuration" \
    --arch "$architecture" \
    -Xswiftc -warnings-as-errors
  bin_path=$(swift build \
    --package-path "$project_dir" \
    --configuration "$configuration" \
    --arch "$architecture" \
    --show-bin-path)
  binary_paths+=("$bin_path/Cida")
done

"$script_dir/assemble-app.sh" "${binary_paths[1]}" "$app_path"
/usr/bin/lipo -create "${binary_paths[@]}" -output "$app_path/Contents/MacOS/Cida"
"$script_dir/verify-app-architectures.sh" "$app_path"
