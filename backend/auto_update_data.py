#!/usr/bin/env python3
"""
EmberEdge - Auto-Update Data Service
Busca NASA FIRMS + OpenWeatherMap automaticamente a cada 30 minutos
"""

import time
import subprocess
import os
from datetime import datetime
import sys

UPDATE_INTERVAL = 30 * 60


def run_script(script_name):
    """Executar script Python"""

    print(f"\n{'='*70}")
    print(f"🔄 Executando {script_name}...")
    print(f"{'='*70}")

    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__),
            timeout=120
        )

        print(result.stdout)

        if result.returncode == 0:
            print(f"✅ {script_name} completado com sucesso")
            return True
        else:
            print(f"⚠️ {script_name} warning:")
            print(result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print(f"⏱️ {script_name} timeout (>2min)")
        return False
    except Exception as e:
        print(f"❌ Erro {script_name}: {e}")
        return False


def update_all_data():
    """Atualizar todos os dados"""

    print("\n" + "="*70)
    print("🛰️ AUTO-UPDATE INICIANDO")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    # 1. NASA FIRMS (fogos ativos)
    firms_ok = run_script('fetch_nasa_firms.py')

    # 2. OpenWeatherMap (meteorologia atual e previsão)
    weather_ok = run_script('fetch_weather.py')

    # 3. NDVI via Copernicus (se disponível)
    ndvi_ok = run_script('fetch_ndvi.py')

    # Resultado
    print("\n" + "="*70)
    print("📊 AUTO-UPDATE RESULTADO:")
    print(f"   NASA FIRMS: {'✅' if firms_ok else '⚠️'}")
    print(f"   OpenWeatherMap: {'✅' if weather_ok else '⚠️'}")
    print(f"   NDVI Copernicus: {'✅' if ndvi_ok else '⚠️'}")
    print(f"   Próxima atualização: {UPDATE_INTERVAL // 60} minutos")
    print("="*70 + "\n")

    return firms_ok and weather_ok


def main():
    """Loop principal auto-update"""

    print("\n" + "🔥"*35)
    print("🔥 EMBEREDGE AUTO-UPDATE SERVICE")
    print("🔥"*35)
    print(f"\n⏱️  Intervalo: {UPDATE_INTERVAL // 60} minutos")
    print(f"🛰️  Fontes: NASA FIRMS + OpenWeatherMap + NDVI Copernicus")
    print(f"🔄  Modo: Loop contínuo")
    print("\n" + "="*70)

    iteration = 0

    while True:
        iteration += 1

        print(f"\n🔄 ITERAÇÃO #{iteration}")

        try:
            success = update_all_data()

            if success:
                print(f"✅ Atualização #{iteration} completa")
            else:
                print(f"⚠️ Atualização #{iteration} com warnings")

            print(f"\n💤 Sleeping {UPDATE_INTERVAL // 60} minutos...")
            print(f"   Próxima: {datetime.now().strftime('%H:%M:%S')} + {UPDATE_INTERVAL // 60}min")
            print(f"   (Ctrl+C para parar)")

            time.sleep(UPDATE_INTERVAL)

        except KeyboardInterrupt:
            print("\n\n⚠️ Auto-update interrompido pelo utilizador")
            print("👋 Bye!")
            break

        except Exception as e:
            print(f"\n❌ Erro no loop: {e}")
            print("⏱️ Retry em 5 minutos...")
            time.sleep(5 * 60)


if __name__ == '__main__':
    main()