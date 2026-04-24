"""
🧹 LIMPIADOR DE BASE DE DATOS v2.0 - Sistema de Bonos

MEJORAS v2.0:
✓ Integración con glosario de técnicos
✓ Asignación de distrito por glosario (no por archivo)
✓ Cross-check de técnicos no encontrados
✓ Conversión correcta de fechas (dd/mm/yyyy)
✓ Eliminación de duplicados por OT
✓ Detección de hallazgos en columna Cuenta

═══════════════════════════════════════════════════════════════════════════════
📝 CONFIGURACIÓN - EDITA AQUÍ:
═══════════════════════════════════════════════════════════════════════════════
"""

import pandas as pd
import os
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 🔧 CONFIGURACIÓN DE ARCHIVOS - EDITA LÍNEAS 25-28
# ============================================================================

# Archivo descargado de la plataforma (crudo)
ARCHIVO_ENTRADA = 'reporteCierre Sem3.xlsx'

# Archivo glosario de técnicos (maestro)
ARCHIVO_GLOSARIO = 'glosario_técnicos.xlsx'

# El archivo limpio se generará automáticamente como: Limpio_reporteCierre_5-ene.xlsx
ARCHIVO_SALIDA = f'Limpio_{ARCHIVO_ENTRADA}'

# Rutas (NO EDITAR)
RUTA_ENTRADA = os.path.join('datos_entrada', ARCHIVO_ENTRADA)
RUTA_GLOSARIO = ARCHIVO_GLOSARIO  # En la raíz de SistemaBonos
RUTA_SALIDA = os.path.join('datos_entrada', ARCHIVO_SALIDA)

# ============================================================================
# ⭐ PONDERACIÓN DE ESTRELLAS POR TIPO DE SERVICIO
# ============================================================================

PONDERACION_TIPO_OS = {
    'Instalación': 4,
    'Soporte': 2,
    'Mantenimiento Mayor': 3,
    'Mantenimiento Menor': 2,
    'Addons': 2,
    'Cambio De Domicilio': 3,
    'Cambio De Equipo': 2,
    'Empresarial': 5,
    'Recolección Pi': 1,
    'Recolección': 1,
    'Cambio De Plan': 2,
    'Factibilidad': 2,
    'Hallazgo Empresarial': 3,
}

# Mapeo alternativo para Tipo (más general)
MAPEO_TIPO_SERVICIO = {
    'instalacion': 'Instalación',
    'soporte': 'Soporte',
    'mantenimiento': 'Mantenimiento Mayor',
    'addon': 'Addons',
    'cambio': 'Cambio De Equipo',
    'recoleccion': 'Recolección',
    'empresarial': 'Empresarial',
}

# ============================================================================
# 📍 MAPEO DE DISTRITOS DEL ARCHIVO (para técnicos sin glosario)
# ============================================================================

