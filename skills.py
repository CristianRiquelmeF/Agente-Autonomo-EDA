import matplotlib
matplotlib.use("Agg")  # Backend headless: evita fallos en entornos sin GUI/pantalla

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from io import StringIO

# ================= RUTAS Y CARPETAS =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
# ====================================================

df = None  # Variable global para el DataFrame
current_out_dir = PROCESSED_DIR  # Carpeta de salida dinámica (por defecto general, hasta cargar un CSV)


def list_raw_files() -> str:
    """Lista los archivos CSV y Excel (.xlsx) disponibles actualmente en la carpeta 'data/raw/'."""
    try:
        archivos = [
            f for f in os.listdir(RAW_DIR)
            if f.lower().endswith((".csv", ".xlsx"))
        ]
    except Exception as e:
        return f"❌ Error al listar la carpeta data/raw/: {str(e)}"

    if not archivos:
        return "No hay archivos CSV o Excel en la carpeta data/raw/ actualmente."
    return "Archivos disponibles en data/raw/: " + ", ".join(sorted(archivos))


def load_dataset(filename: str, sheet_name: str = None) -> str:
    """
    Carga un archivo CSV o Excel (.xlsx) obligatoriamente desde la carpeta 'data/raw/'.
    El usuario solo debe proporcionar el nombre del archivo (ej. 'datos.csv' o 'datos.xlsx').
    Para archivos Excel con varias hojas, se puede indicar 'sheet_name' con el nombre
    de la hoja deseada; si se omite, se carga la primera hoja por defecto.
    Además, crea (o reutiliza) una subcarpeta de salida dedicada a este dataset
    dentro de 'data/processed/', para que los gráficos y reportes de distintos
    archivos no se sobrescriban entre sí.
    """
    global df, current_out_dir
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(RAW_DIR, safe_filename)
    extension = os.path.splitext(safe_filename)[1].lower()

    if extension not in (".csv", ".xlsx"):
        return f"❌ Error: Formato '{extension}' no soportado. Usa un archivo .csv o .xlsx."

    try:
        if extension == ".csv":
            df = pd.read_csv(file_path)
        else:
            # sheet_name=None en pandas devuelve TODAS las hojas como diccionario;
            # aquí forzamos la primera hoja (0) cuando el usuario no especifica una.
            df = pd.read_excel(file_path, sheet_name=sheet_name if sheet_name else 0)

        # Subcarpeta dinámica basada en el nombre del archivo (sin extensión).
        # Se crea solo si la carga fue exitosa, así una carga fallida no
        # genera carpetas vacías ni pisa el dataset previamente cargado.
        dataset_name = os.path.splitext(safe_filename)[0]
        current_out_dir = os.path.join(PROCESSED_DIR, dataset_name)
        os.makedirs(current_out_dir, exist_ok=True)

        return (
            f"✅ Éxito: '{safe_filename}' cargado. Entorno de salida configurado en: "
            f"data/processed/{dataset_name}/. Filas: {df.shape[0]}, Columnas: {df.shape[1]}"
        )
    except FileNotFoundError:
        return f"❌ Error: No se encontró '{safe_filename}' en la carpeta data/raw/. Verifica que el archivo esté allí."
    except pd.errors.EmptyDataError:
        return f"❌ Error: El archivo '{safe_filename}' está vacío o no tiene columnas válidas."
    except ValueError as e:
        # pandas lanza ValueError si, por ejemplo, sheet_name no existe en el Excel.
        return f"❌ Error al leer la hoja de Excel: {str(e)}"
    except pd.errors.EmptyDataError:
        return f"❌ Error: El archivo '{safe_filename}' está vacío o no tiene columnas válidas."
    except Exception as e:
        return f"❌ Error al cargar el CSV: {str(e)}"


def get_info() -> str:
    """Devuelve información general del dataframe: nombres de columnas, tipos de datos y nulos."""
    if df is None:
        return "Error: No hay datos cargados."
    buffer = StringIO()
    df.info(buf=buffer)
    return buffer.getvalue()


def get_describe() -> str:
    """Devuelve un resumen estadístico (media, max, min, cuartiles) de las numéricas."""
    if df is None:
        return "Error: No hay datos cargados."
    numeric = df.describe()
    if numeric.empty:
        return "No hay columnas numéricas para describir."
    return numeric.to_string()


def get_missing() -> str:
    """Muestra la cantidad de valores nulos o faltantes (NaN) por cada columna."""
    if df is None:
        return "Error: No hay datos cargados."
    return df.isnull().sum().to_string()


