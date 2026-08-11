# P12 — ¿Cómo usarías AI en tu trabajo? · GUÍA DE RESPUESTA

> "¿Cómo usarías AI en tu trabajo?"

Pregunta cultural. **No hay respuesta correcta** — evalúan criterio. Los dos extremos pierden:
- *"No la uso, prefiero escribir todo yo"* → rígido, y en 2026 suena a que no te has puesto al día.
- *"Para todo, me ahorra pensar"* → peligroso, y le dice al entrevistador que mergeas código que no entiendes.

**Estructura:** dónde sí / dónde con cuidado / el principio / un caso real. ~2 minutos.

> ⚠️ Las secciones 1–4 son el material. **La 5 tienes que llenarla tú** — es la que no se puede improvisar y la que más pesa.

---

## 1. Dónde aporta más

Habla de **ejemplos concretos**, no de categorías:

- **Boilerplate y andamiaje** — DTOs, migraciones, configuraciones, parsers. Código predecible donde la revisión es trivial.
- **Tests** — sobre todo generar **casos borde que no se te habían ocurrido**, y cubrir código legacy que nadie se atreve a tocar.
- **Refactors mecánicos** repetidos a lo largo de muchos archivos.
- **Explorar una librería desconocida** más rápido que leyendo la doc entera.
- **Documentación, docstrings, mensajes de commit, descripciones de PR** — lo que todos posponen.
- **Primer pase de code review** y análisis de logs o stack traces largos.
- **Rubber-ducking** — explicar un diseño en voz alta y recibir contraargumentos.

---

## 2. Dónde con cuidado

Esta sección es la que demuestra criterio. Es la que separa una buena respuesta de una genérica.

- **Nunca pegar código propietario, credenciales o PII** en herramientas no aprobadas por la empresa. Sale del perímetro y no vuelve.
- **Seguridad y criptografía**: revisión humana obligatoria. Un fallo aquí no da error, da brecha.
- **Dependencias alucinadas** — el modelo sugiere un paquete que no existe. Y hay un ataque que se aprovecha justo de eso: **slopsquatting**, registrar en PyPI/npm los nombres inventados más frecuentes para que alguien los instale. Verifica que el paquete existe **y** que es el que crees.
- **Decisiones de arquitectura**: el modelo no conoce el contexto del negocio, la deuda técnica acumulada, ni las restricciones del equipo. Puede proponer la solución "de libro" que es la equivocada aquí.

---

## 3. El principio

> **Eres responsable del código que mergeas, lo haya escrito quien lo haya escrito. Si no lo entiendes, no entra.**

Y el corolario: **los tests son la red de seguridad que hace seguro aceptar código generado**. Sin cobertura, aceptar código que no escribiste es apostar. Con ella, el riesgo se vuelve manejable — por eso la generación de tests es de los mejores usos, se retroalimenta.

Un tercer punto que suma: **prompts con contexto**. Pegar el código real, las convenciones del equipo y el error exacto, en vez de pedir en abstracto. La calidad de la salida es proporcional al contexto que das.

---

## 4. Multiplicador para un senior, muleta para un junior

La asimetría está en la **capacidad de revisar**:

Un senior reconoce en segundos que la solución propuesta ignora un caso borde, mete un N+1 o no encaja con la arquitectura. Para él la AI elimina el tecleo y deja el juicio, que es donde aporta valor.

Un junior no tiene ese filtro: acepta lo que parece funcionar y aprende a **producir sin entender**. Y como el código funciona, no recibe la señal de error que le enseñaría. La AI **acelera lo que ya sabes revisar** — no sustituye el criterio, lo amplifica. Si el criterio es cero, cero por mucho sigue siendo cero.

---

## 5. Tu cierre — ESTO LO TIENES QUE LLENAR TÚ

Dos anécdotas **reales y tuyas**. Sin esto la respuesta es intercambiable con la de cualquier candidato.

**a) Una vez que te ahorró tiempo de verdad.** Con el número: ¿horas? ¿días? ¿Qué era exactamente?

```
→
```

**b) Una vez que te dio algo mal y lo detectaste.** ← **La importante.**

Es la que prueba que revisas en vez de copiar. Sé específico: qué te propuso, cómo notaste que estaba mal, qué hiciste. Un ejemplo del tipo que funciona: *"me generó un query que parecía correcto pero hacía N+1 al iterar las relaciones; lo detecté porque revisé el log de SQL del test y vi 200 queries donde debía haber 2"*.

```
→
```

**c) Qué herramientas usas y para qué cada una.** (Claude Code, Copilot, Cursor…) Diferenciar los usos es mejor que nombrarlas: autocompletado en el flujo vs. tareas largas de refactor vs. explorar un repo desconocido.

```
→
```

---

## Guion de 2 minutos

1. "La uso a diario, sobre todo para **[2-3 casos concretos tuyos]**."
2. "Donde soy cuidadoso es en **[propietario/PII, seguridad, dependencias alucinadas]**."
3. "Mi principio es que **soy responsable del código que mergeo; si no lo entiendo, no entra** — y los tests son lo que hace seguro aceptarlo."
4. "Por ejemplo, una vez **[caso que ayudó]**… y otra vez **[caso que falló y cómo lo detectaste]**."
