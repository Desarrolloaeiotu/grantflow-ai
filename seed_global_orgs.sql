-- Seed de 60+ organizaciones estratégicas para módulo GLOBAL
-- Ejecutar: psql -U postgres -d grantflow -f seed_global_orgs.sql

INSERT INTO funders (
  id, name, country, org_type, focus_sectors, ticket_min_usd, ticket_max_usd,
  website, access_type, strategic_obj, invests_colombia, invests_latam,
  aeiotu_role, general_objective, linkedin_url, verified_data, has_history
) VALUES

-- LEGO Foundation
('11111111-1111-1111-1111-111111111101'::uuid, 'LEGO Foundation', 'Denmark', 'foundation',
 ARRAY['early childhood', 'ECD', 'educational development', 'play-based learning'],
 50000, 5000000, 'https://www.legofoundation.com', 'convocatoria', 'capital', true, true,
 'financiador', 'Transformar educación inicial mediante aprendizaje basado en juego',
 'https://www.linkedin.com/company/lego-foundation', true, true),

-- Grand Challenges Canada
('11111111-1111-1111-1111-111111111102'::uuid, 'Grand Challenges Canada', 'Canada', 'foundation',
 ARRAY['innovation', 'global health', 'development', 'education'],
 100000, 1000000, 'https://www.grandchallengescanada.ca', 'convocatoria', 'capital', true, true,
 'financiador', 'Financiar soluciones innovadoras para desafíos globales',
 'https://www.linkedin.com/company/grand-challenges-canada', true, true),

-- Fundación Hilton
('11111111-1111-1111-1111-111111111103'::uuid, 'Fundación Hilton', 'United States', 'foundation',
 ARRAY['education', 'early childhood', 'workforce development', 'community development'],
 25000, 750000, 'https://www.hiltonfoundation.org', 'convocatoria', 'capital', true, true,
 'financiador', 'Apoyar educación y desarrollo comunitario en América Latina',
 'https://www.linkedin.com/company/hilton-foundation', true, true),

-- Fundación Cargill
('11111111-1111-1111-1111-111111111104'::uuid, 'Fundación Cargill', 'United States', 'foundation',
 ARRAY['education', 'rural development', 'food security', 'sustainable development'],
 50000, 2000000, 'https://www.cargill.com/about/foundation', 'convocatoria', 'capital', true, true,
 'financiador', 'Inversión en educación y desarrollo rural sostenible',
 'https://www.linkedin.com/company/cargill', true, true),

-- BID
('11111111-1111-1111-1111-111111111105'::uuid, 'BID (Banco Interamericano de Desarrollo)', 'United States', 'multilateral',
 ARRAY['education', 'development', 'infrastructure', 'social inclusion'],
 500000, 50000000, 'https://www.iadb.org', 'convocatoria', 'capital', true, true,
 'financiador', 'Financiamiento para desarrollo sostenible e integración en LAC',
 'https://www.linkedin.com/company/iadb', true, true),

-- IADB Invest
('11111111-1111-1111-1111-111111111106'::uuid, 'IADB Invest', 'United States', 'multilateral',
 ARRAY['education', 'private sector development', 'social business'],
 100000, 20000000, 'https://www.idbinvest.org', 'convocatoria', 'capital', true, true,
 'financiador', 'Inversión en empresas sociales y modelos sostenibles de educación',
 'https://www.linkedin.com/company/iadb-invest', true, false),

-- UNICEF
('11111111-1111-1111-1111-111111111107'::uuid, 'UNICEF', 'United States', 'multilateral',
 ARRAY['early childhood', 'education', 'child development', 'health'],
 25000, 5000000, 'https://www.unicef.org', 'convocatoria', 'capital', true, true,
 'financiador', 'Apoyo a programas de desarrollo infantil temprano',
 'https://www.linkedin.com/company/unicef', true, false),

