# Workflow de compilação da IPA

Arquivo: `.github/workflows/ios-kyojinx.yml`

O workflow espera que `3105-1.1.1-original.tar.gz`, `APIClient.h` e `APIClient+Config.m` estejam na raiz do repositório durante a execução. Ele extrai o projeto, aplica as alterações, integra a API e compila a IPA em macOS.
