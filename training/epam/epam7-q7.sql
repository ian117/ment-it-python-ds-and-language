-- =============================================================
-- P7 — Schema de BD que soporte compartir tareas  ·  RESUELTO
-- =============================================================
--     user1 -> creates -> task1
--     user1 -> shares  -> task1 -> user2
--     user2 -> read    -> task1
--
-- "What would be the schema/db that supports this behaviour?"
--
-- Tu respuesta en la entrevista (pivote usersTask con rol enum:
-- owner/editor/guest) ERA CORRECTA. Aquí está blindada.
--
-- ANALOGÍA: la pivote es la lista de invitados de un evento. La
-- tarea es el evento, el usuario es la persona, y el `role` es
-- qué dice su gafete: organizador, staff o público.
-- =============================================================


-- =============================================================
-- 1. ¿QUÉ CAMBIÓ EN LA RELACIÓN?
-- =============================================================
-- ANTES:  1:N   un usuario tiene muchas tareas, cada tarea tiene
--               UN dueño  ->  bastaba una FK owner_id en tasks.
--
-- AHORA:  N:M   una tarea puede estar compartida con muchos
--               usuarios, y un usuario ve muchas tareas ajenas.
--
-- Por qué la FK ya no alcanza: una columna solo guarda UN valor.
-- Para que task1 esté compartida con user2, user3 y user7
-- necesitarías shared_with_1, shared_with_2... (imposible de
-- consultar e indexar) o una lista serializada en un campo de
-- texto (imposible de hacer JOIN, sin integridad referencial).
--
-- En SQL, un N:M SIEMPRE se resuelve con una TABLA PIVOTE.
-- Y el rol es un ATRIBUTO DE LA RELACIÓN: no es propiedad del
-- usuario ni de la tarea, sino del vínculo entre ambos. Por eso
-- vive en la pivote y no en ninguna de las dos tablas.


-- =============================================================
-- 2. EL DDL
-- =============================================================

