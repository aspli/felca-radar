import spotipy
from spotipy.oauth2 import SpotifyOAuth
import lyricsgenius
import json
import re

# ==========================================
# 1. SUAS CHAVES DE API (Você precisará gerar depois)
# ==========================================
# Crie em: developer.spotify.com
SPOTIPY_CLIENT_ID = '42384f5714744fa7a1ed4125cf01bd29'
SPOTIPY_CLIENT_SECRET = 'c2ca580fa53e43ceabf901232408ca58'

# Crie em: genius.com/api-clients
GENIUS_ACCESS_TOKEN = 'vQss2tNCpI6ACnmvE5AS1Ml2GG3giQ-Rup7YOLaPD9GLaNbdsopvMwKH-ssiAsOK'

# ==========================================
# 2. CONFIGURAÇÃO DAS APIs E DICIONÁRIO
# ==========================================
# (Coloquei um try/except para o código não quebrar se você rodar sem as chaves ainda)
try:
    # A mágica muda aqui: Usamos o SpotifyOAuth e passamos o redirect_uri que você cadastrou!
    spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri="http://127.0.0.1:8080", 
        scope="playlist-read-private playlist-read-collaborative" 
    ))
    genius = lyricsgenius.Genius(GENIUS_ACCESS_TOKEN)
except Exception as e:
    print(f"⚠️ Aviso: As chaves de API não foram configuradas corretamente. Erro: {e}")

DICIONARIO_RISCO = {
    "crime": {
        "pcc": 5,
        "comando vermelho": 5,
        "cv": 3,
        "tudo 2": 4,
        "tudo 3": 4,
        "trem bala": 3,
        "fuzil": 3,
        "biqueira": 2,
        "fogueteiro": 4,
        "mochila": 4,
        "mochilinha": 4,
        "glock": 4,
        "radin": 4,
        "trafico": 4
    },
    "erotizacao_infantil": {
        "novinha": 4,
        "menina": 2,
        "sentando": 3,
        "safado": 3,
        "novinha senta": 5,
        "lambendo": 5,
        "lamber": 5,
        "chupar": 5,
        "satisfazer": 5,
        "rebolo": 5,
        "quicando": 5,
        "de quatro": 10,
        "fuder": 10,
        "porra": 7,
        "raba": 5,
        "calcinha": 5
        # Adicione mais termos conforme mapear as letras
    }
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
        "https://open.spotify.com/intl-pt/track/0YqTL3nSL36OFdHwHoqCag?si=1b8eb72d3f9d4671" 
    ]

    musicas_condenadas = []

    for link in lista_teste:
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

def extrair_tracks_da_playlist(playlist_url):
    """Lê QUALQUER playlist do Spotify (Normal ou Ranking) e extrai os links."""
    try:
        # 1. Extrai o ID
        match = re.search(r"playlist\/([a-zA-Z0-9]+)", playlist_url)
        if not match:
            return {"status": "erro", "erro": "Link inválido."}
        
        playlist_id = match.group(1)
        print(f"📂 Abrindo playlist ID: {playlist_id}")
        
        # 2. Tenta ler como playlist normal, se der erro, tenta como ranking
        try:
            resultados = spotify.playlist_tracks(playlist_id)
        except:
            # Plano B: Algumas playlists de ranking exigem este formato
            resultados = spotify.playlist(playlist_id)['tracks']
            
        tracks = resultados['items']
        
        # Lida com paginação (playlists com mais de 100 músicas)
        while resultados['next']:
            resultados = spotify.next(resultados)
            # Se for o formato do Plano B, precisamos pegar a chave 'tracks'
            if 'tracks' in resultados:
                tracks.extend(resultados['tracks']['items'])
            else:
                tracks.extend(resultados['items'])
            
        links_musicas = []
        for item in tracks:
            # Algumas playlists de ranking têm uma estrutura de dados diferente
            track = item.get('track') if item.get('track') else item
            
            if track and 'external_urls' in track and 'spotify' in track['external_urls']:
                links_musicas.append(track['external_urls']['spotify'])
                
        return {
            "status": "sucesso", 
            "total": len(links_musicas),
            "links": links_musicas
        }
        
    except Exception as e:
        return {"status": "erro", "erro": str(e)}