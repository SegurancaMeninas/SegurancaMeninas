from __future__ import annotations

"""
Classificador de canais do YouTube baseado em evidências de conteúdo.

Fluxo:
1. Recebe inscrições (nome + channel_id).
2. Usa a YouTube Data API para obter a descrição do canal e vídeos recentes.
3. Tenta obter trechos públicos de transcrições com timestamps.
4. Envia somente as evidências coletadas para a OpenAI.
5. Valida a resposta: um nome de canal nunca é evidência e uma reprovação
   exige trecho de transcrição com timestamp.

Este arquivo expõe run_classification_for_payload(...), usado por
youtube_subscribers.py.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    from dotenv import load_dotenv
except ImportError:  # A leitura manual cobre ambientes sem python-dotenv.
    load_dotenv = None

try:
    from googleapiclient.discovery import Resource, build
except ImportError:  # Permite explicar o erro de dependência sem quebrar o import.
    Resource = Any  # type: ignore[misc,assignment]
    build = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIRETRIZES_PATH = PROJECT_ROOT / "diretrizes.json"
SUBSCRIPTIONS_PATH = PROJECT_ROOT / "data" / "subscriptions.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "channel_classifications.json"

DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_VIDEO_LIMIT = 6
DEFAULT_TRANSCRIPT_VIDEO_LIMIT = 3
DEFAULT_TRANSCRIPT_CHUNKS_PER_VIDEO = 8
DEFAULT_MAX_CHARS_PER_CHUNK = 360
MIN_VIDEOS_FOR_POSITIVE_DECISION = 4
MIN_TRANSCRIPTS_FOR_POSITIVE_DECISION = 2

CRITICAL_SEVERITIES = {"CRITICAL"}
HIGH_SEVERITIES = {"HIGH"}

VALID_CHANNEL_STATUSES = {
    "WITHIN_GUIDELINES",
    "NOT_SUITABLE_FOR_MINORS",
    "NOT_SUITABLE_FOR_CHILDREN",
    "RESTRICTED_OR_NOT_SUITABLE",
    "INSUFFICIENT_EVIDENCE",
}

VALID_DECISIONS = {
    "WITHIN_GUIDELINES",
    "HUMAN_REVIEW",
    "HUMAN_REVIEW_CRITICAL",
    "INSUFFICIENT_EVIDENCE",
}


class ClassificationError(RuntimeError):
    """Falha controlada de coleta ou classificação."""


def load_project_env() -> None:
    """
    Carrega .env sem sobrescrever variáveis definidas no PowerShell/Windows.

    O youtube_subscribers.py também carrega o .env; esta função permite que
    classify_channels.py seja executado de forma independente.
    """
    env_path = PROJECT_ROOT / ".env"

    if load_dotenv is not None:
        load_dotenv(env_path, override=False)
        return

    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def read_json(path: Path) -> Any:
    """Lê JSON com uma mensagem de erro clara."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ClassificationError(f"Arquivo não encontrado: {path}") from error
    except json.JSONDecodeError as error:
        raise ClassificationError(
            f"JSON inválido em {path} (linha {error.lineno}, coluna {error.colno})."
        ) from error


def positive_int_from_env(name: str, default: int) -> int:
    """Lê um inteiro positivo do .env; usa default em caso de valor inválido."""
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default

    try:
        value = int(raw)
    except ValueError:
        print(
            f"Aviso: {name}={raw!r} é inválido. Usando {default}.",
            file=sys.stderr,
        )
        return default

    return value if value > 0 else default


def normalize_subscriptions(raw_subscriptions: Any) -> list[dict[str, str]]:
    """
    Aceita a estrutura simplificada atual e também a saída antiga enriquecida.

    A saída sempre contém somente:
      - channel_id
      - name
    """
    if isinstance(raw_subscriptions, dict):
        raw_subscriptions = raw_subscriptions.get("subscriptions", [])

    if not isinstance(raw_subscriptions, list):
        raise ClassificationError(
            "subscriptions.json deve conter uma lista de canais ou um objeto "
            "com a chave 'subscriptions'."
        )

    normalized: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for index, item in enumerate(raw_subscriptions, start=1):
        if not isinstance(item, dict):
            print(
                f"Aviso: inscrição {index} ignorada porque não é um objeto JSON.",
                file=sys.stderr,
            )
            continue

        channel_id = str(item.get("channel_id") or "").strip()
        name = str(item.get("name") or item.get("title") or "").strip()

        if not channel_id:
            print(
                f"Aviso: inscrição {index} ignorada porque não tem channel_id.",
                file=sys.stderr,
            )
            continue

        if channel_id in seen_ids:
            continue

        seen_ids.add(channel_id)
        normalized.append({"channel_id": channel_id, "name": name})

    return normalized


