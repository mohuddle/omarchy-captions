from __future__ import annotations

from typing import Any

from .models import transducer_paths


def pcm16_to_float(chunk: bytes) -> list[float]:
    import array

    samples = array.array("h")
    samples.frombytes(chunk[: len(chunk) - (len(chunk) % 2)])
    return [s / 32768.0 for s in samples]


class StreamingAsr:
    def __init__(self, sample_rate: int = 16000, num_threads: int = 2) -> None:
        import sherpa_onnx

        paths = transducer_paths()
        self.sample_rate = sample_rate
        self.recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(
            tokens=paths["tokens"],
            encoder=paths["encoder"],
            decoder=paths["decoder"],
            joiner=paths["joiner"],
            num_threads=num_threads,
            sample_rate=sample_rate,
            feature_dim=80,
            decoding_method="greedy_search",
            provider="cpu",
            enable_endpoint_detection=True,
            rule1_min_trailing_silence=2.4,
            rule2_min_trailing_silence=1.2,
            rule3_min_utterance_length=20.0,
        )
        self.stream = self.recognizer.create_stream()
        self._last = ""

    def accept(self, pcm16: bytes) -> dict[str, Any] | None:
        samples = pcm16_to_float(pcm16)
        if not samples:
            return None
        self.stream.accept_waveform(self.sample_rate, samples)
        while self.recognizer.is_ready(self.stream):
            self.recognizer.decode_stream(self.stream)
        text = (self.recognizer.get_result(self.stream) or "").strip()
        endpoint = self.recognizer.is_endpoint(self.stream)
        if endpoint:
            self.recognizer.reset(self.stream)
            self._last = ""
            if text:
                return {"event": "final", "text": text}
            return None
        if text and text != self._last:
            self._last = text
            return {"event": "partial", "text": text}
        return None
