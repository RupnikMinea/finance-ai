from pathlib import Path

import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / '.env')  # lokalno bere .env, na Railway ignorira (env vars so že nastavljene)

FINNHUB_TOKEN = os.getenv('FINNHUB_TOKEN', '')
DATA_SOURCE   = os.getenv('DATA_SOURCE', 'yahoo')
DATA_DIR       = BASE_DIR / 'data'
CACHE_DIR      = DATA_DIR / 'cache'
HISTORY_DIR    = DATA_DIR / 'history'
PRED_DIR       = DATA_DIR / 'predictions'
MODEL_DIR      = BASE_DIR / 'models'

SCAN_CACHE     = CACHE_DIR / 'last_scan.json'
JOURNAL_FILE   = HISTORY_DIR / 'ai_journal.json'
PRED_HISTORY   = PRED_DIR / 'prediction_history.json'

# Model params
DOWNLOAD_START   = '2010-01-01'
TRAIN_START      = '2016-01-01'
SAFE_DD          = 10.0
SAFE_THRESHOLD   = 0.60
HORIZON          = 126
DOWNLOAD_WORKERS = 3
TOP_N_SHOW       = 20
MAX_PORTFOLIO    = 10
MAX_CORR         = 0.70
MAX_PER_SECTOR   = 2
DRIFT_THRESHOLD  = 2.5

ENS_W = (0.40, 0.35, 0.15, 0.10)   # ER, DynKelly, P(safe), MaxUpside

NASDAQ100 = [
    'AAPL','MSFT','NVDA','AMZN','META','GOOGL','GOOG','TSLA','AVGO','COST',
    'NFLX','TMUS','AMD','ADBE','QCOM','CSCO','INTU','TXN','AMAT','ISRG',
    'REGN','VRTX','LRCX','MU','KLAC','ADI','PANW','SNPS','CDNS','CRWD',
    'MELI','CHTR','ORLY','ABNB','PCAR','MRVL','ODFL','CTAS','CPRT',
    'FTNT','BIIB','GILD','IDXX','MRNA','DXCM','BKNG','WDAY','FAST',
    'ROST','DLTR','PYPL','EA','TTWO','NXPI','MCHP','ON','MPWR','ENPH',
    'ARM','INTC','SBUX','MDLZ','PEP','HON','AMGN','KDP','AEP','XEL',
    'AXON','CDW','DDOG','ZS','TEAM','ILMN','VEEV','MNST','PAYX','LULU',
    'ANSS','FANG','CEG','GEHC','ROP','VRSK','SIRI','WBA','SMCI',
    'APP','PLTR','DASH','TTD','MSTR',
]

SECTOR_MAP = {
    'NVDA':'Semiconductor','AMD':'Semiconductor','AVGO':'Semiconductor',
    'QCOM':'Semiconductor','TXN':'Semiconductor','AMAT':'Semiconductor',
    'LRCX':'Semiconductor','MU':'Semiconductor','KLAC':'Semiconductor',
    'ADI':'Semiconductor','MRVL':'Semiconductor','NXPI':'Semiconductor',
    'MCHP':'Semiconductor','ON':'Semiconductor','MPWR':'Semiconductor',
    'ARM':'Semiconductor','INTC':'Semiconductor','SMCI':'Semiconductor',
    'MSFT':'Software','ADBE':'Software','INTU':'Software',
    'SNPS':'Software','CDNS':'Software','PANW':'Software',
    'CRWD':'Software','WDAY':'Software','FTNT':'Software',
    'DDOG':'Software','ZS':'Software','TEAM':'Software',
    'ANSS':'Software','VEEV':'Software','CDW':'Software','ROP':'Software',
    'AMZN':'Internet','META':'Internet','GOOGL':'Internet','GOOG':'Internet',
    'NFLX':'Internet','BKNG':'Internet','MELI':'Internet',
    'PYPL':'Internet','TTD':'Internet','DASH':'Internet','ABNB':'Internet',
    'AAPL':'Hardware','CSCO':'Hardware',
    'PLTR':'AI_Data','APP':'AI_Data','MSTR':'AI_Data',
    'AMGN':'Biotech','GILD':'Biotech','REGN':'Biotech','BIIB':'Biotech',
    'MRNA':'Biotech','VRTX':'Biotech','IDXX':'Biotech','ILMN':'Biotech',
    'DXCM':'Biotech','ISRG':'Biotech',
    'COST':'Consumer','ROST':'Consumer','DLTR':'Consumer','MNST':'Consumer',
    'SBUX':'Consumer','MDLZ':'Consumer','PEP':'Consumer','KDP':'Consumer',
    'LULU':'Consumer','WBA':'Consumer','ORLY':'Consumer',
    'TSLA':'EV_Auto','TMUS':'Telecom','CHTR':'Telecom','SIRI':'Telecom',
    'ENPH':'CleanEnergy','CEG':'CleanEnergy','AEP':'Utilities','XEL':'Utilities',
    'GEHC':'MedDevice','PCAR':'Industrial','ODFL':'Industrial','CTAS':'Industrial',
    'CPRT':'Industrial','FAST':'Industrial','HON':'Industrial',
    'PAYX':'Industrial','VRSK':'Industrial','EA':'Gaming','TTWO':'Gaming',
    'AXON':'Defense','FANG':'Energy',
}