def get_public_youtube_service() -> Any | None:
    """
    Cria um serviço público apenas quando classify_channels.py roda sozinho.

    No fluxo normal, youtube_subscribers.py já passa um Resource autenticado,
    portanto YOUTUBE_API_KEY não é necessária.
    """
    api_key = (os.getenv("YOUTUBE_API_KEY") or "").strip()
    if not api_key:
        return None

    if build is None:
        raise ClassificationError(
            "Dependência ausente: instale google-api-python-client."
        )

    return build(
        serviceName="youtube",
        version="v3",
        developerKey=api_key,
        cache_discovery=False,
    )


def safe_execute(request: Any, operation_name: str) -> dict[str, Any]:
    """Executa chamada da API do YouTube e converte falhas em erro controlado."""
    try:
        response = request.execute()
    except Exception as error:
        raise ClassificationError(
            f"Falha na YouTube Data API durante {operation_name}: {error}"
        ) from error

    if not isinstance(response, dict):
        raise ClassificationError(
            f"Resposta inesperada da YouTube Data API durante {operation_name}."
        )

    return response


def to_int(value: Any) -> int | None:
    """Converte timestamps para inteiro quando possível."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    return None


def compact_text(value: Any, max_chars: int) -> str:
    """Remove excesso de espaços e limita tamanho de trecho enviado à LLM."""
    text = " ".join(str(value or "").split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def sample_evenly(items: list[Any], limit: int) -> list[Any]:
    """
    Seleciona itens distribuídos pela transcrição inteira.

    Isso evita analisar somente o início de vídeos longos.
    """
    if limit <= 0 or not items:
        return []

    if len(items) <= limit:
        return items

    if limit == 1:
        return [items[0]]

    indexes = {
        round(position * (len(items) - 1) / (limit - 1))
        for position in range(limit)
    }
    return [items[index] for index in sorted(indexes)]


def fetch_public_transcript(video_id: str) -> list[dict[str, Any]]:
    """
    Busca transcrição pública e devolve trechos normalizados.

    A biblioteca youtube-transcript-api teve duas APIs principais ao longo do
    tempo. O código suporta ambas para não quebrar quando a versão local muda.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return []

    try:
        # API atual (youtube-transcript-api 1.x).
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=["pt", "pt-BR", "en"])

        if hasattr(fetched, "to_raw_data"):
            raw_items = fetched.to_raw_data()
        elif hasattr(fetched, "snippets"):
            raw_items = list(fetched.snippets)
        else:
            raw_items = list(fetched)

    except AttributeError:
        # API legada: método estático.
        try:
            raw_items = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=["pt", "pt-BR", "en"],
            )
        except Exception:
            return []
    except Exception:
        # Transcrição desativada, bloqueada, indisponível ou sem idioma suportado.
        return []

    normalized: list[dict[str, Any]] = []

    for raw_item in raw_items:
        if isinstance(raw_item, dict):
            text = raw_item.get("text", "")
            start = raw_item.get("start")
            duration = raw_item.get("duration")
        else:
            text = getattr(raw_item, "text", "")
            start = getattr(raw_item, "start", None)
            duration = getattr(raw_item, "duration", None)

        snippet = compact_text(text, DEFAULT_MAX_CHARS_PER_CHUNK)
        timestamp_seconds = to_int(start)

        if snippet and timestamp_seconds is not None:
            normalized.append(
                {
                    "text": snippet,
                    "timestamp_seconds": timestamp_seconds,
                    "duration_seconds": to_int(duration),
                }
            )

    return normalized


