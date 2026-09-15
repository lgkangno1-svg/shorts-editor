# Local vision providers

## SmolVLM2 500M via llama.cpp

The first supported local semantic provider is `smolvlm2_llamacpp_provider.py`.
It is designed for the existing Shopping Shorts vision request/provenance contract and does
not change benchmark membership or training evidence.

Recommended lightweight model:

- Hugging Face: `ggml-org/SmolVLM2-500M-Video-Instruct-GGUF`
- Suggested quantization: `Q8_0`
- License: Apache-2.0
- Runtime: current llama.cpp multimodal server

Start the local model server:

```bash
llama serve -hf ggml-org/SmolVLM2-500M-Video-Instruct-GGUF:Q8_0 --host 127.0.0.1 --port 8080
```

Then run it through the engine's outer provider/provenance adapter:

```bash
python3 youtube-shopping-shorts-benchmark/single-product-engine/tools/run_vision_provider_adapter.py \
  /path/to/bound-vision-request.json \
  --provider llama.cpp \
  --model ggml-org/SmolVLM2-500M-Video-Instruct-GGUF:Q8_0 \
  --output /path/to/provider-envelope.json \
  --provider-command \
    python3 youtube-shopping-shorts-benchmark/single-product-engine/providers/smolvlm2_llamacpp_provider.py \
      --base-url http://127.0.0.1:8080/v1 \
      --model auto
```

`--model auto` asks llama.cpp `/v1/models` for the loaded model id. The model name supplied
to `run_vision_provider_adapter.py` remains provenance metadata for the engine.

### Evidence boundary

This provider deliberately refuses to make model inference equivalent to direct verification:

- frame file identity: handled by the outer adapter and may be `confirmed`;
- SmolVLM2 visual semantics: emitted only as `estimated` or `unknown`;
- product identity: `unknown` unless a separate direct verification layer promotes it;
- audio/BGM/SFX/Foley/spoken words from still frames: always `unknown`;
- provider outputs: excluded from benchmark training by the existing vision-provider pipeline.

The provider submits all requested early/mid/late keyframes for a segment to llama.cpp and
uses schema-constrained JSON. A segment becomes `estimated` only when the model returns a
non-empty visible description and at least one controlled semantic tag; otherwise it stays
`unknown`.

### Why this model

The 500M SmolVLM2 variant is small enough to be a practical MiniPC experiment while still
being explicitly trained for image/video understanding. The provider is protocol-based, so a
larger compatible multimodal model can be substituted later without weakening the evidence
contract.
