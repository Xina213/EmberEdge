#!/usr/bin/env python3
"""
EmberEdge - Copernicus Data Space Integration
Busca dados satélite Sentinel para análise de risco
"""

import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from copernicus_auth import get_copernicus_token

load_dotenv()

class CopernicusIntegration:
    """Integração Copernicus Data Space"""
    
    def __init__(self):
        self.token = None
        self.token_expires = None
    
    
    def get_valid_token(self):
        """Obter token válido (cached ou novo)"""
        
        # Se token existe e não expirou (com margem 5min)
        if self.token and self.token_expires:
            if datetime.now() < self.token_expires - timedelta(minutes=5):
                return self.token
        
        # Obter novo token
        print("🔑 Obtendo novo token Copernicus...")
        self.token = get_copernicus_token()
        
        if self.token:
            # Tokens Copernicus expiram em 30 minutos
            self.token_expires = datetime.now() + timedelta(minutes=30)
            print(f"✅ Token válido até: {self.token_expires.strftime('%H:%M:%S')}")
        
        return self.token
    
    
    def search_sentinel_data(self, bbox=(-10, 36, -5, 43), date_from=None, date_to=None):
        """
        Buscar dados Sentinel-2/3
        
        Args:
            bbox: (lon_min, lat_min, lon_max, lat_max) - Portugal por defeito
            date_from: data início (YYYY-MM-DD)
            date_to: data fim (YYYY-MM-DD)
        
        Returns:
            dict: resultados pesquisa
        """
        
        token = self.get_valid_token()
        if not token:
            print("❌ Sem token válido")
            return None
        
        # Datas padrão (últimos 7 dias)
        if not date_to:
            date_to = datetime.now().strftime('%Y-%m-%d')
        if not date_from:
            date_from = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        # API Catalog Copernicus
        url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
        
        # Query OData
        params = {
            '$filter': f"Collection/Name eq 'SENTINEL-3' and "
                      f"OData.CSC.Intersects(area=geography'SRID=4326;POLYGON(("
                      f"{bbox[0]} {bbox[1]}, {bbox[2]} {bbox[1]}, "
                      f"{bbox[2]} {bbox[3]}, {bbox[0]} {bbox[3]}, "
                      f"{bbox[0]} {bbox[1]}))') and "
                      f"ContentDate/Start ge {date_from}T00:00:00.000Z and "
                      f"ContentDate/Start le {date_to}T23:59:59.999Z",
            '$top': 10,
            '$orderby': 'ContentDate/Start desc'
        }
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        print(f"🛰️ Buscando Sentinel-3 ({date_from} a {date_to})...")
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            products = data.get('value', [])
            
            print(f"✅ {len(products)} produtos encontrados")
            
            return products
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro Copernicus API: {e}")
            return None
    
    
    def get_fire_radiative_power(self, product_id):
        """
        Download Fire Radiative Power (FRP) de produto Sentinel-3
        
        Args:
            product_id: ID do produto Copernicus
        
        Returns:
            bytes: dados produto
        """
        
        token = self.get_valid_token()
        if not token:
            return None
        
        url = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value"
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        print(f"📥 Downloading product {product_id}...")
        
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=120)
            response.raise_for_status()
            
            # Salvar ficheiro
            filename = f"../data/sentinel_{product_id}.zip"
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ Download completo: {filename}")
            return filename
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro download: {e}")
            return None


# ===== MAIN =====
if __name__ == '__main__':
    print("=" * 60)
    print("🛰️ COPERNICUS DATA SPACE - INTEGRAÇÃO EMBEREDGE")
    print("=" * 60)
    
    copernicus = CopernicusIntegration()
    
    # Testar token
    token = copernicus.get_valid_token()
    
    if token:
        print(f"\n✅ Token válido!")
        print(f"🔑 Token: {token[:50]}...")
        
        # Buscar produtos Sentinel-3 Portugal (últimos 7 dias)
        print("\n" + "-" * 60)
        products = copernicus.search_sentinel_data()
        
        if products:
            print("\n📦 PRODUTOS SENTINEL-3 ENCONTRADOS:")
            for idx, product in enumerate(products[:5], 1):
                print(f"\n{idx}. {product.get('Name', 'Unknown')}")
                print(f"   ID: {product.get('Id')}")
                print(f"   Data: {product.get('ContentDate', {}).get('Start')}")
                print(f"   Tamanho: {product.get('ContentLength', 0) / 1024 / 1024:.2f} MB")
        else:
            print("\n⚠️ Nenhum produto encontrado (normal se não há fogos activos)")
    
    else:
        print("\n❌ Falha ao obter token")
    
    print("\n" + "=" * 60)
    print("✅ TESTE COPERNICUS COMPLETO!")
