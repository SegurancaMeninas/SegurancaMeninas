import datetime
from newsapi import NewsApiClient

# ==============================
# CONFIGURAÇÃO
# ==============================
#insira-aqui
API_KEY = ""

newsapi = NewsApiClient(api_key=API_KEY)

data_inicio = (
    datetime.date.today() - datetime.timedelta(days=7)
).strftime("%Y-%m-%d")

# Consultas independentes
CONSULTAS = [
    '"deepfake" AND adolescente',
    '"deepfake" AND escola',
    '"deepfake" AND menina',
    '"IA" AND alunas',
    '"nudes falsos"',
    '"imagem íntima"',
    'cyberbullying',
    '"violência digital"',
    'sextorsão',
    '"assédio online"',
    '"exposição íntima"',
    '"pornografia de vingança"',
]

# Palavras que aumentam a relevância
PALAVRAS_RELEVANTES = {
    "deepfake": 5,
    "ia": 4,
    "inteligência artificial": 4,
    "cyberbullying": 5,
    "violência digital": 5,
    "nudes": 5,
    "imagem íntima": 5,
    "sextorsão": 5,
    "adolescente": 3,
    "adolescentes": 3,
    "menina": 3,
    "meninas": 3,
    "aluna": 3,
    "alunas": 3,
    "escola": 2,
    "colégio": 2,
    "instituto": 2,
    "ifrj": 2,
}

# ==============================
# SCORE
# ==============================

def calcular_score(texto):

    texto = texto.lower()

    score = 0

    for palavra, peso in PALAVRAS_RELEVANTES.items():
        if palavra in texto:
            score += peso

    return score


# ==============================
# BUSCA
# ==============================

def buscar_noticias():

    noticias = []
    urls = set()

    for consulta in CONSULTAS:

        print(f"Buscando: {consulta}")

        try:

            resposta = newsapi.get_everything(
                q=consulta,
                language="pt",
                from_param=data_inicio,
                sort_by="publishedAt",
                page_size=100,
            )

            for artigo in resposta["articles"]:

                titulo = artigo["title"]

                if titulo is None:
                    continue

                url = artigo["url"]

                if url in urls:
                    continue

                urls.add(url)

                resumo = artigo["description"] or ""
                conteudo = artigo["content"] or ""

                texto = (
                    titulo
                    + " "
                    + resumo
                    + " "
                    + conteudo
                )

                score = calcular_score(texto)

                noticias.append(
                    {
                        "titulo": titulo,
                        "fonte": artigo["source"]["name"],
                        "url": url,
                        "resumo": resumo,
                        "data": artigo["publishedAt"],
                        "imagem": artigo["urlToImage"],
                        "autor": artigo["author"],
                        "score": score,
                    }
                )

        except Exception as e:
            print(e)

    noticias.sort(
        key=lambda x: (x["score"], x["data"]),
        reverse=True,
    )

    return noticias


# ==============================
# MAIN
# ==============================

noticias = buscar_noticias()

print()

print("=" * 80)
print(f"Foram encontradas {len(noticias)} notícias.")
print("=" * 80)

for n in noticias:

    print()

    print("Score:", n["score"])
    print("Título:", n["titulo"])
    print("Fonte:", n["fonte"])
    print("Data:", n["data"])
    print("Resumo:", n["resumo"])
    print("URL:", n["url"])