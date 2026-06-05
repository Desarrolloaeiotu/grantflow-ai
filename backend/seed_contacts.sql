-- Script para agregar contactos de prueba a la BD
-- Ejecutar en Supabase SQL Editor

-- Obtener los primeros 5 funders
WITH funders_list AS (
  SELECT id, name FROM funders LIMIT 5
)
INSERT INTO contacts (
  id, full_name, last_name, title, email, linkedin_url,
  role_category, funder_id, source, fetched_at, aeiotu_connection
)
SELECT
  gen_random_uuid(),
  CASE row_number() OVER (ORDER BY f.id) % 5
    WHEN 1 THEN 'Maria'
    WHEN 2 THEN 'Carlos'
    WHEN 3 THEN 'Sofia'
    WHEN 4 THEN 'Juan'
    ELSE 'Laura'
  END,
  CASE row_number() OVER (ORDER BY f.id) % 5
    WHEN 1 THEN 'Garcia'
    WHEN 2 THEN 'Lopez'
    WHEN 3 THEN 'Rodriguez'
    WHEN 4 THEN 'Martinez'
    ELSE 'Sanchez'
  END,
  CASE row_number() OVER (ORDER BY f.id) % 5
    WHEN 1 THEN 'Grants Manager'
    WHEN 2 THEN 'Partnerships Director'
    WHEN 3 THEN 'Program Officer'
    WHEN 4 THEN 'Cooperation Specialist'
    ELSE 'Development Officer'
  END,
  CASE row_number() OVER (ORDER BY f.id) % 5
    WHEN 1 THEN 'maria.garcia@' || LOWER(REPLACE(REPLACE(f.name, ' ', ''), '.', '')) || '.org'
    WHEN 2 THEN 'carlos.lopez@' || LOWER(REPLACE(REPLACE(f.name, ' ', ''), '.', '')) || '.org'
    WHEN 3 THEN 'sofia.rodriguez@' || LOWER(REPLACE(REPLACE(f.name, ' ', ''), '.', '')) || '.org'
    WHEN 4 THEN 'juan.martinez@' || LOWER(REPLACE(REPLACE(f.name, ' ', ''), '.', '')) || '.org'
    ELSE 'laura.sanchez@' || LOWER(REPLACE(REPLACE(f.name, ' ', ''), '.', '')) || '.org'
  END,
  CASE row_number() OVER (ORDER BY f.id) % 5
    WHEN 1 THEN 'https://linkedin.com/in/mariagarcia'
    WHEN 2 THEN 'https://linkedin.com/in/carloslopez'
    WHEN 3 THEN 'https://linkedin.com/in/sofiar'
    WHEN 4 THEN 'https://linkedin.com/in/juanm'
    ELSE 'https://linkedin.com/in/laurasanchez'
  END,
  CASE row_number() OVER (ORDER BY f.id) % 5
    WHEN 1 THEN 'grants'
    WHEN 2 THEN 'partnerships'
    WHEN 3 THEN 'innovation'
    WHEN 4 THEN 'cooperation'
    ELSE 'development'
  END,
  f.id,
  'apollo',
  NOW(),
  false
FROM funders_list f;

-- Verificar contactos creados
SELECT COUNT(*) as total_contacts FROM contacts;
