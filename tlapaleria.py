import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import uuid
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE LA INTERFAZ DE LA TLAPALERÍA ---
st.set_page_config(page_title="Tlapalería El Gran Perno ERP v15", layout="wide", initial_sidebar_state="expanded")
DB_NAME = "tlapaleria_v15.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS inventario (
            categoria TEXT, articulo TEXT, marca TEXT, medida_presentacion TEXT, 
            stock INTEGER, p_compra REAL, p_venta REAL, SKU TEXT, 
            PRIMARY KEY (articulo, marca, medida_presentacion))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS ventas (
            transaccion_id TEXT, fecha TEXT, hora TEXT, cliente_id TEXT, categoria TEXT, 
            articulo TEXT, marca TEXT, medida_presentacion TEXT, cantidad INTEGER, 
            p_venta REAL, descuento_aplicado REAL, total REAL, metodo_pago TEXT, estado TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS apartados (
            id TEXT, cliente TEXT, telefono TEXT, fecha TEXT, articulo TEXT, 
            marca TEXT, medida_presentacion TEXT, cantidad INTEGER, total REAL, estado TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS compras_proveedor (
            compra_id TEXT, fecha TEXT, articulo TEXT, marca TEXT, medida_presentacion TEXT, 
            cantidad INTEGER, p_compra REAL, total_invertido REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
            telefono TEXT PRIMARY KEY, nombre TEXT, puntos INTEGER, fecha_registro TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS cupones (
            codigo TEXT PRIMARY KEY, tipo TEXT, valor REAL, activo INTEGER)''')
        conn.commit()

def run_query(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()

def get_df(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql_query(query, conn, params=params)

init_db()

# --- CONFIGURACIÓN DE SESIÓN Y REGISTROS INICIALES ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []
if 'cupón_act' not in st.session_state:
    st.session_state.cupón_act = {"codigo": "", "tipo": "Fijo", "valor": 0.0}
if 'cliente_activo' not in st.session_state:
    st.session_state.cliente_activo = None
if 'ticket_a_imprimir' not in st.session_state:
    st.session_state.ticket_a_imprimir = None

# Cupones promocionales por defecto
if get_df("SELECT COUNT(*) as c FROM cupones").iloc[0]['c'] == 0:
    run_query("INSERT INTO cupones VALUES (?, ?, ?, ?)", ("MAESTRO10", "Porcentaje", 10.0, 1))
    run_query("INSERT INTO cupones VALUES (?, ?, ?, ?)", ("DESCUENTOTLAPA", "Fijo", 50.0, 1))

# Registro automatizado de 50 artículos estables de tlapalería y ferretería
if get_df("SELECT COUNT(*) as c FROM inventario").iloc[0]['c'] == 0:
    herramientas_iniciales = [
        ("Herramienta Manual", "Martillo de Uña Galonero", "Truper", "16 oz", 15, 85.0, 145.0),
        ("Herramienta Manual", "Martillo de Bola", "Pretul", "12 oz", 10, 60.0, 110.0),
        ("Ferretería General", "Tornillo Hexagonal Galvanizado", "Fiero", "1/4 x 2 Pulgadas", 500, 1.2, 3.5),
        ("Ferretería General", "Tornillo Hexagonal Galvanizado", "Fiero", "3/8 x 3 Pulgadas", 300, 2.1, 5.5),
        ("Ferretería General", "Clavo para Madera con Cabeza", "Fiero", "2 Pulgadas - 1kg", 40, 32.0, 65.0),
        ("Ferretería General", "Clavo para Concreto Negro", "Fiero", "1 Pulgada - 1kg", 25, 45.0, 85.0),
        ("Plomería", "Tubo de PVC Sanitario", "Tuboplus", "4 Pulgadas x 6m", 20, 180.0, 310.0),
        ("Plomería", "Tubo de PVC Hidráulico", "Creska", "1/2 Pulgada x 6m", 45, 65.0, 115.0),
        ("Plomería", "Codo 90 PVC Hidráulico", "Truper", "1/2 Pulgada", 120, 4.5, 12.0),
        ("Plomería", "Cople PVC Sanitario", "Genérico", "4 Pulgadas", 80, 12.0, 26.0),
        ("Material Eléctrico", "Cable Conductor Cobre Thw", "Condulac", "Calibre 12 - 100m", 8, 850.0, 1399.0),
        ("Material Eléctrico", "Cable Conductor Cobre Thw", "Iusa", "Calibre 10 - 100m", 5, 1200.0, 1950.0),
        ("Material Eléctrico", "Cinta de Aislar Vinilo", "3M", "18 metros", 150, 14.0, 35.0),
        ("Material Eléctrico", "Apagador Sencillo Pared", "Bticino", "Estándar Blanco", 60, 22.0, 48.0),
        ("Material Eléctrico", "Contacto Doble con Tierra", "Siena", "Estándar Blanco", 75, 25.0, 55.0),
        ("Pinturas y Solventes", "Pintura Vinílica Blanca", "Comex", "Cubeta 19 Litros", 12, 1100.0, 1850.0),
        ("Pinturas y Solventes", "Pintura Vinílica Azul Naval", "Comex", "Galón 4 Litros", 18, 320.0, 540.0),
        ("Pinturas y Solventes", "Thinner Estándar Solvente", "Sayer", "Botella 1 Litro", 50, 28.0, 55.0),
        ("Pinturas y Solventes", "Brocha para Pintar Cerda Natural", "Éxito", "3 Pulgadas", 40, 18.0, 38.0),
        ("Pinturas y Solventes", "Brocha para Pintar Cerda Natural", "Éxito", "5 Pulgadas", 25, 32.0, 68.0),
        ("Herramienta Manual", "Pinzas de Chofer Mecánico", "Truper", "8 Pulgadas", 22, 75.0, 135.0),
        ("Herramienta Manual", "Pinzas de Presión Mordaza", "Urrea", "10 Pulgadas", 14, 190.0, 340.0),
        ("Herramienta Eléctrica", "Rotomartillo Profesional 1/2", "Dewalt", "650 Watts", 6, 950.0, 1599.0),
        ("Herramienta Eléctrica", "Esmeriladora Angular", "Makita", "4-1/2 Pulgadas", 4, 1100.0, 1890.0),
        ("Herramienta Eléctrica", "Juego de Brocas para Concreto", "Bosch", "7 Piezas", 15, 140.0, 260.0),
        ("Ferretería General", "Cerradura de Sobreponer Izquierda", "Phillips", "Clásica AS-550", 11, 210.0, 385.0),
        ("Ferretería General", "Candado de Latón Llave Normal", "Yale", "40 mm", 30, 65.0, 120.0),
        ("Ferretería General", "Flexómetro Cinta Bloqueo", "Stanley", "5 metros", 25, 55.0, 110.0),
        ("Plomería", "Cinta Selladora Teflón", "Truper", "1/2 Pulgada x 7m", 200, 3.5, 9.0),
        ("Plomería", "Pegamento para PVC Cemento", "Oatey", "Adhesivo 240 ml", 35, 48.0, 95.0),
        ("Ferretería General", "Malla Ciclónica Galvanizada", "Deacero", "Abierta 1m x 20m", 5, 850.0, 1480.0),
        ("Ferretería General", "Alambre Recocido Negro", "Genérico", "Rollo de 1kg", 60, 24.0, 48.0),
        ("Jardinería", "Pala Redonda Mango Largo", "Truper", "Estructura Acero", 14, 130.0, 245.0),
        ("Jardinería", "Manguera Reforzada Jardín", "Pretul", "15 metros", 12, 160.0, 299.0),
        ("Jardinería", "Tijeras para Podar Césped", "Truper", "12 Pulgadas", 8, 115.0, 210.0),
        ("Ferretería General", "Carretilla Obra Reforzada", "Truper", "Carga 60 Litros", 7, 680.0, 1199.0),
        ("Ferretería General", "Segueta para Metal Fina", "Lenox", "12 Pulgadas - 24D", 180, 11.0, 26.0),
        ("Material Eléctrico", "Multímetro Digital Escolar", "Steren", "Básico DT-830B", 16, 95.0, 189.0),
        ("Material Eléctrico", "Foco LED Ahorrador Blanco", "Philips", "9 Watts (Equiv 60W)", 140, 16.0, 38.0),
        ("Plomería", "Llave Mezcladora para Fregadero", "Urrea", "Cromo Pulido", 9, 390.0, 690.0),
        ("Plomería", "Valvula de Esfera Latón Gas/Agua", "B&K", "1/2 Pulgada", 45, 52.0, 98.0),
        ("Ferretería General", "Lija de Agua para Metal/Madera", "Fandeli", "Grano 80", 250, 4.0, 10.0),
        ("Ferretería General", "Lija de Agua para Metal/Madera", "Fandeli", "Grano 120", 250, 4.0, 10.0),
        ("Ferretería General", "Lija de Agua para Metal/Madera", "Fandeli", "Grano 220", 250, 4.0, 10.0),
        ("Seguridad Industrial", "Goggles de Protección Claros", "Truper", "Policarbonato", 50, 18.0, 42.0),
        ("Seguridad Industrial", "Guantes de Carnaza Reforzados", "Derma", "Tamaño Estándar", 70, 26.0, 58.0),
        ("Seguridad Industrial", "Casco de Obra Ajustable", "Infra", "Color Amarillo", 15, 65.0, 130.0),
        ("Ferretería General", "Disco de Corte Flap metal", "Austromex", "4-1/2 G60", 90, 21.0, 45.0),
        ("Ferretería General", "Silicon Obra Negro Cartucho", "Sista", "300 ml", 40, 55.0, 115.0),
        ("Herramienta Manual", "Juego Llaves Allen Milimétricas", "Bondhus", "9 Piezas", 12, 180.0, 320.0)
    ]
    for p in herramientas_iniciales:
        sku_auto = f"TLAPA-{p[1][:3].upper()}-{p[2][:2].upper()}-{p[3][:3].replace(' ', '').upper()}"
        run_query("""INSERT INTO inventario (categoria, articulo, marca, medida_presentacion, stock, p_compra, p_venta, SKU) 
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (p[0], p[1], p[2], p[3], p[4], p[5], p[6], sku_auto))
# --- MOTOR DE IMPRESIÓN ---
def ejecutar_impresion(html_content):
    unique_id = str(uuid.uuid4())[:8]
    component_script = f"""
    <div id="ticket-{unique_id}" style="display:none;">{html_content}</div>
    <script>
    (function() {{
        var content = document.getElementById('ticket-{unique_id}').innerHTML;
        var win = window.open('', 'PRINT', 'height=600,width=400');
        win.document.write('<html><head><title>Ticket de Compra</title></head><body>' + content + '</body></html>');
        win.document.close();
        win.focus();
        win.print();
        win.close();
    }})();
    </script>
    """
    components.html(component_script, height=0)

def generar_ticket_html(titulo, id_doc, items, total, descuento=0, cliente=None):
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    items_html = "".join([f"<tr><td>{it['articulo']} ({it['medida_presentacion']})<br><small>Marca: {it['marca']}</small></td><td align='center'>{it['cantidad']}</td><td align='right'>${it['subtotal']:,.2f}</td></tr>" for it in items])
    return f"""
    <div style="font-family: 'Courier New', monospace; width: 260px; padding: 12px; background: white; color: black; border: 1px dashed #000;">
        <center><h3>🛠️ FERRETERÍA EL GRAN PERNO 🛠️</h3><p style="font-size:10px;">¡Soluciones Fuertes e Industriales!</p></center>
        <hr style="border-top: 1px dashed black;">
        <p style="font-size:11px;"><b>{titulo}:</b> #{id_doc}<br><b>Fecha:</b> {fecha}</p>
        {f'<p style="font-size:11px;"><b>Cliente VIP Master:</b> {cliente}</p>' if cliente else ''}
        <hr style="border-top: 1px dashed black;">
        <table style="width:100%; font-size:11px;">
            <thead><tr><th align="left">Material</th><th align="center">Cant</th><th align="right">Total</th></tr></thead>
            <tbody>{items_html}</tbody>
        </table>
        <hr style="border-top: 1px dashed black;">
        {f'<p align="right" style="font-size:11px;">Desc: -${descuento:,.2f}</p>' if descuento > 0 else ''}
        <h3 align="right">TOTAL: ${total:,.2f} MXN</h3>
        <center><p style="font-size:10px;">¡Gracias por su confianza maestro!</p></center>
    </div>
    """

if st.session_state.ticket_a_imprimir:
    ejecutar_impresion(st.session_state.ticket_a_imprimir)
    st.session_state.ticket_a_imprimir = None

# --- MENÚ LATERAL ERP ---
st.sidebar.markdown("# 🏬 tlapaleria las abejitas ")
st.sidebar.markdown("---")
menu = [
    "🛒 Terminal de Ventas (POS)",
    "📦 Control de Almacén & CRUD",
    "🚚 Abastecimiento & Camiones",
    "📝 Sistema de Apartados/Preventas",
    "👥 Padrón de Clientes (CRM)",
    "🎫 Cupones de Descuento",
    "📊 Tablero Financiero (KPIs)"
]
choice = st.sidebar.selectbox("Seleccionar Módulo Operativo", menu)
st.sidebar.markdown("---")

# --- MÓDULO 1: TERMINAL DE VENTAS (POS) ---
if choice == "🛒 Terminal de Ventas (POS)":
    st.header("🛒 Terminal de Ventas de Mostrador")
    busqueda = st.text_input("🔍 Buscar material por Artículo, Marca o código SKU...", "").strip().lower()
    
    if busqueda:
        df_inv = get_df("SELECT * FROM inventario WHERE stock > 0 AND (lower(articulo) LIKE ? OR lower(marca) LIKE ? OR lower(SKU) LIKE ?)", (f"%{busqueda}%", f"%{busqueda}%", f"%{busqueda}%"))
    else:
        df_inv = get_df("SELECT * FROM inventario WHERE stock > 0")
        
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Buscador de Materiales")
        if not df_inv.empty:
            art_sel = st.selectbox("Selecciona el Artículo", sorted(df_inv['articulo'].unique()))
            df_m = df_inv[df_inv['articulo'] == art_sel]
            marca_sel = st.selectbox("Marca Comercial", sorted(df_m['marca'].unique()))
            df_c = df_m[df_m['marca'] == marca_sel]
            medida_sel = st.selectbox("Medida / Presentación", sorted(df_c['medida_presentacion'].unique()))
            
            item = df_c[df_c['medida_presentacion'] == medida_sel].iloc[0]
            st.metric("Disponibilidad en Anaquel", f"{item['stock']} Unidades", f"${item['p_venta']:.2f} Unitario")
            cant = st.number_input("Cantidad Requerida", 1, int(item['stock']), step=1)
            
            if st.button("🛍️ Agregar al Mostrador", use_container_width=True):
                ya_en_carrito = False
                for c in st.session_state.carrito:
                    if c['articulo'] == item['articulo'] and c['marca'] == item['marca'] and c['medida_presentacion'] == item['medida_presentacion']:
                        nueva_cantidad = c['cantidad'] + cant
                        if nueva_cantidad <= item['stock']:
                            c['cantidad'] = nueva_cantidad
                            c['subtotal'] = nueva_cantidad * item['p_venta']
                            ya_en_carrito = True
                            st.toast(f"🔄 Cantidad actualizada: {item['articulo']}", icon="🛒")
                        else:
                            st.error(f"❌ Excede las existencias físicas ({item['stock']} pzas).")
                            ya_en_carrito = True
                        break
                
                if not ya_en_carrito:
                    st.session_state.carrito.append({
                        "categoria": item['categoria'],
                        "articulo": item['articulo'],
                        "marca": item['marca'],
                        "medida_presentacion": item['medida_presentacion'],
                        "cantidad": cant,
                        "precio": item['p_venta'],
                        "subtotal": item['p_venta'] * cant
                    })
                    st.success("Material cargado a la nota.")
                    st.rerun()
        else:
            st.warning("No hay productos con existencias en catálogo.")
            
    with c2:
        st.subheader("🛒 Nota de Venta Actual")
        if st.session_state.carrito:
            df_car = pd.DataFrame(st.session_state.carrito)
            st.dataframe(df_car[['articulo', 'medida_presentacion', 'cantidad', 'subtotal']], use_container_width=True, hide_index=True)
            
            subtotal_neto = df_car['subtotal'].sum()
            
            tel_crm = st.text_input("📱 Teléfono del Cliente Regular/Maestro (Opcional)", max_chars=10)
            if tel_crm:
                res_cli = get_df("SELECT * FROM clientes WHERE telefono = ?", (tel_crm,))
                if not res_cli.empty:
                    st.session_state.cliente_activo = res_cli.iloc[0]['nombre']
                    st.info(f"👷 Conectado: {st.session_state.cliente_activo} | Puntos Obtenidos: {res_cli.iloc[0]['puntos']}")
                else:
                    st.warning("Cliente no registrado en el CRM.")
            
            cod_cup = st.text_input("🎫 Cupón de Descuento")
            if st.button("Validar Código"):
                res_cup = get_df("SELECT * FROM cupones WHERE codigo = ? AND activo = 1", (cod_cup.upper(),))
                if not res_cup.empty:
                    st.session_state.cupón_act = {"codigo": res_cup.iloc[0]['codigo'], "tipo": res_cup.iloc[0]['tipo'], "valor": float(res_cup.iloc[0]['valor'])}
                    st.success(f"Cupón aprobado: Descuento de {st.session_state.cupón_act['valor']}.")
                else:
                    st.error("Código no válido o expirado.")
            
            val_desc = st.session_state.cupón_act['valor']
            tipo_desc = st.session_state.cupón_act['tipo']
            descuento_final = (subtotal_neto * (val_desc / 100)) if tipo_desc == "Porcentaje" else val_desc
            total_final = max(0.0, subtotal_neto - descuento_final)
            
            st.markdown(f"**Descuento aplicado:** -${descuento_final:,.2f}")
            st.header(f"Total: ${total_final:,.2f} MXN")
            
            metodo = st.selectbox("Método de Liquidación", ["Efectivo", "Tarjeta Crédito/Débito", "Transferencia Spei", "MercadoPago QR"])
            
            if st.button("🚀 Confirmar Compra e Imprimir Ticket", type="primary", use_container_width=True):
                t_id = "VTA-" + str(uuid.uuid4())[:8].upper()
                now = datetime.now()
                
                for i in st.session_state.carrito:
                    run_query("INSERT INTO ventas VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                              (t_id, now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), tel_crm, i['categoria'], i['articulo'], i['marca'], i['medida_presentacion'], i['cantidad'], i['precio'], descuento_final / len(st.session_state.carrito), i['subtotal'], metodo, "COMPLETADA"))
                    run_query("UPDATE inventario SET stock = stock - ? WHERE articulo=? AND marca=? AND medida_presentacion=?", (i['cantidad'], i['articulo'], i['marca'], i['medida_presentacion']))
                
                if tel_crm and 'res_cli' in locals() and not res_cli.empty:
                    puntos_nuevos = int(total_final // 100)
                    run_query("UPDATE clientes SET puntos = puntos + ? WHERE telefono = ?", (puntos_nuevos, tel_crm))
                
                st.session_state.ticket_a_imprimir = generar_ticket_html("TICKET DE VENTA", t_id, st.session_state.carrito, total_final, descuento_final, st.session_state.cliente_activo)
                st.session_state.carrito = []
                st.session_state.cupón_act = {"codigo": "", "tipo": "Fijo", "valor": 0.0}
                st.success("¡Transacción Exitosa!")
                st.rerun()
                
            if st.button("🗑️ Vaciar Nota Completa", use_container_width=True):
                st.session_state.carrito = []
                st.rerun()
# --- MÓDULO 2: CONTROL DE ALMACÉN & CRUD ---
elif choice == "📦 Control de Almacén & CRUD":
    st.header("📦 Administración Central de Almacén (CRUD)")
    df_inv = get_df("SELECT * FROM inventario")
    
    stock_critico = df_inv[df_inv['stock'] <= 5]
    if not stock_critico.empty:
        st.error(f"🚨 ALERTA DE ABASTO: Tienes {len(stock_critico)} materiales con stock crítico (Menos de 5 piezas). Solicitar a proveedor.")
    
    st.subheader("Catálogo de Existencias en Sistema")
    st.dataframe(df_inv, use_container_width=True, hide_index=True)
    
    tab_u, tab_d = st.tabs(["✏️ Actualizar Precios/Costos (UPDATE)", "🗑️ Retirar Material de Catálogo (DELETE)"])
    
    with tab_u:
        if not df_inv.empty:
            df_inv['llave_unica'] = df_inv['articulo'] + " - " + df_inv['marca'] + " [" + df_inv['medida_presentacion'] + "]"
            sel_prenda = st.selectbox("Selecciona el material a modificar:", df_inv['llave_unica'].unique())
            fila = df_inv[df_inv['llave_unica'] == sel_prenda].iloc[0]
            
            with st.form("form_update"):
                c1, c2, c3 = st.columns(3)
                with c1: nuevo_stk = st.number_input("Corregir Stock Físico", value=int(fila['stock']), min_value=0)
                with c2: nuevo_pc = st.number_input("Costo de Compra Proveedor ($)", value=float(fila['p_compra']))
                with c3: nuevo_pv = st.number_input("Precio Venta Público ($)", value=float(fila['p_venta']))
                
                if st.form_submit_button("💾 Modificar Parámetros"):
                    run_query("UPDATE inventario SET stock=?, p_compra=?, p_venta=? WHERE articulo=? AND marca=? AND medida_presentacion=?",
                              (nuevo_stk, nuevo_pc, nuevo_pv, fila['articulo'], fila['marca'], fila['medida_presentacion']))
                    st.success("Precios y stock actualizados correctamente.")
                    st.rerun()
                    
    with tab_d:
        if not df_inv.empty:
            sel_borrar = st.selectbox("Selecciona material a purgar de base de datos:", df_inv['llave_unica'].unique(), key="del_box")
            fila_b = df_inv[df_inv['llave_unica'] == sel_borrar].iloc[0]
            st.warning(f"⚠️ Eliminarás permanentemente '{sel_borrar}'. Esto no se puede deshacer.")
            if st.button("🚨 Ejecutar Depuración Definitiva", use_container_width=True):
                run_query("DELETE FROM inventario WHERE articulo=? AND marca=? AND medida_presentacion=?", (fila_b['articulo'], fila_b['marca'], fila_b['medida_presentacion']))
                st.success("Material removido del ERP.")
                st.rerun()

# --- MÓDULO 3: ABASTECIMIENTO & COMPRAS ---
elif choice == "🚚 Abastecimiento & Camiones":
    st.header("🚚 Alta de Facturas de Proveedores (Ingreso de Mercancía)")
    
    with st.form("compra_alta"):
        c1, c2, c3, c4 = st.columns(4)
        with c1: p_cat = st.selectbox("Categoría de Material", ["Herramienta Manual", "Herramienta Eléctrica", "Ferretería General", "Plomería", "Material Eléctrico", "Pinturas y Solventes", "Jardinería", "Seguridad Industrial"])
        with c2: p_mod = st.text_input("Nombre de Material (Ej: Martillo)", "Tubo de Cobre")
        with c3: p_col = st.text_input("Marca de Fábrica (Ej: Truper)", "Iusa")
        with c4: p_tal = st.text_input("Medida / Tipo (Ej: 1/2 Pulgada)", "1/2 Pulgada")
        
        c5, c6, c7 = st.columns(3)
        with c5: p_cant = st.number_input("Cajas / Unidades Recibidas", min_value=1, value=50)
        with c6: p_cost = st.number_input("Costo Unitario Facturado ($)", min_value=0.5, value=45.0)
        with c7: p_vent = st.number_input("Precio de Venta Mostrador ($)", min_value=0.5, value=78.0)
        
        if st.form_submit_button("📥 Procesar Entrada e Incrementar Stock", use_container_width=True):
            if p_mod and p_col and p_tal:
                compra_uuid = "COM-" + str(uuid.uuid4())[:6].upper()
                fecha_reg = datetime.now().strftime("%Y-%m-%d")
                sku_autogenerado = f"TLAPA-{p_mod[:3].upper()}-{p_col[:2].upper()}-{p_tal[:3].replace(' ', '').upper()}"
                
                run_query("INSERT INTO compras_proveedor VALUES (?,?,?,?,?,?,?,?)",
                          (compra_uuid, fecha_reg, p_mod, p_col, p_tal, p_cant, p_cost, p_cant * p_cost))
                
                run_query("""INSERT INTO inventario (categoria, articulo, marca, medida_presentacion, stock, p_compra, p_venta, SKU) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?) 
                          ON CONFLICT(articulo, marca, medida_presentacion) 
                          DO UPDATE SET stock = stock + excluded.stock, 
                                        p_compra = excluded.p_compra, 
                                        p_venta = excluded.p_venta""",
                          (p_cat, p_mod, p_col, p_tal, p_cant, p_cost, p_vent, sku_autogenerado))
                
                st.success(f"✔️ Remisión {compra_uuid} cargada con éxito. Inventario recalculado.")
                st.rerun()
            else:
                st.error("Rellene los campos obligatorios.")

    st.subheader("Auditoría de Compras e Inversiones")
    df_comp = get_df("SELECT * FROM compras_proveedor ORDER BY fecha DESC")
    st.dataframe(df_comp, use_container_width=True, hide_index=True)

# --- MÓDULO 4: SISTEMA DE APARTADOS/PREVENTAS ---
elif choice == "📝 Sistema de Apartados/Preventas":
    st.header("📝 Control de Apartados de Material")
    tab_crear, tab_control = st.tabs(["✨ Crear Nuevo Apartado de Material", "🔍 Estatus y Liquidación de Saldos"])
    
    with tab_crear:
        df_inv_disp = get_df("SELECT * FROM inventario WHERE stock > 0")
        if not df_inv_disp.empty:
            df_inv_disp['llave'] = df_inv_disp['articulo'] + " - " + df_inv_disp['marca'] + " [" + df_inv_disp['medida_presentacion'] + "]"
            
            with st.form("form_apartado"):
                c1, c2 = st.columns(2)
                with c1: cl_nom = st.text_input("Nombre del Contratista / Cliente")
                with c2: cl_tel = st.text_input("Teléfono Móvil", max_chars=10)
                
                sel_p = st.selectbox("Seleccione Material a Congelar:", df_inv_disp['llave'].unique())
                fila_a = df_inv_disp[df_inv_disp['llave'] == sel_p].iloc[0]
                
                ca1, ca2 = st.columns(2)
                with ca1: c_cant = st.number_input("Cantidad", min_value=1, max_value=int(fila_a['stock']), value=1)
                with ca2: anticipo = st.number_input("Monto de Anticipo Dejado ($)", min_value=0.0, value=200.0)
                
                total_ap = fila_a['p_venta'] * c_cant
                st.markdown(f"**Costo Total del Material:** ${total_ap:,.2f} MXN | **Resta en Caja:** ${(total_ap - anticipo):,.2f} MXN")
                
                if st.form_submit_button("💾 Registrar Apartado y Apartar del Almacén"):
                    if cl_nom and cl_tel:
                        ap_id = "APT-" + str(uuid.uuid4())[:6].upper()
                        f_ap = datetime.now().strftime("%Y-%m-%d")
                        
                        run_query("INSERT INTO apartados VALUES (?,?,?,?,?,?,?,?,?,?)",
                                  (ap_id, cl_nom, cl_tel, f_ap, fila_a['articulo'], fila_a['marca'], fila_a['medida_presentacion'], c_cant, total_ap, "VIGENTE"))
                        
                        run_query("UPDATE inventario SET stock = stock - ? WHERE articulo=? AND marca=? AND medida_presentacion=?", 
                                  (c_cant, fila_a['articulo'], fila_a['marca'], fila_a['medida_presentacion']))
                        
                        st.success(f"Apartado {ap_id} guardado con éxito. Material separado físicamente.")
                        st.rerun()
                    else:
                        st.warning("El nombre y teléfono son obligatorios.")
        else:
            st.info("No hay inventario disponible.")
    with tab_control:
        df_ap = get_df("SELECT * FROM apartados WHERE estado = 'VIGENTE'")
        if not df_ap.empty:
            st.dataframe(df_ap, use_container_width=True, hide_index=True)
            sel_ap_id = st.selectbox("Selecciona Registro de Apartado para Cobro:", df_ap['id'].unique())
            fila_ap_sel = df_ap[df_ap['id'] == sel_ap_id].iloc[0]
            
            cc1, cc2 = st.columns(2)
            with cc1:
                if st.button("📦 Entregar Material (Líquido Contra Pago)", use_container_width=True, type="primary"):
                    run_query("UPDATE apartados SET estado = 'ENTREGADO' WHERE id = ?", (sel_ap_id,))
                    
                    t_id_ap = "VTA-" + str(uuid.uuid4())[:8].upper()
                    now_ap = datetime.now()
                    
                    p_v_orig = get_df("SELECT p_venta FROM inventario WHERE articulo=? AND marca=? AND medida_presentacion=?", 
                                      (fila_ap_sel['articulo'], fila_ap_sel['marca'], fila_ap_sel['medida_presentacion'])).iloc[0]['p_venta']
                    
                    run_query("INSERT INTO ventas VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                              (t_id_ap, now_ap.strftime("%Y-%m-%d"), now_ap.strftime("%H:%M"), fila_ap_sel['telefono'], 
                               "Apartado", fila_ap_sel['articulo'], fila_ap_sel['marca'], fila_ap_sel['medida_presentacion'], 
                               fila_ap_sel['cantidad'], p_v_orig, 0.0, fila_ap_sel['total'], "Efectivo", "COMPLETADA"))
                    
                    st.success("¡Apartado liquidado y registrado en libro de ventas!")
                    st.rerun()
            with cc2:
                if st.button("❌ Romper Apartado (Reingresar a Anaqueles)", use_container_width=True):
                    run_query("UPDATE apartados SET estado = 'CANCELADO' WHERE id = ?", (sel_ap_id,))
                    run_query("UPDATE inventario SET stock = stock + ? WHERE articulo=? AND marca=? AND medida_presentacion=?", 
                              (int(fila_ap_sel['cantidad']), fila_ap_sel['articulo'], fila_ap_sel['marca'], fila_ap_sel['medida_presentacion']))
                    st.error("Apartado anulado. La mercancía regresó a stock público.")
                    st.rerun()
        else:
            st.info("No existen apartados pendientes de liquidar.")

# --- MÓDULO 5: PADRÓN DE CLIENTES (CRM) ---
elif choice == "👥 Padrón de Clientes (CRM)":
    st.header("👥 Programa de Descuentos para Maestros y Oficios (CRM)")
    
    with st.form("form_cliente"):
        c1, c2 = st.columns(2)
        with c1: n_nombre = st.text_input("Nombre Completo o Razón Social")
        with c2: n_tel = st.text_input("Teléfono Móvil (ID de Monedero)", max_chars=10)
        
        if st.form_submit_button("➕ Registrar en Sistema"):
            if n_nombre and len(n_tel) == 10:
                try:
                    f_reg = datetime.now().strftime("%Y-%m-%d")
                    run_query("INSERT INTO clientes VALUES (?, ?, 0, ?)", (n_tel, n_nombre, f_reg))
                    st.success(f"Maestro/Cliente {n_nombre} dado de alta.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Ese número ya existe.")
            else:
                st.warning("Verifique los 10 dígitos del teléfono.")
                
    st.subheader("Lista de Clientes Registrados y Puntos Acumulados")
    df_cli = get_df("SELECT * FROM clientes ORDER BY puntos DESC")
    st.dataframe(df_cli, use_container_width=True, hide_index=True)

# --- MÓDULO 6: CUPONES DE DESCUENTO ---
elif choice == "🎫 Cupones de Descuento":
    st.header("🎫 Cupones Especiales de Descuento")
    
    with st.form("form_cupones"):
        c1, c2, c3 = st.columns(3)
        with c1: n_codigo = st.text_input("Código de Cupón (Ej: CONSTRURAMA)").strip().upper()
        with c2: n_tipo = st.selectbox("Tipo de Rebaja", ["Porcentaje", "Fijo"])
        with c3: n_valor = st.number_input("Valor de Beneficio", min_value=0.0)
        
        if st.form_submit_button("⚡ Activar Cupón en Caja"):
            if n_codigo:
                try:
                    run_query("INSERT INTO cupones VALUES (?, ?, ?, 1)", (n_codigo, n_tipo, n_valor))
                    st.success(f"Cupón {n_codigo} cargado.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("El cupón ya existe.")
            else:
                st.warning("Rellene el código.")
                
    st.subheader("Cupones Habilitados")
    df_cup = get_df("SELECT * FROM cupones")
    st.dataframe(df_cup, use_container_width=True, hide_index=True)

# --- MÓDULO 7: TABLERO FINANCIERO (KPIS) ---
elif choice == "📊 Tablero Financiero (KPIs)":
    st.header("📊 Inteligencia Comercial & Rendimiento Financiero")
    
    df_v = get_df("SELECT * FROM ventas WHERE estado='COMPLETADA'")
    df_i = get_df("SELECT * FROM inventario")
    
    if not df_v.empty:
        total_ingresos = df_v['total'].sum()
        total_prendas_vendidas = df_v['cantidad'].sum()
        
        df_v_costos = pd.merge(df_v, df_i[['articulo', 'marca', 'medida_presentacion', 'p_compra']], on=['articulo', 'marca', 'medida_presentacion'], how='left')
        df_v_costos['costo_total_linea'] = df_v_costos['cantidad'] * df_v_costos['p_compra']
        total_costos_ventas = df_v_costos['costo_total_linea'].sum()
        
        utilidad_neta = total_ingresos - total_costos_ventas
        margen_ganancia = (utilidad_neta / total_ingresos * 100) if total_ingresos > 0 else 0
        
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Venta Bruta Total", f"${total_ingresos:,.2f} MXN")
        kpi2.metric("Inversión de Material Desplazado", f"${total_costos_ventas:,.2f} MXN")
        kpi3.metric("Utilidad Operativa Real", f"${utilidad_neta:,.2f} MXN", delta=f"{margen_ganancia:.1f}% Margen")
        kpi4.metric("Unidades Vendidas (Piezas)", f"{total_prendas_vendidas} U")
        
        st.markdown("---")
        g1, g2 = st.columns(2)
        
        with g1:
            st.subheader("📈 Flujo de Caja por Día")
            ventas_tiempo = df_v.groupby('fecha')['total'].sum().reset_index()
            st.line_chart(data=ventas_tiempo, x='fecha', y='total', use_container_width=True)
            
        with g2:
            st.subheader("🛠️ Top 10 Materiales Más Vendidos")
            top_modelos = df_v.groupby('articulo')['cantidad'].sum().sort_values(ascending=False).head(10).reset_index()
            st.bar_chart(data=top_modelos, x='articulo', y='cantidad', use_container_width=True)
            
        st.subheader("Libro Mayor de Transacciones Realizadas")
        st.dataframe(df_v, use_container_width=True, hide_index=True)
    else:
        st.info("Aún no se registran ventas para compilar los KPIs.")
