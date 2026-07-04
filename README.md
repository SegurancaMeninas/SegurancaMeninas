# SegurancaMeninas

Este projeto contém um exemplo em Python que usa a YouTube Data API com OAuth 2.0 para autenticar no Google e listar as inscrições do usuário autenticado.

## Como usar

1. Crie um projeto no Google Cloud Console:
   - Ative a YouTube Data API v3.
   - Crie uma chave de API.
   - Crie um OAuth 2.0 Client ID do tipo Desktop app.
   - Faça download do arquivo client_secret.json.

2. Crie um arquivo .env na raiz do projeto com os valores:

```env
YOUTUBE_API_KEY=SUA_CHAVE
YOUTUBE_CLIENT_SECRETS_FILE=client_secret.json
```

Você também pode usar o arquivo .env.example como modelo.

3. Instale as dependências:

```bash
python3 -m pip install -r requirements.txt
```

4. Execute o script:

```bash
python3 src/youtube_subscribers.py --channel @nome_do_canal --show-subscriptions --limit 10
```

O primeiro acesso abrirá uma janela do navegador para você fazer login com a conta Google e autorizar o acesso.

## Observação

A API do YouTube não expõe uma lista pública de inscritos de um canal. Com OAuth 2.0, este script consegue listar as inscrições do usuário autenticado, o que é o fluxo compatível com a API.
