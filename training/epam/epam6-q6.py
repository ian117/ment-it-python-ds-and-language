"""
=============================================================
P6 — Estrategia de testing (y no gastar dinero)  ·  RESUELTO
=============================================================
Sobre el diseño de P5 te preguntaron:
  - ¿Qué estrategia de testing usarías?
  - ¿Qué librerías de Python?
  - "Este servicio llama a una API, una API REAL. ¿Necesitas hacer
     algo específico? ¿Hay que estar pendiente de algo?"

INSISTIERON en que las llamadas CUESTAN DINERO. Esa insistencia es
la pregunta real: querían oír que la prevención del gasto se
diseña en DOS frentes -> los tests Y el código de producción.

ANALOGÍA
    Probar contra la API real es como aprender a manejar
    practicando en la autopista. El simulador (mocks) es para
    aprender; sales a la autopista una vez, de noche y con
    instructor (smoke test nocturno), solo para confirmar que la
    autopista sigue donde estaba.
=============================================================
"""

# =============================================================
# 1. LA PIRÁMIDE
# =============================================================
# Nivel        | Qué prueba                          | Cuántos
# -------------|-------------------------------------|-------------
# Unit         | Parsers, mappers, lógica de negocio | Miles, ms, gratis
# Integration  | Tu código contra un doble del HTTP, | Decenas
#              | o contra Postgres en contenedor     |
# Contract     | Que el schema de la API externa     | Pocos, vs sandbox
#              | sigue siendo el que esperas         |
# E2E / smoke  | El flujo real contra la API real    | Muy pocos, FUERA del CI
#
# La forma importa: base ancha de tests rápidos y deterministas,
# punta angosta de tests lentos y frágiles. Un "cono de helado"
# (muchos E2E, pocos unit) es lento, caro e inestable.
#
# EL PUNTO CLAVE, y hay que decirlo explícitamente:
#   Gracias al diseño de P5, NewsService se testea con un
#   FakeArticleSource en memoria y NO TOCA RED EN ABSOLUTO.
#   El diseño testeable es consecuencia de la inyección de
#   dependencias, no de la librería de testing que elijas.


# =============================================================
# 2. TEST DOUBLES, CON SUS NOMBRES CORRECTOS
# =============================================================
# Usar bien estos nombres distingue a un senior. "Mock" se usa
# como cajón de sastre para todo, y no son lo mismo:
#
# STUB  - Devuelve datos fijos. No verifica nada.
#         -> un JSON de ejemplo de la respuesta de CNN.
#
# MOCK  - Además VERIFICA CÓMO se le llamó.
#         -> assert_called_once_with(since=ayer)
#            Prueba la interacción, no el resultado.
#
# FAKE  - Implementación funcional pero simplificada.
#         -> FakeArticleSource / InMemoryRepo de P5.
#            Funciona de verdad, solo que en memoria.
#
# SPY   - Envuelve al real y REGISTRA las llamadas.
#         -> el objeto real hace su trabajo y además cuentas
#            cuántas veces se llamó.
#
# Regla práctica: prefiere FAKES y STUBS. Los MOCKS acoplan el
# test a la implementación —si refactorizas sin cambiar el
# comportamiento, el test se rompe igual— y eso genera tests
# frágiles que el equipo acaba borrando.


# =============================================================
# 3. LIBRERÍAS
# =============================================================
# pytest              - el runner. Fixtures, parametrize, marks.
# pytest-mock         - fixture `mocker`, wrapper de unittest.mock
# pytest-cov          - cobertura
# pytest-asyncio      - tests de código async
# unittest.mock       - stdlib: Mock, MagicMock, patch
# responses           - intercepta `requests` a nivel HTTP
# requests-mock       - alternativa a responses
# respx               - el equivalente para `httpx`
# vcrpy / pytest-recording - graba y reproduce cassettes
# freezegun           - congela el tiempo (para probar `since`, TTL de caché)
# factory-boy         - construir objetos de prueba sin repetirte
# hypothesis          - property-based: genera inputs raros que no imaginaste
# testcontainers      - Postgres/Redis reales y efímeros en Docker
# jsonschema / Pydantic - validar el CONTRATO de la respuesta
# beautifulsoup4 + fixtures HTML guardadas - para el scraper


