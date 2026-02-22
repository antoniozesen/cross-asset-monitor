from __future__ import annotations

ALLOWED_TICKERS = [
    "SPY","VGK","EWJ","IEMG","MCHI","XLK","XLF","XLI","XLV","XLP","XLU","XLE","XLB","XLY","XLRE","XLC",
    "QUAL","MTUM","USMV","VLUE","VUG","TLT","IEF","LQD","HYG","GLD","^STOXX","^GDAXI","^FCHI","^IBEX",
    "^FTSE","FTSEMIB.MI","^GSPC","^IXIC","^DJI","^RUT","^N225","^HSI","IVE","IVW","CV9.PA","CG9.PA","ESIF.L",
    "EXV6.DE","HLTH.L","ESIE.F","ESIS.F","ESIN.L","EXV3.DE","ESIC.F","EXV1.DE","EXH6.DE","EXH9.DE","EURUSD=X",
    "EURGBP=X","EURJPY=X","USDJPY=X","GBPUSD=X","USDCHF=X","GC=F","SI=F","BZ=F","CL=F","NG=F","HG=F","EM13.MI",
    "CBE7.AS","LYXD.DE","IEAC.L","IHYG.L","SHY","IEI"
]

TICKER_NAMES = {t: t for t in ALLOWED_TICKERS}
TICKER_NAMES.update({
    "SPY": "SPDR S&P 500 ETF", "VGK": "Vanguard FTSE Europe ETF", "EWJ": "iShares MSCI Japan ETF",
    "IEMG": "iShares Core MSCI EM ETF", "TLT": "iShares 20+ Year Treasury Bond ETF", "IEF": "iShares 7-10 Year Treasury ETF",
    "LQD": "iShares iBoxx $ Investment Grade Corporate Bond ETF", "HYG": "iShares iBoxx $ High Yield Corporate Bond ETF",
    "GLD": "SPDR Gold Shares", "^GSPC": "S&P 500 Index", "^STOXX": "STOXX Europe 600 Index",
    "^GDAXI": "DAX Index", "IVE": "iShares S&P 500 Value ETF", "IVW": "iShares S&P 500 Growth ETF",
    "CV9.PA": "Amundi MSCI Europe Value", "CG9.PA": "Amundi MSCI Europe Growth", "BZ=F": "Brent Crude Futures",
    "CL=F": "WTI Crude Futures", "GC=F": "Gold Futures",
})

PROFILE_ANCHORS = {
    "Conservative": {"equity": 0.35, "bonds": 0.55, "gold": 0.10},
    "Balanced": {"equity": 0.50, "bonds": 0.40, "gold": 0.10},
    "Growth": {"equity": 0.65, "bonds": 0.25, "gold": 0.10},
}

MIN_HISTORY_YEARS_TARGET = 15
MIN_HISTORY_YEARS_HARD = 5
MAX_STALENESS_DAYS_MONTHLY = 60
MAX_MISSINGNESS_AFTER_RESAMPLE = 0.10

CONCEPT_PRIORITY = {
    "us_3m": ["FRED:DTB3", "TREASURY:DGS3MO"],
    "us_2y": ["FRED:DGS2", "TREASURY:DGS2"],
    "us_10y": ["FRED:DGS10", "TREASURY:DGS10"],
    "us_30y": ["FRED:DGS30", "TREASURY:DGS30"],
    "us_real_10y": ["FRED:DFII10", "TREASURY:REAL10Y"],
    "ger_2y": ["BUNDESBANK:GER2Y", "ECB:GER2Y", "FRED:IRLTLT01DEM156N"],
    "ger_10y": ["BUNDESBANK:GER10Y", "ECB:GER10Y", "FRED:IRLTLT01DEM156N"],
    "ger_30y": ["BUNDESBANK:GER30Y", "ECB:GER30Y"],
    "hy_oas": ["FRED:BAMLH0A0HYM2"],
    "ig_oas": ["FRED:BAMLC0A0CM"],
    "hy_yield": ["FRED:BAMLH0A0HYM2SYTW"],
    "ig_yield": ["FRED:BAMLC0A0CMEY"],
    "euro_inflation": ["ECB:EA_HICP", "OECD:CPALTT01EZM661S"],
    "euro_unemployment": ["ECB:EA_UNEMP", "FRED:LRHUTTTTEZM156S"],
    "euro_cli": ["OECD:LOLITOAAEA", "FRED:OECDELOLITONOSTSAM"],
    "japan_inflation": ["OECD:CPGRLE01JPM659N", "FRED:CPGRLE01JPQ657N"],
    "commodities_impulse": ["WB_PINK:CRUDE_BRENT"],
}

RATIO_PAIRS = {
    "VGK/SPY": ("VGK", "SPY"), "EWJ/SPY": ("EWJ", "SPY"), "IEMG/SPY": ("IEMG", "SPY"),
    "QUAL/SPY": ("QUAL", "SPY"), "MTUM/SPY": ("MTUM", "SPY"), "USMV/SPY": ("USMV", "SPY"),
    "HYG/LQD": ("HYG", "LQD"), "TLT/IEF": ("TLT", "IEF"), "GLD/SPY": ("GLD", "SPY"),
    "^STOXX/^GSPC": ("^STOXX", "^GSPC"), "^GDAXI/^GSPC": ("^GDAXI", "^GSPC"),
    "IVE/IVW": ("IVE", "IVW"), "CV9.PA/CG9.PA": ("CV9.PA", "CG9.PA"),
    "IEAC.L/LQD": ("IEAC.L", "LQD"), "IHYG.L/HYG": ("IHYG.L", "HYG"),
    "BZ=F/^GSPC": ("BZ=F", "^GSPC"), "CL=F/^GSPC": ("CL=F", "^GSPC"),
}
