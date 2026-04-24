# Sistema de Bonos QiORA — Contexto del Proyecto

## ¿Qué es esto?

Herramienta interna de QiORA para el **seguimiento, cálculo y visualización de bonos de técnicos** que trabajan para TotalPlay. QiORA es contratista de TotalPlay.

Desarrollado por: **Giacomo Primucci**, Analista de Planeación Financiera.  
Objetivo: alinear productividad y eficiencia operativa con los montos pagados en bono. La herramienta está pensada para ser usada por operaciones, finanzas y directores.

---

## Estructura organizacional

```
Técnicos (base operativa — instalan, dan soporte, mantenimiento)
    ↓
Coordinadores (~15-20 técnicos c/u — exténicos que lideran equipos)
    ↓
Líderes Distritales (operan cada distrito)
    ↓
Divisionales (operan regiones)
    ↓
Nacional
```

---

## Flujo de datos (estado actual vs. futuro)

### Proceso manual actual (en Excel)
1. Se descarga el reporte de órdenes de servicio desde **Field Cloud** (plataforma de TotalPlay)
2. Un operador limpia la base: quita duplicados de OS, elimina técnicos ajenos a QiORA
3. Se copia y pega en el archivo de **Bonos Semanales** (`Bonos BI/`), se actualiza el glosario de técnicos y se calcula todo ahí

### Flujo futuro (lo que estamos construyendo)
1. **ERP interno de QiORA** → fuente de verdad (acceso vía SQL, pendiente de recibir credenciales)
2. Código de cálculo automático (Python) → reemplaza los pasos manuales
3. **Supabase** → BD temporal mientras se da acceso al ERP real (luego se migra)
4. **Dashboard web** (`index.html`) → visualización siempre actualizada para todos los usuarios

> Los archivos `datos_entrada/`, `datos_salida/` y `glosario_técnicos.xlsx` son **temporales**. En producción todo vendrá del ERP vía SQL.

---

## Arquitectura del proyecto

```
SistemaBonos/
├── index.html                  # Dashboard web (QiORA UI) — Chart.js + Supabase JS
├── calculadora_bonos.py        # Cálculo de bonos por semana (v3.0 — EN REVISIÓN)
├── limpiador_base_datos.py     # Limpieza del reporte crudo de Field Cloud (temporal)
├── glosario_técnicos.xlsx      # Catálogo maestro de técnicos (temporal → vendrá del ERP)
├── datos_entrada/              # Reportes crudos y limpios de Field Cloud (temporal)
├── datos_salida/               # Excel con bonos calculados (temporal)
└── Bonos BI/                   # Archivos Excel originales con la lógica de referencia
    ├── Bonos semanales V11.xlsx    # ← FUENTE DE VERDAD de las reglas de negocio
    └── Copia de Bonos General.xlsx
```

---

## Lógica de cálculo de bonos

### Fuente de datos por OT
- Cada Orden de Trabajo (OT) genera **puntos ("estrellas")** según su subtipo de servicio
- Se eliminan duplicados por OT antes de calcular
- Puntos de referencia: Instalación=6, Soporte=3, Mantenimiento Mayor=4, Mantenimiento Menor=3, Empresarial=8, Recolección=1, Factibilidad=1, Cambio de Domicilio=6, etc.

### Variables por técnico
- **Distrito** (17 en total, tipos A / B / C)
- **Tipo de cuadrilla**: Normal, Moto, Híbrida, Elite, Multidistrito
- **Meta semanal**: varía por distrito + tipo de cuadrilla
- **Total de estrellas** acumuladas en la semana
- **Días trabajados** / **Inasistencias** (semana laboral = 6 días)

### Estructura de bonos (extraída de los Excel de referencia)

| Tipo Distrito | 80–89% meta | 90–99% meta | 100%+ meta |
|---------------|-------------|-------------|------------|
| A             | $500        | $900        | $2,500     |
| B             | $450        | $800        | $1,800     |
| C             | $300        | $700        | $1,400     |

### Bono extra por estrellas adicionales

> ⚠️ Esta regla fue corregida el 17-abr-2026. La implementación anterior estaba equivocada.

- **Tipo A**: $500 fijo si alcanza **≥110%** de meta (trigger en 110%, no en 100%)
- **Tipo B/C**: desde el **100% de meta**, se cuentan las estrellas por encima de la meta base:
  - $100 por cada bloque de 6 estrellas extra
  - Tope máximo: $500
  - Las estrellas extra se calculan como `total_estrellas - meta_semanal`

**Ejemplo confirmado:** Meta=84, estrellas=90 (107.1%)
- Bono base 100%+ Tipo B = $1,800
- Extra: 90−84 = 6 estrellas → 1 bloque × $100 = $100
- **Total = $1,900**

### Descuentos por inasistencia

- Aplica solo en algunos distritos (7 distritos con penalización, resto = 0%)
- 1 inasistencia = 50% del bono total
- 2+ inasistencias = 100% del bono total (pierde todo el bono)
- El descuento se aplica sobre (Bono Base + Bono Extra)

### Regla de asistencia semanal

> ⚠️ Corregida el 17-abr-2026. El domingo ya NO es descanso fijo.