# =============================================================
# 4. TRES RAZONES PARA NO LLAMAR A LA API REAL (en este orden)
# =============================================================
# 1) CUESTA DINERO y consume cuota.
#    Cada push de cada dev multiplica las llamadas. Puedes quemar
#    la cuota mensual en una tarde, o rebasar el rate limit y
#    tumbar PRODUCCIÓN desde el CI.
#
# 2) LOS TESTS DEJAN DE SER DETERMINÍSTICOS.
#    Un test rojo por la red caída o porque hoy CNN publicó otra
#    cosa YA NO ES SEÑAL. El equipo empieza a re-ejecutar el CI
#    "a ver si pasa", después a ignorar el rojo, y el CI pierde
#    todo su valor. Este es el argumento más fuerte a largo plazo.
#
# 3) SON LENTOS. Una suite que tarda 20 minutos deja de correrse
#    antes de cada commit, que es justo cuando sirve.
#
# 4) (bonus) COBERTURA DE CASOS BORDE. Con la API real no puedes
#    provocar un 500, un timeout o un JSON malformado cuando
#    quieras. Con mocks sí — y esos son justo los caminos que más
#    se rompen en producción.


# =============================================================
# 5. ¿EN QUÉ CAPA SE MOCKEA?
# =============================================================
# EN EL LÍMITE HTTP. No tu propia lógica.
#
#   MAL:  mocker.patch("CnnApiSource.fetch", return_value=[a1, a2])
#         Acabas de sustituir por completo el código que querías
#         probar. El test pasa siempre y no prueba NADA tuyo:
#         ni el parser, ni el mapeo a Article, ni la paginación,
#         ni el manejo de errores. Es un test que solo verifica
#         que el mock devuelve lo que le dijiste.
#
#   BIEN: responses.get(URL, json=PAYLOAD_REAL)
#         Interceptas la petición y dejas correr TU parser sobre
#         una respuesta realista.
#
# Regla: mockea lo que NO es tuyo (la red, el reloj, el sistema de
# archivos), nunca lo que sí es tuyo.


# =============================================================
# 6. CÓMO SE EVITA EL GASTO EN EL CÓDIGO DE PRODUCCIÓN
# =============================================================
# Este es el frente que casi nadie menciona y el que más valoran:
# los tests previenen gasto DURANTE EL DESARROLLO; el gasto real
# se controla en el DISEÑO.
#
# - CACHÉ con TTL + HTTP condicional (ETag / If-Modified-Since).
#   Un 304 normalmente no cuenta contra la cuota o cuesta menos.
#
# - RATE LIMITER propio (token bucket) para no rebasar el plan.
#
# - BACKOFF EXPONENCIAL CON JITTER en los reintentos.
#   El jitter evita que N clientes reintenten sincronizados y
#   generen un pico que tumba la API justo cuando se recupera.
#
# - NO REINTENTAR 4xx. Un 400/401/404 va a fallar igual las 3
#   veces: solo triplicas el costo. Reintenta solo lo transitorio
#   (red y 5xx). <- esto es literalmente el E7 de P4.
#
# - CIRCUIT BREAKER: tras N fallos consecutivos, deja de llamar
#   durante X minutos. Evita martillar un servicio caído.
#
# - PRESUPUESTO Y KILL SWITCH: contador de llamadas por día; si se
#   rebasa, la app se apaga sola y alerta. Es la red de seguridad
#   final: convierte una factura catastrófica en una incidencia.
#
# - FETCH INCREMENTAL: pedir solo `since=última_ejecución`, con
#   paginación y limit, en vez de traer todo cada vez.
#
# - DEDUPLICACIÓN antes de llamar: si ya tienes el artículo, no lo
#   vuelvas a pedir.
#
# - OBSERVABILIDAD: métrica de llamadas y de costo estimado, con
#   alerta. Sin esto no te enteras hasta que llega la factura.


# =============================================================
# 7. LOS TESTS (E10)
# =============================================================
# Fíjate en los dos últimos: son tests DEL CONTROL DE GASTO, y no
# cuestan un centavo. Esa es la respuesta a "¿cómo previenes el
# gasto con los tests?".

