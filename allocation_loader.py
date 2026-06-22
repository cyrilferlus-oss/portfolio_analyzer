import pandas as pd
import io
from pathlib import Path

RISK_PROFILES = [10, 25, 50, 65, 75, 85, 92.5, 100]

CATEGORY_MAP = {
    "equity":                      "Equities",
    "equities":                    "Equities",
    "bonds":                       "Bonds",
    "fixed income":                "Bonds",
    "cash":                        "Cash",
    "alternatives":                "Alternatives",
    "other investments":           "Other Investments",
    "other":                       "Other Investments",
    "gold and other commodities":  "Gold and other commodities",
}


def normalize_category(raw: str) -> str:
    return CATEGORY_MAP.get(str(raw).strip().lower(), "Other Investments")


class AllocationLoader:
    def __init__(self, filepath: str | Path | io.BytesIO):
        self.filepath = filepath
        self._data: dict[float, dict[str, float]] | None = None

    def load(self) -> dict[float, dict[str, float]]:
        if self._data is not None:
            return self._data

        df = pd.read_excel(self.filepath, header=None)

        # Find header row (contains "Asset Class")
        header_row = None
        for i, row in df.iterrows():
            if row.astype(str).str.contains("Asset Class", case=False).any():
                header_row = i
                break

        if header_row is None:
            raise ValueError("Colonne 'Asset Class' introuvable dans Portfolio Allocation.")

        df = pd.read_excel(self.filepath, header=header_row)
        df = df.dropna(how="all").reset_index(drop=True)

        # First column = asset class names
        asset_col = df.columns[0]
        df = df[df[asset_col].notna()]

        result: dict[float, dict[str, float]] = {}
        for col in df.columns[1:]:
            # Parse equity level from column name (e.g. "25% Equity" → 25.0)
            col_str = str(col).replace(",", ".").replace("%", "").replace("Equity", "").strip()
            try:
                level = float(col_str)
            except ValueError:
                continue

            allocations: dict[str, float] = {}
            for _, row in df.iterrows():
                asset = str(row[asset_col]).strip()
                if asset.lower() == "nan":
                    continue
                try:
                    allocations[asset] = float(str(row[col]).replace(",", "."))
                except (ValueError, TypeError):
                    allocations[asset] = 0.0
            result[level] = allocations

        self._data = result
        return self._data

    def get_profile(self, equity_pct: float) -> dict[str, float]:
        data = self.load()
        return data.get(equity_pct, {})

    def available_profiles(self) -> list[float]:
        return sorted(self.load().keys())
