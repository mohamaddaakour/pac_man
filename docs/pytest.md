```python
# You don't pass tmp_path yourself. pytest automatically
# creates it and passes it to your test function.
config, _ = load(tmp_path, text)
```