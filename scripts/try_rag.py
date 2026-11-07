from app.rag import retrieve, retrieve_reranked

queries = [
    "read_csv fails with semicolon separator",
    "groupby drops NaN keys",
    "how to merge two dataframes on multiple columns",
    "to_datetime wrong format with dayfirst",
    "SettingWithCopyWarning when assigning values",
    "pivot_table with multiple aggfunc",
    "memory error reading large parquet file",
    "rolling window mean with time offset",
    "typo in documentation of DataFrame.apply",
    "feature request: add option to sort_values by key",
]

""""
read_csv falla con el separador de punto y coma",
"groupby suelta claves NaN",
"cómo fusionar dos marcos de datos en varias columnas",
"to_datetime formato incorrecto con dayfirst",
"SettingWithCopyWarning al asignar valores",
"pivot_table con múltiples aggfunc",
"Error de memoria al leer un archivo de parquet grande",
"media de ventana móvil con compensación de tiempo",
"error tipográfico en la documentación de DataFrame.apply",
"solicitud de función: agregar opción a sort_values por clave"
"""


for q in queries:
    print(f"\n### {q}")
    print("  Sin reranker:", [r["metadata"].get("url") for r in retrieve(q, k=3)])
    print("  Con reranker:", [r["metadata"].get("url") for r in retrieve_reranked(q, k=3)])