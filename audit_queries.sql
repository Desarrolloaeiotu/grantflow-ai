-- ============================================================================
-- AUDITORÍA COMPLETA DE BD — GrantFlow AI
-- Ejecutar: psql -d grantflow_dev -f audit_queries.sql
-- ============================================================================

-- 1. RESUMEN GENERAL
SELECT
  COUNT(*) as total_oportunidades,
  COUNT(CASE WHEN title IS NULL THEN 1 END) as null_title,
  COUNT(CASE WHEN deadline IS NULL THEN 1 END) as null_deadline,
  COUNT(CASE WHEN score_total IS NULL THEN 1 END) as null_score,
  COUNT(CASE WHEN decision IS NULL THEN 1 END) as null_decision,
  COUNT(CASE WHEN market_window IS NULL THEN 1 END) as null_window,
  COUNT(CASE WHEN source_name IS NULL THEN 1 END) as null_source
FROM opportunities;

\echo '---'

-- 2. DISTRIBUCIÓN DE VENTANAS
SELECT market_window, COUNT(*) as count
FROM opportunities
GROUP BY market_window
ORDER BY count DESC;

\echo '---'

-- 3. DISTRIBUCIÓN DE DECISIONES
SELECT decision, COUNT(*) as count
FROM opportunities
GROUP BY decision
ORDER BY count DESC;

\echo '---'

-- 4. DISTRIBUCIÓN DE FUENTES
SELECT source_name, COUNT(*) as count
FROM opportunities
GROUP BY source_name
ORDER BY count DESC;

\echo '---'

-- 5. OPORTUNIDADES SIN MONTO POR FUENTE
SELECT source_name, COUNT(*) as without_amount
FROM opportunities
WHERE amount_max_cop IS NULL
GROUP BY source_name
ORDER BY without_amount DESC;

\echo '---'

-- 6. MONTOS ANÓMALOS (< $1M o > $100B COP)
SELECT COUNT(*) as anomalous_amounts FROM opportunities
WHERE (amount_max_cop < 1_000_000 OR amount_max_cop > 100_000_000_000)
  AND amount_max_cop IS NOT NULL;

\echo '---'

-- 7. LISTA DE MONTOS ANÓMALOS (primeras 20)
SELECT id, title, amount_max_cop, source_name
FROM opportunities
WHERE (amount_max_cop < 1_000_000 OR amount_max_cop > 100_000_000_000)
  AND amount_max_cop IS NOT NULL
LIMIT 20;

\echo '---'

-- 8. DEADLINES EN EL PASADO (que NO son no_go)
SELECT COUNT(*) as deadlines_past
FROM opportunities
WHERE deadline < CURRENT_DATE
  AND decision != 'no_go'
  AND decision IS NOT NULL;

\echo '---'

-- 9. LISTA DE DEADLINES EN PASADO (primeras 20)
SELECT id, title, deadline, decision, source_name
FROM opportunities
WHERE deadline < CURRENT_DATE
  AND decision != 'no_go'
LIMIT 20;

\echo '---'

-- 10. DUPLICADOS POTENCIALES
SELECT title, funder_id, COUNT(*) as cnt
FROM opportunities
GROUP BY title, funder_id
HAVING COUNT(*) > 1
ORDER BY cnt DESC
LIMIT 20;

\echo '---'

-- 11. EMAILS VERIFICADOS vs NO VERIFICADOS
SELECT
  COUNT(CASE WHEN ceo_email_verified = TRUE THEN 1 END) as verified_ceo,
  COUNT(CASE WHEN ceo_email_verified = FALSE THEN 1 END) as unverified_ceo,
  COUNT(CASE WHEN ceo_email IS NULL THEN 1 END) as null_ceo_email
FROM opportunities;

\echo '---'

-- 12. COBERTURA DE EMBEDDINGS
SELECT
  COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as with_embedding,
  COUNT(CASE WHEN embedding IS NULL THEN 1 END) as without_embedding
FROM opportunities;

\echo '---'

-- 13. SCORES INVÁLIDOS (> 10 o < 0)
SELECT COUNT(*) as invalid_scores
FROM opportunities
WHERE (score_total > 10 OR score_total < 0)
  AND score_total IS NOT NULL;

\echo '---'

-- 14. ORFANOS: OPORTUNIDADES SIN FUNDER VÁLIDO
SELECT COUNT(*) as orphan_opportunities
FROM opportunities o
LEFT JOIN funders f ON o.funder_id = f.id
WHERE o.funder_id IS NOT NULL AND f.id IS NULL;

\echo '---'

-- 15. ÚLTIMAS ACTUALIZACIONES POR FUENTE
SELECT source_name,
  MAX(detected_at)::DATE as ultima_actualizacion,
  COUNT(*) as opp_detectadas
FROM opportunities
GROUP BY source_name
ORDER BY source_name;

\echo '---'

-- 16. MONTOS PROMEDIO POR FUENTE
SELECT source_name,
  ROUND(AVG(amount_max_cop)::numeric / 1_000_000, 2) as avg_millones,
  MIN(amount_max_cop) as min_amount,
  MAX(amount_max_cop) as max_amount
FROM opportunities
WHERE amount_max_cop IS NOT NULL
GROUP BY source_name
ORDER BY avg_millones DESC;

\echo '---'

-- 17. NACIONAL vs GLOBAL: DISTRIBUCIÓN
SELECT
  COUNT(CASE WHEN source_name IN ('nacional_colombia', 'secop') THEN 1 END) as nacional_count,
  COUNT(CASE WHEN source_name NOT IN ('nacional_colombia', 'secop') THEN 1 END) as global_count
FROM opportunities;

\echo '---'

-- 18. OPORTUNIDADES DETECTADAS HOY vs ÚLTIMOS 7 DÍAS
SELECT
  COUNT(CASE WHEN detected_at::DATE = CURRENT_DATE THEN 1 END) as today,
  COUNT(CASE WHEN detected_at::DATE >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as last_7_days,
  COUNT(CASE WHEN detected_at::DATE >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as last_30_days
FROM opportunities;

\echo '---'

-- 19. CANTIDAD DE FINANCIADORES EN BD
SELECT COUNT(*) as total_funders FROM funders;

\echo '---'

-- 20. CANTIDAD DE CONTACTOS EN BD
SELECT COUNT(*) as total_contacts FROM contacts;
