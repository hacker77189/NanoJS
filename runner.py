# JavascriptCompiler/runner.py
from jsruntime import run_js, run_js_file

lines = run_js_file("test.js")
for line in lines:
    print(line)
