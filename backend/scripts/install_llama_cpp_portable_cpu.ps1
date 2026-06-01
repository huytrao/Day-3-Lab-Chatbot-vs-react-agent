$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$venvPython = Resolve-Path (Join-Path $projectRoot "..\.venv\Scripts\python.exe")

Write-Host "Installing llama-cpp-python with portable CPU flags..."
Write-Host "Python: $venvPython"

$env:CMAKE_ARGS = "-DLLAMA_NATIVE=OFF -DGGML_NATIVE=OFF -DGGML_AVX=OFF -DGGML_AVX2=OFF -DGGML_FMA=OFF -DGGML_F16C=OFF"
$env:FORCE_CMAKE = "1"

& $venvPython -m pip install --force-reinstall --no-cache-dir --no-binary llama-cpp-python llama-cpp-python

Write-Host "Done. Test with:"
Write-Host "  cd $projectRoot"
Write-Host "  ..\.venv\Scripts\python.exe -c `"from backend.agent.local_model import polish_answer_with_local_model; print(polish_answer_with_local_model('Xin chao', 'Xin chao quy khach.'))`""
