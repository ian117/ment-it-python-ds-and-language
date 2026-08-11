# P9 — Autenticación y autorización · RESUELTO

> - ¿Cómo la implementarías?
> - ¿Cómo funciona JWT, respecto al backend y al frontend?
> - ¿**Dónde se almacena** y **dónde se chequea** el token?
> - ¿Cómo se verifica la sesión cuando la auth es mediante sesión?
> - ¿Cómo se chequean los roles y cuál sería una buena práctica?

> **Analogía que resume todo:** el JWT es un boleto de concierto con holograma — el de la puerta lo valida mirándolo, sin llamar a nadie; pero si te lo roban, sirve hasta que termine el evento. La sesión es una lista de invitados: el portero llama a la oficina cada vez, y te pueden tachar al instante.

---

## 1. Anatomía del JWT

Tres partes separadas por puntos, cada una en **base64url**:

```
header.payload.signature

header     {"alg": "HS256", "typ": "JWT"}
payload    {"sub": "42", "role": "admin", "iat": 1712, "exp": 1712900, "jti": "..."}
signature  HMACSHA256(base64(header) + "." + base64(payload), SECRET)
```

**¿El payload está cifrado?** **No. Está FIRMADO, que es otra cosa.**

Base64 no es cifrado, es codificación: cualquiera pega el token en jwt.io y lee el contenido completo. Lo que la firma garantiza es **integridad**, no confidencialidad — nadie puede *modificar* el payload sin invalidar la firma, porque no tiene el secreto.

**La implicación práctica:** nunca metas datos sensibles en un JWT. Nada de emails, teléfonos, PII, ni información interna. Solo identificadores y claims que no te importe publicar. Es el error conceptual que más se cae en entrevistas.

---

## 2. Claims estándar

| Claim | Significado |
|---|---|
| `sub` | subject — quién es el usuario |
| `exp` | expiration — cuándo caduca |
| `iat` | issued at — cuándo se emitió |
| `iss` | issuer — quién lo firmó |
| `aud` | audience — para qué servicio es válido |
| `jti` | JWT ID — identificador único del token |

**El que sirve para revocar es `jti`**: al no poder "borrar" un token ya emitido, guardas su `jti` en una denylist y el middleware lo consulta. Ver el punto 9.

---

## 3. HS256 vs RS256

- **HS256** — simétrico, un **secreto compartido**. Quien verifica también puede firmar. Simple y rápido.
- **RS256** — asimétrico, **par de llaves**. El servidor de auth firma con la privada; cualquier servicio verifica con la pública.

**Monolito → HS256.** Un solo servicio firma y verifica; no hay nada que ganar con la complejidad de gestionar llaves.

**Microservicios → RS256.** Con HS256 tendrías que repartir el secreto de firma a los 12 servicios que solo necesitan *verificar* — y cualquiera de ellos (o cualquiera que comprometa uno) podría emitir tokens falsos. Con RS256 repartes solo la pública: pueden verificar, no falsificar.

---

## 4. El flujo, paso a paso

1. **`POST /auth/login`** con credenciales. El backend valida **contra el hash** almacenado (`bcrypt` o `argon2`, nunca la contraseña en claro, nunca MD5/SHA sin salt) y **firma** dos tokens:
   - un **access token corto** (5–15 min)
   - un **refresh token largo** (días o semanas)
2. **El frontend lo manda en cada request**: `Authorization: Bearer <token>`.
3. **El backend, en un middleware, verifica la firma y el `exp`** — y aquí está la clave: **sin ir a la base de datos**. Eso es lo *stateless*. El token se valida a sí mismo con puro cálculo criptográfico; el servidor no guarda nada sobre él.
4. **Cuando expira**, el frontend llama a `POST /auth/refresh` con el refresh token y obtiene un access token nuevo, sin volver a pedir contraseña.

