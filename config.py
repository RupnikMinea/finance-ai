from pathlib import Path

import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / '.env')  # lokalno bere .env, na Railway ignorira (env vars so že nastavljene)

FINNHUB_TOKEN  = os.getenv('FINNHUB_TOKEN', '')
DATA_SOURCE    = os.getenv('DATA_SOURCE', 'yahoo')
SUPABASE_URL   = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY   = os.getenv('SUPABASE_KEY', '')
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
TRAIN_START      = '2021-01-01'
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

# ── S&P 500 additions (stocks not in NASDAQ-100) ─────────────────────────────
SP500_ADD = [
    # Finance
    'V','MA','JPM','BAC','WFC','GS','MS','AXP','BLK','SPGI','MCO',
    'COF','USB','PNC','TFC','ALL','PGR','MET','PRU','AFL','CB','MMC','AON',
    # Healthcare / Pharma (not biotech — those are in NASDAQ100)
    'JNJ','UNH','LLY','PFE','ABBV','ABT','TMO','DHR','BMY','MDT',
    'CVS','CI','HUM','ELV','MOH','ZBH','BSX','EW','STE','HOLX',
    # Energy
    'XOM','CVX','COP','EOG','OXY','SLB','HAL','MPC','VLO','PSX',
    'DVN','APA','BKR','HES','MRO',
    # Industrials (HON already in NASDAQ100)
    'GE','CAT','DE','BA','UPS','RTX','LMT','NOC','GD','MMM','ITW',
    'ETN','EMR','ROK','PH','CMI','IR','TT','CARR','OTIS','URI','GWW',
    # Consumer Discretionary
    'HD','NKE','MCD','TGT','CMG','MAR','HLT','RCL','CCL','YUM',
    'DPZ','DHI','LEN','PHM','F','GM',
    # Consumer Staples (PEP, MDLZ, KDP, COST already in NASDAQ100)
    'WMT','PG','KO','PM','MO','EL','CL','GIS','K','KHC','STZ',
    'TAP','TSN','HRL','SJM','CAG','CPB',
    # Communication / Media (TMUS, CHTR, NFLX, GOOGL, META already in NASDAQ100)
    'DIS','CMCSA','T','VZ','WBD','PARA',
    # Real Estate
    'PLD','AMT','EQIX','CCI','PSA','EQR','SPG','O','VICI','WELL',
    'DLR','IRM','SBAC',
    # Materials
    'LIN','APD','ECL','SHW','PPG','NEM','FCX','NUE','CF','ALB',
    'DD','DOW','LYB',
    # Utilities (AEP, XEL, CEG already in NASDAQ100)
    'NEE','DUK','SO','D','EXC','SRE','PCG','ED','WEC','ETR',
    'PPL','CMS','AES','CNP',
    # IT / Software non-NASDAQ
    'IBM','ACN','NOW','ORCL','CRM','SAP',
]

# ── ETFs ──────────────────────────────────────────────────────────────────────
ETF_LIST = [
    # Broad market
    'SPY','IWM','DIA','VTI',
    # Sector SPDR
    'XLF','XLK','XLV','XLE','XLI','XLY','XLP','XLU','XLB','XLRE','XLC',
    # Tech thematic
    'SOXX','SMH','IGV',
    # Healthcare thematic
    'XBI','IBB',
    # International
    'EEM','EFA',
    # Commodity
    'GLD','SLV','USO',
    # Bond
    'TLT',
    # Thematic
    'ARKK',
]

# ── Russell 2000 — top liquid members with sufficient history ─────────────────
RUSSELL2000_TOP = [
    # Semiconductor / Hardware small-cap
    'ACLS','CALX','FORM','KLIC','COHU','CEVA','AMBA','SLAB',
    # Biotech small-cap
    'ARWR','PACB','NVAX','FATE','IOVA','EDIT','CRSP','BEAM',
    # Clean energy small-cap
    'PLUG','FCEL','BLNK','CHPT','EVGO',
    # Defense small-cap
    'AVAV','KTOS',
    # Consumer small-cap
    'GME','BOOT',
    # Energy small-cap
    'SM','RRC','SWN',
    # Gaming / Entertainment
    'DKNG','PENN',
    # Crypto mining
    'MARA','RIOT',
    # Fintech small-cap
    'HIMS','LC','UPST',
]

