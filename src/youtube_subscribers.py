from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError


# Permissão mínima necessária:
# permite ler dados do YouTube da conta autenticada.
SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly"
]

# Pasta raiz do projeto (onde ficam client_secret.json, .env e token.json).
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_env_file(env_path: Path) -> None:
    """
    Lê um arquivo .env simples.

    Aceita formatos como:

        NOME=valor
        NOME="valor com espaços"
        export NOME=valor

    Variáveis já existentes no sistema não são sobrescritas.
    """

    if not env_path.exists():
        return

    with env_path.open("r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()

            # Ignora linhas vazias e comentários.
            if not line or line.startswith("#"):
                continue

            # Permite: export NOME=valor
            if line.startswith("export "):
                line = line.removeprefix("export ").strip()

            # Ignora linhas que não possuem "=".
            if "=" not in line:
                continue

            key, value = line.split("=", maxsplit=1)

            key = key.strip()
            value = value.strip().strip("'\"")

            # Só salva se houver nome e ainda não existir no ambiente.
            if key and key not in os.environ:
                os.environ[key] = value


def get_path_from_env_or_argument(
    argument_value: str | None,
    env_name: str,
    default_filename: str,
) -> Path:
    """
    Define um caminho usando esta prioridade:

    1. argumento passado no terminal;
    2. variável do .env;
    3. nome padrão ao lado deste script.
    """

    raw_value = argument_value or os.getenv(env_name) or default_filename

    path = Path(raw_value)

    # Se o caminho for relativo, ele será buscado na pasta do script.
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    return path.resolve()


def create_authenticated_youtube_service(
    client_secret_path: Path,
    token_path: Path,
    force_new_authorization: bool,
) -> Resource:
    """
    Cria um cliente autenticado para acessar a YouTube Data API.

    Etapas:

    1. Verifica se existe client_secret.json.
    2. Tenta reutilizar token.json.
    3. Renova token expirado.
    4. Se não houver token válido, abre o navegador para OAuth.
    5. Salva o novo token em token.json.
    """

    if not client_secret_path.exists():
        raise FileNotFoundError(
            "Arquivo OAuth não encontrado:\n"
            f"{client_secret_path}\n\n"
            "Crie uma credencial OAuth do tipo 'Desktop app' "
            "no Google Cloud e baixe o JSON para esse local."
        )

    # Força um novo login apagando o token antigo.
    if force_new_authorization and token_path.exists():
        token_path.unlink()

    credentials: Credentials | None = None

    # Tenta reaproveitar o token existente.
    if token_path.exists():
        try:
            credentials = Credentials.from_authorized_user_file(
                str(token_path),
                SCOPES,
            )
        except (ValueError, OSError):
            # Token inválido, corrompido ou incompatível.
            credentials = None

    # Se o token venceu, tenta renová-lo.
    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
        except RefreshError:
            credentials = None

    # Sem token válido: usa um fluxo compatível com terminal.
    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_secret_path),
            SCOPES,
        )

        print(
            "Abra o link abaixo no navegador, autorize o aplicativo e cole o "
            "código de autorização no terminal.",
            file=sys.stderr,
        )
        credentials = flow.run_console()

        # Cria pasta do token, se necessário.
        token_path.parent.mkdir(parents=True, exist_ok=True)

        # Salva o token para não pedir login em toda execução.
        token_path.write_text(
            credentials.to_json(),
            encoding="utf-8",
        )

        # Em Linux/macOS, tenta restringir permissões do arquivo.
        try:
            token_path.chmod(0o600)
        except OSError:
            pass

    # Cria o cliente oficial da YouTube Data API.
    return build(
        serviceName="youtube",
        version="v3",
        credentials=credentials,
        cache_discovery=False,
    )


