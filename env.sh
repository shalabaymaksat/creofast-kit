# source ~/creofast-kit/env.sh  — әр Bash командасының басында (shell күйі сақталмайды)
#   E          — engine папкасы
#   CREO_HOME  — пайдаланушы репосындағы жұмыс папкасы: <репо>/creofast (kit өз ішінде іске қосылса — kit түбірі)
K="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"; export E="$K/engine"
R="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
if [ "$R" = "$K" ]; then export CREO_HOME="$K"; else export CREO_HOME="$R/creofast"; fi
mkdir -p "$CREO_HOME"/{inbox,projects,ready}
[ "$CREO_HOME" != "$K" ] && mkdir -p "$CREO_HOME"/assets/{results,photos,reels,cases,works,long} && touch "$CREO_HOME"/assets/{results,photos,reels,cases,works,long}/.gitkeep && [ ! -f "$CREO_HOME/.gitignore" ] && printf 'inbox/\nassets/_c/\nprojects/*/audio/\nprojects/*/chunks/\nprojects/*/masks/\nprojects/*/out/\nprojects/*/test/\nprojects/*/src/\n' > "$CREO_HOME/.gitignore"
true
