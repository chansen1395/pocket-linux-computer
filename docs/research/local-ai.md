# Research — local AI on the 4 GB Pi 5 (arm64, CPU only)

Verified 2026-10-16: every URL was fetched (HTTP 200 with the stated size; sha256 from the Hugging Face API or the
Kiwix sidecar). Anything not fetched is marked **unverified**. Runs only in the *Local AI* power profile
(desktop apps closed, see §6).

## 1. llama.cpp on Raspberry Pi OS Trixie (Debian 13, arm64)

| Route | Status | Notes |
|---|---|---|
| `apt install llama.cpp` | **not available in trixie**; package `llama.cpp 1:0.6.0+dfsg-2` exists only in sid/forky (packages.debian.org) | may appear in trixie-backports later; check `apt policy llama.cpp` |
| Prebuilt binary | **yes**: GitHub build releases (`bNNNN` tags) ship `llama-<build>-bin-ubuntu-arm64.tar.gz`; e.g. `https://github.com/ggml-org/llama.cpp/releases/download/b11683/llama-b11683-bin-ubuntu-arm64.tar.gz` (13.9 MB, 2026-10-15). The versioned release `v0.7.0` carries no binaries, only `nightly-tag.txt`. Built on Ubuntu; a generic ARM build, so expect it slower than a native build (unmeasured). | quick path for testing |
| Build from source | **recommended**: `cmake -B build && cmake --build build --config Release` (docs/build.md); `GGML_NATIVE` is on by default so NEON/dotprod/i8mm kernels for the Cortex-A76 are picked up | ~10–15 min on the Pi 5 (unmeasured) |

```sh
sudo apt install -y build-essential cmake git libcurl4-openssl-dev
git clone --depth 1 https://github.com/ggml-org/llama.cpp ~/src/llama.cpp
cd ~/src/llama.cpp
cmake -B build -DCMAKE_BUILD_TYPE=Release -DGGML_NATIVE=ON
cmake --build build --config Release -j 4 --target llama-server llama-cli llama-bench llama-completion
# binaries: ~/src/llama.cpp/build/bin/{llama-server,llama-cli,llama-bench,llama-completion}
# if the build OOMs with the desktop running, use -j 2
```

Usage (flags verified in `tools/server/README.md`):

```sh
# chat server (OpenAI-compatible); default port is 9931, host 127.0.0.1; --jinja chat templating is on by default
llama-server -m /data/models/llm/qwen2.5-1.5b-instruct-q4_k_m.gguf -c 8192 -t 4 --port 9931
curl -s http://127.0.0.1:9931/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Three signs of hypothermia?"}],"max_tokens":200}'
# interactive terminal chat (llama-cli was rewritten in late 2025 as a chat client; llama-completion keeps the old one-shot
# "-p prompt" behavior — check `llama-cli --help` on the built version; not re-verified here)
llama-cli -m /data/models/llm/qwen2.5-1.5b-instruct-q4_k_m.gguf -c 8192 -t 4
# benchmark
llama-bench -m /data/models/llm/qwen2.5-1.5b-instruct-q4_k_m.gguf -t 4
```

## 2. Models (GGUF, Q4) — exact URLs, sizes, sha256

All `https://huggingface.co/<repo>/resolve/main/<file>` (302 → CDN; use `curl -L`). Decimal MB.