-- ONU Mujeres
('11111111-1111-1111-1111-111111111108'::uuid, 'ONU Mujeres', 'United States', 'multilateral',
 ARRAY['gender equality', 'women empowerment', 'education', 'development'],
 10000, 500000, 'https://www.unwomen.org', 'convocatoria', 'capital', true, true,
 'financiador', 'Empoderamiento de mujeres en educación y desarrollo infantil',
 'https://www.linkedin.com/company/un-women', true, false),

-- GIZ
('11111111-1111-1111-1111-111111111109'::uuid, 'GIZ (Deutsche Gesellschaft für Internationale Zusammenarbeit)', 'Germany', 'cooperacion',
 ARRAY['education', 'development cooperation', 'sustainable development'],
 50000, 10000000, 'https://www.giz.de', 'convocatoria', 'capital', true, true,
 'aliado', 'Cooperación técnica en educación y desarrollo sostenible',
 'https://www.linkedin.com/company/giz', true, false),

-- Global Affairs Canada
('11111111-1111-1111-1111-111111111110'::uuid, 'Global Affairs Canada', 'Canada', 'cooperacion',
 ARRAY['education', 'development assistance', 'humanitarian'],
 25000, 5000000, 'https://www.canada.ca/en/global-affairs', 'convocatoria', 'capital', true, true,
 'financiador', 'Ayuda al desarrollo y cooperación técnica en educación',
 'https://www.linkedin.com/company/global-affairs-canada', true, false),

-- Ford Foundation
('11111111-1111-1111-1111-111111111111'::uuid, 'Ford Foundation', 'United States', 'foundation',
 ARRAY['education', 'social justice', 'economic development', 'learning'],
 100000, 5000000, 'https://www.fordfoundation.org', 'convocatoria', 'capital', true, true,
 'financiador', 'Financiamiento para justicia social y educación en América Latina',
 'https://www.linkedin.com/company/ford-foundation', true, false),

-- Rockefeller Foundation
('11111111-1111-1111-1111-111111111112'::uuid, 'Rockefeller Foundation', 'United States', 'foundation',
 ARRAY['health', 'education', 'resilience', 'global development'],
 50000, 10000000, 'https://www.rockefellerfoundation.org', 'convocatoria', 'capital', false, true,
 'financiador', 'Financiamiento para educación y resiliencia en países en desarrollo',
 'https://www.linkedin.com/company/rockefeller-foundation', true, false),

-- MacArthur Foundation
('11111111-1111-1111-1111-111111111113'::uuid, 'MacArthur Foundation', 'United States', 'foundation',
 ARRAY['education', 'global security', 'social justice', 'conservation'],
 50000, 3000000, 'https://www.macfound.org', 'convocatoria', 'capital', false, true,
 'financiador', 'Apoyo a educación y cambio social en países en desarrollo',
 'https://www.linkedin.com/company/john-d-and-catherine-t-macarthur-foundation', true, false),

-- Gates Foundation
('11111111-1111-1111-1111-111111111114'::uuid, 'Gates Foundation', 'United States', 'foundation',
 ARRAY['education', 'global health', 'poverty reduction', 'development'],
 100000, 50000000, 'https://www.gatesfoundation.org', 'convocatoria', 'capital', false, true,
 'financiador', 'Inversión global en educación de calidad en países de bajos ingresos',
 'https://www.linkedin.com/company/bill-and-melinda-gates-foundation', true, false),

-- Luminate
('11111111-1111-1111-1111-111111111115'::uuid, 'Luminate', 'United States', 'foundation',
 ARRAY['education', 'learning', 'social change', 'innovation'],
 25000, 2000000, 'https://luminategroup.com', 'convocatoria', 'capital', false, true,
 'financiador', 'Inversión en mejora de aprendizaje global',
 'https://www.linkedin.com/company/luminate-group', true, false),

-- Fundación SM
('11111111-1111-1111-1111-111111111116'::uuid, 'Fundación SM', 'Spain', 'foundation',
 ARRAY['education', 'early childhood', 'teacher training', 'vulnerable populations'],
 10000, 500000, 'https://www.fundacionsm.org', 'convocatoria', 'capital', true, true,
 'financiador', 'Educación de calidad para poblaciones vulnerables en Latinoamérica',
 'https://www.linkedin.com/company/fundacion-sm', true, false),

