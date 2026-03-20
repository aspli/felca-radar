from youtube_transcript_api import YouTubeTranscriptApi
import json
import re

# 1. Dicionário de Pesos (O "Cérebro" da moderação)
# Aqui você vai alimentar as gírias usadas em apologia ou erotização.
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

LIMITE_DE_RISCO = 10 # Pontuação mínima para o vídeo ser considerado "Perigoso"

def extrair_id_video(url):
    """Extrai o ID do vídeo a partir da URL do YouTube."""
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

def analisar_video(url):
    """Extrai a legenda e calcula a pontuação de risco."""
    video_id = extrair_id_video(url)
    if not video_id:
        return {"url": url, "status": "erro", "erro": "URL inválida"}

    try:
        # Puxa a legenda em Português
        transcricao = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt'])
        
        # Junta todas as linhas de texto em um único parágrafo e deixa em minúsculo
        texto_completo = " ".join([linha['text'] for linha in transcricao]).lower()
        
        pontuacao_total = 0
        termos_encontrados = []

        # Analisa o texto contra o nosso Dicionário de Risco
        for categoria, palavras in DICIONARIO_RISCO.items():
            for palavra, peso in palavras.items():
                ocorrencias = texto_completo.count(palavra)
                if ocorrencias > 0:
                    pontos = ocorrencias * peso
                    pontuacao_total += pontos
                    termos_encontrados.append(f"{palavra} ({ocorrencias}x)")

        eh_perigoso = pontuacao_total >= LIMITE_DE_RISCO

        return {
            "url": url,
            "status": "sucesso",
            "pontuacao_risco": pontuacao_total,
            "eh_perigoso": eh_perigoso,
            "termos_encontrados": termos_encontrados
        }

    except Exception as e:
        return {"url": url, "status": "erro", "erro": str(e)}

# ---------------------------------------------------------
# Testando o Sistema
# ---------------------------------------------------------
if __name__ == "__main__":
    print("🛡️ Iniciando Motor de Análise Radar FELCA...\n")
    
    # Lista de vídeos de teste (você pode colocar URLs reais aqui)
    lista_teste = [
        "https://www.youtube.com/watch?v=xAkFfiPID08", # Substitua por um clipe de funk problemático
        "https://www.youtube.com/watch?v=ExemploVideo2"  # Substitua por um vídeo normal
    ]

    videos_condenados = []

    for link in lista_teste:
        print(f"Analisando: {link}")
        resultado = analisar_video(link)
        
        if resultado["status"] == "sucesso":
            print(f" -> Pontuação: {resultado['pontuacao_risco']} | Perigoso: {resultado['eh_perigoso']}")
            if resultado['termos_encontrados']:
                print(f" -> Termos detectados: {', '.join(resultado['termos_encontrados'])}")
            
            # Se bateu o limite de risco, adiciona na lista final
            if resultado["eh_perigoso"]:
                videos_condenados.append(resultado["url"])
        else:
            print(f" -> Erro ao analisar: {resultado['erro']} (Pode não ter legenda gerada)")
        print("-" * 40)

    # Gera a saída no formato exato que a sua extensão (Aba Integração) espera ler!
    saida_api = {
        "videos": videos_condenados
    }
    
    print("\n📦 RESULTADO FINAL PARA A EXTENSÃO (JSON):")
    print(json.dumps(saida_api, indent=2))