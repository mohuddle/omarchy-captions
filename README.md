# Captions for Omarchy

Live captions of **whatever is playing on the speakers**. A small TUI and an Omarchy bar plugin. Local, no cloud, no URL box.

Play a lecture in the browser (for example Ligonier). This tool copies the PipeWire speaker mix and runs a streaming [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) Zipformer. It does not fetch the page.

```
browser  →  speakers
              │
              └─ monitor  →  sherpa-onnx  →  TUI / bar popup
```

## Install

```bash
git clone https://github.com/mohuddle/omarchy-captions.git
cd omarchy-captions
./scripts/setup.sh
```

That creates a venv, installs `sherpa-onnx`, downloads a ~20M English streaming model, puts `captions` on `~/.local/bin`, and links the bar plugin.

Place the widget:

```bash
omarchy bar move io.github.mohuddle.captions --section right
```

Or:

```bash
omarchy plugin add https://github.com/mohuddle/omarchy-captions.git --enable
```

(then run `./scripts/setup.sh` once for the Python side and model.)

## TUI

```bash
captions tui
```

| Key | Action |
| --- | --- |
| `space` | start / stop listening |
| `s` | save transcript |
| `c` | clear |
| `q` | quit |

Saved text goes to `~/.local/state/omarchy/captions/transcript.txt`.

## Plugin

Left click the caption mark: popup with live text, Listen / Save / Clear / TUI. Right click toggles listening without opening the panel.

## CLI

```bash
captions start
captions stop
captions status
captions save [path]
captions clear
captions setup
```

## Notes

- Captions the **default sink**, including ads and other tabs on that output.
- English only in this first model (`zipformer-en-20M`). Swap files under `~/.local/share/omarchy/captions/models/` later if you want another sherpa-onnx streaming transducer.
- Accuracy is not courtroom-grade. CPU-only; GPU is unused.
- Needs `pw-record` (PipeWire).

## License

MIT. ASR runtime is Apache-2.0 sherpa-onnx; the default model is from the k2-fsa / icefall exports.

---
Made by [Mobitecture](https://github.com/mohuddle) · apps, architected.
