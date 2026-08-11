# P11 — El mismo stack, con servicios cloud · RESUELTO

> "¿Cómo harías lo de la pregunta 10, pero usando servicios cloud?"

**La trampa:** la respuesta *no* es "todo en Kubernetes". Eso suena a que solo conoces una herramienta. La respuesta correcta es **mapear cada pieza al servicio gestionado que corresponde** y **justificar el nivel de control que cedes**.

---

## 1. El mapeo

| Pieza | AWS | Azure | GCP |
|---|---|---|---|
| App TMS | **ECS Fargate** / EKS / App Runner | Container Apps / AKS | Cloud Run / GKE |
| Email service | **Lambda o ECS + SQS** | Functions + Service Bus | Cloud Functions + Pub/Sub |
| Postgres | **RDS / Aurora** | Azure DB for PostgreSQL | Cloud SQL |
| Redis | **ElastiCache** | Azure Cache for Redis | Memorystore |
| Registry de imágenes | ECR | ACR | Artifact Registry |
| Entrada / TLS | ALB + ACM | App Gateway | Cloud Load Balancing |
| Envío de correo | SES | Communication Services | SendGrid |
| Secretos | Secrets Manager / SSM | Key Vault | Secret Manager |
| Logs y métricas | CloudWatch | Monitor | Cloud Monitoring |
| Archivos | S3 | Blob Storage | GCS |

---

## 2. ¿Por qué gestionado y no correrlo tú?

No digas "es más fácil". Di qué obtienes que no vas a construir mejor:

- **Backups automáticos** con point-in-time recovery.
- **Parches de seguridad** aplicados en ventanas de mantenimiento.
- **Multi-AZ y failover automático** — si se cae una zona de disponibilidad, el standby toma el control en segundos.
- **Réplicas de lectura** con un click.
- **Métricas y slow query log** integrados.

El argumento que cierra: **correr Postgres en un pod es asumir el trabajo de un DBA**. Y el día que falle a las 3am, la diferencia entre un failover automático y tú restaurando un backup a mano es el SLA de tu producto.

---

## 3. El cambio de arquitectura que esperan que propongas

En el compose, `tms` llama al email service por **HTTP directo**. En cloud eso se sustituye por una **cola** (SQS / Pub-Sub / Service Bus).

```
ANTES:   tms  ──HTTP──▶  email-service  ──▶  proveedor
DESPUÉS: tms  ──▶ SQS ──▶  worker  ──▶ SES        ──▶ DLQ (los que fallan siempre)
```

Qué ganas, punto por punto:

- **Si el proveedor de correo se cae** → los mensajes **esperan en la cola** en vez de perderse. Con HTTP directo, la petición falla y el correo se evapora (o tienes que construir tú la lógica de reintento y persistencia… que es exactamente una cola, peor hecha).
- **Si llega un pico de tráfico** → la cola **absorbe el pico** y el worker consume a su ritmo. Con HTTP síncrono, el pico se propaga: el email service se satura y arrastra a `tms` con él.
- **Si un mensaje falla siempre** (dirección inválida, payload corrupto) → tras N intentos va a la **DLQ** (dead letter queue), donde lo inspeccionas sin que bloquee la cola. Sin DLQ, un mensaje envenenado se reintenta para siempre.
- **Cuánto tarda la app en responder** → **inmediato**. `tms` encola y devuelve; no espera al SMTP. El usuario no paga con latencia el envío de un correo.

Es, además, **desacoplamiento real**: `tms` deja de conocer la existencia del email service. Publica un evento y se olvida.

---

## 4. Red

```
VPC
├── Subnets PÚBLICAS   → solo el ALB (y un NAT Gateway)
└── Subnets PRIVADAS   → ECS tasks, RDS, ElastiCache
```

- Nada que tenga datos vive en una subnet pública.
- **Security groups como firewall**, encadenados por referencia y no por IP: el SG de RDS acepta el puerto 5432 **solo desde el SG de la app**. Si mañana la app escala a 10 tareas con IPs nuevas, la regla sigue siendo válida.
- Salida a internet desde las privadas vía **NAT Gateway** (y ojo, cuesta dinero — es una sorpresa clásica en la factura).

