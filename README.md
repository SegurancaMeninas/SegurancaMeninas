# SegurancaMeninas

Este projeto usa a YouTube Data API com OAuth 2.0 para autenticar no Google e listar as inscrições da conta autenticada.

## Estrutura do projeto

```text
SegurancaMeninas/
├── client_secret.json
├── requirements.txt
├── .env
├── subscriptions.json
├── src/
│   ├── main.py
│   ├── youtube_subscribers.py
│   └── youtube_client/
│       ├── __init__.py
│       ├── auth.py
│       ├── cli.py
│       ├── config.py
│       └── services.py
```

## Como usar

1. Crie um projeto no Google Cloud Console:
   - Ative a YouTube Data API v3.
   - Crie um OAuth 2.0 Client ID do tipo Desktop app.
   - Faça download do arquivo client_secret.json e coloque na raiz do projeto.

2. Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

3. Execute o script:

```bash
python src/main.py --limit 10
```

4. O primeiro acesso abrirá um fluxo de autorização no terminal para você entrar com a conta Google e conceder permissão.

## Arquivos de configuração

- [.env](.env): opcional; pode ser usado para sobrescrever caminhos de arquivos.
- [client_secret.json](client_secret.json): credencial OAuth do Google.
- [token.json](token.json): token salvo automaticamente após a autorização.
- [subscriptions.json](subscriptions.json): saída com as inscrições encontradas.

## Saída em data

O projeto agora também gera uma pasta [data](data) com:

- [data/subscriptions.json](data/subscriptions.json): resumo das inscrições com metadados de vídeo e transcrição.
- [data/videos](data/videos): arquivos de áudio baixados dos últimos vídeos.
- [data/transcripts](data/transcripts): transcrições em texto.
- [data/metadata](data/metadata): arquivos JSON com os metadados de cada canal/vídeo.

## Resetar o token de autenticação

Se você quiser trocar de conta Google ou forçar uma nova autorização, use:

```bash
python src/main.py --reauthorize --limit 10
```

Esse parâmetro remove o token antigo e pede uma nova autorização do Google. Ele é útil quando:

- você quer mudar de conta do Google;
- o token ficou inválido ou expirou;
- você quer refazer o fluxo OAuth do zero.

## Observação

A API do YouTube não expõe uma lista pública de inscritos de um canal. Com OAuth 2.0, este script consegue listar as inscrições do usuário autenticado, que é o fluxo compatível com a API.
