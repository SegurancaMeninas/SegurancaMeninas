#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import load_dotenv as dotenv
from typing import Any, Dict, List, Optional

API_BASE = "https://www.googleapis.com/youtube/v3"

dotenv.load_dotenv()

def load_env_file(path: Optional[str] = None) -> None:
    env_path = path or os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"').strip("\"")
            if key and key not in os.environ:
                os.environ[key] = value


def build_url(path: str, params: Dict[str, Any]) -> str:
    return f"{API_BASE}{path}?{urllib.parse.urlencode(params)}"


def fetch_json(url: str) -> Dict[str, Any]:
    try:
        with urllib.request.urlopen(url) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Erro na API do YouTube: {exc.code} - {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Falha de conexão: {exc}") from exc


def get_channel_info(api_key: str, channel_query: str) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "part": "snippet,statistics",
        "key": api_key,
        "maxResults": 1,
    }

    if channel_query.startswith("@"):
        params["forHandle"] = channel_query
    else:
        params["id"] = channel_query

    data = fetch_json(build_url("/channels", params))
    items = data.get("items") or []
    if not items:
        raise RuntimeError("Nenhum canal encontrado para o identificador informado.")

    item = items[0]
    stats = item.get("statistics", {})
    snippet = item.get("snippet", {})

    return {
        "channel_id": item.get("id"),
        "title": snippet.get("title"),
        "description": snippet.get("description", ""),
        "subscriber_count": int(stats.get("subscriberCount", 0)),
        "view_count": int(stats.get("viewCount", 0)),
        "video_count": int(stats.get("videoCount", 0)),
        "custom_url": snippet.get("customUrl", ""),
    }


def get_authenticated_service(api_key: str, client_secret_path: str, token_path: str):
    if not client_secret_path:
        raise RuntimeError("Informe o arquivo client_secret.json via YOUTUBE_CLIENT_SECRETS_FILE ou --client-secret.")

    creds = None
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(token_path, "w", encoding="utf-8") as handle:
                handle.write(creds.to_json())

    return build("youtube", "v3", credentials=creds, developerKey=api_key)


def list_user_subscriptions(service, limit: int = 10) -> List[Dict[str, Any]]:
    subscriptions: List[Dict[str, Any]] = []
    page_token: Optional[str] = None
    remaining = max(limit, 0)

    while remaining > 0:
        request = service.subscriptions().list(
            part="snippet",
            mine=True,
            maxResults=min(remaining, 50),
            order="alphabetical",
        )
        if page_token:
            request = service.subscriptions().list(
                part="snippet",
                mine=True,
                maxResults=min(remaining, 50),
                order="alphabetical",
                pageToken=page_token,
            )

        try:
            response = request.execute()
        except HttpError as exc:
            raise RuntimeError(f"Erro ao listar inscrições do usuário autenticado: {exc}") from exc

        items = response.get("items") or []
        if not items:
            break

        for item in items:
            snippet = item.get("snippet", {})
            subscriptions.append(
                {
                    "title": snippet.get("title"),
                    "channel_id": snippet.get("resourceId", {}).get("channelId"),
                    "description": snippet.get("description", ""),
                }
            )

        if len(subscriptions) >= limit:
            break

        page_token = response.get("nextPageToken")
        if not page_token:
            break
        remaining = max(limit - len(subscriptions), 0)

    return subscriptions[:limit]


def parse_args() -> argparse.Namespace:
    load_env_file()
    parser = argparse.ArgumentParser(description="Consulta informações públicas de um canal do YouTube e lista as inscrições do usuário autenticado")
    parser.add_argument("--channel", default=os.getenv("YOUTUBE_CHANNEL", ""), help="ID ou handle do canal, por exemplo @nome ou UCxxxx")
    parser.add_argument("--api-key", default=os.getenv("YOUTUBE_API_KEY", ""), help="Chave da API do YouTube Data API v3")
    parser.add_argument("--client-secret", default=os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", ""), help="Caminho para o arquivo client_secret.json do OAuth 2.0")
    parser.add_argument("--token-file", default=os.getenv("YOUTUBE_TOKEN_FILE", ""), help="Caminho para o arquivo token.json gerado pelo OAuth")
    parser.add_argument("--limit", type=int, default=10, help="Quantos itens de inscrições mostrar (opcional)")
    parser.add_argument("--show-subscriptions", action="store_true", help="Abre o login do Google e lista as inscrições do usuário autenticado")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.api_key:
        print("Defina a variável de ambiente YOUTUBE_API_KEY ou passe --api-key.", file=sys.stderr)
        return 2

    token_file = args.token_file or os.path.join(os.path.dirname(os.path.dirname(__file__)), "token.json")
    client_secret_path = args.client_secret or os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "")

    try:
        channel_info: Optional[Dict[str, Any]] = None
        if args.channel:
            channel_info = get_channel_info(args.api_key, args.channel)

        payload: Dict[str, Any] = {
            "channel": channel_info,
            "note": "A API do YouTube não expõe uma lista pública de inscritos de um canal. Com OAuth 2.0, este script consegue listar as inscrições do usuário autenticado.",
        }

        if args.show_subscriptions:
            service = get_authenticated_service(args.api_key, client_secret_path, token_file)
            payload["subscriptions"] = list_user_subscriptions(service, limit=args.limit)

        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