def collect_channel_content(
    service: Any,
    subscription: dict[str, str],
    *,
    video_limit: int,
    transcript_video_limit: int,
    transcript_chunks_per_video: int,
) -> dict[str, Any]:
    """
    Coleta dados de conteúdo de um canal.

    O nome do canal só é preservado para identificação na saída. Ele NÃO é
    enviado como evidência para a decisão de adequação.
    """
    channel_id = subscription["channel_id"]

    channel_response = safe_execute(
        service.channels().list(
            part="snippet,contentDetails,statistics,status",
            id=channel_id,
            maxResults=1,
        ),
        f"consulta do canal {channel_id}",
    )

    channels = channel_response.get("items", [])
    if not channels:
        raise ClassificationError(
            f"Canal não encontrado ou indisponível na API: {channel_id}"
        )

    channel = channels[0]
    snippet = channel.get("snippet", {}) if isinstance(channel.get("snippet"), dict) else {}
    content_details = (
        channel.get("contentDetails", {})
        if isinstance(channel.get("contentDetails"), dict)
        else {}
    )
    related_playlists = (
        content_details.get("relatedPlaylists", {})
        if isinstance(content_details.get("relatedPlaylists"), dict)
        else {}
    )
    uploads_playlist_id = related_playlists.get("uploads")

    channel_description = compact_text(snippet.get("description", ""), 3500)

    base_result: dict[str, Any] = {
        "channel_id": channel_id,
        "channel_name": subscription.get("name", ""),
        "channel_description": channel_description,
        "published_at": snippet.get("publishedAt"),
        "statistics": channel.get("statistics", {}),
        "uploads_playlist_id": uploads_playlist_id,
        "videos": [],
        "collection_errors": [],
    }

    if not uploads_playlist_id:
        base_result["collection_errors"].append(
            "A API não retornou a playlist pública de uploads do canal."
        )
        return base_result

    playlist_response = safe_execute(
        service.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=min(50, video_limit),
        ),
        f"consulta de vídeos recentes do canal {channel_id}",
    )

    playlist_items = playlist_response.get("items", [])
    video_ids: list[str] = []

    for item in playlist_items:
        if not isinstance(item, dict):
            continue
        content = item.get("contentDetails", {})
        snippet_item = item.get("snippet", {})
        content = content if isinstance(content, dict) else {}
        snippet_item = snippet_item if isinstance(snippet_item, dict) else {}

        video_id = str(
            content.get("videoId")
            or (snippet_item.get("resourceId", {}) or {}).get("videoId")
            or ""
        ).strip()

        if video_id and video_id not in video_ids:
            video_ids.append(video_id)

    if not video_ids:
        base_result["collection_errors"].append(
            "Nenhum vídeo público recente foi retornado pela playlist de uploads."
        )
        return base_result

    details_response = safe_execute(
        service.videos().list(
            part="snippet,contentDetails,status,statistics",
            id=",".join(video_ids),
            maxResults=len(video_ids),
        ),
        f"consulta de detalhes dos vídeos do canal {channel_id}",
    )

    details_by_id = {
        str(item.get("id")): item
        for item in details_response.get("items", [])
        if isinstance(item, dict) and item.get("id")
    }

    transcripts_collected = 0

    for index, video_id in enumerate(video_ids):
        video = details_by_id.get(video_id)
        if not video:
            continue

        video_snippet = (
            video.get("snippet", {})
            if isinstance(video.get("snippet"), dict)
            else {}
        )
        video_status = (
            video.get("status", {})
            if isinstance(video.get("status"), dict)
            else {}
        )
        video_content_details = (
            video.get("contentDetails", {})
            if isinstance(video.get("contentDetails"), dict)
            else {}
        )

        transcript_chunks: list[dict[str, Any]] = []
        if transcripts_collected < transcript_video_limit:
            transcript = fetch_public_transcript(video_id)
            if transcript:
                transcript_chunks = sample_evenly(
                    transcript,
                    transcript_chunks_per_video,
                )
                transcripts_collected += 1

        base_result["videos"].append(
            {
                "video_id": video_id,
                "title": compact_text(video_snippet.get("title", ""), 600),
                "description": compact_text(
                    video_snippet.get("description", ""),
                    3500,
                ),
                "published_at": video_snippet.get("publishedAt"),
                "duration_iso8601": video_content_details.get("duration"),
                "made_for_kids": video_status.get("madeForKids"),
                "privacy_status": video_status.get("privacyStatus"),
                "transcript_chunks": transcript_chunks,
            }
        )

    return base_result


