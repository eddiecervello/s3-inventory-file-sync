import pandas as pd
from typing import List

def get_skus_from_excel(excel_path: str) -> List[str]:
    df = pd.read_excel(excel_path)
    return df['SKU'].dropna().astype(str).tolist()
