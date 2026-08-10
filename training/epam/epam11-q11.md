# P11 — El mismo stack, con servicios cloud

> **Lo que te preguntaron**
> "¿Cómo harías lo de la pregunta 10, pero usando servicios cloud?"

Los mismos 4 servicios: `tms`, `email-service`, `postgres`, `redis`.

**Trampa a evitar:** la respuesta *no* es "todo en Kubernetes". Eso suena a que solo conoces una herramienta.

## Tu tarea

**1.** Mapea cada pieza a su servicio gestionado. Completa la tabla (haz al menos AWS; las otras dos como bonus):

| Pieza | AWS | Azure | GCP |
|---|---|---|---|
| App TMS | | | |
| Email service | | | |
| Postgres | | | |
| Redis | | | |
| Registry de imágenes | | | |
| Entrada / TLS | | | |
| Envío de correo | | | |
| Secretos | | | |
| Logs y métricas | | | |
| Archivos | | | |

**2. El argumento de fondo:** ¿por qué gestionado y no correrlo tú? Da razones concretas, no "es más fácil".

**3. El cambio de arquitectura que esperan que propongas:** en el compose, `tms` llama al email service por HTTP. En cloud eso se sustituye por otra cosa. ¿Por qué? Enumera qué ganas:
- si el proveedor de correo se cae…
- si llega un pico de tráfico…
- si un mensaje falla siempre…
- ¿cuánto tarda la app en responderle al usuario?

**4. Red.** Diseña la VPC: qué va en subnet pública, qué en privada, y cómo restringes el acceso a la BD. Relaciónalo con las `networks` de P10 — es la misma idea un nivel arriba.

**5. Escalado.** ¿Por qué métrica escalas la app? ¿Y el worker de correo? (no es la misma)

**6. IaC y CI/CD.** ¿Por qué nada se crea a mano en la consola? Describe el pipeline: de un commit a producción.

**7. Costo.** Mencionarlo demuestra madurez. ¿Qué es más caro por hora y por qué aun así lo eliges?

**8. 💬 (E18) La pregunta que de verdad evalúan:** por cada servicio, di **por qué NO** elegiste la opción más obvia. Al menos estos tres:
- ¿Por qué **no** EKS/Kubernetes, si vienes de contenedores?
- ¿Por qué **no** Postgres en un contenedor?
- ¿Por qué **no** una llamada HTTP directa al email service?

---

## Tus respuestas
