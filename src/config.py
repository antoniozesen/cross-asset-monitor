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
    "SPY": "SPDR S&P 500 ETF", "VGK": "Vanguard FTSE Europe ETF", "EWJ": "iShares MSCI Japan ETF", "IEMG": "iShares Core MSCI EM ETF",
    "XLK": "Technology Select Sector SPDR", "XLF": "Financial Select Sector SPDR", "XLI": "Industrial Select Sector SPDR",
    "XLV": "Health Care Select Sector SPDR", "XLP": "Consumer Staples Select Sector SPDR", "XLU": "Utilities Select Sector SPDR",
    "XLE": "Energy Select Sector SPDR", "XLB": "Materials Select Sector SPDR", "XLY": "Consumer Discretionary Select Sector SPDR",
    "XLRE": "Real Estate Select Sector SPDR", "XLC": "Communication Services Select Sector SPDR",
    "QUAL": "iShares MSCI USA Quality Factor ETF", "MTUM": "iShares MSCI USA Momentum Factor ETF", "USMV": "iShares MSCI USA Min Vol ETF",
    "TLT": "iShares 20+ Year Treasury Bond ETF", "IEF": "iShares 7-10 Year Treasury ETF", "LQD": "iShares IG Corp Bond ETF",
    "HYG": "iShares High Yield Corp Bond ETF", "GLD": "SPDR Gold Shares", "SHY": "iShares 1-3Y Treasury ETF", "IEI": "iShares 3-7Y Treasury ETF",
    "^GSPC": "S&P 500 Index", "^IXIC": "NASDAQ Composite", "^DJI": "Dow Jones Industrial Average", "^RUT": "Russell 2000",
    "^STOXX": "STOXX Europe 600", "^GDAXI": "DAX 40", "^FCHI": "CAC 40", "^IBEX": "IBEX 35", "^FTSE": "FTSE 100",
    "FTSEMIB.MI": "FTSE MIB", "^N225": "Nikkei 225", "^HSI": "Hang Seng Index",
    "EURUSD=X": "EUR/USD", "EURGBP=X": "EUR/GBP", "EURJPY=X": "EUR/JPY", "USDJPY=X": "USD/JPY", "GBPUSD=X": "GBP/USD", "USDCHF=X": "USD/CHF",
    "GC=F": "Gold Futures", "SI=F": "Silver Futures", "BZ=F": "Brent Crude Futures", "CL=F": "WTI Crude Futures", "NG=F": "Natural Gas Futures", "HG=F": "Copper Futures",
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
    "us_3m": ["FRED:DTB3", "FRED:DGS3MO", "TREASURY:DGS3MO"],
    "us_2y": ["FRED:DGS2", "TREASURY:DGS2"],
    "us_10y": ["FRED:DGS10", "TREASURY:DGS10"],
    "us_30y": ["FRED:DGS30", "TREASURY:DGS30"],
    "us_real_10y": ["FRED:DFII10", "FRED:REAINTRATREARAT10Y", "TREASURY:REAL10Y"],
    "hy_oas": ["FRED:BAMLH0A0HYM2"],
    "ig_oas": ["FRED:BAMLC0A0CM"],
    "hy_yield": ["FRED:BAMLH0A0HYM2SYTW"],
    "ig_yield": ["FRED:BAMLC0A0CMEY"],
    "euro_inflation": ["FRED:CP0000EZ19M086NEST", "FRED:CPHPTT01EZM659N", "ECB:EA_HICP", "OECD:CPALTT01EZM661S"],
    "euro_unemployment": ["FRED:LRHUTTTTEZM156S", "EUROSTAT:une_rt_m?geo=EA19&sex=T&age=Y15-74&s_adj=SA&unit=PC_ACT", "FRED:UNRTEU", "ECB:EA_UNEMP"],
    "euro_cli": ["FRED:OECDELOLITONOSTSAM", "OECD:LOLITOAAEA"],

    "hard_us_ip": ["FRED:INDPRO"],
    "hard_us_retail": ["FRED:RRSFS"],
    "hard_us_labor": ["FRED:PAYEMS"],
    "soft_us_confidence": ["FRED:UMCSENT"],
    "soft_eu_cli": ["FRED:OECDELOLITONOSTSAM"],
    "public_debt_us": ["FRED:GFDEGDQ188S"],
    "private_debt_us": ["FRED:QUSPAM770A"],
    "fiscal_balance_us": ["FRED:FYFSD"],
    "public_debt_de": ["WORLDBANK:DEU|GC.DOD.TOTL.GD.ZS"],
    "public_debt_fr": ["WORLDBANK:FRA|GC.DOD.TOTL.GD.ZS"],
    "public_debt_it": ["WORLDBANK:ITA|GC.DOD.TOTL.GD.ZS"],
    "public_debt_es": ["WORLDBANK:ESP|GC.DOD.TOTL.GD.ZS"],
    "public_debt_jp": ["WORLDBANK:JPN|GC.DOD.TOTL.GD.ZS"],
    "private_debt_de": ["WORLDBANK:DEU|FS.AST.PRVT.GD.ZS"],
    "private_debt_fr": ["WORLDBANK:FRA|FS.AST.PRVT.GD.ZS"],
    "private_debt_it": ["WORLDBANK:ITA|FS.AST.PRVT.GD.ZS"],
    "private_debt_es": ["WORLDBANK:ESP|FS.AST.PRVT.GD.ZS"],
    "private_debt_jp": ["WORLDBANK:JPN|FS.AST.PRVT.GD.ZS"],
    "fiscal_balance_de": ["WORLDBANK:DEU|GC.BAL.CASH.GD.ZS"],
    "fiscal_balance_fr": ["WORLDBANK:FRA|GC.BAL.CASH.GD.ZS"],
    "fiscal_balance_it": ["WORLDBANK:ITA|GC.BAL.CASH.GD.ZS"],
    "fiscal_balance_es": ["WORLDBANK:ESP|GC.BAL.CASH.GD.ZS"],
    "fiscal_balance_jp": ["WORLDBANK:JPN|GC.BAL.CASH.GD.ZS"],
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
