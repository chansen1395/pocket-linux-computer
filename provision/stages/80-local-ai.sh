#!/usr/bin/env bash
# 80-local-ai: llama.cpp built from source (Debian 13 has no package), the default chat model, and the
# ~/.local/bin/llama-chat wrapper. Choices and alternatives: docs/research/local-ai.md.
# Runs only in the "Local AI" power profile sense: close the desktop apps before chatting on 4 GB.
#   POCKET_LLAMA_JOBS=4        build parallelism (use 2 while the desktop is running)
#   POCKET_LLAMA_REBUILD=1     force a rebuild
#   POCKET_LLAMA_TAG=b11683    llama.cpp release tag to build (a pinned default; change it on purpose)
. "$(dirname "$0")/../lib.sh"
stage_begin 80-local-ai
require_root
[ -n "$POCKET_HOME" ] || die "cannot find the home directory of $POCKET_USER"
ensure_pkg build-essential cmake git libcurl4-openssl-dev jq curl ca-certificates

model_dir=/data/models/llm
model=qwen2.5-1.5b-instruct-q4_k_m.gguf
model_url="https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/$model"
model_sha=6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e
src="$POCKET_HOME/src/llama.cpp"

run mkdir -p "$model_dir" "$POCKET_HOME/src" "$POCKET_HOME/.local/bin" "$POCKET_HOME/.pocket"
run chown -R "$POCKET_USER:$POCKET_USER" /data/models "$POCKET_HOME/src" "$POCKET_HOME/.local" "$POCKET_HOME/.pocket"

if [ ! -d "$src/.git" ]; then
  log "cloning llama.cpp ${POCKET_LLAMA_TAG:-b11683}"
  as_user git clone --depth 1 --branch "${POCKET_LLAMA_TAG:-b11683}" https://github.com/ggml-org/llama.cpp "$src"
fi
if [ ! -x "$src/build/bin/llama-server" ] || [ "${POCKET_LLAMA_REBUILD:-0}" = 1 ]; then
  log "building llama.cpp (10-15 minutes on a Pi 5)"
  as_user cmake -S "$src" -B "$src/build" -DCMAKE_BUILD_TYPE=Release -DGGML_NATIVE=ON
  as_user cmake --build "$src/build" --config Release -j "${POCKET_LLAMA_JOBS:-4}" --target llama-server llama-cli llama-bench
fi
for b in llama-server llama-cli llama-bench; do
  [ -x "$src/build/bin/$b" ] && as_user ln -sf "$src/build/bin/$b" "$POCKET_HOME/.local/bin/$b"
done

if ! echo "$model_sha  $model_dir/$model" | sha256sum -c --quiet 2>/dev/null; then
  log "downloading $model (~1.1 GB)"
  as_user curl -fL --retry 5 -C - -o "$model_dir/$model" "$model_url"
  [ "$DRY_RUN" = 1 ] || echo "$model_sha  $model_dir/$model" | sha256sum -c --quiet || die "model checksum failed"
fi

install_home .local/bin/llama-chat 0755

# Benchmark only on a supply that negotiated 5 A: on a 3 A phone charger the four-thread load spikes
# the current and the PMIC cuts power (seen twice on 2026-10-16). POCKET_LLAMA_BENCH=1 forces it.
supply_ma="$(od -An -tu4 --endian=big /proc/device-tree/chosen/power/max_current 2>/dev/null | tr -d ' ')"
if [ "$DRY_RUN" != 1 ] && [ -x "$POCKET_HOME/.local/bin/llama-bench" ]; then
  if [ "${POCKET_LLAMA_BENCH:-auto}" = 1 ] || { [ "${POCKET_LLAMA_BENCH:-auto}" = auto ] && [ "${supply_ma:-0}" -ge 5000 ]; }; then
    wait_cool 65 180
    log "benchmark: $(as_user "$POCKET_HOME/.local/bin/llama-bench" -m "$model_dir/$model" -t 4 -p 64 -n 32 2>/dev/null | tail -2 | tr '\n' ' ')"
  else
    warn "benchmark skipped: supply negotiated ${supply_ma:-unknown} mA (< 5000). Use the 27 W supply, or POCKET_LLAMA_BENCH=1 with LLAMA_THREADS=2"
  fi
fi
warn "try: llama-chat            (interactive)   |   llama-chat 'how do I purify water'   (one-shot)"
stage_end
