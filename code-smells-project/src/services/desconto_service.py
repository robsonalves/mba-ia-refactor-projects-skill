from src.config.constants import DESCONTO_TIERS


def calcular_desconto(faturamento):
    for limite, taxa in DESCONTO_TIERS:
        if faturamento > limite:
            return round(faturamento * taxa, 2)
    return 0.0