MAPEO_DISTRITOS_ARCHIVO = {
    # LEON
    'LEON': 'GS2-BAJ-LON LEON',
    'LEON C': 'GS2-BAJ-LON LEON',
    
    # IRAPUATO
    'IRAPUATO D': 'GS2-BAJ-IRA IRAPUATO',
    'IRAPUATO': 'GS2-BAJ-IRA IRAPUATO',
    
    # SALAMANCA → LEON (no existe distrito Salamanca)
    'SALAMANCA D': 'GS2-BAJ-IRA IRAPUATO',
    'SALAMANCA': 'GS2-BAJ-IRA IRAPUATO',
    
    # GUANAJUATO → LEON (no existe distrito Guanajuato)
    'GUANAJUATO D': 'GS2-BAJ-LON LEON',
    'GUANAJUATO': 'GS2-BAJ-LON LEON',
    
    # GUADALAJARA (4 distritos oficiales)
    'GDL BARRANCA': 'GS2-OCC-GDL BARRANCA',
    'GDL ESTADIO': 'GS2-OCC-GDL ESTADIO',
    'GDL LOPEZ MATEOS': 'GS2-OCC-GDL LOPEZ MATEOS',
    'GDL LA PRIMAVERA': 'GS2-OCC-GDL PRIMAVERA',
    'PRIMAVERA': 'GS2-OCC-GDL PRIMAVERA',
    
    # GDL - Distritos que NO existen → mapear a existentes
    'GDL COLOMOS': 'GS2-OCC-GDL ESTADIO',  # Mapear a Estadio
    'GDL LAZARO CARDENAS': 'GS2-OCC-GDL BARRANCA',  # Mapear a Barranca
    'GDL CHAPULTEPEC': 'GS2-OCC-GDL PRIMAVERA',  # Mapear a Primavera
    
    # COLIMA
    'COLIMA D': 'GS2-OCC-COL COLIMA',
    'COLIMA': 'GS2-OCC-COL COLIMA',
    
    # VERACRUZ
    'VERACRUZ D': 'GS2-OTE-VER VERACRUZ',
    'VERACRUZ': 'GS2-OTE-VER VERACRUZ',
    
    # MORELIA
    'MORELIA D': 'GS2-OCC-MOR MORELIA',
    'MORELIA  D': 'GS2-OCC-MOR MORELIA',  # Con doble espacio
    'MORELIA': 'GS2-OCC-MOR MORELIA',
    
    # TEPIC
    'TEPIC D': 'GS2-OCC-TEP TEPIC',
    'TEPIC': 'GS2-OCC-TEP TEPIC',
    
    # CANCUN
    'CANCUN 1': 'GS2-SUR-CUN CANCUN 1',
    'CANCUN': 'GS2-SUR-CUN CANCUN 1',
    
    # CORDOBA/ORIZABA
    'CORDOBA/ORIZABA D': 'GS2-OTE-CBA CORDOBA ORIZABA',
    'CORDOBA/ORIZABA D ': 'GS2-OTE-CBA CORDOBA ORIZABA',  # Con espacio al final
    'CORDOBA': 'GS2-OTE-CBA CORDOBA ORIZABA',
    'ORIZABA': 'GS2-OTE-CBA CORDOBA ORIZABA',
    
    # PUEBLA - Varios subdistritos → PUEBLA principal
    'PUEBLA D': 'GS2-OTE-PUE PUEBLA',
    'PUEBLA': 'GS2-OTE-PUE PUEBLA',
    'PUEBLA 1 ANGELOPOLIS': 'GS2-OTE-PUE PUEBLA',
    'PUEBLA 3 LA NORIA': 'GS2-OTE-PUE PUEBLA',
    
    # XALAPA
    'XALAPA D': 'GS2-OTE-XAL XALAPA',
    'XALAPA': 'GS2-OTE-XAL XALAPA',
    
    # AGUASCALIENTES
    'AGUASCALIENTES D': 'GS2-OCC-AGS AGUASCALIENTES',
    'AGUASCALIENTES': 'GS2-OCC-AGS AGUASCALIENTES',
    
    # TUXTLA
    'TUXTLA D': 'GS2-SUR-TUX TUXTLA',
    'TUXTLA': 'GS2-SUR-TUX TUXTLA',
    
    # MERIDA
    'MERIDA D': 'GS2-SUR-MER MERIDA',
    'MERIDA': 'GS2-SUR-MER MERIDA',
    'MERIDA ORIENTE': 'GS2-SUR-MER MERIDA',
}

# ============================================================================
# 🔧 FUNCIONES AUXILIARES
# ============================================================================

def normalizar_distrito_archivo(distrito):
    """Normaliza el nombre del distrito del archivo para técnicos sin glosario"""
    if pd.isna(distrito):
        return None
    
    distrito_str = str(distrito).strip()
    distrito_upper = distrito_str.upper()
    
    # Buscar match exacto (case insensitive)
    for key, value in MAPEO_DISTRITOS_ARCHIVO.items():
        if key.upper() == distrito_upper:
            return value
    
    # Buscar match parcial
    for key, value in MAPEO_DISTRITOS_ARCHIVO.items():
        if key.upper() in distrito_upper or distrito_upper in key.upper():
            return value
    
    # Si no encuentra match, retornar None para que se pueda detectar
    print(f"         ⚠️  Distrito no reconocido: '{distrito_str}'")
    return None

def verificar_carpetas():
    """Verifica y crea carpetas necesarias"""
    if not os.path.exists('datos_entrada'):
        os.makedirs('datos_entrada')
        print("📁 Carpeta 'datos_entrada' creada")

def mapear_tipo_cuadrilla_glosario(tipo_glosario):
    """Mapea tipos de cuadrilla del glosario al sistema"""
    if pd.isna(tipo_glosario):
        return 'Normal'
    
    tipo = str(tipo_glosario).strip().upper()
    
    # Mapeo directo
    if 'PLANTA INTERNA' in tipo or tipo == 'NORMAL':
        return 'Normal'
    elif 'MOTO' in tipo:
        return 'Moto'
    elif 'HIBRIDA' in tipo or 'HÍBRIDA' in tipo:
        return 'Hibrida'
    elif 'ELITE' in tipo:
        return 'Elite'
    elif 'DOBLE TURNO' in tipo:
        return 'Normal'  # Doble turno se trata como Normal
    elif 'MULTIDISTRITO' in tipo or 'MULTI' in tipo:
        return 'Multidistrito'
    else:
        return 'Normal'  # Por defecto

def limpiar_sucursal(sucursal):
    """Limpia espacios extras en nombres de sucursales"""
    if pd.isna(sucursal):
        return None
    return str(sucursal).strip()

def obtener_puntos(tipo, subtipo):
    """
    Calcula puntos según el subtipo de servicio
    Tabla oficial de ponderaciones por subtipo
    """
    if pd.isna(subtipo):
        subtipo_val = 0
    else:
        subtipo_str = str(subtipo).strip()
        
        # Tabla de ponderaciones exacta por SUBTIPO
        PUNTOS_SUBTIPO = {
            # Addons - 2 puntos
            'Adicional': 2,
            'Wifi Extender': 2,
            'Cambio De Plan': 2,
            'Camara Web': 2,
            'Vsb': 2,
            
            # Cambio De Plan - 2 puntos
            'Instalacion Y Recoleccion': 2,
            'Upgrade. Instalacion Equipos': 2,
            
            # Cambio de domicilio - 6 puntos
            'Cambio De Domicilio Tp': 6,
            
            # Cambio de equipo - 2 puntos
            'Cambio De Equipo': 2,
            'Renovacion Tecnologica': 2,
            
            # Factibilidad - 1 punto
            'Factibilidad De Instalacion': 1,
            'Factibilidad': 1,
            'Factibilidad Cambio De Domicilio': 1,
            
            # Instalacion - 6 puntos
            'Instalación Huawei': 6,
            'Instalación Venta Tecnico': 6,
            'Instalación Zte': 6,
            'Ins Vsb': 6,
            'Venta Express': 6,
            'Instalacion Factibilidad': 6,
            
            # Instalacion Empresarial - 8 puntos
            'Instalación Ar': 8,
            'Instalación Empresarial': 8,
            
            # Mantenimiento - 3 puntos
            'Acomodo Y Tensado En Altura': 3,
            'Retiro De Acometida': 3,
            'Organización De Acometidas': 3,
            'Restauración 2n': 3,
            'Mantenimiento Residencial': 3,
            'Colocar Rotulo En La Caja': 3,
            'Validación De Potencias En 2n': 3,
            'Distribuidor': 3,
            'Depuración Orgánica': 3,
            'Mantenimiento Menor': 3,
            
            # Mantenimiento mayor - 4 puntos
            'Mantenimiento Mayor': 4,
            'Libranza De Cfe': 4,
            'Migración De Acometida': 4,
            'Levantamiento De Construcción (Aéreas Y Canalizadas)': 4,
            'Poda De Árboles': 4,
            'Red Ligera': 4,
            
            # Recoleccion - 1 punto
            'Voluntaria': 1,
            'Recolección Vsb': 1,
            'Recolección Empresarial': 1,
            'Entrega De Equipos': 1,
            'Downgrade. Recoleccion Equipos': 1,
            'Recolección Pi': 1,
            
            # Soporte - 3 puntos
            'Ticket Proactivo': 3,
            'Soporte Sin Potencia Huawei': 3,
            'Soporte Con Potencia Huawei': 3,
            'Soporte': 3,
            'Soporte Hogar Seguro': 3,
            
            # Soporte empresarial - 5 puntos
            'Configuracion Por Falla': 5,
            'Instalación Compleja': 5,
            'Validar Adecuaciones': 5,
            'Configuración Y Prueba De Servivios (Nocturno)': 5,
            'Configuración Y Prueba De Servicios': 5,
            'Instalación De Mw': 5,
            'Acometida Especial': 5,
            
            # No aplica - 0 puntos
            'Visita Fallida': 0,
            'Firma De Aceptación': 0,
        }
        
        # Buscar puntos exactos
        if subtipo_str in PUNTOS_SUBTIPO:
            return PUNTOS_SUBTIPO[subtipo_str]
        
        # Si no se encuentra exacto, buscar por similitud (case-insensitive)
        subtipo_lower = subtipo_str.lower()
        for key, value in PUNTOS_SUBTIPO.items():
            if key.lower() == subtipo_lower:
                return value
        
        subtipo_val = None
    
    # Si no se encontró por subtipo, intentar por TIPO
    if subtipo_val is None and pd.notna(tipo):
        tipo_str = str(tipo).lower()
        
        if 'instalación' in tipo_str or 'instalacion' in tipo_str:
            if 'empresarial' in tipo_str:
                return 8
            return 6
        elif 'mantenimiento mayor' in tipo_str:
            return 4
        elif 'mantenimiento' in tipo_str:
            return 3
        elif 'soporte' in tipo_str:
            if 'empresarial' in tipo_str:
                return 5
            return 3
        elif 'recolección' in tipo_str or 'recoleccion' in tipo_str:
            return 1
        elif 'factibilidad' in tipo_str:
            return 1
        elif 'cambio' in tipo_str:
            if 'domicilio' in tipo_str:
                return 6
            return 2
    
    # Por defecto
    return 2

def es_hallazgo(cuenta, tipo):
    """Identifica si una orden es un hallazgo"""
    # Verificar en la columna Cuenta
    if pd.notna(cuenta):
        cuenta_str = str(cuenta).lower()
        if 'hallazgo' in cuenta_str:
            return True
    
    # Verificar en tipo (por si acaso)
    if pd.notna(tipo):
        tipo_str = str(tipo).lower()
        if 'hallazgo' in tipo_str:
            return True
    
    return False

# ============================================================================
# 📊 CARGA DE DATOS
# ============================================================================

# ============================================================================
# 📍 MAPEO DE SUCURSALES: CTA → GS2 (Nombres viejos → nuevos)
# ============================================================================

MAPEO_CTA_A_GS2 = {
    'CTA-TPI-INT-AGS AGUASCALIENTES': 'GS2-OCC-AGS AGUASCALIENTES',
    'CTA-TPI-INT-CUN CANCUN 1': 'GS2-SUR-CUN CANCUN 1',
    'CTA-TPI-INT-CUN CANCUN': 'GS2-SUR-CUN CANCUN 1',
    'CTA-TPI-INT-COL COLIMA': 'GS2-OCC-COL COLIMA',
    'CTA-TPI-INT-CBA CORDOBA ORIZABA': 'GS2-OTE-CBA CORDOBA ORIZABA',
    'CTA-TPI-INT-CBA CORDOBA': 'GS2-OTE-CBA CORDOBA ORIZABA',
    'CTA-TPI-INT-GBA GDL BARRANCA': 'GS2-OCC-GDL BARRANCA',
    'CTA-TPI-INT-GES GDL ESTADIO': 'GS2-OCC-GDL ESTADIO',
    'CTA-TPI-INT-GLM GDL LOPEZ MATEOS': 'GS2-OCC-GDL LOPEZ MATEOS',
    'CTA-TPI-INT-GPR GDL PRIMAVERA': 'GS2-OCC-GDL PRIMAVERA',
    'CTA-TPI-INT-IRA IRAPUATO': 'GS2-BAJ-IRA IRAPUATO',
    'CTA-TPI-INT-LON LEON': 'GS2-BAJ-LON LEON',
    'CTA-TPI-INT-LEO LEON': 'GS2-BAJ-LON LEON',
    'CTA-TPI-INT-MER MERIDA': 'GS2-SUR-MER MERIDA',
    'CTA-TPI-INT-MOR MORELIA': 'GS2-OCC-MOR MORELIA',
    'CTA-TPI-INT-MTY MONTERREY': 'GS2-NTE-MTY MONTERREY',
    'CTA-TPI-INT-PUE PUEBLA': 'GS2-OTE-PUE PUEBLA',
    'CTA-TPI-INT-TEP TEPIC': 'GS2-OCC-TEP TEPIC',
    'CTA-TPI-INT-TUX TUXTLA': 'GS2-SUR-TUX TUXTLA',
    'CTA-TPI-INT-VRZ VERACRUZ': 'GS2-OTE-VER VERACRUZ',
    'CTA-TPI-INT-VER VERACRUZ': 'GS2-OTE-VER VERACRUZ',
    'CTA-TPI-INT-XAL XALAPA': 'GS2-OTE-XAL XALAPA',
}

def normalizar_sucursal_glosario(sucursal):
    """Normaliza sucursal del glosario: CTA-XXX → GS2-XXX"""
    if pd.isna(sucursal):
        return None
    
    sucursal_str = str(sucursal).strip()
    
    # Si ya es GS2, limpiar espacios y retornar
    if sucursal_str.startswith('GS2-'):
        return sucursal_str.strip()
    
    # Si es CTA, mapear a GS2
    if sucursal_str in MAPEO_CTA_A_GS2:
        return MAPEO_CTA_A_GS2[sucursal_str]
    
    # Si no encuentra match, advertir y retornar original
    print(f"         ⚠️  Sucursal no mapeada: '{sucursal_str}'")
    return sucursal_str

def cargar_glosario():
    """Carga el glosario de técnicos de la hoja 'Tecnicos'"""
    print(f"\n📚 Cargando glosario: {RUTA_GLOSARIO}")
    
    if not os.path.exists(RUTA_GLOSARIO):
        raise FileNotFoundError(
            f"\n❌ No se encontró el glosario: {RUTA_GLOSARIO}\n"
            f"   Verifica que el archivo esté en la raíz de SistemaBonos/"
        )
    
    # Leer la hoja "Tecnicos " (con espacio al final)
    xl_file = pd.ExcelFile(RUTA_GLOSARIO)
    
    # Buscar hoja que contenga "Tecnicos" (puede tener espacio al final)
    hoja_tecnicos = None
    for sheet in xl_file.sheet_names:
        if 'tecnicos' in sheet.lower().strip():
            hoja_tecnicos = sheet
            break
    
    if not hoja_tecnicos:
        raise ValueError(
            f"No se encontró la hoja 'Tecnicos' en el glosario.\n"
            f"Hojas disponibles: {', '.join(xl_file.sheet_names)}"
        )
    
    print(f"   📋 Leyendo hoja: '{hoja_tecnicos}'")
    
    # Leer con header en fila 1
    df_glosario = pd.read_excel(RUTA_GLOSARIO, sheet_name=hoja_tecnicos, header=1)
    
    # Limpiar nombres de columnas
    df_glosario.columns = df_glosario.columns.str.strip()
    
    # Seleccionar columnas necesarias
    columnas_necesarias = ['USUARIO FFM', 'SUCURSAL', 'TIPO DE CUADRILLA', 'NOMBRE DEL TÉCNICO']
    
    # Verificar que existan
    for col in columnas_necesarias:
        if col not in df_glosario.columns:
            print(f"   ⚠️  Advertencia: Columna '{col}' no encontrada")
    
    columnas_existentes = [col for col in columnas_necesarias if col in df_glosario.columns]
    df_glosario = df_glosario[columnas_existentes].copy()
    
    # Renombrar para facilitar uso
    df_glosario = df_glosario.rename(columns={
        'USUARIO FFM': 'Usuario',
        'SUCURSAL': 'Distrito_Glosario_Original',
        'TIPO DE CUADRILLA': 'Tipo_Cuadrilla_Glosario',
        'NOMBRE DEL TÉCNICO': 'Nombre_Glosario',
    })
    
    # Agregar columna Coordinador vacía (no está en hoja Tecnicos)
    df_glosario['Coordinador'] = 'SIN ASIGNAR'
    
    # Normalizar sucursales: CTA-XXX → GS2-XXX
    print(f"   🗺️  Normalizando sucursales (CTA → GS2)...")
    df_glosario['Distrito_Glosario'] = df_glosario['Distrito_Glosario_Original'].apply(normalizar_sucursal_glosario)
    
    # Mapear tipos de cuadrilla
    df_glosario['Tipo_Cuadrilla_Normalizado'] = df_glosario['Tipo_Cuadrilla_Glosario'].apply(
        mapear_tipo_cuadrilla_glosario
    )
    
    print(f"✅ {len(df_glosario):,} técnicos cargados")
    print(f"   Distritos únicos: {df_glosario['Distrito_Glosario'].nunique()}")
    print(f"   Tipos de cuadrilla: {df_glosario['Tipo_Cuadrilla_Normalizado'].nunique()}")
    
    return df_glosario

def cargar_datos():
    """Carga el archivo crudo de la plataforma"""
    print(f"\n📂 Cargando: {RUTA_ENTRADA}")
    
    if not os.path.exists(RUTA_ENTRADA):
        raise FileNotFoundError(
            f"\n❌ No se encontró el archivo: {RUTA_ENTRADA}\n"
            f"   Verifica que el archivo esté en la carpeta 'datos_entrada/'"
        )
    
    # Leer con header en fila 1 (la fila 0 puede estar vacía)
    df = pd.read_excel(RUTA_ENTRADA, header=1)
    
    print(f"✅ {len(df):,} registros cargados")
    print(f"   OS en archivo: {df['OS'].nunique():,}")
    print(f"   OT en archivo: {df['OT'].nunique():,}")
    
    return df

# ============================================================================
# 🧹 LIMPIEZA DE DATOS
# ============================================================================

def limpiar_datos(df, df_glosario):
    """Aplica todos los filtros de limpieza con integración de glosario"""
    print("\n🧹 LIMPIANDO BASE DE DATOS...")
    
    registros_iniciales = len(df)
    
    # PASO 1: Filtrar solo usuarios MEG
    print(f"\n   [1/6] Filtrando usuarios MEG...")
    df_meg = df[df['Usuario instalador'].str.startswith('MEG', na=False)].copy()
    eliminados_meg = registros_iniciales - len(df_meg)
    print(f"         ✓ Usuarios MEG: {len(df_meg):,} registros")
    print(f"         ✗ Otros eliminados: {eliminados_meg:,} registros")
    
    # PASO 2: MERGE con glosario
    print(f"\n   [2/6] Cruzando con glosario de técnicos...")
    
    # Limpiar espacios en usuarios antes del merge
    df_meg['Usuario_Limpio'] = df_meg['Usuario instalador'].str.strip()
    df_glosario['Usuario_Limpio'] = df_glosario['Usuario'].str.strip()
    
    # Hacer merge por Usuario limpio
    df_limpio = df_meg.merge(
        df_glosario,
        on='Usuario_Limpio',
        how='left',
        indicator=True
    )
    
    # Identificar técnicos encontrados/no encontrados
    encontrados = (df_limpio['_merge'] == 'both').sum()
    no_encontrados = (df_limpio['_merge'] == 'left_only').sum()
    
    print(f"         ✓ {encontrados:,} registros con técnico en glosario")
    
    if no_encontrados > 0:
        print(f"         ⚠️  {no_encontrados:,} registros SIN técnico en glosario")
        
        # Crear flag
        df_limpio['En_Glosario'] = df_limpio['_merge'] == 'both'
        
        # Para los que NO están en glosario, usar datos del archivo como fallback
        print(f"         📋 Usando distrito del archivo como fallback para técnicos sin glosario")
        
        # Si NO está en glosario, normalizar distrito del archivo
        mask_sin_glosario = df_limpio['_merge'] == 'left_only'
        
        # Aplicar normalización a los distritos
        df_limpio.loc[mask_sin_glosario, 'Distrito_Glosario'] = df_limpio.loc[mask_sin_glosario, 'Distrito'].apply(normalizar_distrito_archivo).values
        df_limpio.loc[mask_sin_glosario, 'Tipo_Cuadrilla_Glosario'] = 'Planta Interna'
        df_limpio.loc[mask_sin_glosario, 'Tipo_Cuadrilla_Normalizado'] = 'Normal'
        df_limpio.loc[mask_sin_glosario, 'Coordinador'] = 'SIN ASIGNAR'
        df_limpio.loc[mask_sin_glosario, 'Nombre_Glosario'] = df_limpio.loc[mask_sin_glosario, 'Nombre tecnico']
        
        # Técnicos no encontrados (mostrar por usuario único, no por registro)
        tecnicos_no_encontrados = df_limpio[mask_sin_glosario].groupby(
            ['Usuario instalador', 'Nombre tecnico', 'Distrito']
        ).size().reset_index(name='Total_OT')
        
        tecnicos_no_encontrados = tecnicos_no_encontrados.sort_values('Total_OT', ascending=False)
        
        print(f"\n         📋 TÉCNICOS NO ENCONTRADOS EN GLOSARIO:")
        print(f"         Total técnicos únicos sin glosario: {len(tecnicos_no_encontrados)}")
        print(f"         (se usó distrito del archivo como fallback)")
        print(f"\n         Top 20 técnicos sin glosario:")
        for idx, row in tecnicos_no_encontrados.head(20).iterrows():
            # Mostrar distrito normalizado
            dist_normalizado = normalizar_distrito_archivo(row['Distrito'])
            print(f"            - {row['Usuario instalador']} ({row['Nombre tecnico']}) - {row['Distrito']} → {dist_normalizado}: {row['Total_OT']:,} OT")
        
        if len(tecnicos_no_encontrados) > 20:
            print(f"            ... y {len(tecnicos_no_encontrados) - 20} técnicos más")
    else:
        df_limpio['En_Glosario'] = True
    
    # Eliminar columnas auxiliares
    df_limpio = df_limpio.drop(['_merge', 'Usuario_Limpio'], axis=1, errors='ignore')
    
    # PASO 3: Convertir Fecha termino a formato datetime válido
    print(f"\n   [3/6] Convirtiendo fechas a formato válido...")
    try:
        # IMPORTANTE: dayfirst=True porque el formato es dd/mm/yyyy
        df_limpio['Fecha termino'] = pd.to_datetime(df_limpio['Fecha termino'], dayfirst=True)
        print(f"         ✓ Fechas convertidas correctamente (formato dd/mm/yyyy)")
        
        # Mostrar rango de fechas
        fecha_min = df_limpio['Fecha termino'].min()
        fecha_max = df_limpio['Fecha termino'].max()
        print(f"         📅 Rango: {fecha_min.strftime('%Y-%m-%d')} a {fecha_max.strftime('%Y-%m-%d')}")
        
        # Contar días únicos
        dias_unicos = df_limpio['Fecha termino'].dt.date.nunique()
        print(f"         📊 Días únicos: {dias_unicos}")
    except Exception as e:
        print(f"         ⚠️  Error al convertir fechas: {e}")
    
    # PASO 4: Agregar columna PUNTOS
    print(f"\n   [4/6] Calculando puntos por tipo de servicio...")
    df_limpio['PUNTOS'] = df_limpio.apply(
        lambda row: obtener_puntos(row['Tipo'], row['Subtipo']), axis=1
    )
    
    # Mostrar subtipos no reconocidos
    subtipos_cero = df_limpio[df_limpio['PUNTOS'] == 0]
    if len(subtipos_cero) > 0:
        subtipos_unicos = subtipos_cero.groupby(['Tipo', 'Subtipo']).size().reset_index(name='Count')
        if len(subtipos_unicos) > 0:
            print(f"         ⚠️  {len(subtipos_cero):,} registros con 0 puntos ({len(subtipos_unicos)} subtipos únicos)")
    
    print(f"         ✓ Puntos calculados para {len(df_limpio):,} órdenes")
    print(f"         ✓ Total puntos: {df_limpio['PUNTOS'].sum():,.0f}")
    
    # PASO 5: Identificar hallazgos
    print(f"\n   [5/6] Identificando hallazgos...")
    df_limpio['Es_Hallazgo'] = df_limpio.apply(
        lambda row: es_hallazgo(row['Cuenta'], row['Tipo']), axis=1
    )
    hallazgos_count = df_limpio['Es_Hallazgo'].sum()
    print(f"         ✓ {hallazgos_count:,} hallazgos identificados")
    
    # PASO 6: Eliminar OTs duplicadas (errores en descarga)
    print(f"\n   [6/6] Eliminando OTs duplicadas (errores de descarga)...")
    print(f"         ℹ️  Nota: Cada OT genera puntos independientes")
    antes_duplicados = len(df_limpio)
    puntos_antes = df_limpio['PUNTOS'].sum()
    
    # Eliminar duplicados manteniendo el primero
    df_limpio = df_limpio.drop_duplicates(subset='OT', keep='first')
    
    duplicados_eliminados = antes_duplicados - len(df_limpio)
    puntos_despues = df_limpio['PUNTOS'].sum()
    puntos_perdidos = puntos_antes - puntos_despues
    
    print(f"         ✓ OT únicas: {len(df_limpio):,}")
    if duplicados_eliminados > 0:
        print(f"         ✗ OT duplicadas eliminadas: {duplicados_eliminados:,}")
        print(f"         ⚠️  Puntos perdidos: {puntos_perdidos:,.0f}")
    else:
        print(f"         ✓ No se encontraron OT duplicadas")
    
    # Renombrar columnas para compatibilidad con calculador de bonos
    df_limpio = df_limpio.rename(columns={
        'Usuario instalador': 'Usuario para pago',
        'Nombre tecnico': 'Tecnico',
        'Fecha termino': 'Fecha Termino',
        'Tipo': 'Servicio',
    })
    
    # Crear columna TIPO DE CUADRILLA para compatibilidad
    # Si está en glosario, usar del glosario; si no, dejar vacío
    df_limpio['TIPO DE CUADRILLA'] = df_limpio['Tipo_Cuadrilla_Normalizado'].fillna('Normal')
    
    return df_limpio

# ============================================================================
# 💾 GUARDAR ARCHIVO LIMPIO
# ============================================================================

def guardar_limpio(df):
    """Guarda el archivo limpio"""
    print(f"\n💾 Guardando archivo limpio: {RUTA_SALIDA}")
    
    # Seleccionar columnas relevantes
    columnas_importantes = [
        # Identificación
        'Usuario para pago', 'Tecnico', 'TÉCNICO O AUXILIAR',
        
        # Del glosario
        'Distrito_Glosario', 'Tipo_Cuadrilla_Glosario', 'Tipo_Cuadrilla_Normalizado',
        'Coordinador', 'En_Glosario',
        
        # De la orden
        'Cuenta', 'OS', 'OT', 'Servicio', 'Subtipo', 'Fecha Termino',
        'Estatus', 'Estado', 'PUNTOS', 'Es_Hallazgo',
        
        # Información adicional
        'Ciudad', 'Distrito', 'Cluster', 'Empresa(proveedor)', 'Tipo cuadrilla',
        'Usuario auxiliar', 'Nombre auxiliar',
    ]
    
    # Filtrar solo columnas que existan
    columnas_existentes = [col for col in columnas_importantes if col in df.columns]
    
    # Verificar columnas críticas
    columnas_criticas = ['Fecha Termino', 'Distrito_Glosario', 'TIPO DE CUADRILLA']
    for col in columnas_criticas:
        if col not in columnas_existentes:
            print(f"   ⚠️  Advertencia: Columna '{col}' no encontrada")
    
    df_final = df[columnas_existentes].copy()
    df_final.to_excel(RUTA_SALIDA, index=False)
    
    print(f"✅ Archivo guardado con {len(df_final):,} registros")
    print(f"   Columnas: {len(columnas_existentes)}")
    
    # Mostrar columnas incluidas
    cols_fecha = [c for c in columnas_existentes if 'fecha' in c.lower()]
    if cols_fecha:
        print(f"   📅 Columnas de fecha: {', '.join(cols_fecha)}")
    
    cols_glosario = [c for c in columnas_existentes if 'glosario' in c.lower() or c in ['Coordinador', 'En_Glosario']]
    if cols_glosario:
        print(f"   📚 Columnas del glosario: {', '.join(cols_glosario)}")