CREATE TABLE users (
    id            BIGSERIAL   PRIMARY KEY,
    email         CITEXT      UNIQUE NOT NULL,   -- CITEXT: case-insensitive
    password_hash TEXT        NOT NULL,          -- el HASH, nunca la password
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE tasks (
    id          BIGSERIAL   PRIMARY KEY,
    owner_id    BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       TEXT        NOT NULL,
    description TEXT,
    status      TEXT        NOT NULL DEFAULT 'todo',
    due_date    DATE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_tasks_owner ON tasks(owner_id);

CREATE TYPE share_role AS ENUM ('viewer', 'editor');

CREATE TABLE task_shares (                        -- LA TABLA PIVOTE
    task_id    BIGINT      NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id    BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role       share_role  NOT NULL DEFAULT 'viewer',
    granted_by BIGINT      NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (task_id, user_id)                -- no compartir 2x al mismo
);
CREATE INDEX idx_task_shares_user ON task_shares(user_id);


-- =============================================================
-- 3. JUSTIFICACIONES  (hay que decirlas EN VOZ ALTA)
-- =============================================================
--
-- --- PK COMPUESTA (task_id, user_id) vs un id propio ----------
-- La compuesta garantiza la unicidad del share SIN un UNIQUE
-- extra: es imposible insertar dos veces el mismo par. Además el
-- índice de la PK sirve para "¿qué usuarios ven esta tarea?".
-- Contra: si tu ORM se lleva mal con PKs compuestas (algunos lo
-- hacen), usa `id BIGSERIAL PRIMARY KEY` + `UNIQUE(task_id, user_id)`.
-- Lo que NO es defendible es no tener ninguna de las dos: sin
-- restricción, un doble click crea shares duplicados.
--
-- --- owner_id en tasks  vs  'owner' dentro del enum -----------
-- Las dos son defendibles y conviene presentar ambas:
--
--   CON owner_id en tasks:
--     + consultas de propiedad triviales
--     + NOT NULL garantiza que TODA tarea tenga exactamente un dueño
--     - transferir la propiedad es un UPDATE, no un cambio de rol
--
--   TODO EN LA PIVOTE (owner/editor/viewer):
--     + modelo uniforme, permite transferir propiedad y hasta
--       tener varios dueños
--     - pierdes la garantía de "exactamente un owner" salvo con
--       un índice parcial único:
--         CREATE UNIQUE INDEX ON task_shares(task_id)
--           WHERE role = 'owner';
--
--   RESPUESTA MADURA: owner_id en tasks Y el enum limitado a
--   viewer/editor. Si mañana piden transferencia de propiedad,
--   se migra. No pagues hoy la complejidad de un requisito que
--   nadie pidió.
--
-- --- ÍNDICES: qué consulta muere si falta cada uno ------------
--   idx_tasks_owner        -> "mis tareas". Sin él, seq scan de
--                             toda la tabla tasks.
--   idx_task_shares_user   -> "compartidas conmigo". Sin él,
--                             listar el inbox de UN usuario
--                             escanea TODA la pivote. Es el más
--                             fácil de olvidar: la PK compuesta
--                             empieza por task_id, así que NO
--                             sirve para buscar por user_id.
--                             (Un índice compuesto solo se usa de
--                              izquierda a derecha: eso es el
--                              "leftmost prefix rule".)
--
-- --- ON DELETE CASCADE vs RESTRICT ----------------------------
--   tasks.owner_id  -> CASCADE: borrar al usuario borra sus tareas.
--                      ¿Seguro? En la práctica casi siempre
--                      quieres SOFT DELETE (deleted_at) para no
--                      perder historial ni romper auditoría.
--   task_shares.*   -> CASCADE está bien: si la tarea muere, sus
--                      shares no tienen sentido.
--   granted_by      -> deliberadamente SIN cascade: si borras al
--                      que compartió, no quieres perder el share.
--
-- --- AUDITORÍA ------------------------------------------------
--   granted_by + created_at responden "¿quién me compartió esto y
--   cuándo?", que es literalmente la primera pregunta que llega a
--   soporte. Cuestan dos columnas y evitan un forense imposible.


-- =============================================================
-- 4. TODAS LAS TAREAS VISIBLES PARA UN USUARIO, CON SU ROL
-- =============================================================

SELECT t.*, 'owner' AS role
FROM tasks t
WHERE t.owner_id = :uid

UNION ALL                       -- ALL: no hay duplicados posibles
                                -- (eres owner O tienes share, no ambos)
                                -- y evita el DISTINCT implícito de UNION
SELECT t.*, s.role::text
FROM tasks t
JOIN task_shares s ON s.task_id = t.id
WHERE s.user_id = :uid;


-- =============================================================
-- 5. (E12) TAREAS QUE PUEDE EDITAR, ORDENADAS Y PAGINADAS
-- =============================================================

SELECT t.*
FROM tasks t
WHERE t.owner_id = :uid
   OR EXISTS (
        SELECT 1 FROM task_shares s
        WHERE s.task_id = t.id
          AND s.user_id = :uid
          AND s.role = 'editor'
      )
ORDER BY t.due_date NULLS LAST, t.id     -- desempate obligatorio
LIMIT 20 OFFSET :offset;

-- ÍNDICES QUE NECESITA:
--   tasks(owner_id)
--   task_shares(user_id, role)   -- o (user_id) INCLUDE (role)
--   tasks(due_date, id)          -- para el ORDER BY
--
-- POR QUÉ `EXISTS` Y NO UN JOIN:
--   con JOIN a la pivote, una tarea compartida contigo aparecería
--   duplicada si además eres owner, y necesitarías DISTINCT (que
--   fuerza una ordenación extra). EXISTS corta en el primer match.
--
-- POR QUÉ EL ORDER BY LLEVA `, t.id`:
--   sin un desempate, dos tareas con el mismo due_date pueden
--   salir en orden distinto entre páginas -> la paginación repite
--   o se salta filas. Es un bug clásico y muy difícil de rastrear.
--
-- POR QUÉ OFFSET ESCALA MAL:
--   OFFSET 100000 obliga a la BD a leer y descartar 100.000 filas
--   antes de devolver 20. Se degrada linealmente con la página.
--   La alternativa es PAGINACIÓN POR CURSOR (keyset):
--
--     WHERE (t.due_date, t.id) > (:last_due, :last_id)
--     ORDER BY t.due_date, t.id
--     LIMIT 20;
--
--   Coste constante en cualquier página. Contra: no puedes saltar
--   a "la página 50", solo avanzar. Para un feed infinito es
--   ideal; para una tabla con paginador numerado, no sirve.


-- =============================================================
-- CÓMO EVOLUCIONA (menciónalo como evolución, NO lo construyas)
-- =============================================================
-- - COMPARTIR CON EQUIPOS: tablas teams y team_members, y la
--   pivote acepta user_id O team_id (o dos pivotes separadas).
--
-- - PERMISOS GRANULARES: modelo genérico
--     permissions(subject_type, subject_id, resource_type,
--                 resource_id, action)
--   Flexible, pero MATA LA INTEGRIDAD REFERENCIAL: no puedes
--   poner una FK sobre resource_id porque apunta a varias tablas.
--   Solo si de verdad hace falta.
--
-- - ENLACES PÚBLICOS: share_links(token, task_id, expires_at, role).
--
-- - CUIDADO CON N+1: al listar 20 tareas con sus colaboradores,
--   un JOIN o selectinload — nunca un query por tarea. Es el bug
--   de rendimiento más común con un ORM, y en la entrevista
--   mencionarlo demuestra que has sufrido producción.
