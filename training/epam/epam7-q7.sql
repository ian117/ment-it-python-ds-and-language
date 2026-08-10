-- =============================================================
-- P7 — Schema de BD que soporte compartir tareas
-- =============================================================
-- Nivel base de datos. Tienes dos tablas: User y Task.
--     User -> CRUD -> Tasks
--
-- Nueva feature: TASK SHARING
--     user1 -> creates -> task1
--     user1 -> shares  -> task1 -> user2
--     user2 -> read    -> task1
--
-- "What would be the schema/db that supports this behaviour?"
--
-- TU TAREA
--   1. ¿Qué tipo de relación es ahora entre User y Task?
--      ¿Por qué la FK que tenías antes ya no alcanza?
--   2. Escribe el DDL completo: users, tasks y la tabla nueva.
--   3. Justifica CADA decisión en voz alta:
--        - ¿PK compuesta o id propio en la pivote? ¿por qué?
--        - ¿el 'owner' va en el enum de roles o como owner_id
--          en tasks? defiende las dos y elige una.
--        - ¿qué índices y qué consulta hace lenta cada uno si falta?
--        - ¿ON DELETE CASCADE o RESTRICT? ¿en cuál FK?
--        - ¿qué campos de auditoría añades y qué pregunta responden?
--   4. Escribe la consulta: todas las tareas visibles para un
--      usuario, con su rol.
--   5. (E12) Todas las tareas que un usuario puede EDITAR (suyas +
--      compartidas con rol editor), ordenadas por due_date,
--      paginadas de 20 en 20. ¿Qué índices necesita?
--      ¿Por qué OFFSET escala mal y qué usarías en su lugar?
--
-- EVOLUCIÓN (menciónalo, no lo construyas):
--   compartir con equipos, permisos granulares, enlaces públicos,
--   y el problema N+1 al listar tareas con sus colaboradores.


-- --- 2. Tu DDL:


-- --- 3. Justificaciones:


-- --- 4. Tareas visibles con su rol:


-- --- 5. Tareas editables, paginadas:
