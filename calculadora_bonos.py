"""
🎯 SISTEMA DE CÁLCULO DE BONOS v3.0
ACTUALIZACIONES v3.0:
✓ Reglas exactas extraídas del archivo real de bonos
✓ Bonos escalonados: 80-89%, 90-99%, 100%+
✓ Bono 110% Tipo A: $500 fijo
✓ Bono 110% Tipo B/C: $100 por cada 6 estrellas (tope $500)
✓ Descuentos por inasistencia según distrito
✓ Semana laboral = 6 días
✓ Regla del 70% para técnicos híbridos
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 🔧 CONFIGURACIÓN - EDITA AQUÍ
# ============================================================================
ARCHIVO_ENTRADA = 'Limpio_reporteCierre Sem3.xlsx'
ARCHIVO_SALIDA = 'bonos_calculados.xlsx'

RUTA_ENTRADA = os.path.join('datos_entrada', ARCHIVO_ENTRADA)
RUTA_SALIDA = os.path.join('datos_salida', ARCHIVO_SALIDA)

DIAS_SEMANA_LABORAL = 6

# ============================================================================
# 📅 SEMANAS A PROCESAR
# ============================================================================
SEMANAS_PERSONALIZADAS = [
    {'nombre': 'Semana 1', 'fecha_inicio': '2025-12-29', 'fecha_fin': '2026-01-04'},
    {'nombre': 'Semana 2', 'fecha_inicio': '2026-01-05', 'fecha_fin': '2026-01-11'},
    {'nombre': 'Semana 3', 'fecha_inicio': '2026-01-12', 'fecha_fin': '2026-01-18'},
    {'nombre': 'Semana 4', 'fecha_inicio': '2026-01-19', 'fecha_fin': '2026-01-25'},
]

# ============================================================================
# 📊 METAS POR DISTRITO (Extraídas del archivo real)
# ============================================================================
METAS_DISTRITO = {
    'GS2-BAJ-IRA IRAPUATO': {
        'tipo_distrito': 'B',
        'Normal': 75,
        'Moto': 60,
        'Hibrida': 75,
        'Elite': 75,
        'Multidistrito': 75,
    },
    'GS2-BAJ-LON LEON': {
        'tipo_distrito': 'B',
        'Normal': 75,
        'Moto': 70,
        'Hibrida': 75,
        'Elite': 75,
        'Multidistrito': 75,
    },
    'GS2-OCC-COL COLIMA': {
        'tipo_distrito': 'B',
        'Normal': 90,
        'Moto': 70,
        'Hibrida': 90,
        'Elite': 90,
        'Multidistrito': 90,
    },
    'GS2-OCC-GDL BARRANCA': {
        'tipo_distrito': 'A',
        'Normal': 90,
        'Moto': 70,
        'Hibrida': 90,
        'Elite': 90,
        'Multidistrito': 90,
    },
    'GS2-OCC-GDL ESTADIO': {
        'tipo_distrito': 'A',
        'Normal': 90,
        'Moto': 60,
        'Hibrida': 90,
        'Elite': 90,
        'Multidistrito': 90,
    },
    'GS2-OCC-GDL LOPEZ MATEOS': {
        'tipo_distrito': 'A',
        'Normal': 75,
        'Moto': 60,
        'Hibrida': 75,
        'Elite': 75,
        'Multidistrito': 75,
    },
    'GS2-OCC-GDL PRIMAVERA': {
        'tipo_distrito': 'A',
        'Normal': 90,
        'Moto': 60,
        'Hibrida': 90,
        'Elite': 90,
        'Multidistrito': 90,
    },
    'GS2-OCC-MOR MORELIA': {
        'tipo_distrito': 'B',
        'Normal': 84,
        'Moto': 70,
        'Hibrida': 84,
        'Elite': 84,
        'Multidistrito': 84,
    },
    'GS2-OCC-TEP TEPIC': {
        'tipo_distrito': 'B',
        'Normal': 84,
        'Moto': 70,
        'Hibrida': 84,
        'Elite': 84,
        'Multidistrito': 84,
    },
    'GS2-SUR-CUN CANCUN 1': {
        'tipo_distrito': 'B',
        'Normal': 84,
        'Moto': 70,
        'Hibrida': 84,
        'Elite': 84,
        'Multidistrito': 84,
    },
    'GS2-OTE-CBA CORDOBA ORIZABA': {
        'tipo_distrito': 'B',
        'Normal': 75,
        'Moto': 60,
        'Hibrida': 75,
        'Elite': 75,
        'Multidistrito': 75,
    },
    'GS2-OTE-PUE PUEBLA': {
        'tipo_distrito': 'B',
        'Normal': 84,
        'Moto': 70,
        'Hibrida': 84,
        'Elite': 84,
        'Multidistrito': 84,
    },
    'GS2-OTE-VER VERACRUZ': {
        'tipo_distrito': 'B',
        'Normal': 84,
        'Moto': 70,
        'Hibrida': 84,
        'Elite': 84,
        'Multidistrito': 84,
    },
    'GS2-OTE-XAL XALAPA': {
        'tipo_distrito': 'B',
        'Normal': 84,
        'Moto': 70,
        'Hibrida': 84,
        'Elite': 84,
        'Multidistrito': 84,
    },
    'GS2-OCC-AGS AGUASCALIENTES': {
        'tipo_distrito': 'B',
        'Normal': 84,
        'Moto': 70,
        'Hibrida': 84,
        'Elite': 84,
        'Multidistrito': 84,
    },
    'GS2-SUR-TUX TUXTLA': {
        'tipo_distrito': 'B',
        'Normal': 84,
        'Moto': 70,
        'Hibrida': 84,
        'Elite': 84,
        'Multidistrito': 84,
    },
    'GS2-SUR-MER MERIDA': {
        'tipo_distrito': 'B',
        'Normal': 84,
        'Moto': 70,
        'Hibrida': 84,
        'Elite': 84,
        'Multidistrito': 84,
    },
}

# ============================================================================
# 💰 BONOS BASE POR NIVEL (Extraídos del archivo real)
# ============================================================================
BONOS_BASE = {
    'A': {
        '80-89': 500,
        '90-99': 900,
        '100+': 2500,
    },
    'B': {
        '80-89': 450,
        '90-99': 800,
        '100+': 1800,
    },
    'C': {
        '80-89': 300,
        '90-99': 700,
        '100+': 1400,
    },
}

# ============================================================================
# 📉 DESCUENTOS POR INASISTENCIA (Extraídos del archivo real)
# ============================================================================
DESCUENTOS_DISTRITO = {
    # Distritos con descuento (50%-100%)
    'GS2-BAJ-IRA IRAPUATO': {1: 0.50, 2: 1.00, 3: 1.00},
    'GS2-BAJ-LON LEON': {1: 0.50, 2: 1.00, 3: 1.00},
    'GS2-OCC-GDL BARRANCA': {1: 0.50, 2: 1.00, 3: 1.00},
    'GS2-OCC-GDL ESTADIO': {1: 0.50, 2: 1.00, 3: 1.00},
    'GS2-OCC-GDL LOPEZ MATEOS': {1: 0.50, 2: 1.00, 3: 1.00},
    'GS2-OCC-GDL PRIMAVERA': {1: 0.50, 2: 1.00, 3: 1.00},
    
    # Distritos sin descuento (0%)
    'GS2-OCC-COL COLIMA': {1: 0, 2: 0, 3: 0},
    'GS2-OCC-MOR MORELIA': {1: 0, 2: 0, 3: 0},
    'GS2-OCC-TEP TEPIC': {1: 0, 2: 0, 3: 0},
    'GS2-SUR-CUN CANCUN 1': {1: 0, 2: 0, 3: 0},
    'GS2-OTE-CBA CORDOBA ORIZABA': {1: 0, 2: 0, 3: 0},
    'GS2-OTE-PUE PUEBLA': {1: 0, 2: 0, 3: 0},
    'GS2-OTE-VER VERACRUZ': {1: 0, 2: 0, 3: 0},
    'GS2-OTE-XAL XALAPA': {1: 0, 2: 0, 3: 0},
    'GS2-OCC-AGS AGUASCALIENTES': {1: 0, 2: 0, 3: 0},
    'GS2-SUR-TUX TUXTLA': {1: 0, 2: 0, 3: 0},
    'GS2-SUR-MER MERIDA': {1: 0, 2: 0, 3: 0},
}

# ============================================================================
# 🔧 FUNCIONES AUXILIARES
# ============================================================================

def obtener_meta(distrito, tipo_cuadrilla):
    """Obtiene la meta semanal según distrito y tipo de cuadrilla"""
    if distrito not in METAS_DISTRITO:
        print(f"⚠️  Distrito no reconocido: {distrito}, usando meta por defecto")
        return 84  # Meta por defecto
    
    distrito_info = METAS_DISTRITO[distrito]
    
    if tipo_cuadrilla in distrito_info:
        return distrito_info[tipo_cuadrilla]
    else:
        # Por defecto usar Normal
        return distrito_info.get('Normal', 84)

def obtener_tipo_distrito(distrito):
    """Obtiene el tipo de distrito (A, B, o C)"""
    if distrito not in METAS_DISTRITO:
        return 'B'  # Por defecto
    
    return METAS_DISTRITO[distrito].get('tipo_distrito', 'B')

def calcular_bono_base(porcentaje_meta, tipo_distrito):
    """Calcula el bono base según el porcentaje de meta alcanzado"""
    if tipo_distrito not in BONOS_BASE:
        tipo_distrito = 'B'  # Por defecto
    
    bonos = BONOS_BASE[tipo_distrito]
    
    if porcentaje_meta < 80:
        return 0
    elif 80 <= porcentaje_meta < 90:
        return bonos['80-89']
    elif 90 <= porcentaje_meta < 100:
        return bonos['90-99']
    else:  # >= 100%
        return bonos['100+']

def calcular_bono_110(porcentaje_meta, total_estrellas, meta_semanal, tipo_distrito):
    """Calcula el bono adicional al 110% según tipo de distrito"""
    if porcentaje_meta < 110:
        return 0
    
    if tipo_distrito == 'A':
        # Tipo A: $500 fijo
        return 500
    else:
        # Tipo B y C: $100 por cada 6 estrellas adicionales (tope $500)
        estrellas_extra = total_estrellas - meta_semanal
        bloques_de_6 = int(estrellas_extra // 6)
        bono = bloques_de_6 * 100
        return min(bono, 500)  # Tope máximo $500

def obtener_descuento(distrito, inasistencias):
    """Obtiene el % de descuento según distrito e inasistencias"""
    if distrito not in DESCUENTOS_DISTRITO:
        return 0  # Sin descuento por defecto
    
    descuentos = DESCUENTOS_DISTRITO[distrito]
    
    # Si tiene 3+ inasistencias, usar el descuento de 3
    inasist_key = min(inasistencias, 3)
    
    if inasist_key == 0:
        return 0
    
    return descuentos.get(inasist_key, 0)

def formatear_dia(fecha):
    """Formatea fecha como '05 Lun'"""
    dias_sem = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    dia_num = fecha.strftime('%d')
    dia_sem = dias_sem[fecha.weekday()]
    return f"{dia_num} {dia_sem}"

# ============================================================================
# 📊 PROCESAR SEMANAS
# ============================================================================

def procesar_semanas(df):
    print("\n💰 Procesando bonos por semana...")
    
    # Detectar nombre de columna de fecha
    fecha_col = None
    for col in df.columns:
        if col.lower() == 'fecha termino':
            fecha_col = col
            break
    
    if not fecha_col:
        raise ValueError("No se encontró columna 'Fecha Termino'")
    
    df['Fecha Termino'] = pd.to_datetime(df[fecha_col])
    df['Fecha'] = df['Fecha Termino'].dt.date
    
    # Usar distrito del glosario
    dist_col = 'Distrito_Glosario' if 'Distrito_Glosario' in df.columns else 'Distrito'
    
    print(f"   📅 {len(SEMANAS_PERSONALIZADAS)} semanas configuradas")
    print(f"   📍 Usando distrito de: {dist_col}")
    
    resultados = {}
    
    for idx, sem in enumerate(SEMANAS_PERSONALIZADAS, 1):
        nombre = sem['nombre']
        fi = pd.to_datetime(sem['fecha_inicio']).date()
        ff = pd.to_datetime(sem['fecha_fin']).date()
        
        print(f"\n   [{idx}/{len(SEMANAS_PERSONALIZADAS)}] {nombre}: {fi} al {ff}")
        
        df_s = df[(df['Fecha'] >= fi) & (df['Fecha'] <= ff)].copy()
        if len(df_s) == 0:
            print(f"      ⚠️  Sin datos")
            continue
        
        print(f"      ✓ {len(df_s):,} órdenes")
        
        # ============================================================
        # PROCESAR ESTRELLAS POR DÍA
        # ============================================================
        
        # Cada OT genera puntos, NO sumar por técnico/día primero
        df_s['Fecha'] = df_s['Fecha Termino'].dt.date
        df_s['DiaSem'] = df_s['Fecha Termino'].dt.weekday
        
        dias_u = sorted(df_s['Fecha'].unique())
        dias_map = {pd.to_datetime(d).weekday(): formatear_dia(pd.to_datetime(d)) for d in dias_u}
        
        # Pivot directo - cada fila es una OT con sus puntos
        piv = df_s.pivot_table(
            index=['Usuario para pago', 'Tecnico'],
            columns='DiaSem',
            values='PUNTOS',
            aggfunc='sum',  # Sumar puntos por técnico/día
            fill_value=0
        ).reset_index()
        
        piv.rename(columns={i: dias_map.get(i, f"D{i}") for i in range(7)}, inplace=True)
        for dc in dias_map.values():
            if dc not in piv.columns:
                piv[dc] = 0
        
        # ============================================================
        # APLICAR REGLA DEL 70% PARA TÉCNICOS HÍBRIDOS
        # ============================================================
        
        # Contar OS totales y OS de mantenimiento/hallazgo
        os_stats = df_s.groupby(['Usuario para pago', 'Tecnico']).agg({
            'OS': 'count',
            'Tipo_Cuadrilla_Normalizado': lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0],
            dist_col: lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0],
        }).reset_index()
        
        os_stats.columns = ['ID_Tecnico', 'Nombre_Tecnico', 'Total_OS', 'TC_Glosario', 'Dist_Glosario']
        
        # Contar OS de mantenimiento/hallazgo
        es_mtto_hallazgo = (
            (df_s['Servicio'].str.contains('Mantenimiento', case=False, na=False)) |
            (df_s['Es_Hallazgo'] == True)
        )
        
        mtto_hallazgo_count = df_s[es_mtto_hallazgo].groupby(['Usuario para pago', 'Tecnico']).size().reset_index(name='OS_Mtto_Hallazgo')
        
        os_stats = os_stats.merge(mtto_hallazgo_count, left_on=['ID_Tecnico', 'Nombre_Tecnico'],
                                  right_on=['Usuario para pago', 'Tecnico'], how='left')
        os_stats['OS_Mtto_Hallazgo'] = os_stats['OS_Mtto_Hallazgo'].fillna(0)
        
        # Calcular porcentaje
        os_stats['Porcentaje_Mtto'] = (os_stats['OS_Mtto_Hallazgo'] / os_stats['Total_OS'] * 100).fillna(0)
        
        # Aplicar regla del 70%
        def aplicar_regla_70(row):
            if row['TC_Glosario'] == 'Hibrida':
                if row['Porcentaje_Mtto'] >= 70:
                    return 'Hibrida'
                else:
                    return 'Normal'
            else:
                return row['TC_Glosario']
        
        os_stats['Tipo_Cuadrilla_Final'] = os_stats.apply(aplicar_regla_70, axis=1)
        
        info = os_stats[['ID_Tecnico', 'Nombre_Tecnico', 'Total_OS', 'TC_Glosario',
                        'Dist_Glosario', 'Porcentaje_Mtto', 'Tipo_Cuadrilla_Final']].copy()
        
        # Merge con pivot
        res = info.merge(piv, left_on=['ID_Tecnico', 'Nombre_Tecnico'],
                        right_on=['Usuario para pago', 'Tecnico'], how='left')
        res.drop(['Usuario para pago', 'Tecnico'], axis=1, errors='ignore', inplace=True)
        
        cols_dias = sorted([c for c in res.columns if any(d in c for d in dias_map.values())])
        
        # Cálculos de bonos
        res['Total_Estrellas'] = res[cols_dias].sum(axis=1)
        res['Dias_Trabajados'] = (res[cols_dias] > 0).sum(axis=1)
        res['Inasistencias'] = (DIAS_SEMANA_LABORAL - res['Dias_Trabajados']).clip(lower=0)
        
        res['Distrito'] = res['Dist_Glosario']
        
        # Obtener meta según tipo final
        res['Meta_Semanal'] = res.apply(
            lambda r: obtener_meta(r['Distrito'], r['Tipo_Cuadrilla_Final']), axis=1
        )
        
        res['Tipo_Distrito'] = res['Distrito'].apply(obtener_tipo_distrito)
        res['Porcentaje_Meta'] = (res['Total_Estrellas'] / res['Meta_Semanal'] * 100).round(1)
        
        # Bono base
        res['Bono_Base'] = res.apply(
            lambda r: calcular_bono_base(r['Porcentaje_Meta'], r['Tipo_Distrito']), axis=1
        ).round(2)
        
        # Bono 110%
        res['Bono_110'] = res.apply(
            lambda r: calcular_bono_110(r['Porcentaje_Meta'], r['Total_Estrellas'],
                                       r['Meta_Semanal'], r['Tipo_Distrito']), axis=1
        ).round(2)
        
        # Descuento por inasistencias
        res['Descuento_%'] = res.apply(
            lambda r: obtener_descuento(r['Distrito'], r['Inasistencias']), axis=1
        )
        
        res['Descuento_Monto'] = ((res['Bono_Base'] + res['Bono_110']) * res['Descuento_%']).round(2)
        res['Bono_Final'] = (res['Bono_Base'] + res['Bono_110'] - res['Descuento_Monto']).clip(lower=0).round(2)
        
        # Resumen
        hibridos_70 = len(res[(res['TC_Glosario'] == 'Hibrida') & (res['Tipo_Cuadrilla_Final'] == 'Hibrida')])
        hibridos_normal = len(res[(res['TC_Glosario'] == 'Hibrida') & (res['Tipo_Cuadrilla_Final'] == 'Normal')])
        
        print(f"      ✓ {len(res):,} técnicos procesados")
        if hibridos_70 > 0 or hibridos_normal > 0:
            print(f"      📊 Híbridos: {hibridos_70} cumplieron 70% | {hibridos_normal} como Normal")
        
        resultados[nombre] = {'datos': res, 'fi': fi, 'ff': ff, 'cols_dias': cols_dias}
    
    return resultados

# ============================================================================
# 📝 GENERAR EXCEL
# ============================================================================

def generar_excel(resultados):
    print("\n📝 Generando Excel...")
    
    if not resultados or len(resultados) == 0:
        print("⚠️  No hay datos para generar Excel")
        return
    
    # Hoja RESUMEN
    resumen_gral = []
    for nom, dat in resultados.items():
        r = dat['datos']
        por_dist = r.groupby('Distrito').agg({
            'ID_Tecnico': 'count',
            'Bono_Final': ['sum', lambda x: (x > 0).sum()],
            'Total_Estrellas': 'sum',
            'Total_OS': 'sum',
            'Inasistencias': 'sum',
        }).reset_index()
        por_dist.columns = ['Distrito', 'Tecs_Activos', 'Bono_Total', 'Tecs_Con_Bono', 'Total_Estrellas', 'Total_OS', 'Total_Inasist']
        por_dist['Cobertura_%'] = (por_dist['Tecs_Con_Bono'] / por_dist['Tecs_Activos'] * 100).round(1)
        por_dist['Semana'] = nom
        resumen_gral.append(por_dist)
    
    if len(resumen_gral) == 0:
        print("⚠️  No hay datos de resumen")
        return
    
    df_resumen = pd.concat(resumen_gral, ignore_index=True)
    df_resumen = df_resumen[['Semana', 'Distrito', 'Tecs_Activos', 'Tecs_Con_Bono', 'Cobertura_%', 'Total_OS', 'Total_Estrellas', 'Total_Inasist', 'Bono_Total']]
    
    with pd.ExcelWriter(RUTA_SALIDA, engine='openpyxl') as w:
        df_resumen.to_excel(w, sheet_name='RESUMEN', index=False)
        print(f"   ✅ Hoja RESUMEN: {len(df_resumen)} registros")
        
        for nom, dat in resultados.items():
            r = dat['datos']
            cols_dias = dat['cols_dias']
            
            cols_ord = ['ID_Tecnico', 'Nombre_Tecnico', 'Distrito', 'TC_Glosario',
                       'Tipo_Cuadrilla_Final', 'Porcentaje_Mtto', 'Total_OS'] + cols_dias + [
                'Total_Estrellas', 'Meta_Semanal', 'Porcentaje_Meta', 'Tipo_Distrito',
                'Dias_Trabajados', 'Inasistencias', 'Bono_Base', 'Bono_110',
                'Descuento_%', 'Descuento_Monto', 'Bono_Final'
            ]
            
            hoja = nom[:31]
            r[cols_ord].sort_values('Bono_Final', ascending=False).to_excel(w, sheet_name=hoja, index=False)
            print(f"   ✅ Hoja {hoja}")
    
    print(f"\n💾 Guardado en: {RUTA_SALIDA}")

# ============================================================================
# 🚀 MAIN
# ============================================================================

def main():
    print("\n" + "="*80)
    print("🎯 SISTEMA DE BONOS v3.0")
    print("="*80)
    print("\nREGLAS v3.0 (Extraídas del archivo real):")
    print("✓ Bonos escalonados: 80-89%, 90-99%, 100%+")
    print("✓ Bono 110% Tipo A: $500 fijo")
    print("✓ Bono 110% Tipo B/C: $100 por cada 6 estrellas (tope $500)")
    print("✓ Descuentos por distrito: 0%, 50%, 100%")
    print("✓ Regla 70% para técnicos híbridos")
    print("✓ Semana laboral = 6 días")
    
    try:
        if not os.path.exists('datos_salida'):
            os.makedirs('datos_salida')
        
        print(f"\n📂 Cargando: {RUTA_ENTRADA}")
        df = pd.read_excel(RUTA_ENTRADA)
        
        print(f"✅ {len(df):,} registros - Sin duplicados por OT")
        
        # Mostrar fechas disponibles
        fecha_col = None
        for col in df.columns:
            if col.lower() == 'fecha termino':
                fecha_col = col
                break
        
        if fecha_col:
            df['Fecha Termino'] = pd.to_datetime(df[fecha_col])
            fecha_min = df['Fecha Termino'].min()
            fecha_max = df['Fecha Termino'].max()
            print(f"\n📅 Fechas disponibles:")
            print(f"   Desde: {fecha_min.strftime('%Y-%m-%d')} ({fecha_min.strftime('%A')})")
            print(f"   Hasta: {fecha_max.strftime('%Y-%m-%d')} ({fecha_max.strftime('%A')})")
        
        resultados = procesar_semanas(df)
        generar_excel(resultados)
        
        print("\n" + "="*80)
        print("✅ PROCESO COMPLETADO")
        print("="*80)
        
        # Resumen
        if resultados:
            print(f"\n📊 RESUMEN:")
            for nom, dat in resultados.items():
                r = dat['datos']
                total_bonos = r['Bono_Final'].sum()
                total_tecs = len(r)
                tecs_con_bono = (r['Bono_Final'] > 0).sum()
                print(f"   {nom}: {total_tecs} técnicos | {tecs_con_bono} con bono | Total: ${total_bonos:,.2f}")
        
        print(f"\n📁 Archivo generado: {RUTA_SALIDA}")
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
    input("\nPresiona ENTER para salir...")