def get_correlation() -> str:
    """Calcula y devuelve la matriz de correlación lineal entre variables numéricas."""
    if df is None:
        return "Error: No hay datos cargados."
    numeric = df.select_dtypes(include=["number"])
    if numeric.shape[1] < 2:
        return "Error: Se necesitan al menos 2 columnas numéricas para calcular correlaciones."
    return numeric.corr().to_string()


def plot_histogram(column: str) -> str:
    """Genera y guarda un histograma en la subcarpeta de salida del dataset actual."""
    if df is None:
        return "Error: No hay datos cargados."
    if column not in df.columns:
        return f"Error: La columna '{column}' no existe."
    if not pd.api.types.is_numeric_dtype(df[column]):
        return f"Error: La columna '{column}' no es numérica, no se puede graficar un histograma."

    try:
        plt.figure(figsize=(8, 5))
        sns.histplot(df[column].dropna(), kde=True)
        plt.title(f"Histograma de {column}")

        safe_filename = f"hist_{os.path.basename(column)}.png"
        file_path = os.path.join(current_out_dir, safe_filename)

        plt.savefig(file_path)
        return f"Gráfico guardado exitosamente en {file_path}"
    except Exception as e:
        return f"❌ Error al generar el histograma: {str(e)}"
    finally:
        plt.close()


def plot_correlation_matrix() -> str:
    """Genera y guarda un mapa de calor visual de la matriz de correlación en la subcarpeta del dataset actual."""
    if df is None:
        return "Error: No hay datos cargados."
    numeric = df.select_dtypes(include=["number"])
    if numeric.shape[1] < 2:
        return "Error: Se necesitan al menos 2 columnas numéricas para graficar la matriz de correlación."

    try:
        plt.figure(figsize=(10, 8))
        sns.heatmap(numeric.corr(), annot=True, cmap="coolwarm", fmt=".2f")
        plt.title("Matriz de Correlación")

        safe_filename = "correlacion.png"
        file_path = os.path.join(current_out_dir, safe_filename)

        plt.savefig(file_path)
        return f"Gráfico guardado exitosamente en {file_path}"
    except Exception as e:
        return f"❌ Error al generar la matriz de correlación: {str(e)}"
    finally:
        plt.close()


def generate_markdown_report(report_content: str, filename: str = "Reporte_EDA.md") -> str:
    """Guarda el informe final del EDA en formato Markdown dentro de la subcarpeta del dataset actual."""
    safe_filename = os.path.basename(filename)
    if not safe_filename.endswith(".md"):
        safe_filename += ".md"

    file_path = os.path.join(current_out_dir, safe_filename)

    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(report_content)
        return f"✅ Informe generado y guardado en {file_path}"
    except Exception as e:
        return f"❌ Error al guardar el informe: {str(e)}"



def run_full_eda(top_n: int = 3) -> str:
    """
    Ejecuta un Análisis Exploratorio de Datos (EDA) completo en una sola llamada:
    información general, estadísticas descriptivas, valores faltantes, matriz de
    correlación (si hay al menos 2 columnas numéricas) y un histograma para cada
    una de las 'top_n' columnas numéricas con mayor varianza. Útil para obtener
    una vista panorámica rápida del dataset cargado sin encadenar varias llamadas.
    """
    if df is None:
        return "Error: No hay datos cargados."

    secciones = []

    secciones.append("## Información general\n" + get_info())
    secciones.append("## Estadísticas descriptivas\n" + get_describe())
    secciones.append("## Valores faltantes\n" + get_missing())

    numeric = df.select_dtypes(include=["number"])
    if numeric.shape[1] >= 2:
        secciones.append("## Correlación\n" + get_correlation())
    else:
        secciones.append("## Correlación\nSe necesitan al menos 2 columnas numéricas.")

    graficos_generados = []
    if not numeric.empty:
        # Selecciona las columnas numéricas con mayor varianza como las más
        # informativas para graficar sin sobrecargar al usuario de imágenes.
        columnas_top = numeric.var().sort_values(ascending=False).head(top_n).index.tolist()
        for columna in columnas_top:
            resultado = plot_histogram(columna)
            graficos_generados.append(resultado)

    if numeric.shape[1] >= 2:
        graficos_generados.append(plot_correlation_matrix())

    resumen = "\n\n".join(secciones)
    if graficos_generados:
        resumen += "\n\n## Gráficos generados\n" + "\n".join(graficos_generados)

    return resumen