def get_authenticated_channel(service: Resource) -> dict[str, Any] | None:
    """
    Descobre qual canal do YouTube pertence à conta autenticada.

    Isso serve apenas para registrar no JSON qual conta foi usada.
    """

    response = service.channels().list(
        part="snippet",
        mine=True,
        maxResults=1,
    ).execute()

    items = response.get("items", [])

    if not items:
        return None

    channel = items[0]
    snippet = channel.get("snippet", {})

    channel_id = channel.get("id")

    return {
        "channel_id": channel_id,
        "title": snippet.get("title"),
        "url": f"https://www.youtube.com/channel/{channel_id}",
    }


def normalize_subscription(item: dict[str, Any]) -> dict[str, Any]:
    """
    Transforma o objeto grande retornado pela API em um formato menor.

    O campo mais importante é channel_id.

    Ele será usado futuramente para:
    - buscar vídeos do canal;
    - obter o vídeo mais recente;
    - tentar coletar transcrição;
    - enviar o texto para um classificador.
    """

    snippet = item.get("snippet", {})
    resource_id = snippet.get("resourceId", {})
    thumbnails = snippet.get("thumbnails", {})

    channel_id = resource_id.get("channelId")

    # Tenta pegar uma thumbnail grande; se não existir, usa menor.
    thumbnail_url = (
        thumbnails.get("high", {}).get("url")
        or thumbnails.get("medium", {}).get("url")
        or thumbnails.get("default", {}).get("url")
    )

    return {
        # ID da relação de inscrição.
        "subscription_id": item.get("id"),

        # ID real do canal inscrito.
        "channel_id": channel_id,

        # Nome do canal.
        "title": snippet.get("title"),

        # Descrição pública do canal.
        "description": snippet.get("description", ""),

        # Data em que a conta se inscreveu nesse canal.
        "subscribed_at": snippet.get("publishedAt"),

        # Imagem do canal.
        "thumbnail_url": thumbnail_url,

        # Link direto para o canal.
        "channel_url": (
            f"https://www.youtube.com/channel/{channel_id}"
            if channel_id
            else None
        ),
    }


def list_user_subscriptions(
    service: Resource,
    limit: int,
) -> list[dict[str, Any]]:
    """
    Busca todos os canais aos quais a conta autenticada está inscrita.

    limit = 0:
        Busca todas as inscrições.

    limit > 0:
        Busca no máximo essa quantidade.

    A API permite no máximo 50 resultados por requisição,
    então usamos pageToken para navegar pelas páginas.
    """

    subscriptions: list[dict[str, Any]] = []

    # page_token identifica a próxima página.
    page_token: str | None = None

    while True:
        # Se houver limite, calcula quantos itens faltam.
        remaining = limit - len(subscriptions) if limit > 0 else 50

        # A API aceita no máximo 50 por chamada.
        page_size = min(50, remaining) if limit > 0 else 50

        response = service.subscriptions().list(
            part="snippet",
            mine=True,
            maxResults=page_size,
            order="alphabetical",
            pageToken=page_token,
        ).execute()

        items = response.get("items", [])

        # Converte cada resposta para nosso formato simplificado.
        subscriptions.extend(
            normalize_subscription(item)
            for item in items
        )

        # Caso tenha atingido o limite solicitado.
        if limit > 0 and len(subscriptions) >= limit:
            return subscriptions[:limit]

        # Recebe token da próxima página.
        page_token = response.get("nextPageToken")

        # Se não houver próxima página, terminou.
        if not page_token:
            return subscriptions


