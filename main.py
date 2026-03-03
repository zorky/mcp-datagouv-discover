"""
Explorateur du serveur MCP data.gouv.fr
https://mcp.data.gouv.fr/mcp
"""

import asyncio
import json
import streamlit as st
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

MCP_URL = "https://mcp.data.gouv.fr/mcp"

# ── helpers async ──────────────────────────────────────────────────────────────

async def fetch_tools():
    async with streamablehttp_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return result.tools

async def fetch_resources():
    async with streamablehttp_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            try:
                result = await session.list_resources()
                return result.resources
            except Exception:
                return []

async def fetch_prompts():
    async with streamablehttp_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            try:
                result = await session.list_prompts()
                return result.prompts
            except Exception:
                return []

async def call_tool(tool_name: str, arguments: dict):
    async with streamablehttp_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=arguments)
            return result

# ── wrappers sync ──────────────────────────────────────────────────────────────

def run(coro):
    return asyncio.run(coro)

# ── UI ────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="data.gouv.fr MCP Explorer",
    page_icon="🇫🇷",
    layout="wide",
)

st.title("🇫🇷 data.gouv.fr — MCP Explorer")
st.caption(f"Connecté à : `{MCP_URL}`")

# ── Sidebar : navigation ──────────────────────────────────────────────────────
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Section",
    ["🔧 Outils disponibles", "📦 Ressources & Prompts", "▶️ Appeler un outil"],
)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Outils
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🔧 Outils disponibles":
    st.header("🔧 Outils disponibles")

    if st.button("🔄 Charger les outils", type="primary"):
        with st.spinner("Connexion au serveur MCP..."):
            try:
                tools = run(fetch_tools())
                st.session_state["tools"] = tools
                st.success(f"{len(tools)} outil(s) trouvé(s)")
            except Exception as e:
                st.error(f"Erreur : {e}")

    if "tools" in st.session_state:
        tools = st.session_state["tools"]

        # Filtre texte
        search = st.text_input("🔍 Filtrer par nom / description", "")
        filtered = [
            t for t in tools
            if search.lower() in t.name.lower()
            or search.lower() in (t.description or "").lower()
        ] if search else tools

        st.markdown(f"**{len(filtered)} outil(s) affichés**")

        for tool in filtered:
            with st.expander(f"**`{tool.name}`**  —  {tool.description or ''}"):
                schema = tool.inputSchema or {}
                props = schema.get("properties", {})
                required = schema.get("required", [])

                if props:
                    st.markdown("**Paramètres :**")
                    rows = []
                    for param, meta in props.items():
                        rows.append({
                            "Nom": param,
                            "Type": meta.get("type", "?"),
                            "Requis": "✅" if param in required else "",
                            "Description": meta.get("description", ""),
                        })
                    st.table(rows)
                else:
                    st.info("Aucun paramètre.")

                st.markdown("**Schéma JSON brut :**")
                st.json(schema)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Ressources & Prompts
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📦 Ressources & Prompts":
    st.header("📦 Ressources & Prompts")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Ressources")
        if st.button("Charger les ressources"):
            with st.spinner("..."):
                try:
                    resources = run(fetch_resources())
                    st.session_state["resources"] = resources
                except Exception as e:
                    st.error(str(e))

        if "resources" in st.session_state:
            resources = st.session_state["resources"]
            if resources:
                for r in resources:
                    st.markdown(f"- **{r.name}** — `{r.uri}`")
            else:
                st.info("Aucune ressource exposée.")

    with col2:
        st.subheader("Prompts")
        if st.button("Charger les prompts"):
            with st.spinner("..."):
                try:
                    prompts = run(fetch_prompts())
                    st.session_state["prompts"] = prompts
                except Exception as e:
                    st.error(str(e))

        if "prompts" in st.session_state:
            prompts = st.session_state["prompts"]
            if prompts:
                for p in prompts:
                    with st.expander(f"**{p.name}**"):
                        st.write(p.description or "")
                        if hasattr(p, "arguments") and p.arguments:
                            st.json([a.__dict__ for a in p.arguments])
            else:
                st.info("Aucun prompt exposé.")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Appeler un outil
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "▶️ Appeler un outil":
    st.header("▶️ Appeler un outil")

    # Charger les outils si pas encore fait
    if "tools" not in st.session_state:
        with st.spinner("Chargement de la liste des outils..."):
            try:
                st.session_state["tools"] = run(fetch_tools())
            except Exception as e:
                st.error(str(e))
                st.stop()

    tools = st.session_state.get("tools", [])
    tool_names = [t.name for t in tools]

    selected_name = st.selectbox("Choisir un outil", tool_names)
    selected_tool = next((t for t in tools if t.name == selected_name), None)

    if selected_tool:
        st.markdown(f"> {selected_tool.description or ''}")

        schema = selected_tool.inputSchema or {}
        props = schema.get("properties", {})
        required = schema.get("required", [])

        # Formulaire dynamique
        st.subheader("Paramètres")
        arg_values = {}

        if props:
            for param, meta in props.items():
                label = f"**{param}**{'  *(requis)*' if param in required else ''}"
                desc = meta.get("description", "")
                ptype = meta.get("type", "string")

                if ptype == "integer":
                    arg_values[param] = st.number_input(
                        label, step=1, help=desc, value=1
                    )
                elif ptype == "number":
                    arg_values[param] = st.number_input(label, help=desc, value=0.0)
                elif ptype == "boolean":
                    arg_values[param] = st.checkbox(label, help=desc)
                else:
                    arg_values[param] = st.text_input(label, help=desc)
        else:
            st.info("Cet outil ne prend aucun paramètre.")

        # Option : JSON brut
        with st.expander("Ou saisir les arguments en JSON brut"):
            raw_json = st.text_area("Arguments JSON", value="{}", height=100)

        # Bouton d'appel
        if st.button("🚀 Exécuter", type="primary"):
            # Priorité au JSON brut s'il est modifié
            try:
                parsed_raw = json.loads(raw_json)
                arguments = parsed_raw if parsed_raw else {
                    k: v for k, v in arg_values.items() if v not in ("", None)
                }
            except json.JSONDecodeError:
                st.error("JSON invalide dans le champ brut.")
                st.stop()

            with st.spinner(f"Appel de `{selected_name}`..."):
                try:
                    result = run(call_tool(selected_name, arguments))
                    st.success("Réponse reçue ✅")

                    for block in result.content:
                        if block.type == "text":
                            # Essayer d'afficher comme JSON si possible
                            try:
                                parsed = json.loads(block.text)
                                st.json(parsed)
                            except Exception:
                                st.markdown(block.text)
                        else:
                            st.write(block)

                    if result.isError:
                        st.warning("Le serveur a retourné une erreur dans le résultat.")

                except Exception as e:
                    st.error(f"Erreur lors de l'appel : {e}")

# ── Footer ────────────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown(
    "[🔗 GitHub datagouv-mcp](https://github.com/datagouv/datagouv-mcp)  \n"
    "[🔗 data.gouv.fr](https://www.data.gouv.fr)"
)