# ============================================================================
# 📊 RESUMEN
# ============================================================================

def mostrar_resumen(df):
    """Muestra resumen de la limpieza"""
    print("\n" + "="*80)
    print("📊 RESUMEN DEL ARCHIVO LIMPIO")
    print("="*80)
    
    print(f"\n✅ Total de órdenes (OT): {len(df):,}")
    print(f"✅ OS únicas: {df['OS'].nunique():,}")
    print(f"✅ Técnicos únicos: {df['Usuario para pago'].nunique():,}")
    
    if 'En_Glosario' in df.columns:
        tecnicos_en_glosario = df[df['En_Glosario']]['Usuario para pago'].nunique()
        tecnicos_sin_glosario = df[~df['En_Glosario']]['Usuario para pago'].nunique()
        print(f"   - En glosario: {tecnicos_en_glosario:,}")
        if tecnicos_sin_glosario > 0:
            print(f"   - ⚠️ Sin glosario: {tecnicos_sin_glosario:,}")
    
    if 'Distrito_Glosario' in df.columns:
        print(f"✅ Distritos (del glosario): {df['Distrito_Glosario'].nunique():,}")
    
    print(f"✅ Total puntos: {df['PUNTOS'].sum():,.0f}")
    
    if 'Es_Hallazgo' in df.columns:
        hallazgos = df['Es_Hallazgo'].sum()
        print(f"✅ Hallazgos identificados: {hallazgos:,}")
    
    # Top 5 técnicos
    print(f"\n🏆 Top 5 técnicos por número de OT:")
    top_tecnicos = df.groupby('Usuario para pago').size().nlargest(5)
    for i, (tecnico, count) in enumerate(top_tecnicos.items(), 1):
        print(f"   {i}. {tecnico}: {count:,} OT")
    
    # Top 5 distritos (del glosario)
    if 'Distrito_Glosario' in df.columns:
        print(f"\n📍 Top 5 distritos (del glosario):")
        top_distritos = df['Distrito_Glosario'].value_counts().head(5)
        for i, (distrito, count) in enumerate(top_distritos.items(), 1):
            if pd.notna(distrito):
                print(f"   {i}. {distrito}: {count:,} OT")
    
    # Distribución de puntos
    print(f"\n⭐ Distribución de puntos:")
    dist_puntos = df['PUNTOS'].value_counts().sort_index()
    for puntos, count in dist_puntos.items():
        print(f"   {puntos} puntos: {count:,} órdenes")
    
    # Distribución de tipos de cuadrilla
    if 'Tipo_Cuadrilla_Normalizado' in df.columns:
        print(f"\n🔧 Distribución de tipos de cuadrilla:")
        dist_cuadrilla = df.groupby('Tipo_Cuadrilla_Normalizado')['Usuario para pago'].nunique()
        for tipo, count in dist_cuadrilla.items():
            print(f"   {tipo}: {count:,} técnicos")

# ============================================================================
# 🚀 MAIN
# ============================================================================

def main():
    print("\n" + "="*80)
    print("🧹 LIMPIADOR DE BASE DE DATOS v2.0")
    print("   Sistema de Cálculo de Bonos - Con Glosario")
    print("="*80)
    
    try:
        # Verificar carpetas
        verificar_carpetas()
        
        print(f"\n📄 Archivo entrada:  {ARCHIVO_ENTRADA}")
        print(f"📄 Archivo glosario: {ARCHIVO_GLOSARIO}")
        print(f"📄 Archivo salida:   {ARCHIVO_SALIDA}")
        
        # Proceso
        df_glosario = cargar_glosario()
        df = cargar_datos()
        df_limpio = limpiar_datos(df, df_glosario)
        guardar_limpio(df_limpio)
        mostrar_resumen(df_limpio)
        
        print("\n" + "="*80)
        print("✅ LIMPIEZA COMPLETADA")
        print("="*80)
        print(f"\n📁 Archivo limpio guardado en: {RUTA_SALIDA}")
        print("\n💡 Ahora puedes usar este archivo en el calculador de bonos")
        print(f"   Configura ARCHIVO_ENTRADA = '{ARCHIVO_SALIDA.split('/')[-1]}'")
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
    input("\nPresiona ENTER para salir...")