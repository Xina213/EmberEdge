import requests
import os
from dotenv import load_dotenv

load_dotenv()

COPERNICUS_CLIENT_ID = os.getenv('COPERNICUS_CLIENT_ID', 'your_client_id')
COPERNICUS_CLIENT_SECRET = os.getenv('COPERNICUS_CLIENT_SECRET', 'your_client_secret')

def get_copernicus_token():
    """Obter token OAuth2 Copernicus"""
    
    url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    
    data = {
        "grant_type": "client_credentials",
        "client_id": COPERNICUS_CLIENT_ID,
        "client_secret": COPERNICUS_CLIENT_SECRET
    }
    
    try:
        response = requests.post(url, data=data, timeout=30)
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get('access_token')
        
        print(f"✅ Token obtido: {access_token[:50]}...")
        return access_token
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro obter token: {e}")
        return None


# Testar
if __name__ == '__main__':
    token = get_copernicus_token()
    
    if token:
        print("\n🔑 TOKEN COPERNICUS:")
        print(f"Bearer {token}")
