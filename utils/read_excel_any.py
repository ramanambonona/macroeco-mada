import io
import os
import csv
import pandas as pd
from typing import Optional, Union

FileLike = Union[str, bytes, bytearray, io.BufferedIOBase, io.BytesIO]

def _to_bytesio(file: FileLike) -> io.BytesIO:
    """
    Uniformise l'entrée en BytesIO (utile pour relire plusieurs fois le flux).
    - file peut être un chemin, un UploadedFile Streamlit, un buffer, etc.
    """
    # Cas chemin (str)
    if isinstance(file, str) and os.path.exists(file):
        with open(file, "rb") as f:
            return io.BytesIO(f.read())

    # Cas UploadedFile (Streamlit) ou buffer
    if hasattr(file, "getvalue"):  # UploadedFile a getvalue()
        return io.BytesIO(file.getvalue())
    if hasattr(file, "read"):      # fichiers/buffers
        pos = file.tell() if hasattr(file, "tell") else None
        data = file.read()
        if pos is not None and hasattr(file, "seek"):
            try: file.seek(pos)
            except Exception: pass
        return io.BytesIO(data)

    # Cas bytes / bytearray
    if isinstance(file, (bytes, bytearray)):
        return io.BytesIO(file)

    raise ValueError("Type de fichier non supporté. Passez un chemin, un UploadedFile, ou un buffer binaire.")


def _sniff_delimiter(sample: bytes) -> Optional[str]:
    """
    Devine le séparateur CSV à partir d'un échantillon.
    Retourne ',' ';' '\\t' ou None si indéterminé.
    """
    try:
        text = sample.decode("utf-8", errors="ignore")
    except Exception:
        return None
    try:
        dialect = csv.Sniffer().sniff(text, delimiters=[",", ";", "\t", "|"])
        return dialect.delimiter
    except Exception:
        # Heuristique simple
        if text.count(";") > text.count(",") and text.count(";") >= 2:
            return ";"
        if text.count("\t") > 0:
            return "\t"
        if text.count(",") >= 2:
            return ","
        return None


def _try_read_csv(buf: io.BytesIO, encoding: str = "utf-8", delimiter: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Tente pd.read_csv sur un buffer BytesIO. Retourne un DataFrame ou None en cas d'échec.
    """
    try:
        buf.seek(0)
        if delimiter is None:
            # Laisse pandas deviner si possible (engine='python' plus permissif)
            return pd.read_csv(buf, encoding=encoding, engine="python")
        # Astuce décimale : en Europe, le séparateur ';' va souvent avec decimal=','
        decimal = "," if delimiter == ";" else "."
        return pd.read_csv(buf, encoding=encoding, sep=delimiter, engine="python", decimal=decimal)
    except Exception:
        return None


def _try_read_excel(buf: io.BytesIO, sheet_name=0, skiprows=None) -> Optional[pd.DataFrame]:
    """
    Tente pd.read_excel. Essaye d'abord le moteur openpyxl (xlsx), puis xlrd (xls) si dispo.
    """
    # Tentative openpyxl (xlsx)
    try:
        buf.seek(0)
        return pd.read_excel(buf, sheet_name=sheet_name, skiprows=skiprows, engine="openpyxl")
    except Exception:
        pass
    # Tentative xlrd (xls) si installé
    try:
        import xlrd  # noqa: F401
        buf.seek(0)
        return pd.read_excel(buf, sheet_name=sheet_name, skiprows=skiprows, engine="xlrd")
    except Exception:
        return None


def read_excel_any(
    file: FileLike,
    sheet_name: Union[int, str] = 0,
    skiprows: Optional[Union[int, list]] = None,
) -> pd.DataFrame:
    """
    Lecture "tolérante" d'un fichier utilisateur (CSV, XLSX, éventuellement XLS).
    - Détecte le type par extension quand possible, sinon essaie CSV puis Excel.
    - Devine le séparateur CSV ; gère utf-8 / utf-8-sig / latin1.
    - Pour XLS, xlrd doit être installé (sinon convertir en XLSX).

    Parameters
    ----------
    file : chemin, UploadedFile Streamlit, buffer binaire, ou bytes
    sheet_name : index ou nom de feuille (Excel)
    skiprows : lignes à ignorer (Excel/CSV)

    Returns
    -------
    pandas.DataFrame
    """
    buf = _to_bytesio(file)

    # Détermine l'extension si disponible
    ext = None
    name = getattr(file, "name", None)
    if isinstance(file, str):
        name = file
    if name and isinstance(name, str) and "." in name:
        ext = name.lower().rsplit(".", 1)[-1]

    # 1) CSV explicite
    if ext == "csv":
        # Sniff delimiter sur un échantillon
        buf.seek(0)
        sample = buf.read(8192)
        delim = _sniff_delimiter(sample)

        # Essais d'encodage courants
        for enc in ("utf-8", "utf-8-sig", "latin1"):
            df = _try_read_csv(io.BytesIO(sample + buf.read()), encoding=enc, delimiter=delim)
            if df is not None:
                return df
            buf.seek(0)

    # 2) Excel explicite (xlsx/xls)
    if ext in ("xlsx", "xls"):
        df = _try_read_excel(buf, sheet_name=sheet_name, skiprows=skiprows)
        if df is not None:
            return df

    # 3) Type inconnu : on tente d'abord CSV, puis Excel
    #   3a) CSV avec sniff + encodages
    buf.seek(0)
    sample = buf.read(8192)
    delim = _sniff_delimiter(sample)
    for enc in ("utf-8", "utf-8-sig", "latin1"):
        df = _try_read_csv(io.BytesIO(sample + buf.read()), encoding=enc, delimiter=delim)
        if df is not None:
            return df
        buf.seek(0)

    #   3b) Excel
    df = _try_read_excel(buf, sheet_name=sheet_name, skiprows=skiprows)
    if df is not None:
        return df

    # Échec total
    raise ValueError(
        "Impossible de lire le fichier. Essayez un CSV (utf-8) ou un Excel .xlsx. "
        "Pour les .xls, installez xlrd ou convertissez en .xlsx."
    )