def build_clean_subscription_payload(
    subscriptions: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Cria uma saída simples com nome e channel_id para exportação."""

    return [
        {
            "name": subscription.get("title") or "",
            "channel_id": subscription.get("channel_id") or "",
        }
        for subscription in subscriptions
    ]


def print_subscriptions(
    authenticated_channel: dict[str, Any] | None,
    subscriptions: list[dict[str, Any]],
) -> None:
    """Exibe as inscrições de forma legível no terminal."""

    print("\n=== Inscrições do canal autenticado ===")

    if authenticated_channel:
        print(
            f"Conta autenticada: {authenticated_channel.get('title')}"
            f" ({authenticated_channel.get('channel_id')})"
        )
    else:
        print("Conta autenticada: não foi possível identificar o canal.")

    if not subscriptions:
        print("Nenhuma inscrição encontrada.")
        return

    print(f"Total de inscrições encontradas: {len(subscriptions)}")
    for index, subscription in enumerate(subscriptions, start=1):
        title = subscription.get("title") or "Sem título"
        channel_id = subscription.get("channel_id") or "-"
        print(f"{index}. {title} ({channel_id})")


def parse_args() -> argparse.Namespace:
    """
    Lê argumentos informados no terminal.
    """

    # Carrega .env antes de ler argumentos.
    load_env_file(PROJECT_ROOT / ".env")

    parser = argparse.ArgumentParser(
        description=(
            "Lista os canais do YouTube aos quais "
            "a conta autenticada está inscrita."
        )
    )

    parser.add_argument(
        "--client-secret",
        help=(
            "Caminho para client_secret.json. "
            "Alternativa: YOUTUBE_CLIENT_SECRETS_FILE no .env."
        ),
    )

    parser.add_argument(
        "--token-file",
        help=(
            "Caminho para token.json. "
            "Alternativa: YOUTUBE_TOKEN_FILE no .env."
        ),
    )

    parser.add_argument(
        "--output",
        help=(
            "Arquivo JSON de saída. "
            "Alternativa: YOUTUBE_SUBSCRIPTIONS_OUTPUT no .env."
            " Padrão: data/subscriptions.json."
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help=(
            "Quantidade máxima de inscrições. "
            "Use 0 para buscar todas. Padrão: 0."
        ),
    )

    parser.add_argument(
        "--reauthorize",
        action="store_true",
        help=(
            "Apaga o token atual e força um novo login OAuth."
        ),
    )

    args = parser.parse_args()

    if args.limit < 0:
        parser.error("--limit deve ser 0 ou um inteiro positivo.")

    return args


def main() -> int:
    """
    Função principal.

    Ela:

    1. Lê configurações;
    2. Faz login OAuth;
    3. Busca o canal autenticado;
    4. Busca as inscrições;
    5. Salva tudo em subscriptions.json.
    """

    args = parse_args()

    client_secret_path = get_path_from_env_or_argument(
        argument_value=args.client_secret,
        env_name="YOUTUBE_CLIENT_SECRETS_FILE",
        default_filename="client_secret.json",
    )

    token_path = get_path_from_env_or_argument(
        argument_value=args.token_file,
        env_name="YOUTUBE_TOKEN_FILE",
        default_filename="token.json",
    )

    output_path = get_path_from_env_or_argument(
        argument_value=args.output,
        env_name="YOUTUBE_SUBSCRIPTIONS_OUTPUT",
        default_filename="data/subscriptions.json",
    )

    try:
        # Faz autenticação OAuth.
        service = create_authenticated_youtube_service(
            client_secret_path=client_secret_path,
            token_path=token_path,
            force_new_authorization=args.reauthorize,
        )

        # Descobre qual canal autenticou.
        authenticated_channel = get_authenticated_channel(service)

        # Lista os canais aos quais a conta segue.
        subscriptions = list_user_subscriptions(
            service=service,
            limit=args.limit,
        )

        # Estrutura final salva em um JSON limpo com nome e channel_id.
        clean_payload = build_clean_subscription_payload(subscriptions)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            json.dumps(
                clean_payload,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print_subscriptions(authenticated_channel, subscriptions)

        print(
            f"\nConcluído: {len(clean_payload)} inscrições foram salvas em:\n"
            f"{output_path}"
        )

        return 0

    except FileNotFoundError as error:
        print(
            f"ERRO: {error}",
            file=sys.stderr,
        )
        return 2

    except HttpError as error:
        print(
            "ERRO na YouTube Data API:\n"
            f"Status: {error.resp.status}\n"
            f"Detalhes: "
            f"{error.content.decode('utf-8', errors='replace')}",
            file=sys.stderr,
        )
        return 3

    except Exception as error:
        print(
            f"ERRO inesperado: {error}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())