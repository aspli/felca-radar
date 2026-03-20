import streamlit as st
import json
from engine_spotify import analisar_musica_spotify, extrair_tracks_da_playlist

# Configuração da página
st.set_page_config(page_title="Radar FELCA", page_icon="🛡️", layout="wide")

st.title("🛡️ Radar FELCA")
st.subheader("Central de Comando e Análise de Risco (Módulo Spotify)")

# Criando Abas para separar as ferramentas
aba1, aba2 = st.tabs(["🎵 Músicas Avulsas", "📂 Varredura de Playlists"])

links_para_analisar = []

# ==========================================
# ABA 1: MÚSICAS AVULSAS
# ==========================================
with aba1:
    st.markdown("Cole os links do Spotify abaixo (um por linha).")
    links_input = st.text_area("Links das músicas:", height=150, key="avulsas")
    
    if st.button("Iniciar Varredura em Lote", type="primary", key="btn_avulso"):
        if links_input.strip():
            links_para_analisar = [link.strip() for link in links_input.split('\n') if link.strip()]
        else:
            st.warning("⚠️ Insira pelo menos um link.")

# ==========================================
# ABA 2: PLAYLISTS INTEIRAS
# ==========================================
with aba2:
    st.markdown("Cole o link de uma Playlist do Spotify. O sistema vai extrair todas as músicas e analisar uma por uma.")
    playlist_input = st.text_input("Link da Playlist:", placeholder="https://open.spotify.com/playlist/...")
    
    if st.button("Extrair e Analisar Playlist", type="primary", key="btn_playlist"):
        if playlist_input.strip():
            with st.spinner("Extraindo músicas da playlist..."):
                extracao = extrair_tracks_da_playlist(playlist_input.strip())
                
                if extracao["status"] == "sucesso":
                    links_para_analisar = extracao["links"]
                    st.success(f"📦 Encontradas {extracao['total']} músicas na playlist! Iniciando varredura profunda...")
                else:
                    st.error(f"❌ Erro ao ler playlist: {extracao['erro']}")
        else:
            st.warning("⚠️ Insira o link da playlist.")

# ==========================================
# O MOTOR DE EXECUÇÃO (Serve para as duas abas)
# ==========================================
if links_para_analisar:
    st.info(f"⏳ Analisando {len(links_para_analisar)} música(s)... Isso pode levar alguns minutos.")
    
    progress_bar = st.progress(0)
    resultados_perigosos = []
    links_condenados = []
    
    for i, link in enumerate(links_para_analisar):
        with st.spinner(f"Analisando link {i+1} de {len(links_para_analisar)}..."):
            resultado = analisar_musica_spotify(link)
            
            if resultado["status"] == "sucesso" and resultado["eh_perigoso"]:
                resultados_perigosos.append(resultado)
                links_condenados.append(resultado["url"])
        
        progress_bar.progress((i + 1) / len(links_para_analisar))
        
    st.success("✅ Varredura concluída!")
    st.divider()
    
    if resultados_perigosos:
        st.error(f"🚨 Encontramos {len(resultados_perigosos)} música(s) classificada(s) como Risco Alto!")
        
        for res in resultados_perigosos:
            with st.expander(f"🎵 {res['musica']} — Pontuação: {res['pontuacao_risco']}"):
                st.write(f"**Termos detectados:** {', '.join(res['termos_encontrados'])}")
                st.write(f"**Link:** {res['url']}")
        
        st.subheader("📦 Pacote de Integração")
        payload = {"spotify_tracks": links_condenados}
        st.json(payload)
    else:
        st.success("🎉 Nenhuma música perigosa encontrada nesta remessa. Tudo limpo!")