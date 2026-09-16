# RapidOCR integration notes

Install the optional local OCR runtime with:

```bash
pip install -e '.[ocr]'
```

The default Korean engine factory enables `return_word_box=True`. Line boxes feed subtitle tracking; word-level polygons feed precise removal masks. Broad line-mask fallback stays disabled in `run_rapidocr_frame()`.
