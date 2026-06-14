import streamlit as st
import pandas as pd
import plotly.express as px
from ai_core import engine# Usamos la librería gráfica avanzada e interactiva

def render_all_metrics(data_dict, area):
    """Muestra la superficie y las tarjetas de métricas integrando la desviación como delta."""
    st.metric("📐 Superficie del Área Seleccionada", f"{area:.2f} Hectáreas")
    st.markdown("### 📊 Diagnóstico Biofísico del Lote")
    
    # Cuadrícula de 3 columnas para optimizar el espacio horizontal
    cols = st.columns(3)
    
    for idx, (capa, metrica) in enumerate(data_dict.items()):
        with cols[idx % 3]:
            # Formato original limpio: Desviación estándar abajo como delta sutil
            st.metric(
                label=f"Índice {capa}", 
                value=f"{metrica['mean']:.4f}", 
                delta=f"± {metrica['std']:.4f} (Disp.)",
                delta_color="neutral"  # Tono gris para no confundir con alertas agrícolas
            )

def render_historical_chart(datos_historial, title):
    """Construye gráficos interactivos con Plotly detallando y filtrando datos corruptos."""
    if not datos_historial:
        st.info("No hay datos históricos registrados.")
        return
    
    # 1. Preparación de los datos base
    df = pd.DataFrame(list(datos_historial.items()), columns=["Fecha", "Valor"])
    df = df.dropna().sort_values(by="Fecha")
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    
    # Guardamos una copia intacta del valor original para poder contrastar en el gráfico
    df["Valor Original"] = df["Valor"]
    df["Estado"] = "Dato Limpio"

    st.markdown("#### 🧼 Depuración y Diagnóstico de la Serie Temporal")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtrar = st.checkbox("Activar filtro atmosférico (Suavizar picos por nubes)", value=True, key=f"clip_{title}")
    with col_f2:
        umbral = st.slider("Sensibilidad del filtro (Desviaciones Sigma)", 1.0, 3.0, 2.0, step=0.5, key=f"sig_{title}")
    
    # 2. Algoritmo Estadístico de Detección de Anomalías Atmosféricas
    if filtrar and len(df) > 3:
        # Mediana móvil central para calcular el comportamiento real del cultivo
        rolling_median = df["Valor"].rolling(window=3, center=True, min_periods=1).median()
        rolling_std = df["Valor"].rolling(window=3, center=True, min_periods=1).std().fillna(0)
        
        # Si la caída o pico supera el umbral sigma local, se etiqueta como corrupto (nubes/ruido)
        anomalos = (df["Valor"] - rolling_median).abs() > (umbral * rolling_std)
        
        # Marcamos los puntos corruptos en la metadata del gráfico
        df.loc[anomalos, "Estado"] = "Ruido/Nube Detectada"
        # Reemplazamos el valor corrupto por la tendencia limpia estimada
        df.loc[anomalos, "Valor"] = rolling_median[anomalos]

    # 3. Construcción del Gráfico Avanzado Interactiva con Plotly
    fig = px.line(
        df, 
        x="Fecha", 
        y="Valor", 
        title=f"Evolución Cronológica: {title}",
        markers=True,
        labels={"Valor": "Valor del Índice", "Fecha": "Fecha de Captura"}
    )
    
    # Si hay datos filtrados, agregamos los puntos corruptos originales en color rojo para que se puedan auditar
    if filtrar and df["Estado"].str.contains("Ruido/Nube Detectada").any():
        df_anomalos = df[df["Estado"] == "Ruido/Nube Detectada"]
        fig.add_scatter(
            x=df_anomalos["Fecha"],
            y=df_anomalos["Valor Original"],
            mode="markers",
            name="⚠️ Picos Corruptos (Nubes)",
            marker=dict(color="crimson", size=10, symbol="x"),
            hovertemplate="<b>Fecha:</b> %{x}<br><b>Valor Corrupto:</b> %{y}<br><extra></extra>"
        )

    # Personalización estética del lienzo gráfico para que combine con Vortex 2.0
    fig.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=50, b=20),
        height=400
    )
    
    # Renderizado final en la interfaz
    st.plotly_chart(fig, use_container_width=True)
    
    if filtrar and df["Estado"].str.contains("Ruido/Nube Detectada").any():
        st.caption("✨ El gráfico muestra la tendencia suavizada. Las marcas rojas (X) indican las capturas corruptas por nubosidad aisladas automáticamente.")