TESTS = '''
import pytest, responses
from news.sources import CnnApiSource, ClientError

URL = "https://api.cnn.com/v1/articles"
A1 = {"id": "1", "title": "Uno", "url": "...", "published": "2026-01-01T00:00:00Z"}
A2 = {"id": "2", "title": "Dos", "url": "...", "published": "2026-01-02T00:00:00Z"}


@pytest.fixture
def source():
    return CnnApiSource(base_url=URL, api_key="test", http_client=...)


@responses.activate
def test_happy_path_parsea_dos_articulos(source):
    responses.get(URL, json={"articles": [A1, A2]}, status=200)
    articles = source.fetch()
    assert len(articles) == 2
    assert articles[0].title == "Uno"          # se probó EL PARSER, no el mock
    assert articles[0].published_at.tzinfo is not None   # timezone-aware


@responses.activate
def test_reintenta_en_500(source):
    responses.get(URL, status=500)
    responses.get(URL, status=500)
    responses.get(URL, json={"articles": []}, status=200)
    source.fetch()
    assert len(responses.calls) == 3           # reintentó lo transitorio


@responses.activate
def test_no_reintenta_en_401(source):
    responses.get(URL, status=401)
    with pytest.raises(ClientError):
        source.fetch()
    assert len(responses.calls) == 1           # ni un centavo de más


@responses.activate
def test_segunda_llamada_usa_cache(source):
    responses.get(URL, json={"articles": [A1]}, status=200)
    source.fetch()
    source.fetch()
    assert len(responses.calls) == 1           # la segunda salió de caché
'''


# =============================================================
# VCR / CASSETTES
# =============================================================
# Grabas la respuesta REAL una vez, se versiona en el repo y se
# reproduce siempre. Te da realismo sin costo recurrente.
#
# REGLA OBLIGATORIA: filtrar Authorization y las API keys ANTES de
# commitear el cassette. Un cassette es un archivo de texto con la
# petición completa: si no filtras, acabas de subir tu API key al
# repositorio.
#
#   @pytest.mark.vcr(filter_headers=["authorization"])
#
# Y hay que refrescarlos cada cierto tiempo, o acabas probando
# contra una respuesta de hace dos años.


# =============================================================
# SMOKE TESTS CONTRA LA API REAL
# =============================================================
# Un puñado MÍNIMO, y con cuatro condiciones:
#   - marcados        @pytest.mark.live
#   - apagados por defecto en pyproject.toml:
#       [tool.pytest.ini_options]
#       addopts = '-m "not live"'
#   - en un cron nocturno, no en el CI de cada PR
#   - con SANDBOX KEY y presupuesto acotado
#
# Para qué sirven: para detectar que LA API CAMBIÓ. No para
# validar tu lógica — de eso se encargan los unit tests.
#
# CONTRACT TESTING: valida la respuesta contra un JSON Schema. Si
# la API renombra un campo, falla ahí y no en producción.
#
# Para el scraper, el equivalente: HTML fixtures guardados + un
# job canario aparte que descarga la página real y avisa si la
# estructura cambió.


# =============================================================
# 💬 E11 — "Los mocks no prueban nada, peguemos a la API real"
# =============================================================
# TRES ARGUMENTOS:
#
# 1. DETERMINISMO. Un test que falla por la red o porque hoy CNN
#    publicó otra cosa deja de ser señal. El equipo empieza a
#    ignorar el rojo y perdemos el CI como red de seguridad.
#
# 2. COSTO Y CUOTA. Cada push de cada dev multiplica las llamadas.
#    Podemos consumir la cuota mensual en una tarde, o rebasar el
#    rate limit y romper producción desde el CI.
#
# 3. COBERTURA DE CASOS BORDE. Con la API real no puedo provocar
#    un 500, un timeout o un JSON malformado cuando quiero. Con
#    mocks sí, y esos son los caminos que más se rompen.
#
# LA PROPUESTA (esto es lo que cierra la discusión, porque le das
# lo que pide en vez de solo decir que no):
#   contract tests contra el SANDBOX + un smoke test NOCTURNO
#   mínimo contra la API real, con presupuesto acotado y alerta a
#   Slack. Detecta un cambio de contrato en menos de 24h, sin
#   meter la red en el CI de cada PR.
#
# El fondo del argumento: tiene razón en QUÉ quiere (saber si la
# API cambió) y se equivoca en DÓNDE ponerlo (en el CI de cada PR).


if __name__ == "__main__":
    print(__doc__)
    print(TESTS)
