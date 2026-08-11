"""
=============================================================
P5 — Diseño que soporte scraping Y API  ·  RESUELTO
=============================================================
    CNN -> release -> API -> extract articles

Dos formas de obtener artículos: Scraping (lo implementamos) y
API (la consumimos). "What would be your design to support both?"

Te dieron esta clase de partida:

    class NewsScrappingService:
        def __init__(self, url):
            self.url = url
        def scrapper(self):   # Extract articles cnn.com

-------------------------------------------------------------
LA IDEA CENTRAL, EN UNA FRASE
    El servicio no debe saber CÓMO se obtienen los artículos,
    solo que ALGUIEN sabe hacerlo.

EL ERROR QUE EVALÚAN SI COMETES
    if source == "api": ...  elif source == "scraper": ...
    Cada fuente nueva obliga a abrir y modificar el servicio.

ANALOGÍA
    ArticleSource es el enchufe de la pared. Tu casa (el servicio)
    no sabe si la luz viene de un panel solar o de la hidroeléctrica;
    solo sabe que ahí hay 127V. Cambiar la generadora no te obliga
    a recablear la casa.
=============================================================
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone


# =============================================================
# 1. CRÍTICA A LA CLASE DE PARTIDA
# =============================================================
# Dos problemas, y conviene decirlos en voz alta antes de escribir:
#
# a) EL NOMBRE ACOPLA EL SERVICIO A UNA TÉCNICA.
#    "NewsScrappingService" mete el CÓMO en el nombre del QUÉ.
#    El día que consumas la API, o el nombre miente o creas un
#    segundo servicio duplicado. El servicio debe llamarse por su
#    responsabilidad de negocio (NewsService: ingerir noticias),
#    no por el mecanismo.
#
# b) `url` EN EL CONSTRUCTOR NO MODELA UNA API.
#    Un scraper necesita una URL. Una API necesita base_url +
#    api_key + paginación + rate limit + headers. Meter todo eso
#    en un solo parámetro `url` no escala; y meterlo como campos
#    opcionales convierte la clase en un cajón de sastre donde la
#    mitad de los atributos son None según el modo.
#
# CONCLUSIÓN: hay que subir un nivel de abstracción. Cada fuente
# guarda SU propia configuración; el servicio no la conoce.


# =============================================================
# 2. MODELO DE DOMINIO COMÚN
# =============================================================
# Todo termina aquí, venga de HTML o de JSON. Es lo que hace que
# el resto del sistema no sepa de dónde salió el artículo.

@dataclass(frozen=True)          # frozen: inmutable y hashable
class Article:
    external_id: str             # id en el origen -> deduplicación
    title: str
    url: str
    published_at: datetime       # SIEMPRE timezone-aware (UTC)
    body: str
    source: str                  # "cnn_api" | "cnn_scraper" | ...

# Por qué dataclass y no dict: tipos explícitos, autocompletado,
# y el contrato queda documentado en el código.
# Por qué frozen: un artículo ya extraído no debe mutar; además
# poder meterlo en un set() facilita deduplicar.


# =============================================================
# 3. EL CONTRATO (el "puerto")
# =============================================================

class ArticleSource(ABC):
    @abstractmethod
    def fetch(self, since: datetime | None = None) -> list[Article]:
        """Devuelve los artículos publicados después de `since`."""

# ¿Por qué UN SOLO método?
#   Interface Segregation. Si el contrato fuera
#       login() / parse_html() / paginate() / build_headers()
#   estarías obligando al scraper a implementar `login`, que no
#   tiene sentido para él, y filtrando detalles de la API hacia
#   la abstracción. El contrato debe ser lo MÍNIMO que el servicio
#   necesita: "dame artículos".
#
# Nota sobre `since`: es lenguaje de DOMINIO (fecha), no de
# transporte (cursor, page, offset). Eso es clave -> ver E9 abajo.


# =============================================================
# 4. LOS ADAPTADORES
# =============================================================
# Cada uno sabe hablar SU formato y traducirlo a Article.
# El http_client entra por constructor: inyección de dependencias
# -> testeable sin tocar la red.

class CnnScraperSource(ArticleSource):
    def __init__(self, url: str, http_client, parser=None):
        self._url = url
        self._http = http_client
        self._parser = parser

    def fetch(self, since=None) -> list[Article]:
        html = self._http.get(self._url).text
        return [self._to_article(node) for node in self._parse(html)]

    def _parse(self, html):          # BeautifulSoup en la vida real
        return []

    def _to_article(self, node) -> Article:
        ...                          # HTML -> Article


class CnnApiSource(ArticleSource):
    def __init__(self, base_url: str, api_key: str, http_client,
                 page_size: int = 100):
        self._base_url = base_url
        self._api_key = api_key
        self._http = http_client
        self._page_size = page_size

    def fetch(self, since=None) -> list[Article]:
        # La PAGINACIÓN vive aquí dentro: es un detalle de ESTA
        # fuente y nunca sale hacia NewsService.
        articles, cursor = [], None
        while True:
            payload = self._get_page(since, cursor)
            articles += [self._to_article(item) for item in payload["items"]]
            cursor = payload.get("next_cursor")
            if not cursor:
                return articles

    def _get_page(self, since, cursor):
        return {"items": [], "next_cursor": None}

    def _to_article(self, item) -> Article:
        ...                          # JSON -> Article


# =============================================================
# 5. EL SERVICIO
# =============================================================

class NewsService:
    def __init__(self, sources: list[ArticleSource], repo):
        self._sources = sources      # <- recibe las fuentes YA construidas
        self._repo = repo

    def ingest(self, since: datetime | None = None) -> int:
        total = 0
        for source in self._sources:
            articles = source.fetch(since)
            self._repo.save_many(articles)
            total += len(articles)
        return total

# ¿Cómo recibe las fuentes? POR CONSTRUCTOR (inyección de
# dependencias). Consecuencias:
#   - En tests le pasas un FakeArticleSource en memoria: cero red.
#   - No hay un solo `import requests` ni `from bs4 import ...`
#     en este archivo. El servicio no sabe que existe HTTP.
#
# ¿Por qué NO un if? Porque un `if source == "api"` obliga a
# MODIFICAR esta clase cada vez que aparece una fuente nueva:
# rompe Open/Closed, y cada cambio arriesga romper lo que ya
# funcionaba y sus tests.


# --- La factory / registry: elegir por configuración, no por if ---

SOURCES: dict[str, type[ArticleSource]] = {
    "cnn_api": CnnApiSource,
    "cnn_scraper": CnnScraperSource,
}

def build_source(kind: str, **params) -> ArticleSource:
    try:
        return SOURCES[kind](**params)
    except KeyError:
        raise ValueError(f"fuente desconocida: {kind}") from None

# El `if` no desaparece por magia: se concentra en UN punto (el
# borde de la aplicación, donde se lee la config) en vez de estar
# repartido por la lógica de negocio. Eso es lo que se gana.


# =============================================================
# 6. LOS PATRONES
# =============================================================
#   STRATEGY  -> ArticleSource es la estrategia intercambiable;
#                NewsService es el contexto que la usa.
#   ADAPTER   -> cada implementación traduce un formato externo
#                (HTML, JSON) al modelo interno Article.
#   FACTORY / REGISTRY -> SOURCES + build_source eligen la
#                implementación por configuración.
#   (+ Repository para la persistencia, y Dependency Injection
#     como técnica transversal.)


# =============================================================
# 7. SOLID, UNO POR UNO
# =============================================================
# S - Single Responsibility
#     El scraper solo extrae. El repo solo persiste. El servicio
#     solo orquesta. Cada clase tiene una razón para cambiar:
#     si CNN cambia su HTML, tocas UN archivo.
#
# O - Open/Closed
#     Agregar una fuente = crear una clase + una línea en SOURCES.
#     NewsService no se abre. Ver la prueba de fuego abajo.
#
# L - Liskov Substitution
#     Cualquier ArticleSource es sustituible: mismo tipo de
#     retorno y mismas excepciones documentadas. Un adaptador que
#     devuelva None en vez de [] cuando no hay resultados ROMPE
#     Liskov aunque el tipo cuadre.
#
# I - Interface Segregation
#     Contrato mínimo (fetch), no un mega-interface con login(),
#     parse_html(), paginate().
#
# D - Dependency Inversion
#     NewsService depende de la abstracción ArticleSource, no de
#     CnnApiSource. Ambos (servicio y adaptador) dependen del
#     contrato; el detalle depende de la política, no al revés.


# =============================================================
# PRUEBA DE FUEGO (E8): mañana piden un feed RSS
# =============================================================
# TOCAS:
#   - un archivo NUEVO: RssSource(ArticleSource) con su fetch()
#   - una línea en SOURCES
#   - la configuración
#
# NO TOCAS:
#   - NewsService  (ni su código ni sus tests)
#   - Article
#   - CnnApiSource / CnnScraperSource  (ni sus tests)
#
# Eso ES el Open/Closed Principle en la práctica. Si tuvieras que
# abrir NewsService para añadir un elif, el diseño falló.

class RssSource(ArticleSource):
    def __init__(self, feed_url: str, http_client):
        self._feed_url = feed_url
        self._http = http_client

    def fetch(self, since=None) -> list[Article]:
        return []

SOURCES["rss"] = RssSource        # <- la única línea que se "modifica"


# =============================================================
# 💬 E9: la API exige paginación por cursor, el scraper no
# =============================================================
# La paginación es un DETALLE DE IMPLEMENTACIÓN de esa fuente:
# vive dentro de CnnApiSource.fetch() (mira el while de arriba).
# El contrato fetch(since) -> list[Article] NO cambia.
#
# Lo que NUNCA debe pasar: que NewsService reciba, guarde o pase
# un `cursor`. En cuanto la abstracción habla de cursores, ya está
# filtrando el detalle de una implementación concreta -> se llama
# LEAKY ABSTRACTION, y mata el beneficio del diseño.
#
# Matiz que suma: si necesitas streaming para no cargar 50.000
# artículos en memoria, cambia el retorno a Iterator[Article] EN
# LA INTERFAZ. Eso sí es un cambio de contrato legítimo, y el
# scraper simplemente hará yield de su única página.


# =============================================================
# DETALLES QUE SUMAN (menciónalos, no los construyas)
# =============================================================
# - Normalizar zona horaria: todo a UTC al entrar. Mezclar naive y
#   aware es la fuente #1 de bugs de fechas.
# - Deduplicación por external_id o hash de la URL: la API y el
#   scraper van a traer el mismo artículo.
# - Reintentos con backoff, y NO reintentar 4xx (ver P4/P6).
# - Logger estructurado por fuente: cuando falle, saber cuál.
# - El repo también detrás de una interfaz -> tests con
#   InMemoryRepo.


# --- Fake para tests: cero red, y demuestra el punto del diseño ---
class FakeArticleSource(ArticleSource):
    def __init__(self, articles): self._articles = articles
    def fetch(self, since=None): return self._articles


class InMemoryRepo:
    def __init__(self): self.saved = []
    def save_many(self, articles): self.saved.extend(articles)


if __name__ == "__main__":
    a = Article("1", "Titular", "https://cnn.com/1",
                datetime.now(timezone.utc), "cuerpo", "fake")

    repo = InMemoryRepo()
    service = NewsService([FakeArticleSource([a])], repo)

    print("ingeridos:", service.ingest())
    print("en repo  :", repo.saved[0].title)
    print("fuentes registradas:", list(SOURCES))
