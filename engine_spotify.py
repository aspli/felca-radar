import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import lyricsgenius
import json
import re

# ==========================================
# 1. SUAS CHAVES DE API (Você precisará gerar depois)
# ==========================================
# Crie em: developer.spotify.com
SPOTIPY_CLIENT_ID = 'COLE_SEU_CLIENT_ID_AQUI'
SPOTIPY_CLIENT_SECRET = 'COLE_SEU_CLIENT_SECRET_AQUI'

# Crie em: genius.com/api-clients
GENIUS_ACCESS_TOKEN = 'COLE_SEU_TOKEN_DO_GENIUS_AQUI'

# ==========================================
# 2. CONFIGURAÇÃO DAS APIs E DICIONÁRIO
# ==========================================
# (Coloquei um try/except para o código não quebrar se você rodar sem as chaves ainda)
try:
    spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET))
    genius = lyricsgenius.Genius(GENIUS_ACCESS_TOKEN, verbose=False)
except:
    print("⚠️ Aviso: As chaves de API não foram configuradas corretamente.")

DICIONARIO_RISCO = {
    "crime": {"pcc": 5, "comando vermelho": 5, "cv": 3, "tudo 2": 4, "tudo 3": 4, "trem bala": 3},
    "erotizacao_infantil": {"novinha": 4, "menina": 2, "sentando": 3}
}
LIMITE_DE_RISCO = 10

# ==========================================
# 3. MOTOR DE ANÁLISE
# ==========================================
def analisar_musica_spotify(spotify_url):
    """Puxa a música do Spotify, busca a letra no Genius e analisa."""
    try:
        # 1. Pega os dados da música no Spotify
        track_info = spotify.track(spotify_url)
        nome_musica = track_info['name']
        nome_artista = track_info['artists'][0]['name']
        
        print(f"🎵 Encontrado: {nome_musica} - {nome_artista}")

        # 2. Busca a letra no Genius
        musica_genius = genius.search_song(nome_musica, nome_artista)
        
        if not musica_genius:
            return {"url": spotify_url, "status": "erro", "erro": "Letra não encontrada no Genius"}

        letra = musica_genius.lyrics.lower()

        # 3. Passa o Filtro de Risco
        pontuacao_total = 0
        termos_encontrados = []

        for categoria, palavras in DICIONARIO_RISCO.items():
            for palavra, peso in palavras.items():
                ocorrencias = letra.count(palavra)
                if ocorrencias > 0:
                    pontuacao_total += (ocorrencias * peso)
                    termos_encontrados.append(f"{palavra} ({ocorrencias}x)")

        eh_perigoso = pontuacao_total >= LIMITE_DE_RISCO

        return {
            "url": spotify_url,
            "status": "sucesso",
            "musica": f"{nome_musica} - {nome_artista}",
            "pontuacao_risco": pontuacao_total,
            "eh_perigoso": eh_perigoso,
            "termos_encontrados": termos_encontrados
        }

    except Exception as e:
        return {"url": spotify_url, "status": "erro", "erro": str(e)}

# ==========================================
# 4. TESTANDO O SISTEMA
# ==========================================
if __name__ == "__main__":
    print("🛡️ Iniciando Radar FELCA (Módulo Spotify)...\n")
    
    # Exemplo: Cole o link de uma música do Spotify aqui
    lista_teste = [
        "https://open.spotify.com/track/EXEMPLO_ID_MUSICA" 
    ]

    musicas_condenadas = []

    for link in lista_teste:
        if SPOTIPY_CLIENT_ID == 'COLE_SEU_CLIENT_ID_AQUI':
            print("❌ Erro: Você precisa colocar suas chaves de API no código para testar.")
            break
            
        resultado = analisar_musica_spotify(link)
        
        if resultado["status"] == "sucesso":
            print(f" -> Pontuação: {resultado['pontuacao_risco']} | Perigoso: {resultado['eh_perigoso']}")
            if resultado['termos_encontrados']:
                print(f" -> Termos: {', '.join(resultado['termos_encontrados'])}")
            
            if resultado["eh_perigoso"]:
                musicas_condenadas.append(resultado["url"])
        else:
            print(f" -> Erro: {resultado['erro']}")
        print("-" * 40)

    # Saída final
    print("\n📦 RESULTADO FINAL:")
    print(json.dumps({"spotify_tracks": musicas_condenadas}, indent=2))