- Semana laboral = **lunes a domingo** (7 días)
- Cada técnico tiene derecho a **1 día de descanso por semana** (cualquier día)
- Para considerar un día como trabajado: debe tener **≥1 OS completada** ese día
- Si en la semana tiene **más de 1 día sin OS** → los días extra sin OS son **falta**
- Cálculo: `faltas = max(0, días_sin_OS_en_período_activo - 1)` por semana

### Regla del 70% para híbridos

- Si un técnico con cuadrilla Híbrida tiene **<70%** de sus OS como mantenimiento/hallazgo → se trata como cuadrilla Normal para el cálculo de meta y bono

### Estado del cálculo

> `calculadora_bonos.py` tiene múltiples errores y está **descontinuado**. El cálculo definitivo se implementará directamente en el dashboard JS cuando se conecte al ERP.

---

## Dashboard (`index.html`)

App web de una sola página (SPA). Sin framework — HTML/CSS/JS puro.

### Vistas disponibles
| Vista | Descripción |
|-------|-------------|
| Nacional | KPIs globales, gráficas de bonos y productividad por semana |
| Distritos | Lista y detalle por distrito: tendencia, top técnicos, distribución de OS |
| Coordinadores | Vista por coordinador: ranking de su equipo, tendencia |
| Técnicos | Ficha individual: heatmap de asistencia, desglose de bono, historial |
| Cálculo de Bonos | (En construcción) |
| Ajustes | (En construcción) |

### Stack técnico
- **Chart.js** — gráficas
- **SheetJS (xlsx)** — lectura de Excel en el navegador
- **Supabase JS** — backend temporal (auth + base de datos)
- Fuente: Inter (Google Fonts)
- Paleta de marca: naranja QiORA (`#E85420`)

### Datos
- Actualmente se cargan subiendo un Excel manualmente o desde Supabase
- En producción: datos siempre actualizados desde el ERP vía SQL

### Funcionalidades implementadas en el dashboard (al 21-abr-2026)

**Drill-down de auditoría:**
- Vista Nacional → tabla "Análisis por Nivel de Alcance": clic en cada bracket (100%+, 90-99%, 80-89%, <80%) abre modal con todos los técnicos de ese bracket, columnas ordenables
- Vista Nacional → tabla "Distribución de Inasistencias": clic en cada fila abre modal con desglose de técnicos
- Vista Distrito → gráfica de inasistencias: barras clickeables + tabla resumen con drill-down por bucket
- Todos los drill-downs respetan los filtros activos (cuadrilla, semana, distrito)

**Ordenamiento:**
- Top 10 técnicos del distrito: siempre descendente (mejor primero) según el dropdown seleccionado
- Top coordinadores del distrito: ordenados por mayor productividad promedio (OS/día), descendente
- Ranking de técnicos del coordinador: al abrir un coordinador siempre reinicia en % meta descendente

**Top coordinadores por distrito:**
- Columna "Cuadrillas" agregada (técnicos a cargo)
- Productividad calculada y mostrada como OS/cuadrilla/día (÷6)
- Ampliado a top 10 (antes era 7)

**Productividad:** todos los KPIs de productividad muestran OS/cuadrilla/día

**Logo:** sidebar muestra "QiORA / Bonos Técnicos" (antes decía "TotalPlay")

---

## Seguridad y usuarios (roadmap)

- Sistema de login con usuarios generados por Giacomo
- Roles y permisos según puesto:
  - **Coordinador**: solo ve a sus propios técnicos
  - **Líder distrital**: ve su distrito completo
  - **Finanzas / Directores**: acceso total
- Sin usuario válido = sin acceso a ningún dato
- Plataforma de gestión de usuarios a cargo del analista

---

## Tareas pendientes (al 17 de abril 2026)

- [ ] Conectar al ERP interno vía SQL (pendiente de credenciales)
- [ ] Completar vistas "Cálculo" y "Config" del dashboard
- [ ] Implementar sistema de autenticación y roles en Supabase
- [ ] Migrar de Supabase temporal al ERP real cuando esté disponible
- [ ] Hacer datos del dashboard siempre actualizados (sin carga manual)
- [ ] Seguir afinando reglas de cálculo en el JS del dashboard contra los Excel de `Bonos BI/`

## Reglas ya confirmadas y corregidas

| Fecha | Regla | Corrección |
|-------|-------|------------|
| 17-abr-2026 | Bono extra Tipo B/C | Trigger en 100% (no 110%); estrellas extra desde meta base, no desde umbral 110% |
| 17-abr-2026 | Bono extra Tipo A | $500 fijo si alcanza ≥110% de meta — nada más, sin escala por estrellas |
| 17-abr-2026 | Asistencia semanal | Descanso no es fijo en domingo; 1 día libre por semana (cualquier día); días extra sin OS = falta |

---

## Glosario

| Término | Significado |
|---------|-------------|
| OS / OT | Orden de Servicio / Orden de Trabajo |
| Estrellas | Puntos que acumula un técnico por OS completadas |
| Meta semanal | Número de estrellas que debe alcanzar para ganar bono |
| Field Cloud | Plataforma de TotalPlay desde donde se descargan los reportes |
| Cuadrilla | Tipo de técnico según su modalidad de trabajo |
| Híbrido | Técnico que mezcla instalaciones y mantenimientos |
| Hallazgo | OS detectada proactivamente por el técnico (cuenta como mantenimiento) |
| ERP | Sistema interno de QiORA (fuente de verdad en producción) |