FEATURE_COLS = [
    'price_vs_sma20','price_vs_sma50','price_vs_sma200','sma20_vs_sma50','sma50_vs_sma200',
    'ret_1m','ret_3m','ret_6m','ret_12m','rs_1m','rs_3m','rs_6m','rs_12m',
    'rsi28','macd_hist','rel_vol_5d','atr_pct','vol_20d','vol_60d','vol_120d',
    'vc_2060','vc_60120','pct_52wh','pct_52wl','ath_pct','roc10',
    'sharpe_30','sharpe_90','maxdd_60','trend_cons','vol_regime',
    'slope_sma50','slope_sma200',
    'atr_ratio','rel_vol_90d','days_since_ath',
    'sector_rs_20d','sector_rs_60d','breakout20','breakout50',
    'dollar_vol_20d','rel_vol_20d','ath_strength',
]
CS_COLS  = [f'cs_{f}' for f in FEATURE_COLS]
ALL_FEATS = [
    'ath_pct','ath_strength','atr_pct','atr_ratio','days_since_ath','dollar_vol_20d',
    'macd_hist','maxdd_60','pct_52wl','ret_12m','roc10','rs_12m','rs_1m','rs_6m',
    'sector_rs_60d','slope_sma200','slope_sma50','sma50_vs_sma200','vc_60120',
    'vol_120d','vol_20d','vol_60d',
    'cs_ath_pct','cs_ath_strength','cs_atr_pct','cs_atr_ratio','cs_breakout50',
    'cs_days_since_ath','cs_dollar_vol_20d','cs_pct_52wl','cs_rel_vol_20d',
    'cs_ret_12m','cs_ret_3m','cs_slope_sma200','cs_slope_sma50','cs_sma50_vs_sma200',
    'cs_trend_cons','cs_vc_60120','cs_vol_120d','cs_vol_60d',
]

FEAT_DISPLAY = {
    'ath_strength':'ATH Strength','cs_ath_strength':'CS ATH Strength',
    'dollar_vol_20d':'Dollar Volume','cs_dollar_vol_20d':'CS Dollar Volume',
    'vol_120d':'Volatility 120d','cs_vol_120d':'CS Volatility 120d',
    'days_since_ath':'Days from ATH','cs_days_since_ath':'CS Days from ATH',
    'ret_12m':'12M Return','cs_ret_12m':'CS 12M Return',
    'rs_1m':'Relative Strength 1M','rs_6m':'Relative Strength 6M',
    'rs_12m':'Relative Strength 12M','sector_rs_60d':'Sector RS 60d',
    'sma50_vs_sma200':'SMA 50/200','cs_sma50_vs_sma200':'CS SMA 50/200',
    'slope_sma50':'Slope SMA50','slope_sma200':'Slope SMA200',
    'cs_slope_sma50':'CS Slope SMA50','cs_slope_sma200':'CS Slope SMA200',
    'atr_pct':'ATR %','atr_ratio':'ATR Ratio','cs_atr_pct':'CS ATR %',
    'cs_atr_ratio':'CS ATR Ratio','maxdd_60':'MaxDD 60d',
    'pct_52wl':'52W Low %','cs_pct_52wl':'CS 52W Low',
    'ath_pct':'ATH %','cs_ath_pct':'CS ATH %',
    'macd_hist':'MACD Histogram','roc10':'ROC 10d',
    'vc_60120':'Vol Compression','cs_vc_60120':'CS Vol Compression',
    'vol_20d':'Volatility 20d','vol_60d':'Volatility 60d',
    'cs_rel_vol_20d':'CS Relative Volume','cs_breakout50':'CS Breakout 50d',
    'cs_trend_cons':'CS Trend Consistency','cs_ret_3m':'CS 3M Return',
    'cs_vol_60d':'CS Volatility 60d','cs_vol_120d':'CS Volatility 120d',
}
