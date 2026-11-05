"""
Generador de datos del Sistema de Bonos (esquema OS / folios).

Lee los folios de Snowflake (SOLO LECTURA: un SELECT sobre CONECTA.INSTALACIONES.CIERRE_FC),
los cruza con el catálogo de técnicos y calcula por técnico y semana:
asistencias (días con ≥1 orden), folios, mantenimientos, empresariales y el bono del esquema OS.

Salida: datos_salida/bonos_os.json  (ignorado por git — contiene datos personales)

Uso:
    .venv/bin/python snowflake/generar_bonos.py            # consulta Snowflake (abre login OAuth)
    .venv/bin/python snowflake/generar_bonos.py --offline  # recalcula con el último caché local
"""
import argparse
import csv
import datetime as dt
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "esquema_os.json"
CATALOGO = ROOT / "catalogos" / "tecnicos.csv"
SALIDA = ROOT / "datos_salida"
CACHE_DIARIO = SALIDA / "snowflake_diario.csv"
CACHE_TECNICOS = SALIDA / "snowflake_tecnicos.csv"
JSON_OUT = SALIDA / "bonos_os.json"

CONEXION = "a6059471880971-qiora"
WAREHOUSE = "CARGA_WH"
EMPRESAS = ("MEGON 3", "MEGON")

# Fecha de término viene como 'DD/MM/YYYY HH:MM:SS' y a veces con saltos de línea/tabs.
FECHA_SQL = r"try_to_date(left(regexp_replace(FECHA_TERMINO,'\\s+',' '),10),'DD/MM/YYYY')"

# Categorías (igual que la columna "Servicio" del v13):
#   M = mantenimiento (Mayor/Menor) → cuenta para el mínimo de mantenimientos
#   E = empresarial con factor (Instalación Empresarial = TIPO Empresarial,
#       Soporte Empresarial = TIPO Hallazgo Empresarial). Recolección Empresarial = 1x.
#   R = resto (residencial), 1 folio
SQL_DIARIO = f"""
with base as (
  select OT,
         USUARIO_INSTALADOR as u,
         {FECHA_SQL} as f,
         case when TIPO in ('Mantenimiento Menor','Mantenimiento Mayor') then 'M'
              when TIPO in ('Empresarial','Hallazgo Empresarial') then 'E'
              else 'R' end as cat
  from CONECTA.INSTALACIONES.CIERRE_FC
  where EMPRESA_PROVEEDOR in {EMPRESAS} and USUARIO_INSTALADOR is not null
  qualify row_number() over (partition by OT, USUARIO_INSTALADOR order by {FECHA_SQL}) = 1
)
select u, f, cat, count(*) as n from base where f is not null group by 1,2,3
"""

SQL_TECNICOS = f"""
select USUARIO_INSTALADOR as u,
       mode(regexp_replace(trim(NOMBRE_TECNICO),'\\\\s+',' ')) as nombre,
       mode(DISTRITO_ORIGEN) as distrito,
       mode(TIPO_CUADRILLA) as cuadrilla,
       mode(SEGMENTO) as segmento
from CONECTA.INSTALACIONES.CIERRE_FC
where EMPRESA_PROVEEDOR in {EMPRESAS} and USUARIO_INSTALADOR is not null
group by 1
"""


def leer_snowflake():
    import snowflake.connector  # import tardío: --offline no lo necesita

    con = snowflake.connector.connect(connection_name=CONEXION, warehouse=WAREHOUSE)
    try:
        cur = con.cursor()
        cur.execute(SQL_DIARIO)
        diario = [(u, f.isoformat(), cat, int(n)) for u, f, cat, n in cur.fetchall()]
        cur.execute(SQL_TECNICOS)
        tecnicos = cur.fetchall()
    finally:
        con.close()
    SALIDA.mkdir(exist_ok=True)
    with open(CACHE_DIARIO, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["u", "f", "cat", "n"])
        w.writerows(diario)
    with open(CACHE_TECNICOS, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["u", "nombre", "distrito", "cuadrilla", "segmento"])
        w.writerows(tecnicos)


def leer_cache():
    with open(CACHE_DIARIO, encoding="utf-8") as fh:
        diario = [(r["u"], r["f"], r["cat"], int(r["n"])) for r in csv.DictReader(fh)]
    with open(CACHE_TECNICOS, encoding="utf-8") as fh:
        tecnicos = {r["u"]: r for r in csv.DictReader(fh)}
    return diario, tecnicos


def leer_catalogo():
    with open(CATALOGO, encoding="utf-8") as fh:
        return {r["usuario_ffm"].strip().upper(): r for r in csv.DictReader(fh)}


def lunes(fecha: dt.date) -> dt.date:
    return fecha - dt.timedelta(days=fecha.weekday())