# ── Universe map ──────────────────────────────────────────────────────────────
UNIVERSE_MAP = {
    'NASDAQ-100':           None,          # placeholder — set to NASDAQ100 after definition
    'S&P 500':              SP500_ADD,
    'ETFs':                 ETF_LIST,
    'Russell 2000 Top 80':  RUSSELL2000_TOP,
}


def get_universe(selections: list) -> list:
    """Return combined deduplicated ticker list for the given universe selection names."""
    from config import NASDAQ100 as _N100
    mapping = {
        'NASDAQ-100':           _N100,
        'S&P 500':              SP500_ADD,
        'ETFs':                 ETF_LIST,
        'Russell 2000 Top 80':  RUSSELL2000_TOP,
    }
    seen = set(); out = []
    for sel in selections:
        for t in mapping.get(sel, []):
            if t not in seen:
                seen.add(t); out.append(t)
    return out or _N100


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
    # ── S&P 500 Finance ──
    'V':'Finance','MA':'Finance','JPM':'Finance','BAC':'Finance','WFC':'Finance',
    'GS':'Finance','MS':'Finance','AXP':'Finance','BLK':'Finance','SPGI':'Finance',
    'MCO':'Finance','COF':'Finance','USB':'Finance','PNC':'Finance','TFC':'Finance',
    'ALL':'Finance','PGR':'Finance','MET':'Finance','PRU':'Finance','AFL':'Finance',
    'CB':'Finance','MMC':'Finance','AON':'Finance',
    # ── S&P 500 Healthcare ──
    'JNJ':'Healthcare','UNH':'Healthcare','LLY':'Healthcare','PFE':'Healthcare',
    'ABBV':'Healthcare','ABT':'Healthcare','TMO':'Healthcare','DHR':'Healthcare',
    'BMY':'Healthcare','MDT':'Healthcare','CVS':'Healthcare','CI':'Healthcare',
    'HUM':'Healthcare','ELV':'Healthcare','MOH':'Healthcare','ZBH':'Healthcare',
    'BSX':'Healthcare','EW':'Healthcare','STE':'Healthcare','HOLX':'Healthcare',
    # ── S&P 500 Energy ──
    'XOM':'Energy','CVX':'Energy','COP':'Energy','EOG':'Energy','OXY':'Energy',
    'SLB':'Energy','HAL':'Energy','MPC':'Energy','VLO':'Energy','PSX':'Energy',
    'DVN':'Energy','APA':'Energy','BKR':'Energy','HES':'Energy','MRO':'Energy',
    # ── S&P 500 Industrials ──
    'GE':'Industrial','CAT':'Industrial','DE':'Industrial','BA':'Industrial',
    'UPS':'Industrial','RTX':'Industrial','LMT':'Industrial','NOC':'Industrial',
    'GD':'Industrial','MMM':'Industrial','ITW':'Industrial','ETN':'Industrial',
    'EMR':'Industrial','ROK':'Industrial','PH':'Industrial','CMI':'Industrial',
    'IR':'Industrial','TT':'Industrial','CARR':'Industrial','OTIS':'Industrial',
    'URI':'Industrial','GWW':'Industrial',
    # ── S&P 500 Consumer ──
    'HD':'Consumer','NKE':'Consumer','MCD':'Consumer','TGT':'Consumer',
    'CMG':'Consumer','MAR':'Consumer','HLT':'Consumer','RCL':'Consumer',
    'CCL':'Consumer','YUM':'Consumer','DPZ':'Consumer','DHI':'Consumer',
    'LEN':'Consumer','PHM':'Consumer','F':'Consumer','GM':'Consumer',
    'WMT':'Consumer','PG':'Consumer','KO':'Consumer','PM':'Consumer',
    'MO':'Consumer','EL':'Consumer','CL':'Consumer','GIS':'Consumer',
    'K':'Consumer','KHC':'Consumer','STZ':'Consumer','TAP':'Consumer',
    'TSN':'Consumer','HRL':'Consumer','SJM':'Consumer','CAG':'Consumer','CPB':'Consumer',
    # ── S&P 500 Media / Comm ──
    'DIS':'Media','CMCSA':'Media','WBD':'Media','PARA':'Media',
    'T':'Telecom','VZ':'Telecom',
    # ── S&P 500 Real Estate ──
    'PLD':'RealEstate','AMT':'RealEstate','EQIX':'RealEstate','CCI':'RealEstate',
    'PSA':'RealEstate','EQR':'RealEstate','SPG':'RealEstate','O':'RealEstate',
    'VICI':'RealEstate','WELL':'RealEstate','DLR':'RealEstate',
    'IRM':'RealEstate','SBAC':'RealEstate',
    # ── S&P 500 Materials ──
    'LIN':'Materials','APD':'Materials','ECL':'Materials','SHW':'Materials',
    'PPG':'Materials','NEM':'Materials','FCX':'Materials','NUE':'Materials',
    'CF':'Materials','ALB':'Materials','DD':'Materials','DOW':'Materials','LYB':'Materials',
    # ── S&P 500 Utilities ──
    'NEE':'Utilities','DUK':'Utilities','SO':'Utilities','D':'Utilities',
    'EXC':'Utilities','SRE':'Utilities','PCG':'Utilities','ED':'Utilities',
    'WEC':'Utilities','ETR':'Utilities','PPL':'Utilities','CMS':'Utilities',
    'AES':'Utilities','CNP':'Utilities',
    # ── S&P 500 IT non-NASDAQ ──
    'IBM':'Software','ACN':'Software','NOW':'Software','ORCL':'Software',
    'CRM':'Software','SAP':'Software',
    # ── ETFs ──
    'SPY':'ETF','IWM':'ETF','DIA':'ETF','VTI':'ETF',
    'XLF':'ETF','XLK':'ETF','XLV':'ETF','XLE':'ETF','XLI':'ETF',
    'XLY':'ETF','XLP':'ETF','XLU':'ETF','XLB':'ETF','XLRE':'ETF','XLC':'ETF',
    'SOXX':'ETF','SMH':'ETF','IGV':'ETF','XBI':'ETF','IBB':'ETF',
    'EEM':'ETF','EFA':'ETF','GLD':'ETF','SLV':'ETF','USO':'ETF',
    'TLT':'ETF','ARKK':'ETF',
    # ── Russell 2000 ──
    'ACLS':'Semiconductor','CALX':'Software','FORM':'Semiconductor',
    'KLIC':'Semiconductor','COHU':'Semiconductor','CEVA':'Semiconductor',
    'AMBA':'Semiconductor','SLAB':'Semiconductor',
    'ARWR':'Biotech','PACB':'Biotech','NVAX':'Biotech','FATE':'Biotech',
    'IOVA':'Biotech','EDIT':'Biotech','CRSP':'Biotech','BEAM':'Biotech',
    'PLUG':'CleanEnergy','FCEL':'CleanEnergy','BLNK':'CleanEnergy',
    'CHPT':'CleanEnergy','EVGO':'CleanEnergy',
    'AVAV':'Defense','KTOS':'Defense',
    'GME':'Consumer','BOOT':'Consumer',
    'SM':'Energy','RRC':'Energy','SWN':'Energy',
    'DKNG':'Gaming','PENN':'Gaming',
    'MARA':'AI_Data','RIOT':'AI_Data',
    'HIMS':'Healthcare','LC':'Finance','UPST':'Finance',
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
