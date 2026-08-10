# P8 — Diseño de endpoints REST

> **Lo que te preguntaron**
> "¿Cuál sería tu diseño de endpoints siguiendo REST?"
> Lo respondiste dibujando las rutas en papel, con status codes,
> nombres de recursos, método HTTP y algo de DTOs.

Sobre el dominio de P7 (usuarios, tareas y shares).

## Tu tarea

**1.** Escribe la tabla completa de endpoints: CRUD de tareas + gestión de shares. Para cada uno: método, ruta, código de éxito y códigos de error posibles.

**2.** Reglas de nombrado — ¿por qué estas rutas están mal?
```
/getTasks
/api/v1/task/create
POST /api/v1/deleteTask/5
```

**3.** Status codes. Di cuándo usas cada uno y en qué se diferencian los que se confunden:
`200` · `201` · `204` · `400` · `401` · `403` · `404` · `409` · `422` · `429` · `500`

- 401 vs 403 vs 404 → ¿cuál es la diferencia real?
- 400 vs 422 → ¿dónde está la línea?
- ¿Cuándo devuelves **404 en vez de 403** a propósito, y qué ganas?

**4.** DTOs. Escribe el de entrada y el de salida para crear una tarea. Luego responde:
- ¿Por qué no exponer directamente la entidad de BD?
- ¿Qué ataque previene separar el DTO de entrada? (nombre concreto)
- ¿Qué campos NUNCA deben aceptarse del cliente y por qué?

**5.** Los extras que rematan: versionado, paginación, filtrado, formato de error consistente, idempotencia. ¿Cuáles verbos HTTP son idempotentes y cuál no? ¿Cómo haces idempotente el que no lo es?

**6. (E13)** Diseña tres endpoints concretos:
- revocar un share
- listar quién tiene acceso a una tarea
- que un usuario **abandone** una tarea compartida con él

Método, ruta, código de éxito y errores de cada uno. Pista: los dos últimos son parecidos pero **no** deben ser el mismo endpoint. ¿Por qué?

**7. 💬 (E14)** Un usuario con rol `viewer` sobre `task1` hace `PATCH /api/v1/tasks/1` y **funciona**.
- ¿Dónde estuvo el fallo?
- ¿En qué capa se arregla? (y en cuál **jamás**)
- ¿Qué código HTTP debía haber devuelto?
- ¿Cómo se llama esta vulnerabilidad y qué puesto ocupa en el OWASP API Top 10?

---

## Tus respuestas
