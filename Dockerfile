FROM python:3.12-slim

WORKDIR /app
COPY vwap_wave_monitor.py .

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('https://fapi.binance.com/fapi/v1/ping')" || exit 1

CMD ["python3", "vwap_wave_monitor.py", "--symbol", "XAUUSDT"]
LABEL description="Chris Drysdale VWAP Wave Gold Futures Monitor"
LABEL maintainer="Hermes Agent <hermes@local>"
