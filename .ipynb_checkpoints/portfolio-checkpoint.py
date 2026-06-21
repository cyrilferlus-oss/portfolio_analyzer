from dataclasses import dataclass
import pandas as pd
from data_loader import DatabaseLoader


@dataclass
class Position:
    isin: str
    weight: float
    name: str
    last_price: float
    devise: str
    geographie: str


class Portfolio:
    def __init__(self, loader: DatabaseLoader):
        self.loader = loader
        self.positions: list[Position] = []
        self.errors: list[str] = []

    def load_from_input(self, isins: list[str], weights: list[float]) -> None:
        self.positions = []
        self.errors = []

        for isin, weight in zip(isins, weights):
            sec = self.loader.get_security(isin)
            if sec is None:
                self.errors.append(f"ISIN introuvable : {isin}")
                continue
            self.positions.append(
                Position(
                    isin=isin,
                    weight=weight,
                    name=str(sec.get("Name", isin)),
                    last_price=float(sec.get("Last_Price", 0)),
                    devise=str(sec.get("Devise", "N/A")),
                    geographie=str(sec.get("Geographie", "N/A")),
                )
            )

    def total_weight(self) -> float:
        return sum(p.weight for p in self.positions)

    def normalized_weights(self) -> list[float]:
        total = self.total_weight()
        if total == 0:
            return [0.0] * len(self.positions)
        return [p.weight / total for p in self.positions]

    def geo_breakdown(self) -> pd.DataFrame:
        return self._breakdown("geographie")

    def currency_breakdown(self) -> pd.DataFrame:
        return self._breakdown("devise")

    def holdings_breakdown(self) -> pd.DataFrame:
        norm = self.normalized_weights()
        data = [
            {"Titre": p.name, "ISIN": p.isin, "Poids (%)": w * 100}
            for p, w in zip(self.positions, norm)
        ]
        return pd.DataFrame(data).sort_values("Poids (%)", ascending=False)

    def _breakdown(self, field: str) -> pd.DataFrame:
        norm = self.normalized_weights()
        totals: dict[str, float] = {}
        for p, w in zip(self.positions, norm):
            key = getattr(p, field)
            totals[key] = totals.get(key, 0) + w * 100
        df = pd.DataFrame(list(totals.items()), columns=["Catégorie", "Poids (%)"])
        return df.sort_values("Poids (%)", ascending=False).reset_index(drop=True)

    def summary_table(self) -> pd.DataFrame:
        norm = self.normalized_weights()
        rows = [
            {
                "ISIN": p.isin,
                "Nom": p.name,
                "Devise": p.devise,
                "Géographie": p.geographie,
                "Prix": p.last_price,
                "Poids (%)": round(w * 100, 2),
            }
            for p, w in zip(self.positions, norm)
        ]
        return pd.DataFrame(rows)