**Por qué dos tokens y no uno largo:** el access token viaja en cada petición, así que tiene más superficie de robo — por eso dura poco. El refresh token viaja solo al endpoint de refresh, se puede guardar mejor protegido, y **sí es revocable** porque vive en la BD.

---

## 5. Dónde se guarda el token

| Lugar | Pro | Contra |
|---|---|---|
| Cookie `HttpOnly; Secure; SameSite=Strict` | JS no puede leerla → **inmune a XSS**; el navegador la manda sola | Necesitas protección **CSRF**; más fricción cross-domain |
| `localStorage` | Simple, control total desde JS, fácil cross-domain | **Cualquier XSS roba el token**; persiste tras cerrar el navegador |
| Memoria (variable JS) | No sobrevive a un XSS persistente ni a recarga | Se pierde al refrescar la página |

**El trade-off XSS vs CSRF** es el corazón de la pregunta:

- **`localStorage`** → vulnerable a **XSS**. Si un atacante logra ejecutar UN `<script>` en tu página (una dependencia npm comprometida basta), lee el token y se lo lleva. No hay mitigación posible: el token está ahí y JS puede leerlo.
- **Cookie `HttpOnly`** → inmune a XSS, porque JS literalmente no puede acceder a ella. Pero como el navegador la envía **automáticamente**, un sitio malicioso puede provocar peticiones a tu API desde la sesión de la víctima → **CSRF**.

La asimetría que decide: **CSRF tiene defensas conocidas y completas** (`SameSite=Strict/Lax`, tokens anti-CSRF, verificar `Origin`). **XSS no tiene mitigación una vez ocurre** — si ejecutan JS en tu dominio, ya perdiste. Por eso se prefiere el riesgo que sí sabes cerrar.

**Respuesta recomendada:** **access token en memoria + refresh token en cookie `HttpOnly`**. El access nunca toca disco, y al recargar la página se pide uno nuevo con el refresh. Si te obligan a elegir una sola opción: **cookie `HttpOnly`**.

---

## 6. Revocación: el hueco del JWT

Un JWT válido lo es **hasta que expira**. No hay "logout" del lado del servidor porque el servidor no guarda nada sobre él — esa es justo la propiedad que lo hace stateless. Si te roban un token con una hora de vida, el atacante tiene una hora.

Tres soluciones:
1. **Tokens de vida corta** (5–15 min). No elimina el problema, acota la ventana.
2. **Refresh tokens rotativos guardados en BD.** Cada refresh emite uno nuevo e invalida el anterior. Son revocables, y **si llega un refresh ya usado, es señal de robo** → revocas toda la familia de tokens de ese usuario.
3. **Denylist de `jti` en Redis**, con TTL igual al tiempo restante del token.

---

## 7. Sesiones (la alternativa stateful)

1. Login → el servidor genera un **session id aleatorio** (no lleva información, es solo una clave opaca) y lo guarda en un store (Redis/BD) junto al `user_id`.
2. Lo manda en cookie `HttpOnly`.
3. En cada request, el servidor **busca la sesión en el store** y carga el usuario.

| | JWT | Sesión |
|---|---|---|
| **Estado** | Stateless | Stateful (store) |
| **Verificación** | Firma, sin I/O | Lookup en Redis/BD |
| **Revocación** | Difícil | Instantánea (borras la sesión) |
| **Escala horizontal** | Trivial | Requiere store compartido |
| **Bueno para** | APIs, móvil, microservicios | Apps web monolíticas |

**Cuándo cada uno:** si tienes un monolito web con login de navegador, **sesiones** — son más simples, más seguras por defecto y el logout funciona de verdad. Si tienes una API consumida por móvil y varios servicios que deben validar sin compartir base de datos, **JWT**.

El matiz que suma: la gente elige JWT "porque escala" cuando tiene un solo servidor y 200 usuarios. Ahí las sesiones son la respuesta correcta y JWT es complejidad prematura.

---

## 8. Roles

