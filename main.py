#!/usr/bin/env python3
# main.py
# Punto de entrada principal para línea de comandos

import logging
import argparse
from core.engine import GoldenEngine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Golden Capital Engine Ω')
    parser.add_argument('--markets', type=str, default='spot,margin,futures',
                        help='Mercados a analizar (separados por comas)')
    parser.add_argument('--capital', type=float, default=1000.0,
                        help='Capital inicial')
    parser.add_argument('--risk', type=float, default=0.02,
                        help='Riesgo por operación')
    args = parser.parse_args()

    config = {
        'capital': args.capital,
        'risk_per_trade': args.risk,
        'markets': args.markets.split(',')
    }

    engine = GoldenEngine(config)
    results = engine.run()

    logger.info("=" * 60)
    logger.info("🏛️ GOLDEN CAPITAL ENGINE Ω — RESULTADOS")
    logger.info("=" * 60)

    top5 = results.get('top5', pd.DataFrame())
    if not top5.empty:
        logger.info("\n🏆 TOP 5 ACTIVOS:")
        logger.info(top5[['symbol', 'market', 'score', 'win_rate', 'profit_factor']].to_string(index=False))
    else:
        logger.info("No se encontraron activos con señales válidas.")

    logger.info(f"\n📁 Resultados guardados en data/results/")

if __name__ == "__main__":
    main()