| Model | File (repo) | Size | sha256 | License | Fits 4 GB? |
|---|---|---|---|---|---|
| **Qwen2.5-1.5B-Instruct Q4_K_M** | `Qwen/Qwen2.5-1.5B-Instruct-GGUF` → `qwen2.5-1.5b-instruct-q4_k_m.gguf` | 1,117 MB | `6a1a2eb6…9407e` (full value in the manifest) | Apache-2.0 | yes, with desktop |
| Qwen2.5-1.5B-Instruct Q4_K_M (alt. quant) | `bartowski/Qwen2.5-1.5B-Instruct-GGUF` → `Qwen2.5-1.5B-Instruct-Q4_K_M.gguf` | 986 MB | — | Apache-2.0 | yes |
| **Qwen3-1.7B Q4_K_M** | `unsloth/Qwen3-1.7B-GGUF` → `Qwen3-1.7B-Q4_K_M.gguf` (official `Qwen/Qwen3-1.7B-GGUF` has only `Qwen3-1.7B-Q8_0.gguf`, 1,834 MB) | 1,107 MB | `b139949c…1897` | Apache-2.0 | yes; KV cache is 4× Qwen2.5's (see §6); use `/no_think` |
| Qwen3-0.6B Q4_K_M (tiny fallback) | `unsloth/Qwen3-0.6B-GGUF` → `Qwen3-0.6B-Q4_K_M.gguf` | 397 MB | — | Apache-2.0 | yes |
| **Llama-3.2-1B-Instruct Q4_K_M** | `bartowski/Llama-3.2-1B-Instruct-GGUF` → `Llama-3.2-1B-Instruct-Q4_K_M.gguf` | 808 MB | `6f85a640…df83` | Llama 3.2 Community License | yes, with desktop |
| Llama-3.2-3B-Instruct Q4_K_M | `bartowski/Llama-3.2-3B-Instruct-GGUF` → `Llama-3.2-3B-Instruct-Q4_K_M.gguf` | 2,019 MB | `6c1a2b41…28ff` | Llama 3.2 Community License | **console mode only** (≈2.6 GB with 4k ctx; an Ollama run measured 4.66 GB RSS) |
| Gemma-3-1b-it Q4_K_M | `ggml-org/gemma-3-1b-it-GGUF` → `gemma-3-1b-it-Q4_K_M.gguf` (Google's `google/gemma-3-1b-it-qat-q4_0-gguf` is gated: 401) | 806 MB | `8ccc5cd1…a135` | Gemma Terms of Use | yes |
| SmolLM2-1.7B-Instruct Q4_K_M | `HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF` → `smollm2-1.7b-instruct-q4_k_m.gguf` | 1,056 MB | `decd2598…4f33` | Apache-2.0 | yes, but MHA → 192 KB/token KV; keep ctx ≤ 4k |
| Phi-4-mini-instruct Q4_K_M | `bartowski/microsoft_Phi-4-mini-instruct-GGUF` → `microsoft_Phi-4-mini-instruct-Q4_K_M.gguf` | 2,492 MB | `01999f17…c0c2` | MIT | **marginal**: ≈3.1 GB with 4k ctx; expect swapping — not recommended |
| Qwen3-4B-Instruct-2507 Q4_K_M | `unsloth/Qwen3-4B-Instruct-2507-GGUF` | 2,497 MB | — | Apache-2.0 | same verdict as Phi-4-mini |

Published Pi 5 speeds (CPU, 4 threads; decode = generation tokens/s):

| Model (Q4_K_M) | tok/s | Source |
|---|---|---|
| Llama-3.2-1B | **11.5** (prefill 30) · 11.2 | benchmarklist.com Edge LLM leaderboard, llama.cpp on Pi 5 8 GB, updated 2026-05-06 · Stratosphere IPS "LLM performance on the Raspberry Pi 5" (Ollama) |
| Gemma-3-1b | 11.5 (1.39 GB RSS) | Stratosphere (Ollama) |
| Qwen2.5-1.5B | **9.6** (prefill 22) · 10.0 (1.85 GB RSS) | benchmarklist · Stratosphere |
| SmolLM2-1.7B | 8.5 · 8.2 | benchmarklist · Stratosphere |
| Qwen2.5-3B / Llama-3.2-3B | 4.8 / 4.7 (Llama 3B: 4.66 GB RSS under Ollama) | benchmarklist · Stratosphere |
| Qwen3-1.7B, Phi-4-mini | no published Pi 5 number found — **unverified**; expect ≈ 8 and ≈ 3.5 tok/s by parameter count | — |

benchmarklist also shows the ARM-repacked `Q4_0` format giving ~3× faster prefill (Llama-1B: 87 vs 30 tok/s) at the same
decode speed; current llama.cpp repacks `Q4_0` automatically on AArch64, so a `q4_0` file is worth a `llama-bench` test
(URL not verified here). Sources: `https://benchmarklist.com/benchmarks/edge_llm_raspberry_pi_5/`,
`https://stratospherelinuxips.readthedocs.io/en/develop/immune/research_rpi_llm_performance.html`.

**Recommendation.** Default chat: **Qwen2.5-1.5B-Instruct Q4_K_M** (≈10 tok/s, 1.1 GB, cheapest KV cache of the
set at 28 KB/token so 8k–16k context fits, Apache-2.0). "Summarize this Kiwix article": **Llama-3.2-1B-Instruct
Q4_K_M** (fastest at ≈11.5 tok/s, 32 KB/token KV, summarization/rewriting is a stated target use of the model) with
`-c 8192`; if only one model should stay resident, use Qwen2.5-1.5B for both. Qwen3-1.7B is the upgrade once
thinking-mode output is wanted and the device is in console mode.

## 3. whisper.cpp (speech → text)

Not in Debian trixie (`packages.debian.org/trixie/whisper.cpp` → no package). Build from source (commands from the
project README):

```sh
sudo apt install -y build-essential cmake git ffmpeg libsdl2-dev     # SDL2 only for whisper-stream (mic)
git clone --depth 1 https://github.com/ggml-org/whisper.cpp ~/src/whisper.cpp      # latest tag v1.9.5
cd ~/src/whisper.cpp
cmake -B build -DCMAKE_BUILD_TYPE=Release -DWHISPER_SDL2=ON
cmake --build build -j 4 --config Release
# models (or: sh ./models/download-ggml-model.sh base.en)
curl -L -o /data/models/whisper/ggml-base.en.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
./build/bin/whisper-cli -m /data/models/whisper/ggml-base.en.bin -t 4 -f note.wav       # 16 kHz mono WAV
ffmpeg -i note.m4a -ar 16000 -ac 1 -c:a pcm_s16le note.wav                              # convert anything else
./build/bin/whisper-stream -m /data/models/whisper/ggml-tiny.en.bin -t 4 --step 4000 --length 8000   # live mic
```

| Model | URL (`https://huggingface.co/ggerganov/whisper.cpp/resolve/main/…`) | Size | sha256 | RAM (README) |
|---|---|---|---|---|
| `ggml-tiny.en.bin` | 77.7 MB | `921e4cf8…b1f` | ~273 MB |
| `ggml-base.en.bin` | 148.0 MB | `a03779c8…002` | ~388 MB |
| `ggml-tiny.en-q5_1.bin` / `ggml-base.en-q5_1.bin` | 32.2 / 59.7 MB | — | smaller, slightly faster |
| `ggml-small.en.bin` | 487.6 MB | — | ~852 MB; below real time on the Pi 5 |

Speed: the project publishes no Pi 5 number. Its benchmark thread (issue #89) lists a **Pi 4** at 4 threads:
tiny.en encode 13.8 s and base.en 30.6 s per 30 s audio window (≈ 2× and ≈ 1× real time). The Pi 5 is roughly
2–3× faster per core, so expect base.en at ≈ 2–3× real time and tiny.en ≈ 5× (extrapolation, **unverified**);
third-party pages claim "base ≈ real time with -t 4" (low confidence). Measure with `./build/bin/whisper-bench -m … -t 4`.
License: MIT (code and ggml models).

## 4. Piper (text → speech)

| Item | Verified |
|---|---|
| Install | `pip install piper-tts` — **1.8.0** (OHF-Voice/piper1-gpl, GPL-3.0), wheel `piper_tts-1.8.0-cp39-abi3-manylinux_2_17_aarch64….whl` on PyPI and GitHub. Trixie is PEP 668, so use a venv. |
| Older static binary | `https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_aarch64.tar.gz` (26.0 MB) — `echo text \| ./piper -m voice.onnx -f out.wav` |
| Voice | `https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx` (63.2 MB, sha256 `5efe09e6…019f`) + `en_US-lessac-medium.onnx.json` (4.9 KB). Alt: `en/en_US/amy/medium/en_US-amy-medium.onnx` (63.2 MB). License per the voice's MODEL_CARD (lessac derives from the Blizzard 2013 data; **not re-checked**). |
| Beware | Debian's `piper` package (0.8-1) is the Logitech mouse configurator, not TTS. |

```sh
python3 -m venv ~/.venvs/piper && ~/.venvs/piper/bin/pip install piper-tts
# voices: either the two URLs above into /data/models/piper/, or
~/.venvs/piper/bin/python -m piper.download_voices en_US-lessac-medium --data-dir /data/models/piper
~/.venvs/piper/bin/python -m piper -m en_US-lessac-medium --data-dir /data/models/piper -f out.wav -- 'Water is boiling.'
~/.venvs/piper/bin/python -m piper -m en_US-lessac-medium --data-dir /data/models/piper -- 'Plays on the speakers.'
# the CLI reloads the model each call; for Pocket TUI use the HTTP server mode documented in docs/API_HTTP.md
```

## 5. Embeddings for a local RAG

| Model | URL | Size | sha256 | License | Notes |
|---|---|---|---|---|---|
| **nomic-embed-text-v1.5 Q8_0** | `https://huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF/resolve/main/nomic-embed-text-v1.5.Q8_0.gguf` | 146 MB | `3e243421…c3b7` | Apache-2.0 | 768-d, 8k ctx; prefix texts with `search_document: ` / `search_query: ` (model card) |
| bge-small-en-v1.5 q8_0 | `https://huggingface.co/CompendiumLabs/bge-small-en-v1.5-gguf/resolve/main/bge-small-en-v1.5-q8_0.gguf` | 36.8 MB | `ec38e8da…f514` | MIT | 384-d, 512 ctx, `--pooling cls` |
| embeddinggemma-300M Q8_0 | `https://huggingface.co/ggml-org/embeddinggemma-300M-GGUF/resolve/main/embeddinggemma-300M-Q8_0.gguf` | 334 MB | — | Gemma Terms | |
| Qwen3-Embedding-0.6B Q8_0 | `https://huggingface.co/Qwen/Qwen3-Embedding-0.6B-GGUF/resolve/main/Qwen3-Embedding-0.6B-Q8_0.gguf` | 639 MB | — | Apache-2.0 | strongest, heaviest |

`llama-server --embedding` runs on the CPU backend, which is architecture-independent, so it works on arm64
(flags verified in the server README: `--embedding`, `--pooling {none,mean,cls,last,rank}`, `POST /v1/embeddings`,
`--rerank` for a reranker model):

```sh
llama-server -m /data/models/embed/nomic-embed-text-v1.5.Q8_0.gguf --embedding --pooling mean -c 2048 -t 4 --port 9932
curl -s http://127.0.0.1:9932/v1/embeddings -H 'Content-Type: application/json' \
  -d '{"input":"search_query: how to purify water"}'
```

RAG plan (stretch): extract article text from the ZIMs with python-libzim (or kiwix-serve's `/search` as the
first-stage retriever, which is what `kb.search` uses), chunk ~500 tokens, embed with nomic, store in SQLite
(`sqlite-vec`) — 10k chunks ≈ 30 MB of vectors. Not prototyped.

## 6. What 4 GB means

Rule of thumb: **resident ≈ GGUF size (mmap'd weights) + KV cache (bytes/token × ctx) + ~0.2 GB compute buffers**, on
top of the OS (console mode ≈ 0.3 GB, desktop ≈ 0.7 GB, a browser 0.5–1.5 GB more; estimates). KV cache per token =
2 × layers × kv_heads × head_dim × 2 bytes (f16).

| Model (Q4_K_M) | Weights | KV/token | @4k ctx | @8k ctx | Verdict on 4 GB |
|---|---|---|---|---|---|
| Llama-3.2-1B | 0.81 GB | 32 KB | 1.1 GB | 1.3 GB | fine with the desktop up |
| Qwen2.5-1.5B | 1.12 GB | 28 KB | 1.4 GB | 1.6 GB | fine with the desktop up; 16k ctx (1.8 GB) in console mode |
| Gemma-3-1b | 0.81 GB | ~27 KB (global layers; local layers capped at 512) | 1.1 GB | 1.2 GB | fine |
| Qwen3-1.7B | 1.11 GB | 112 KB | 1.8 GB | 2.2 GB | console mode; keep ctx ≤ 8k |
| SmolLM2-1.7B | 1.06 GB | 192 KB (MHA) | 2.0 GB | 2.8 GB | console mode, ctx ≤ 4k |
| Llama-3.2-3B | 2.02 GB | 112 KB | 2.7 GB | 3.1 GB | console mode only, nothing else running, ≈ 4.7 tok/s |
| Phi-4-mini (3.8B) | 2.49 GB | 128 KB | 3.2 GB | — | does not fit usefully |

Rules: (1) *Local AI* power profile = desktop and browser closed (`display.mode console`), otherwise the model
pages in and out and tok/s halves or the OOM killer hits the browser; (2) one LLM at a time, plus at most whisper
(≈0.4 GB) *or* piper (≈0.1–0.2 GB, unmeasured); (3) `-t 4`, never more; (4) `-ctk q8_0 -ctv q8_0 -fa on` halves the
KV cache if context is the constraint (CPU flash-attention; verify speed with `llama-bench`); (5) keep `mmap` on
(default) so weights are evictable, do not `--mlock`; (6) add a 2 GB zram swap (`zram-tools`) as a safety net, not as
working memory; (7) sustained 4-thread inference throttles the Pi 5 without active cooling — the numbers above
assume a fan.

## 7. Commands for `provision/stages/80-local-ai.sh` (to be written as a stage; not written here)

```sh
#!/usr/bin/env bash
# 80-local-ai: llama.cpp from source + default model + ~/.local/bin/llama-chat wrapper
set -euo pipefail
MODEL_DIR=/data/models/llm
MODEL=qwen2.5-1.5b-instruct-q4_k_m.gguf
MODEL_URL=https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/$MODEL
MODEL_SHA=6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e
SRC=$HOME/src/llama.cpp

sudo apt install -y build-essential cmake git libcurl4-openssl-dev jq curl
sudo mkdir -p "$MODEL_DIR" && sudo chown "$USER" "$MODEL_DIR"

# 1. build (native ARM kernels); ~10-15 min; -j 2 if the desktop is running
if [ ! -d "$SRC" ]; then git clone --depth 1 https://github.com/ggml-org/llama.cpp "$SRC"; fi
cmake -S "$SRC" -B "$SRC/build" -DCMAKE_BUILD_TYPE=Release -DGGML_NATIVE=ON
cmake --build "$SRC/build" --config Release -j 4 --target llama-server llama-cli llama-bench llama-completion
mkdir -p "$HOME/.local/bin"
for b in llama-server llama-cli llama-bench llama-completion; do ln -sf "$SRC/build/bin/$b" "$HOME/.local/bin/$b"; done

# 2. default model, resumable, checksum-verified
if ! echo "$MODEL_SHA  $MODEL_DIR/$MODEL" | sha256sum -c --quiet 2>/dev/null; then
  curl -L -C - -o "$MODEL_DIR/$MODEL" "$MODEL_URL"
  echo "$MODEL_SHA  $MODEL_DIR/$MODEL" | sha256sum -c
fi

# 3. wrapper: interactive chat by default; `llama-chat "prompt"` for one-shot via llama-server's API
cat > "$HOME/.local/bin/llama-chat" <<'EOF'
#!/usr/bin/env bash
# llama-chat            -> interactive chat (llama-cli)
# llama-chat "question" -> one-shot answer through a background llama-server (started on demand)
set -euo pipefail
MODEL="${LLAMA_MODEL:-/data/models/llm/qwen2.5-1.5b-instruct-q4_k_m.gguf}"
CTX="${LLAMA_CTX:-8192}"; PORT="${LLAMA_PORT:-9931}"; THREADS=4
if [ $# -eq 0 ]; then exec llama-cli -m "$MODEL" -c "$CTX" -t $THREADS; fi
if ! curl -sf "http://127.0.0.1:$PORT/health" >/dev/null; then
  nohup llama-server -m "$MODEL" -c "$CTX" -t $THREADS --port "$PORT" >"$HOME/.pocket/llama-server.log" 2>&1 &
  until curl -sf "http://127.0.0.1:$PORT/health" >/dev/null; do sleep 1; done
fi
jq -n --arg q "$*" '{messages:[{role:"user",content:$q}],max_tokens:400}' \
  | curl -s "http://127.0.0.1:$PORT/v1/chat/completions" -H 'Content-Type: application/json' -d @- \
  | jq -r '.choices[0].message.content'
EOF
chmod +x "$HOME/.local/bin/llama-chat"
mkdir -p "$HOME/.pocket"
echo "ok: $(llama-bench -m "$MODEL_DIR/$MODEL" -t 4 -p 64 -n 32 2>/dev/null | tail -3)"
```

A `llama-summarize <zim-url-or-text>` sibling is the same wrapper with `LLAMA_MODEL=/data/models/llm/Llama-3.2-1B-Instruct-Q4_K_M.gguf`
and a system prompt ("Summarize in five bullet points…"); fetch article text with `curl http://127.0.0.1:8090/content/<zim>/A/<title> | lynx -dump -stdin`.
