# P9 — Autenticación y autorización

> **Lo que te preguntaron**
> - ¿Cómo la implementarías?
> - ¿Cómo funciona JWT? ¿Cómo funciona respecto al backend y al frontend?
> - ¿**Dónde se almacena** y **dónde se chequea** el token?
> - ¿Cómo se verifica la sesión cuando la auth es mediante sesión?
> - ¿Cómo se chequean los roles y cuál sería una buena práctica?

## Tu tarea

**1. Anatomía del JWT.** Dibuja las tres partes y di qué lleva cada una. Luego la pregunta trampa: **¿el payload está cifrado?** ¿Qué implicación práctica tiene tu respuesta sobre qué puedes meter dentro?

**2. Claims.** ¿Qué son `sub`, `exp`, `iat`, `iss`, `aud`, `jti`? ¿Cuál te sirve para revocar?

**3. HS256 vs RS256.** ¿Cuál eliges en un monolito y cuál en microservicios? ¿Por qué?

**4. El flujo completo, paso a paso.** Login → uso → expiración → refresh. En cada paso di **quién hace qué**:
- ¿Contra qué valida el backend las credenciales? (no "contra la contraseña")
- ¿En qué header viaja el token?
- ¿El backend consulta la BD para validar el token? ← esta es la clave de "stateless"

**5. Dónde se guarda el token.** Compara las tres opciones con su pro y su contra:

| Lugar | Pro | Contra |
|---|---|---|
| Cookie `HttpOnly` | | |
| `localStorage` | | |
| Memoria JS | | |

¿Cuál recomiendas? ¿Cuál es el trade-off **XSS vs CSRF**?

**6. El hueco del JWT: revocación.** ¿Por qué no existe un "logout" real del lado del servidor? Nombra tres soluciones.

**7. Sesiones.** Explica el flujo stateful y luego compara en 4 ejes: estado, verificación, revocación, escala horizontal. ¿Cuándo usarías cada uno?

**8. Roles.** 
- ¿Qué tablas modelan RBAC?
- ¿Meter el rol como claim en el token? ¿Qué problema trae y cómo lo mitigas?
- ¿Por qué `if user.role == "admin"` esparcido por el código es mala práctica? ¿Qué se hace en su lugar?
- ¿Por qué **permisos** escalan mejor que **roles**?
- **La más importante:** ¿por qué chequear el rol a nivel de RUTA no basta? Da el ejemplo concreto.

**9. (E15)** El equipo quiere **logout inmediato** con JWT. Diseña la solución completa: qué guardas, dónde, con qué TTL, qué pasa con el refresh token, y **qué has sacrificado** del modelo stateless. ¿Hay alternativa sin infraestructura extra?

---

## Tus respuestas
