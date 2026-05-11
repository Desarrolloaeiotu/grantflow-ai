/**
 * Oportunidades nacionales estratégicas — curadas del CLAUDE.md sección 16.
 *
 * Estas NO vienen de scraping. Son objetivos 2026 que aeioTU persigue
 * vía negociación directa con financiadores históricos (MEN, ICBF, CAFAM, ACEP).
 */

export type Category = 'gobierno' | 'privado' | 'cajas' | 'politica'

export interface CEO {
  name: string
  title: string
  email: string
  linkedin?: string
  verified: boolean
}

export interface Organization {
  name: string
  website: string
  email: string
  linkedin?: string
  verified: boolean
}

export interface NationalOpp {
  id: string
  title: string
  score: number
  decision: 'go' | 'pending'
  category: Category
  tags: { label: string; cls: 'tag-window' | 'tag-capital' | 'tag-source' }[]
  description: string
  actions: { step: number; text: string }[]
  organization: Organization
  ceo: CEO
  ally?: { name: string; website?: string; email?: string; verified: boolean; role?: string }
  amountCOP: string
  amountMinM: number
  deadlineText: string
  startQuarter: 1 | 2 | 3 | 4
  criteria: { label: string; pts: 0 | 1 | 2 }[]
  rfpUrl: string
  reasoning: string
}