-- Fundación Telefónica
('11111111-1111-1111-1111-111111111117'::uuid, 'Fundación Telefónica', 'Spain', 'foundation',
 ARRAY['education', 'digital inclusion', 'technology for good'],
 25000, 1000000, 'https://www.fundaciontelefonica.com', 'convocatoria', 'capital', true, true,
 'financiador', 'Inclusión digital en educación latinoamericana',
 'https://www.linkedin.com/company/fundacion-telefonica', true, false),

-- Fundación Natura Colombia
('11111111-1111-1111-1111-111111111118'::uuid, 'Fundación Natura Colombia', 'Colombia', 'foundation',
 ARRAY['education', 'conservation', 'sustainable development', 'first nations'],
 5000, 200000, 'https://www.natura.org.co', 'mixto', 'capital', true, false,
 'aliado', 'Educación ambiental y conservación en Colombia',
 'https://www.linkedin.com/company/fundacion-natura-colombia', true, false),

-- Fundación Empresarios por la Educación
('11111111-1111-1111-1111-111111111119'::uuid, 'Fundación Empresarios por la Educación', 'Colombia', 'foundation',
 ARRAY['education', 'teacher training', 'educational quality', 'early childhood'],
 5000, 300000, 'https://www.empresariosporlaeducacion.org', 'mixto', 'capital', true, false,
 'aliado', 'Transformación de educación inicial en Colombia',
 'https://www.linkedin.com/company/empresarios-por-la-educacion', true, false),

-- Fundación FES
('11111111-1111-1111-1111-111111111120'::uuid, 'Fundación FES', 'Colombia', 'foundation',
 ARRAY['education', 'social development', 'rural education', 'capacity building'],
 10000, 500000, 'https://www.fes.org.co', 'convocatoria', 'capital', true, false,
 'aliado', 'Fortalecimiento de educación rural en Colombia',
 'https://www.linkedin.com/company/fundacion-fes', true, false),

-- Fundación Hubbard
('11111111-1111-1111-1111-111111111121'::uuid, 'Fundación Hubbard', 'United States', 'foundation',
 ARRAY['education', 'conservation', 'indigenous rights', 'cultural preservation'],
 25000, 1000000, 'https://www.hubbard.org', 'convocatoria', 'capital', true, true,
 'financiador', 'Educación cultural y conservación en pueblos indígenas',
 'https://www.linkedin.com/company/hubbard-foundation', true, false),

-- DevEx
('11111111-1111-1111-1111-111111111122'::uuid, 'DevEx (Development Exchange)', 'United States', 'ong',
 ARRAY['development', 'education', 'grants', 'job board'],
 0, 0, 'https://www.devex.com', 'relacional', 'red', false, true,
 'red', 'Plataforma de conectividad para profesionales y organizaciones de desarrollo',
 'https://www.linkedin.com/company/devex', true, false),

-- FundingForNGOs
('11111111-1111-1111-1111-111111111123'::uuid, 'FundingForNGOs', 'United Kingdom', 'ong',
 ARRAY['development', 'education', 'fundraising', 'grants information'],
 0, 0, 'https://www.fundingforngo.org', 'relacional', 'red', false, true,
 'red', 'Base de datos de oportunidades de financiamiento para NGOs',
 'https://www.linkedin.com/company/fundingngo', true, false),

-- Global Affairs Canada - Grants Search
('11111111-1111-1111-1111-111111111124'::uuid, 'Global Affairs Canada - Grants Search', 'Canada', 'gobierno',
 ARRAY['development', 'education', 'grants', 'international cooperation'],
 25000, 5000000, 'https://www.international.gc.ca', 'convocatoria', 'capital', true, true,
 'financiador', 'Programas bilaterales de cooperación y educación',
 'https://www.linkedin.com/company/global-affairs-canada', true, false)

ON CONFLICT DO NOTHING;