def build_evidence_catalog(channel_content: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Constrói itens citáveis pela LLM.

    Cada source_id é validado após a resposta. Dessa forma, a LLM não consegue
    inserir um vídeo, trecho ou timestamp que não tenha sido coletado.
    """
    catalog: list[dict[str, Any]] = []
    channel_id = channel_content["channel_id"]

    description = compact_text(channel_content.get("channel_description", ""), 3500)
    if description:
        catalog.append(
            {
                "source_id": f"channel:{channel_id}:description",
                "source_type": "CHANNEL_DESCRIPTION",
                "video_id": None,
                "video_title": None,
                "timestamp_seconds": None,
                "text": description,
            }
        )

    for video in channel_content.get("videos", []):
        if not isinstance(video, dict):
            continue

        video_id = str(video.get("video_id") or "")
        title = compact_text(video.get("title", ""), 600)
        description = compact_text(video.get("description", ""), 3500)

        # Títulos são visíveis à LLM, mas não podem ser tratados como DIRECT.
        if title:
            catalog.append(
                {
                    "source_id": f"video:{video_id}:title",
                    "source_type": "VIDEO_TITLE",
                    "video_id": video_id,
                    "video_title": title,
                    "timestamp_seconds": None,
                    "text": title,
                }
            )

        if description:
            catalog.append(
                {
                    "source_id": f"video:{video_id}:description",
                    "source_type": "VIDEO_DESCRIPTION",
                    "video_id": video_id,
                    "video_title": title,
                    "timestamp_seconds": None,
                    "text": description,
                }
            )

        for chunk_index, chunk in enumerate(video.get("transcript_chunks", []), start=1):
            if not isinstance(chunk, dict):
                continue

            timestamp = to_int(chunk.get("timestamp_seconds"))
            excerpt = compact_text(chunk.get("text", ""), DEFAULT_MAX_CHARS_PER_CHUNK)

            if timestamp is None or not excerpt:
                continue

            catalog.append(
                {
                    "source_id": (
                        f"video:{video_id}:transcript:"
                        f"{timestamp}:{chunk_index}"
                    ),
                    "source_type": "TRANSCRIPT",
                    "video_id": video_id,
                    "video_title": title,
                    "timestamp_seconds": timestamp,
                    "text": excerpt,
                }
            )

    return catalog


def build_coverage(channel_content: dict[str, Any]) -> dict[str, int]:
    """Resume o tamanho da amostra coletada."""
    videos = [
        video
        for video in channel_content.get("videos", [])
        if isinstance(video, dict)
    ]
    transcript_videos = sum(
        1 for video in videos if video.get("transcript_chunks")
    )
    transcript_chunks = sum(
        len(video.get("transcript_chunks", []))
        for video in videos
    )

    return {
        "recent_videos_found": len(videos),
        "transcripts_available": transcript_videos,
        "timestamped_transcript_chunks": transcript_chunks,
    }


def classification_schema() -> dict[str, Any]:
    """
    Schema da resposta gerada pela OpenAI.

    O schema proíbe campos extras; posteriormente também validamos as fontes.
    """
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "decision",
            "channel_status",
            "primary_category",
            "categories_detected",
            "analysis_summary",
            "evidence",
        ],
        "properties": {
            "decision": {
                "type": "string",
                "enum": sorted(VALID_DECISIONS),
            },
            "channel_status": {
                "type": "string",
                "enum": sorted(VALID_CHANNEL_STATUSES),
            },
            "primary_category": {
                "type": ["string", "null"],
            },
            "categories_detected": {
                "type": "array",
                "items": {"type": "string"},
            },
            "analysis_summary": {
                "type": "string",
            },
            "evidence": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "source_id",
                        "criterion_id",
                        "assessment",
                        "why_relevant",
                    ],
                    "properties": {
                        "source_id": {"type": "string"},
                        "criterion_id": {"type": "string"},
                        "assessment": {
                            "type": "string",
                            "enum": ["DIRECT", "CONTEXTUAL", "UNCERTAIN"],
                        },
                        "why_relevant": {"type": "string"},
                    },
                },
            },
        },
    }


def build_llm_instructions() -> str:
    """
    Instruções fundamentais para impedir classificação baseada no nome.
    """
    return """
Você classifica a adequação de canais do YouTube para crianças e adolescentes.

Regras obrigatórias:
1. O nome do canal existe somente para identificação e NUNCA é evidência.
   Não infira violência, terror, sexo, apostas ou qualquer outra categoria
   por termos no nome do canal.
2. Use exclusivamente o catálogo de evidências recebido: descrição pública,
   títulos, descrições de vídeos e trechos de transcrição.
3. Uma menção contextual não é promoção. Notícia, crítica, educação,
   ficção, gameplay, humor, denúncia ou relato sobre um tema não equivalem,
   por si só, a incentivo, glorificação, instrução ou conteúdo gráfico.
4. VIDEO_TITLE, VIDEO_DESCRIPTION e CHANNEL_DESCRIPTION não podem receber
   assessment DIRECT. DIRECT só é permitido para TRANSCRIPT com timestamp.
5. Para marcar uma categoria como encontrada, cite source_id existente e o
   criterion_id exato presente na política.
6. Não invente vídeo, trecho, timestamp, citação ou fato externo.
7. Não faça alegações de crime, ilegalidade ou violação da plataforma.
   Avalie apenas adequação ao escopo da política fornecida.
8. Se as evidências forem insuficientes, ambíguas ou sem transcrição
   relevante, retorne decision=INSUFFICIENT_EVIDENCE e
   channel_status=INSUFFICIENT_EVIDENCE.
9. Caso exista evidência DIRECT de critério CRITICAL, retorne
   decision=HUMAN_REVIEW_CRITICAL e use o channel_status definido para esse
   critério. Para critério HIGH com evidência DIRECT, use
   decision=HUMAN_REVIEW e o channel_status do critério.
10. Use WITHIN_GUIDELINES apenas quando a amostra for razoável e não houver
    evidência válida de critério a evitar.
""".strip()


def ask_openai(
    policy: dict[str, Any],
    channel_content: dict[str, Any],
    evidence_catalog: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Solicita uma classificação estruturada pela Responses API.

    O import fica dentro da função para que a coleta do YouTube não quebre
    caso o pacote openai ainda não tenha sido instalado.
    """
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise ClassificationError(
            "OPENAI_API_KEY não está definida no arquivo .env ou no ambiente."
        )

    try:
        from openai import OpenAI
    except ImportError as error:
        raise ClassificationError(
            "Pacote 'openai' não instalado. Execute: "
            "python -m pip install openai"
        ) from error

    policy_criteria = policy.get("criteria_to_avoid", [])
    coverage = build_coverage(channel_content)

    # Não mandamos channel_name ou channel.snippet.title: ambos poderiam levar
    # o modelo a classificar por palavras do nome, exatamente o problema evitado.
    payload = {
        "policy_version": policy.get("policy_version"),
        "classification_scope": policy.get("classification_scope"),
        "criteria_to_avoid": policy_criteria,
        "channel": {
            "channel_id": channel_content.get("channel_id"),
            "channel_description": channel_content.get("channel_description", ""),
            "published_at": channel_content.get("published_at"),
            "statistics": channel_content.get("statistics", {}),
        },
        "coverage": coverage,
        "evidence_catalog": evidence_catalog,
    }

    model = (os.getenv("OPENAI_MODEL") or DEFAULT_MODEL).strip()
    client = OpenAI(api_key=api_key)

    try:
        response = client.responses.create(
            model=model,
            instructions=build_llm_instructions(),
            input=json.dumps(payload, ensure_ascii=False),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "ueca_channel_classification",
                    "strict": True,
                    "schema": classification_schema(),
                }
            },
            temperature=0,
        )
    except Exception as error:
        raise ClassificationError(
            f"Falha ao consultar a OpenAI com o modelo {model!r}: {error}"
        ) from error

    raw_text = getattr(response, "output_text", "")
    if not raw_text:
        raise ClassificationError(
            "A OpenAI não retornou texto estruturado para a classificação."
        )

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError as error:
        raise ClassificationError(
            "A OpenAI retornou um conteúdo que não é JSON válido."
        ) from error

    if not isinstance(result, dict):
        raise ClassificationError("A resposta estruturada da OpenAI não é um objeto.")

    return result


