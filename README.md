# SegurancaMeninas

Este projeto usa a YouTube Data API com OAuth 2.0 para autenticar no Google e listar as inscrições da conta autenticada.

## Estrutura do projeto

```text
SegurancaMeninas/
├── client_secret.json
├── requirements.txt
├── .env
├── token.json
├── src/
│   ├── main.py
│   └── youtube_subscribers.py
└── data/
    └── subscriptions.json
```

## Pré-requisitos

1. Crie um projeto no Google Cloud Console.
2. Ative a YouTube Data API v3.
3. Crie uma credencial OAuth 2.0 do tipo Desktop app.
4. Baixe o arquivo client_secret.json e coloque na raiz do projeto.

## Instalação

```bash
python -m pip install -r requirements.txt
```

## Como usar

Execute o script abaixo para listar as inscrições da conta autenticada:

```bash
python src/main.py --limit 10
```

No primeiro acesso, o script abrirá um fluxo de autorização no terminal. Você precisará:

- abrir o link exibido;
- fazer login com a conta Google;
- conceder permissão ao aplicativo;
- copiar o código de autorização de volta para o terminal.

O token será salvo automaticamente em token.json para futuras execuções.

## Saída

Os resultados são salvos em um arquivo JSON limpo em data/subscriptions.json, com o seguinte formato:

```json
[
  {
    "name": "Canal Exemplo",
    "channel_id": "UC1234567890"
  }
]
```

## Reautorização

Se quiser trocar de conta ou forçar um novo login OAuth, use:

```bash
python src/main.py --reauthorize --limit 10
```

## Observação

A API do YouTube não expõe uma lista pública de inscritos de um canal. Com OAuth 2.0, este script consegue listar as inscrições do usuário autenticado, que é o fluxo compatível com a API.
