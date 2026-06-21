import pandas as pd
from pathlib import Path


class DatabaseLoader:
    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)
        self._data: pd.DataFrame | None = None

    def load(self) -> pd.DataFrame:
        if self._data is not None:
            return self._data

        df = pd.read_excel(self.filepath, header=None)

        # Find the header row (contains 'ISIN')
        header_row = None
        for i, row in df.iterrows():
            if row.astype(str).str.contains("ISIN", case=False).any():
                header_row = i
                break

        if header_row is None:
            raise ValueError("Impossible de trouver l'en-tête ISIN dans le fichier Excel.")

        df = pd.read_excel(self.filepath, header=header_row)
        df = df.dropna(how="all", axis=1).dropna(how="all", axis=0)
        df.columns = df.columns.str.strip()

        # Normalize ISIN: remove spaces, uppercase
        df["ISIN"] = df["ISIN"].astype(str).str.replace(" ", "").str.upper().str.strip()

        self._data = df.reset_index(drop=True)
        return self._data

    def get_security(self, isin: str) -> dict | None:
        df = self.load()
        isin_clean = isin.replace(" ", "").upper().strip()
        row = df[df["ISIN"] == isin_clean]
        if row.empty:
            return None
        return row.iloc[0].to_dict()

    def list_isins(self) -> list[str]:
        return self.load()["ISIN"].tolist()