**Es exactamente la misma idea que las `networks` de Compose, un nivel arriba:** `frontend`/`backend` se convierten en subnets pública/privada, y "quitar `ports:`" se convierte en "no darle IP pública ni regla de entrada".

---

## 5. Escalado

No es la misma métrica para cada servicio, y notar eso es lo que evalúan:

- **TMS (API síncrona)** → escala por **CPU/memoria**, o mejor por **requests por target** del ALB o latencia p95. Lo que importa es el tiempo de respuesta del usuario.
- **Worker de correo (asíncrono)** → escala por **profundidad de la cola** (`ApproximateNumberOfMessagesVisible`) o por antigüedad del mensaje más viejo. La CPU del worker puede estar al 5% mientras 10.000 mensajes esperan: escalar por CPU aquí no haría nada.

---

## 6. IaC y CI/CD

**Terraform** (o CDK/Bicep/Pulumi). **Nada se crea a mano en la consola**, por tres razones:

1. **Reproducibilidad** — levantar staging idéntico a producción es `terraform apply`, no un documento de 40 pasos.
2. **Revisable en un PR** — un cambio de security group se discute antes de aplicarse, como cualquier código.
3. **Contra el drift** — si alguien toca algo a mano, el plan lo detecta. La infraestructura manual es infraestructura que nadie sabe reconstruir cuando se cae.

**El pipeline:**
```
commit → tests → build de imagen → push a ECR → terraform plan/apply
       → deploy con rolling update (o blue/green) → smoke test → alerta si falla
```

---

## 7. Costo

Mencionarlo demuestra madurez, porque la respuesta técnicamente óptima no siempre es la correcta.

**Fargate cuesta más por hora que una EC2 equivalente** — y aun así lo eliges, porque el ahorro de EC2 desaparece en cuanto sumas el tiempo de ingeniería de parchear AMIs, gestionar el autoscaling group y depurar nodos. Pagas por no tener ese trabajo.

Y el criterio general: **empezar con instancias pequeñas y escalar por métricas**, no dimensionar para el pico imaginario del año que viene. Añade alertas de presupuesto (enlaza con el kill switch de P6).

---

## 8. 💬 (E18) El "por qué NO" — la parte que de verdad evalúan

**¿Por qué no EKS/Kubernetes, si vienes de contenedores?**
Porque EKS te cobra el control plane **y** te obliga a operar el clúster: upgrades de versión, add-ons, CNI, RBAC, node groups. Con **dos servicios** no hay nada que justifique esa carga operativa. Fargate te da contenedores sin nodos que parchear. K8s entra cuando ya tienes varios equipos que necesitan el mismo sustrato, o dependes de su ecosistema (operators, service mesh, Helm charts existentes). Elegir K8s "porque es lo estándar" es cargar con la complejidad de una organización que no tienes.

**¿Por qué no Postgres en un contenedor de ECS?**
Porque perderías backups automáticos, failover, Multi-AZ y parches — y los tendrías que construir tú, peor. El almacenamiento persistente es solo *una parte* del problema; el resto es operación continua. Correr tu propia BD es asumir un rol de DBA a cambio de ahorrar relativamente poco.

**¿Por qué no una llamada HTTP directa al email service?**
Porque acopla la disponibilidad de `tms` a la del proveedor de correo. La cola desacopla, absorbe picos, reintenta sola, aísla la caída del proveedor y te da DLQ para los mensajes envenenados. Y la app responde sin esperar el envío. (Desarrollado en el punto 3.)

**Bonus, si quieres rematar — ¿por qué no Lambda para la app principal?**
Cold starts en una API con latencia sensible, límite de 15 minutos, y el modelo de conexiones a BD encaja mal (cada invocación abre la suya; necesitas RDS Proxy). Para el *worker* de correo, en cambio, Lambda es ideal: tareas cortas, event-driven, tráfico irregular. **Distinto servicio, distinta herramienta** — que es justo el criterio que la pregunta busca.