export const NATIONAL_OPPS: NationalOpp[] = [
  {
    id: 'cdi-men',
    title: 'Fortalecimiento de CDI en contextos de vulnerabilidad',
    score: 9,
    decision: 'go',
    category: 'gobierno',
    tags: [
      { label: 'Gobierno', cls: 'tag-window' },
      { label: 'Consultoría', cls: 'tag-capital' },
      { label: 'MEN + Fondos Regional.', cls: 'tag-source' },
    ],
    description:
      'Ministerio de Educación y Fondos de Compensación buscan mejorar calidad de CDI públicos en municipios vulnerables (post-conflicto, zonas rurales). Incluye: formación docente, acompañamiento pedagógico, transformación de ambientes y medición del desarrollo infantil.',
    actions: [
      { step: 1, text: 'Diagnóstico de 50–80 CDI en 3 regiones.' },
      { step: 2, text: 'Formación de 200+ docentes basada en modelo aeioTU.' },
      { step: 3, text: 'Acompañamiento pedagógico 6 meses + medición ConecTU.' },
    ],
    organization: {
      name: 'Ministerio de Educación Nacional',
      website: 'https://www.mineducacion.gov.co',
      email: 'atencionalciudadano@mineducacion.gov.co',
      linkedin: 'https://www.linkedin.com/company/ministerio-de-educacion-nacional-colombia/',
      verified: true,
    },
    ceo: {
      name: 'Por verificar',
      title: 'Viceministro(a) de Educación Preescolar, Básica y Media',
      email: 'viceministerio@mineducacion.gov.co',
      linkedin: 'https://www.linkedin.com/search/results/people/?keywords=Viceministra%20Educacion%20Preescolar%20Colombia',
      verified: false,
    },
    ally: {
      name: 'Fundación Cargill',
      website: 'https://www.cargill.com/about/cargill-foundation',
      email: 'colombia@fundacioncargill.org',
      verified: false,
      role: 'Aliado histórico',
    },
    amountCOP: 'COP $280–450M',
    amountMinM: 280,
    deadlineText: 'Inicio Q2 2026',
    startQuarter: 2,
    criteria: [
      { label: 'Alineación', pts: 2 },
      { label: 'Modelo probado', pts: 2 },
      { label: 'Escala nacional', pts: 2 },
      { label: 'Viabilidad', pts: 2 },
      { label: 'Relacional', pts: 1 },
    ],
    rfpUrl: 'https://www.mineducacion.gov.co/',
    reasoning:
      'Conecta directamente con expertise aeioTU en CDI públicos. Línea Innovación y Calidad + operación jardines como modelo. Potencial de sistematización nacional.',
  },
  {
    id: 'cajas-comp',
    title: 'Diplomado de Primera Infancia Integral para Cajas de Compensación',
    score: 9,
    decision: 'go',
    category: 'cajas',
    tags: [
      { label: 'Cajas Comp.', cls: 'tag-window' },
      { label: 'Licenciamiento', cls: 'tag-capital' },
      { label: 'CAFAM + Multinivel', cls: 'tag-source' },
    ],
    description:
      'CAFAM, Caja Nariño y otras cajas de compensación necesitan fortalecer formación de docentes y cuidadores en educación inicial de calidad. Incluye: modalidades institucional y familiar, acompañamiento pedagógico modular, certificación aeioTU.',
    actions: [
      { step: 1, text: 'Diseñar diplomado modular (120 horas, 6 módulos).' },
      { step: 2, text: 'Negociar con CAFAM como piloto: 50 docentes/caja.' },
      { step: 3, text: 'Escalar a 6–8 cajas multinivel (ingresos recurrentes).' },
    ],
    organization: {
      name: 'CAFAM',
      website: 'https://www.cafam.com.co',
      email: 'servicioalcliente@cafam.com.co',
      linkedin: 'https://www.linkedin.com/company/cafam/',
      verified: true,
    },
    ceo: {
      name: 'Por verificar',
      title: 'Director(a) de Educación / Innovación CAFAM',
      email: 'innovacion@cafam.com.co',
      linkedin: 'https://www.linkedin.com/search/results/people/?keywords=Director%20Educacion%20CAFAM',
      verified: false,
    },
    ally: {
      name: 'Asocajas (Confederación)',
      website: 'https://www.asocajas.org.co',
      verified: false,
      role: 'Red',
    },
    amountCOP: 'COP $180–320M / caja',
    amountMinM: 180,
    deadlineText: 'Negociación 2026',
    startQuarter: 2,
    criteria: [
      { label: 'Econ. cuidado', pts: 2 },
      { label: 'Formación docente', pts: 2 },
      { label: 'Ingresos rec.', pts: 2 },
      { label: 'Socio histórico', pts: 2 },
      { label: 'Escalabilidad', pts: 1 },
    ],
    rfpUrl: 'https://www.cafam.com.co/',
    reasoning:
      'CAFAM es socio operativo histórico de aeioTU. Combina Jardines en alianza + Economía del Cuidado. Sostenibilidad financiera clara (cuota anual / maestro / caja).',
  },
  {
    id: 'jardines-privados',
    title: 'Acompañamiento Integrado de Calidad para Jardines Privados',
    score: 7,
    decision: 'pending',
    category: 'privado',
    tags: [
      { label: 'Privado', cls: 'tag-window' },
      { label: 'Consultoría', cls: 'tag-capital' },
      { label: 'Iniciativa propia', cls: 'tag-source' },
    ],
    description:
      'Jardines privados urbanos y rurales buscan mejorar calidad sin expansión de infraestructura. Necesitan: formación docente, acompañamiento pedagógico modular, acceso a Red aeioTU y medición continua con ConecTU. Modelo escalable por ciudad.',
    actions: [
      { step: 1, text: 'Diseñar propuesta comercial clara: grupos de 15–20 jardines.' },
      { step: 2, text: 'Piloto en Bogotá: diagnóstico + 3 meses formación.' },
      { step: 3, text: 'Replicar modelo en 5 ciudades (Medellín, Cali, Barranquilla).' },
    ],
    organization: {
      name: 'Asociación Colombiana de Educación Preescolar (ACEP)',
      website: 'https://acepcolombia.org',
      email: 'info@acepcolombia.org',
      linkedin: 'https://www.linkedin.com/company/asociacion-colombiana-de-educacion-preescolar/',
      verified: false,
    },
    ceo: {
      name: 'Por verificar',
      title: 'Presidente Ejecutivo ACEP',
      email: 'presidencia@acepcolombia.org',
      linkedin: 'https://www.linkedin.com/search/results/people/?keywords=Presidente%20ACEP%20Colombia',
      verified: false,
    },
    amountCOP: 'COP $120–200M / grupo',
    amountMinM: 120,
    deadlineText: 'Piloto Q2 2026',
    startQuarter: 2,
    criteria: [
      { label: 'Alineación', pts: 2 },
      { label: 'Escalabilidad', pts: 2 },
      { label: 'Cap. pago', pts: 1 },
      { label: 'Relacional', pts: 1 },
      { label: 'Sostenibilidad', pts: 1 },
    ],
    rfpUrl: 'https://acepcolombia.org',
    reasoning:
      'Segmento estable de ingresos. Bajo costo de entrada. Crea demanda de Red aeioTU + ConecTU (sostenibilidad digital).',
  },
  {
    id: 'icbf-men-politica',
    title: 'Estándares de Calidad en Primera Infancia: aeioTU + ICBF + MEN',
    score: 8,
    decision: 'go',
    category: 'politica',
    tags: [
      { label: 'Política Pública', cls: 'tag-window' },
      { label: 'Incidencia', cls: 'tag-capital' },
      { label: 'ICBF + MEN + GIZ', cls: 'tag-source' },
    ],
    description:
      'Gobierno actualiza marcos de calidad en primera infancia (CERO A SIEMPRE, estándares ICBF, orientaciones MEN 2026). Busca socio técnico para diseñar guías de formación docente, operación CDI, modalidades familiar e institucional, y medición con ConecTU.',
    actions: [
      { step: 1, text: 'Acercamiento directo a ICBF y DNP en Q1 2026.' },
      { step: 2, text: 'Propuesta de co-diseño: guías + seminarios en 10 regiones.' },
      { step: 3, text: 'Posicionamiento como voz autorizada en política pública.' },
    ],
    organization: {
      name: 'Instituto Colombiano de Bienestar Familiar (ICBF)',
      website: 'https://www.icbf.gov.co',
      email: 'atencionalciudadano@icbf.gov.co',
      linkedin: 'https://www.linkedin.com/company/icbf-colombia/',
      verified: true,
    },
    ceo: {
      name: 'Por verificar',
      title: 'Director(a) General del ICBF',
      email: 'direccion.general@icbf.gov.co',
      linkedin: 'https://www.linkedin.com/search/results/people/?keywords=Director%20General%20ICBF%20Colombia',
      verified: false,
    },
    ally: {
      name: 'GIZ Colombia',
      website: 'https://www.giz.de/en/worldwide/12348.html',
      email: 'giz-kolumbien@giz.de',
      verified: false,
      role: 'Cooperación técnica',
    },
    amountCOP: 'COP $200–350M',
    amountMinM: 200,
    deadlineText: 'Convocatoria 2026',
    startQuarter: 1,
    criteria: [
      { label: 'Sistémico', pts: 2 },
      { label: 'Legitimidad', pts: 2 },
      { label: 'Ciclos pol.', pts: 1 },
      { label: 'Expansión int\'l', pts: 2 },
      { label: 'Rapidez', pts: 1 },
    ],
    rfpUrl: 'https://www.icbf.gov.co/',
    reasoning:
      'Posiciona a aeioTU como voz autorizada en política pública. Acceso a datos de impacto nacional. Base para relaciones internacionales (BID, GIZ).',
  },
]