**Modelo RBAC** — los roles viven en la BD, no hardcodeados:

```
users ── user_roles ── roles ── role_permissions ── permissions
```

**¿El rol como claim en el token?** Se puede, y evita un query por request. Pero trae un problema: **si le quitas el rol de admin a alguien, su token viejo sigue diciendo `admin`** hasta que expire. Mitigaciones: tokens cortos (la ventana se reduce a minutos), o consultar la BD en las operaciones sensibles aunque confíes en el claim para el resto.

**Por qué `if user.role == "admin"` disperso es mala práctica:** la política de acceso queda repartida en 50 sitios. Cuando cambie (y va a cambiar), tienes que encontrarlos todos — y el que olvides es un agujero. Además no es auditable: nadie puede responder "¿quién puede borrar tareas?" sin leer todo el código. Se centraliza:

```python
@router.delete("/tasks/{id}")
def delete(id: int, user = Depends(require_permission("task:delete"))):
    ...
```

**Por qué permisos escalan mejor que roles:** un rol es un *paquete de permisos*. Si el código pregunta por permisos (`task:delete`), crear el rol "moderador" es una fila en la BD y **cero cambios de código**. Si el código pregunta por roles, cada rol nuevo obliga a tocar todos los `if`.

**Y la más importante — por qué el chequeo por ruta no basta:**

Un middleware que valida "este usuario tiene el rol `editor`" te deja pasar a `PATCH /tasks/1`… **pero no verifica que seas editor _de la tarea 1_**. Puedes ser editor de tu propia tarea 55 y estar editando la tarea 1 de otra persona. Ser `editor` es un rol *sobre un recurso concreto*, no un atributo global del usuario.

La autorización tiene **dos niveles** y necesitas los dos:
- **Nivel de ruta** — ¿este endpoint permite este tipo de usuario?
- **Nivel de recurso** — ¿este usuario puede hacer esta acción **sobre este objeto**?

Saltarse el segundo es **IDOR / BOLA**, el **#1 del OWASP API Security Top 10**. (Es literalmente el E14 de P8.)

**Cierre:** nunca confíes en el frontend — ocultar un botón no es seguridad. Y **menor privilegio por defecto**: deniega salvo que exista un permiso explícito, en vez de permitir salvo prohibición.

---

## 9. (E15) Logout inmediato con JWT

**La solución: denylist de `jti` en Redis.**

- **Qué guardas:** el `jti` del access token.
- **Dónde:** Redis.
- **Con qué TTL:** `exp - now`, el tiempo que le quedaba de vida al token. Pasado eso el token expira solo y la entrada sobra.
- **El middleware** consulta la denylist antes de aceptar cualquier token.

Como los access tokens son cortos (5–15 min), **la denylist se mantiene diminuta y se autolimpia por TTL**: nunca crece sin control, a diferencia de una tabla de sesiones.

**Qué pasa con el refresh token:** se **borra o marca como revocado en la BD**, y esto es lo que realmente cierra la sesión. Sin refresh no se pueden emitir access tokens nuevos, así que el acceso muere como mucho al expirar el actual. Añade **rotación con detección de reuso**: si llega un refresh ya utilizado, revocas toda la familia — es señal de robo.

**Qué sacrificaste:** la validación deja de ser **puramente stateless**. Ahora hay un lookup a Redis en cada request, y Redis se vuelve una dependencia crítica de tu ruta de autenticación (si cae, decides si fallas abierto o cerrado).

**Por qué vale la pena igualmente:** es un `GET` de microsegundos contra memoria, mucho más barato que una sesión en BD, y solo se consulta la denylist —que está casi vacía— no un registro por usuario activo.

**Alternativa sin infraestructura extra:** bajar el `exp` a 5 minutos y aceptar que el logout tarda hasta 5 minutos en surtir efecto. Para muchos productos es suficiente, y no añades Redis. Decir esto demuestra que sabes evaluar el costo de una solución, no solo implementarla.