def criterion_index(policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Indexa critérios por id para validação determinística."""
    return {
        str(item.get("id")): item
        for item in policy.get("criteria_to_avoid", [])
        if isinstance(item, dict) and item.get("id")
    }


def materialize_valid_evidence(
    llm_evidence: Any,
    catalog: list[dict[str, Any]],
    valid_criteria: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Descarta referências inventadas e copia o texto/timestamp reais coletados.

    A LLM controla somente a interpretação; a evidência exibida sempre vem da
    YouTube API/transcrição que foi realmente coletada.
    """
    if not isinstance(llm_evidence, list):
        return []

    catalog_by_id = {
        str(item["source_id"]): item
        for item in catalog
        if item.get("source_id")
    }

    validated: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()

    for item in llm_evidence:
        if not isinstance(item, dict):
            continue

        source_id = str(item.get("source_id") or "")
        criterion_id = str(item.get("criterion_id") or "")
        assessment = str(item.get("assessment") or "")
        source = catalog_by_id.get(source_id)

        if source is None or criterion_id not in valid_criteria:
            continue

        if assessment not in {"DIRECT", "CONTEXTUAL", "UNCERTAIN"}:
            assessment = "UNCERTAIN"

        # A própria regra do sistema impede DIRECT fora de transcrição; aqui
        # repetimos a restrição de forma determinística.
        if (
            assessment == "DIRECT"
            and (
                source.get("source_type") != "TRANSCRIPT"
                or source.get("timestamp_seconds") is None
            )
        ):
            assessment = "CONTEXTUAL"

        pair = (source_id, criterion_id)
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)

        validated.append(
            {
                "criterion_id": criterion_id,
                "source_id": source_id,
                "source_type": source.get("source_type"),
                "video_id": source.get("video_id"),
                "video_title": source.get("video_title"),
                "timestamp_seconds": source.get("timestamp_seconds"),
                "excerpt": source.get("text"),
                "assessment": assessment,
                "why_relevant": compact_text(item.get("why_relevant", ""), 600),
            }
        )

    return validated


