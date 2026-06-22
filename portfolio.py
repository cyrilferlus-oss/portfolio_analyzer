from dataclasses import dataclass
import pandas as pd
from data_loader import DatabaseLoader
from allocation_loader import normalize_category


@dataclass
class Position:
    isin: str
    weight: float
    name: str
    last_price: float
    devise: str
    geographie: str
    categorie: str


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

            raw_cat = sec.get("Catégorie", None)
            categorie = "Other Investments" if (raw_cat is None or str(raw_cat).strip() in ("", "nan", "NaN")) else str(raw_cat).strip()

            self.positions.append(
                Position(
                    isin=isin,
                    weight=weight,
                    name=str(sec.get("Name", isin)),
                    last_price=float(sec.get("Last_Price", 0)),
                    devise=str(sec.get("Devise", "N/A")),
                    geographie=str(sec.get("Geographie", "N/A")),
                    categorie=categorie,
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
        # Géographie uniquement sur les positions Equity
        norm = self.normalized_weights()
        equity_total = sum(
            w for p, w in zip(self.positions, norm)
            if normalize_category(p.categorie) == "Equities"
        )
        totals: dict[str, float] = {}
        for p, w in zip(self.positions, norm):
            if normalize_category(p.categorie) != "Equities":
                continue
            key = p.geographie
            pct = (w / equity_total * 100) if equity_total > 0 else 0
            totals[key] = totals.get(key, 0) + pct
        df = pd.DataFrame(list(totals.items()), columns=["Catégorie", "Poids (%)"])
        return df.sort_values("Poids (%)", ascending=False).reset_index(drop=True)

    def currency_breakdown(self) -> pd.DataFrame:
        return self._breakdown("devise")

    def category_breakdown(self) -> pd.DataFrame:
        norm = self.normalized_weights()
        totals: dict[str, float] = {}
        for p, w in zip(self.positions, norm):
            key = normalize_category(p.categorie)
            totals[key] = totals.get(key, 0) + w * 100
        df = pd.DataFrame(list(totals.items()), columns=["Catégorie", "Poids (%)"])
        return df.sort_values("Poids (%)", ascending=False).reset_index(drop=True)

    def holdings_breakdown(self) -> pd.DataFrame:
        norm = self.normalized_weights()
        data = [
            {"Titre": p.name, "ISIN": p.isin, "Poids (%)": w * 100}
            for p, w in zip(self.positions, norm)
        ]
        return pd.DataFrame(data).sort_values("Poids (%)", ascending=False)

    def overweight_positions(self, threshold: float = 5.0) -> pd.DataFrame:
        norm = self.normalized_weights()
        rows = [
            {
                "ISIN": p.isin,
                "Nom": p.name,
                "Catégorie": p.categorie,
                "Devise": p.devise,
                "Géographie": p.geographie,
                "Poids (%)": round(w * 100, 2),
            }
            for p, w in zip(self.positions, norm)
            if w * 100 > threshold
        ]
        return pd.DataFrame(rows).sort_values("Poids (%)", ascending=False)

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
                "Catégorie": p.categorie,
                "Devise": p.devise,
                "Géographie": p.geographie,
                "Prix": p.last_price,
                "Poids (%)": round(w * 100, 2),
            }
            for p, w in zip(self.positions, norm)
        ]
        return pd.DataFrame(rows)