def render_weather_dashboard(data):
    """Renderiza el panel de datos climáticos obtenidos en la UI."""
    if not data:
        st.warning("No hay datos climáticos disponibles para esta región.")
        return
        
    st.subheader("☁️ Condiciones Climáticas Actuales")
    col1, col2, col3 = st.columns(3)
    col1.metric("Temperatura", f"{data.get('temp', 0.0):.1f} °C")
    col2.metric("Humedad", f"{data.get('humidity', 0)} %")
    col3.metric("Precipitación", f"{data.get('precipitation', 0.0)} mm")
    st.write(f"Condición predominante: **{data.get('condition', 'Desconocida')}**")

def render_ndvi_preview(url, layer_name):
    """Muestra la miniatura estática de la capa generada por Google Earth Engine."""
    if url:
        st.image(url, caption=f"Previsualización actual de la capa: {layer_name}", use_container_width=True)
    else:
        st.info(f"Previsualización estática no disponible para la capa {layer_name} en este rango.")

def render_suggestion_buttons():
    """Renderiza tarjetas de sugerencias para el agricultor."""
    st.markdown("#### ¿En qué puedo ayudarte hoy?")
    cols = st.columns(3)
    
    # Definimos sugerencias inteligentes
    sugerencias = [
        ("🔍 Analizar anomalías", "Identifica las zonas de menor vigor en esta imagen satelital."),
        ("💧 Estrés Hídrico", "¿Cómo se correlaciona el índice NDWI con el estado hídrico actual?"),
        ("📈 Tendencia Lote", "Resume el comportamiento histórico del cultivo según los datos mostrados.")
    ]
    
    for i, (label, prompt) in enumerate(sugerencias):
        if cols[i].button(label, use_container_width=True, key=f"sug_{i}"):
            st.session_state.pending_prompt = prompt
            st.rerun()

def render_ai_chat_tab(api_configurada, system_prompt, obtener_contexto_fn):
    """
    Renderiza la interfaz tipo Gemini centrada y moderna.
    """
    # Layout centralizado (10% | 80% | 10%)
    _, col_main, _ = st.columns([1, 8, 1])

    with col_main:
        st.subheader("🤖 Gemini Agronómico")
        
        if not api_configurada:
            st.error("Motor de IA no configurado.")
            return

        if "gemini_chat_history" not in st.session_state:
            st.session_state.gemini_chat_history = []

        # Historial de mensajes
        for message in st.session_state.gemini_chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Si no hay historial, mostramos sugerencias iniciales
        if not st.session_state.gemini_chat_history:
            render_suggestion_buttons()

        # Captura de input (Usuario escribe o clic en sugerencia)
        prompt_input = st.chat_input("Consulta diagnóstica...")
        
        # Lógica para manejar input del usuario O clic en sugerencia
        final_prompt = None
        if prompt_input:
            final_prompt = prompt_input
        elif "pending_prompt" in st.session_state:
            final_prompt = st.session_state.pending_prompt
            del st.session_state.pending_prompt # Limpiamos

        if final_prompt:
            # Flujo de respuesta unificado
            st.session_state.gemini_chat_history.append({"role": "user", "content": final_prompt})
            with st.chat_message("user"):
                st.markdown(final_prompt)

            with st.chat_message("assistant"):
                with st.spinner("Analizando con referencia espacial..."):
                    try:
                        # Obtenemos el contexto (esto carga la imagen y el bbox)
                        contexto_total = obtener_contexto_fn() 
                        
                        respuesta = engine.consultar_agronomo(
                            prompt=final_prompt, 
                            contexto_espacial=contexto_total,
                            imagen_bytes=st.session_state.get("temp_img_bytes")
                        )
                        st.markdown(respuesta)
                        st.session_state.gemini_chat_history.append({"role": "assistant", "content": respuesta})
                        
                        # Recargamos para limpiar botones si es necesario
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error técnico: {e}")