def direct_criteria(
    validated_evidence: Iterable[dict[str, Any]],
) -> set[str]:
    """Retorna critérios que possuem ao menos evidência DIRECT validada."""
    return {
        str(item["criterion_id"])
        for item in validated_evidence
        if item.get("assessment") == "DIRECT"
    }


def fallback_insufficient_result(
    subscription: dict[str, str],
    channel_content: dict[str, Any] | None,
    *,
    reason: str,
) -> dict[str, Any]:
    """Resultado seguro quando a coleta ou a LLM não pode concluir."""
    coverage = (
        build_coverage(channel_content)
        if isinstance(channel_content, dict)
        else {
            "recent_videos_found": 0,
            "transcripts_available": 0,
            "timestamped_transcript_chunks": 0,
        }
    )

    return {
        "channel_id": subscription["channel_id"],
        "channel_name": subscription.get("name", ""),
        "is_within_ueca_guidelines": None,
        "channel_status": "INSUFFICIENT_EVIDENCE",
        "decision": "INSUFFICIENT_EVIDENCE",
        "needs_human_review": False,
        "primary_category": None,
        "categories_detected": [],
        "analysis_summary": (
            "Não foi possível concluir a adequação do canal com as evidências "
            f"coletadas. Motivo técnico/operacional: {reason}"
        ),
        "evidence": [],
        "coverage": coverage,
        "collection_errors": (
            channel_content.get("collection_errors", [])
            if isinstance(channel_content, dict)
            else []
        ),
        "classification_engine": "not_completed",
    }


