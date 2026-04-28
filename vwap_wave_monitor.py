#!/usr/bin/env python3
"""
Futures Trading Monitor: Chris Drysdale VWAP Wave System
Alerts on price touching 2nd deviation bands for potential reversals.
Uses Binance BTCUSDT perpetual futures (public API, no key needed).
Rolling 500 1m bars (~8hr window).
"""

import urllib.request
import json
import time
import sys
import math
from datetime import datetime

def fetch_klines(symbol='XAUUSDT', interval='1m', limit=500):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        bars = []
        for bar in data:
            # [ts, o, h, l, c, v, ...]
            o, h, l, c, v = map(float, bar[1:6])
            tp = (h + l + c) / 3
            bars.append({'o':o, 'h':h, 'l':l, 'c':c, 'tp':tp, 'v':v})
        return bars
    except Exception as e:
        print(f"Fetch error: {e}", file=sys.stderr)
        return []

def compute_vwap_bands(bars):
    if not bars:
        return None
    cum_pv = 0.0
    cum_vol = 0.0
    cum_var = 0.0
    vwap_history = []
    sd_history = []
    for bar in bars:
        tpv = bar['tp'] * bar['v']
        cum_pv += tpv
        cum_vol += bar['v']
        vwap = cum_pv / cum_vol if cum_vol > 0 else bar['c']
        dev = bar['tp'] - vwap
        cum_var += bar['v'] * dev * dev
        sd = math.sqrt(cum_var / cum_vol) if cum_vol > 0 else 0
        vwap_history.append(vwap)
        sd_history.append(sd)
        bar['vwap'] = vwap
        bar['sd'] = sd
    upper_2sd = vwap_history[-1] + 2 * sd_history[-1]
    lower_2sd = vwap_history[-1] - 2 * sd_history[-1]
    return bars[-1], upper_2sd, lower_2sd  # latest bar + bands

def main(symbol='XAUUSDT'):
    print(f"🚀 Gold Futures VWAP Wave Monitor (XAUUSDT perp, Chris Drysdale system)")
    print("Press Ctrl+C to stop")
    while True:
        try:
            bars = fetch_klines(symbol)
            if not bars:
                time.sleep(30)
                continue
            latest, upper2, lower2 = compute_vwap_bands(bars)
            prev = bars[-2] if len(bars) > 1 else latest

            # Alert logic: touch but close inside (rejection)
            alert = ""
            if latest['h'] >= upper2 and latest['c'] < upper2:
                alert = f"🚨 SHORT REVERSAL ALERT: High {latest['h']:.2f} touched upper 2SD {upper2:.2f}, closed {latest['c']:.2f}"
            elif latest['l'] <= lower2 and latest['c'] > lower2:
                alert = f"🚨 LONG REVERSAL ALERT: Low {latest['l']:.2f} touched lower 2SD {lower2:.2f}, closed {latest['c']:.2f}"

            ts = datetime.fromtimestamp(bars[-1]['o']/1000/60*60).strftime('%H:%M')  # approx bar time
            print(f"[{ts}] Price: {latest['c']:.2f} | VWAP: {latest['vwap']:.2f} | U2: {upper2:.2f} | L2: {lower2:.2f} {alert}")

            if alert:
                print(alert)

            time.sleep(30)  # Poll every 30s (mid-bar updates via latest closed)
        except KeyboardInterrupt:
            print("\n🛑 Monitor stopped")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            time.sleep(30)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', default='BTCUSDT', help='Futures symbol e.g. BTCUSDT ETHUSDT')
    args = parser.parse_args()
    main(args.symbol)