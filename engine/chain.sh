#!/bin/bash
# Кезекпен: маска (жоқ болса) -> рендер -> freeze -> ready/<seg>/ көшіру
#   cd projects/<аты>; ../../engine/chain.sh 1 2 3
E=$(cd "$(dirname "$0")" && pwd); ROOT=$(dirname "$E"); W=$PWD
export RAZBOR_WORK=$W/ RAZBOR_SRC=$W/src/
DST=${CREO_DST:-$ROOT/ready}; mkdir -p out masks
for n in "$@"; do
  nn=$(printf %02d $n)
  if [ ! -f masks/$nn.mp4 ]; then python3 "$E/mask.py" $n > masks/$n.log 2>&1 || { rm -f masks/$nn.mp4; echo "FAIL mask $n" >> out/chain.log; continue; }; fi
  python3 -W ignore "$E/render_b.py" $n > out/$nn.logb 2>&1 || { echo "FAIL $n" >> out/chain.log; continue; }
  o=$(ls out/${nn}_*.mp4 | head -1); fz=$(python3 "$E/freeze.py" "$o")
  seg=$(python3 -c "import sys; sys.path.insert(0,'.'); from videos import VIDEOS; print(VIDEOS[$n].get('seg',''))")
  mkdir -p "$DST/$seg"; cp "$o" "$DST/$seg/"
  echo "DONE $n -> $seg/$(basename "$o") | $fz" >> out/chain.log
done
echo ALLDONE >> out/chain.log
