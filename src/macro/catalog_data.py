from __future__ import annotations

CATALOG_INDICATORS = [
    {"id":"oecd_cli_us","display_name":"OECD CLI United States","source":"OECD","source_key":"OECD.SDD.STES,DSD_STES@DF_CLI,4.1/.M.LI...AA...H","country":"US","frequency":"M","type":"SOFT","timing":"LEADING","pillar":"GROWTH","transform":"zscore_36","weight":1.0},
    {"id":"eurostat_consumer_conf","display_name":"Eurostat Consumer Confidence EU","source":"EUROSTAT","source_key":"teibs020","country":"EA","frequency":"M","type":"SOFT","timing":"LEADING","pillar":"GROWTH","transform":"zscore_36","weight":1.0},
    {"id":"eurostat_industry_conf","display_name":"Eurostat Industry Confidence EU","source":"EUROSTAT","source_key":"ei_bsco_m","country":"EA","frequency":"M","type":"SOFT","timing":"LEADING","pillar":"GROWTH","transform":"zscore_36","weight":1.0},
    {"id":"us_umcsent","display_name":"US Michigan Sentiment","source":"FRED","source_key":"UMCSENT","country":"US","frequency":"M","type":"SOFT","timing":"LEADING","pillar":"GROWTH","transform":"zscore_36","weight":1.0},
    {"id":"us_indpro","display_name":"US Industrial Production","source":"FRED","source_key":"INDPRO","country":"US","frequency":"M","type":"HARD","timing":"COINCIDENT","pillar":"GROWTH","transform":"yoy","weight":1.0},
    {"id":"us_retail","display_name":"US Retail Sales","source":"FRED","source_key":"RRSFS","country":"US","frequency":"M","type":"HARD","timing":"COINCIDENT","pillar":"GROWTH","transform":"yoy","weight":1.0},
    {"id":"us_unrate","display_name":"US Unemployment Rate","source":"FRED","source_key":"UNRATE","country":"US","frequency":"M","type":"HARD","timing":"LAGGING","pillar":"LABOR","transform":"zscore_36_inv","weight":1.0},
    {"id":"us_cpi","display_name":"US CPI Inflation","source":"FRED","source_key":"CPIAUCSL","country":"US","frequency":"M","type":"HARD","timing":"LAGGING","pillar":"INFLATION","transform":"yoy","weight":1.0},
    {"id":"us_slope","display_name":"US 10Y-2Y Slope","source":"FRED","source_key":"T10Y2Y","country":"US","frequency":"D","type":"HARD","timing":"LEADING","pillar":"FINANCIAL","transform":"zscore_252","weight":1.0},
    {"id":"ea_slope","display_name":"Euro Area 10Y-2Y Slope","source":"ECB","source_key":"YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y","country":"EA","frequency":"D","type":"HARD","timing":"LEADING","pillar":"FINANCIAL","transform":"zscore_252","weight":1.0},
    {"id":"us_pmi_proxy","display_name":"US ISM PMI Proxy","source":"FRED","source_key":"NAPM","country":"US","frequency":"M","type":"SOFT","timing":"LEADING","pillar":"GROWTH","transform":"zscore_36","weight":1.0},
    {"id":"eu_unemployment","display_name":"Euro Area Unemployment","source":"FRED","source_key":"LRHUTTTTEZM156S","country":"EA","frequency":"M","type":"HARD","timing":"LAGGING","pillar":"LABOR","transform":"zscore_36_inv","weight":1.0},
    {"id":"eu_hicp","display_name":"Euro Area HICP","source":"FRED","source_key":"CP0000EZ19M086NEST","country":"EA","frequency":"M","type":"HARD","timing":"LAGGING","pillar":"INFLATION","transform":"yoy","weight":1.0},
    {"id":"eu_ip","display_name":"Euro Area Industrial Production","source":"FRED","source_key":"PRMNTO01EZM661N","country":"EA","frequency":"M","type":"HARD","timing":"COINCIDENT","pillar":"GROWTH","transform":"yoy","weight":1.0},
    {"id":"us_housing","display_name":"US Housing Starts","source":"FRED","source_key":"HOUST","country":"US","frequency":"M","type":"HARD","timing":"LEADING","pillar":"GROWTH","transform":"yoy","weight":0.8},
    {"id":"us_wages","display_name":"US Average Hourly Earnings","source":"FRED","source_key":"CES0500000003","country":"US","frequency":"M","type":"HARD","timing":"LAGGING","pillar":"INFLATION","transform":"yoy","weight":0.8},
]