def sanitize_llm_result(
    subscription: dict[str, str],
    policy: dict[str, Any],
    channel_content: dict[str, Any],
    catalog: list[dict[str, Any]],
    llm_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Valida a decisão do modelo contra regras que não podem depender da LLM.

    Uma decisão negativa só se sustenta com transcrição timestampada e DIRECT.
    Sem esse nível de evidência, o resultado é INSUFFICIENT_EVIDENCE.
    """
    criteria_by_id = criterion_index(policy)
    evidence = materialize_valid_evidence(
        llm_result.get("evidence"),
        catalog,
        criteria_by_id,
    )
    direct_ids = direct_criteria(evidence)
    coverage = build_coverage(channel_content)

    requested_categories = llm_result.get("categories_detected", [])
    if not isinstance(requested_categories, list):
        requested_categories = []

    categories_detected = [
        str(category_id)
        for category_id in requested_categories
        if str(category_id) in criteria_by_id and str(category_id) in direct_ids
    ]

    # Garante que todo critério DIRECT validado seja exposto, mesmo se a LLM
    # esqueceu de repetir o id em categories_detected.
    for criterion_id in sorted(direct_ids):
        if criterion_id not in categories_detected:
            categories_detected.append(criterion_id)

    direct_critical = [
        criterion_id
        for criterion_id in categories_detected
        if criteria_by_id[criterion_id].get("severity") in CRITICAL_SEVERITIES
    ]
    direct_high = [
        criterion_id
        for criterion_id in categories_detected
        if criteria_by_id[criterion_id].get("severity") in HIGH_SEVERITIES
    ]

    requested_primary = llm_result.get("primary_category")
    primary_category = (
        str(requested_primary)
        if requested_primary in categories_detected
        else (direct_critical[0] if direct_critical else (
            direct_high[0] if direct_high else None
        ))
    )

    summary = compact_text(llm_result.get("analysis_summary", ""), 1400)
    if not summary:
        summary = "Classificação produzida a partir da amostra coletada."

    # Critérios críticos sempre exigem revisão humana segundo diretrizes.json.
    if direct_critical:
        criterion = criteria_by_id[primary_category or direct_critical[0]]
        return {
            "channel_id": subscription["channel_id"],
            "channel_name": subscription.get("name", ""),
            "is_within_ueca_guidelines": False,
            "channel_status": criterion.get(
                "channel_status",
                "NOT_SUITABLE_FOR_MINORS",
            ),
            "decision": "HUMAN_REVIEW_CRITICAL",
            "needs_human_review": True,
            "primary_category": primary_category,
            "categories_detected": categories_detected,
            "analysis_summary": summary,
            "evidence": evidence,
            "coverage": coverage,
            "collection_errors": channel_content.get("collection_errors", []),
            "classification_engine": "openai_validated",
        }

    # Critérios HIGH também exigem revisão, porém não crítica.
    if direct_high:
        criterion = criteria_by_id[primary_category or direct_high[0]]
        return {
            "channel_id": subscription["channel_id"],
            "channel_name": subscription.get("name", ""),
            "is_within_ueca_guidelines": False,
            "channel_status": criterion.get(
                "channel_status",
                "NOT_SUITABLE_FOR_CHILDREN",
            ),
            "decision": "HUMAN_REVIEW",
            "needs_human_review": True,
            "primary_category": primary_category,
            "categories_detected": categories_detected,
            "analysis_summary": summary,
            "evidence": evidence,
            "coverage": coverage,
            "collection_errors": channel_content.get("collection_errors", []),
            "classification_engine": "openai_validated",
        }

    # Só aceita "dentro das diretrizes" com uma amostra mínima.
    enough_for_positive = (
        coverage["recent_videos_found"] >= MIN_VIDEOS_FOR_POSITIVE_DECISION
        and coverage["transcripts_available"] >= MIN_TRANSCRIPTS_FOR_POSITIVE_DECISION
    )

    requested_decision = str(llm_result.get("decision") or "")
    if requested_decision == "WITHIN_GUIDELINES" and enough_for_positive:
        return {
            "channel_id": subscription["channel_id"],
            "channel_name": subscription.get("name", ""),
            "is_within_ueca_guidelines": True,
            "channel_status": "WITHIN_GUIDELINES",
            "decision": "WITHIN_GUIDELINES",
            "needs_human_review": False,
            "primary_category": None,
            "categories_detected": [],
            "analysis_summary": summary,
            "evidence": evidence,
            "coverage": coverage,
            "collection_errors": channel_content.get("collection_errors", []),
            "classification_engine": "openai_validated",
        }

    reason = (
        "A amostra não contém evidência DIRECT com transcrição timestampada "
        "para uma categoria de risco ou não atende à cobertura mínima para "
        "declarar o canal dentro das diretrizes."
    )
    result = fallback_insufficient_result(
        subscription,
        channel_content,
        reason=reason,
    )
    result["analysis_summary"] = summary + " " + reason
    result["evidence"] = evidence
    result["classification_engine"] = "openai_validated"
    return result


def classify_one_channel(
    subscription: dict[str, str],
    policy: dict[str, Any],
    service: Any | None,
    *,
    video_limit: int,
    transcript_video_limit: int,
    transcript_chunks_per_video: int,
) -> dict[str, Any]:
    """Coleta e classifica um canal sem deixar uma falha parar os demais."""
    if service is None:
        return fallback_insufficient_result(
            subscription,
            None,
            reason=(
                "Não há serviço da YouTube Data API. Execute pelo "
                "youtube_subscribers.py ou defina YOUTUBE_API_KEY no .env."
            ),
        )

    channel_content: dict[str, Any] | None = None

    try:
        channel_content = collect_channel_content(
            service,
            subscription,
            video_limit=video_limit,
            transcript_video_limit=transcript_video_limit,
            transcript_chunks_per_video=transcript_chunks_per_video,
        )
        catalog = build_evidence_catalog(channel_content)

        if not catalog:
            return fallback_insufficient_result(
                subscription,
                channel_content,
                reason="A coleta não retornou descrição, vídeos ou transcrições utilizáveis.",
            )

        llm_result = ask_openai(policy, channel_content, catalog)
        return sanitize_llm_result(
            subscription,
            policy,
            channel_content,
            catalog,
            llm_result,
        )

    except ClassificationError as error:
        return fallback_insufficient_result(
            subscription,
            channel_content,
            reason=str(error),
        )
    except Exception as error:  # proteção para que um canal não derrube o lote
        return fallback_insufficient_result(
            subscription,
            channel_content,
            reason=f"Erro inesperado durante classificação: {error}",
        )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Cria a pasta e grava JSON formatado."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def run_classification_for_payload(
    subscriptions: list[dict[str, Any]] | dict[str, Any],
    output_path: Path | None = None,
    service: Any | None = None,
) -> dict[str, Any]:
    """
    Ponto de integração usado por youtube_subscribers.py.

    Assinatura propositalmente compatível com o arquivo já existente:
        run_classification_for_payload(
            clean_payload,
            output_path=classification_output_path,
            service=service,
        )
    """
    load_project_env()

    policy = read_json(DIRETRIZES_PATH)
    normalized_subscriptions = normalize_subscriptions(subscriptions)

    # Quando chamado isoladamente, a chave de API pública permite a coleta.
    if service is None:
        try:
            service = get_public_youtube_service()
        except ClassificationError:
            service = None

    video_limit = positive_int_from_env(
        "CHANNEL_ANALYSIS_VIDEO_LIMIT",
        DEFAULT_VIDEO_LIMIT,
    )
    transcript_video_limit = positive_int_from_env(
        "CHANNEL_ANALYSIS_TRANSCRIPT_VIDEOS",
        DEFAULT_TRANSCRIPT_VIDEO_LIMIT,
    )
    transcript_chunks_per_video = positive_int_from_env(
        "CHANNEL_ANALYSIS_TRANSCRIPT_CHUNKS_PER_VIDEO",
        DEFAULT_TRANSCRIPT_CHUNKS_PER_VIDEO,
    )

    results: list[dict[str, Any]] = []

    for index, subscription in enumerate(normalized_subscriptions, start=1):
        display_name = subscription["name"] or subscription["channel_id"]
        print(
            f"[Classificação {index}/{len(normalized_subscriptions)}] "
            f"Coletando evidências de: {display_name}",
            file=sys.stderr,
        )

        result = classify_one_channel(
            subscription,
            policy,
            service,
            video_limit=video_limit,
            transcript_video_limit=transcript_video_limit,
            transcript_chunks_per_video=transcript_chunks_per_video,
        )
        results.append(result)

        print(
            f"  -> {result['decision']} | {result['channel_status']}",
            file=sys.stderr,
        )

    payload = {
        "policy_version": policy.get("policy_version"),
        "classification_scope": policy.get("classification_scope"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_method": {
            "name": "youtube_content_evidence_with_timestamped_transcripts",
            "channel_name_used_as_evidence": False,
            "negative_decision_requires_direct_timestamped_transcript": True,
            "critical_cases_require_human_review": True,
        },
        "results": results,
    }

    destination = output_path or OUTPUT_PATH
    write_json(destination, payload)
    print(f"Classificações salvas em: {destination}")
    return payload


def parse_args() -> argparse.Namespace:
    """Argumentos para executar este classificador sem atualizar inscrições."""
    parser = argparse.ArgumentParser(
        description=(
            "Classifica canais presentes em subscriptions.json usando conteúdo "
            "coletado pela YouTube Data API e transcrições públicas."
        )
    )
    parser.add_argument(
        "--input",
        default=str(SUBSCRIPTIONS_PATH),
        help="Arquivo de inscrições. Padrão: data/subscriptions.json.",
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_PATH),
        help="Arquivo de classificação. Padrão: data/channel_classifications.json.",
    )
    return parser.parse_args()


def main() -> int:
    """
    Executa somente a classificação de um subscriptions.json já existente.

    Para essa forma independente, adicione YOUTUBE_API_KEY ao .env. Para usar
    o OAuth que você já possui, rode `python src/main.py --limit 10`.
    """
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.is_absolute():
        input_path = (PROJECT_ROOT / input_path).resolve()
    if not output_path.is_absolute():
        output_path = (PROJECT_ROOT / output_path).resolve()

    try:
        subscriptions = read_json(input_path)
        run_classification_for_payload(
            subscriptions,
            output_path=output_path,
            service=None,
        )
    except ClassificationError as error:
        print(f"ERRO: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