def calcular_bono(cfg, suc, dias, os_tot, mant, emp, aplicar_min_mant=True):
    """Bono de una semana. Devuelve (tier, base, adicional, descuento, total, meta_alta_tier).

    tier: 0 = no llegó a Meta Base, 1 = Base, 2 = Medio, 3 = Alto.
    - Tier con folios ponderados (empresariales × factor).
    - Si la sucursal tiene mínimo de mantenimientos y lo cumple, la Meta Alta del tier se topa en 24.
    - Adicionales con folios REALES por arriba de la Meta Alta original.
    - Descuento por días trabajados sobre (tier + adicionales).
    """
    m_base, m_medio, m_alto = suc["metas"]
    alto_tier = m_alto
    if aplicar_min_mant and suc["min_mant"] > 0 and mant >= suc["min_mant"]:
        alto_tier = min(m_alto, cfg["meta_alta_con_min_mantenimiento"])
    pond = (os_tot - emp) + emp * cfg["factor_empresarial"]
    if pond >= alto_tier:
        tier = 3
    elif pond >= m_medio:
        tier = 2
    elif pond >= m_base:
        tier = 1
    else:
        tier = 0
    base = suc["bonos"][tier - 1] if tier else 0
    adicional = max(0, os_tot - m_alto) * cfg["os_adicional"] if tier else 0
    pct = 0.0
    for regla in sorted(cfg["descuento_inasistencia"], key=lambda r: r["dias_max"]):
        if dias <= regla["dias_max"]:
            pct = regla["pct"]
            break
    descuento = round((base + adicional) * pct, 2)
    return tier, base, adicional, descuento, base + adicional - descuento, alto_tier


def construir(diario, sf_tecnicos, catalogo, cfg):
    sucursales = cfg["sucursales"]
    vigente = dt.date.fromisoformat(cfg["vigente_desde"])
    fecha_max = max(dt.date.fromisoformat(f) for _, f, _, _ in diario)
    fecha_min = min(dt.date.fromisoformat(f) for _, f, _, _ in diario)

    semanas = []
    s = lunes(fecha_min)
    while s <= fecha_max:
        semanas.append(s)
        s += dt.timedelta(days=7)
    idx = {s: i for i, s in enumerate(semanas)}

    # por técnico → semana → [mask_dias, os, mant, emp]
    act = defaultdict(lambda: defaultdict(lambda: [0, 0, 0, 0]))
    for u, f, cat, n in diario:
        u = u.strip().upper()
        d = dt.date.fromisoformat(f)
        cel = act[u][idx[lunes(d)]]
        cel[0] |= 1 << d.weekday()
        cel[1] += n
        if cat == "M":
            cel[2] += n
        elif cat == "E":
            cel[3] += n

    sin_bono = set(cfg["polizas_sin_bono"])
    mapa_dist = cfg["distrito_origen_a_sucursal"]
    tecnicos = []
    for u in sorted(act):
        cat_row = catalogo.get(u)
        sf = sf_tecnicos.get(u, {})
        if cat_row:
            suc = cat_row["sucursal"]
            coord = cat_row["coordinador"].strip()
            info = dict(n=cat_row["nombre"].title(),
                        c=coord.title() if coord not in ("", "0", "#N/A") else "Sin coordinador",
                        cu=cat_row["tipo_cuadrilla"], p=cat_row["poliza"], ct=cat_row["contratista"], k=1)
        else:
            suc = mapa_dist.get((sf.get("distrito") or "").strip(), (sf.get("distrito") or "Sin distrito").strip())
            info = dict(n=(sf.get("nombre") or u).title(), c="Fuera de catálogo",
                        cu=sf.get("cuadrilla") or "", p="", ct="", k=0)
        semanas_t = []
        bonos_t = []
        for wi in sorted(act[u]):
            mask, os_tot, mant, emp = act[u][wi]
            semanas_t.append([wi, mask, os_tot, mant, emp])
            if (info["k"] and suc in sucursales and info["p"] not in sin_bono
                    and semanas[wi] >= vigente):
                dias = bin(mask).count("1")
                tier, base, adic, desc, total, alto = calcular_bono(cfg, sucursales[suc], dias, os_tot, mant, emp)
                bonos_t.append([wi, tier, base, adic, desc, total, alto])
        tecnicos.append(dict(u=u, s=suc, w=semanas_t, b=bonos_t, **info))

    # días con datos por semana (marca la semana inicial incompleta y la semana en curso)
    dias_semana = [(min(s + dt.timedelta(days=6), fecha_max) - max(s, fecha_min)).days + 1 for s in semanas]
    return dict(
        meta=dict(
            generado=dt.datetime.now().isoformat(timespec="seconds"),
            fuente="Snowflake CONECTA.INSTALACIONES.CIERRE_FC (EMPRESA_PROVEEDOR = MEGON 3 / MEGON)",
            fecha_min=fecha_min.isoformat(), fecha_max=fecha_max.isoformat(),
            vigente_desde=cfg["vigente_desde"],
            ordenes=sum(n for *_, n in diario),
        ),
        semanas=[s.isoformat() for s in semanas],
        dias_semana=dias_semana,
        sucursales={k: dict(v) for k, v in sucursales.items()},
        esquema={k: cfg[k] for k in ("factor_empresarial", "os_adicional", "meta_alta_con_min_mantenimiento",
                                      "descuento_inasistencia", "polizas_sin_bono")},
        tecnicos=tecnicos,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="no consultar Snowflake; usar el caché local")
    args = ap.parse_args()
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not args.offline:
        print("Consultando Snowflake (solo lectura)…")
        leer_snowflake()
    diario, sf_tecnicos = leer_cache()
    catalogo = leer_catalogo()
    data = construir(diario, sf_tecnicos, catalogo, cfg)
    JSON_OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    en_cat = sum(t["k"] for t in data["tecnicos"])
    print(f"✓ {JSON_OUT.relative_to(ROOT)}  ·  {len(data['tecnicos'])} técnicos ({en_cat} en catálogo)  ·  "
          f"{len(data['semanas'])} semanas  ·  {data['meta']['ordenes']:,} folios  ·  "
          f"datos al {data['meta']['fecha_max']}  ·  {JSON_OUT.stat().st_size/1e6:.1f} MB")


if __name__ == "__main__":
    main()
