# 📅 CALENDARIO COMERCIAL ESTRATÉGICO - COLOMBIA (Base de Datos de Eventos)

Este documento define los "Disparadores Temporales" (Triggers) para el sistema de predicción de Dahell Intelligence.
El objetivo es que el sistema anticipe la demanda analizando qué categorías explotaron históricamente en estas fechas.

---

## 🟢 Q1: ENERO - MARZO (Regreso a Clases & Inicio de Año)

| Evento / Temporada | Fecha Aprox. | Ventana de Prep. (Días antes) | Categorías Clave (Keywords) | Notas Estratégicas |
| :--- | :--- | :--- | :--- | :--- |
| **Temporada Escolar** | Enero 15 - Feb 10 | **45 días** (Dic 1) | Morrales, Loncheras, Termos, Papelería kawaii, Organizadores, Zapatos escolares | El pico de búsqueda es Enero 20. La compra dropshipping empieza antes. |
| **Propósitos de Año Nuevo** | Enero 1 - Enero 31 | **30 días** (Dic 1) | Fitness casero (bandas, pesas), Agendas, Organizadores de hogar, Detox | La gente quiere organizar su vida y bajar de peso. |
| **San Valentín (Global)** | Feb 14 | **30 días** (Ene 15) | Peluches, Joyería, Parejas, Regalos personalizados | Aunque es gringo, en Colombia ha ganado fuerza comercial reciente. |
| **Día de la Mujer** | Marzo 8 | **20 días** (Feb 15) | Belleza, Cuidado Facial, Detalles oficina, Joyería económica | Evento de alto volumen corporativo y personal. |

## 🟡 Q2: ABRIL - JUNIO (Familia & Primas)

| Evento / Temporada | Fecha Aprox. | Ventana de Prep. (Días antes) | Categorías Clave (Keywords) | Notas Estratégicas |
| :--- | :--- | :--- | :--- | :--- |
| **Semana Santa** | (Movible) Abril | **30 días** | Accesorios viaje, Ropa playa, Camping, Accesorios auto, Maletas | La gente viaja por carretera. Accesorios de carro se mueven bien. |
| **Día del Niño** | Abril (Último Sab) | **30 días** | Juguetes, Tecnología niños, Luces LED, Disfraces simples | Enfoque en regalos económicos para colegios/piñatas. |
| **Día de la Madre** | Mayo (2do Domingo) | **45 días** (Marzo fin) | Cocina, Decoración hogar, Belleza anti-edad, Fajas, Ropa cómoda | **EVENTO #2 MÁS IMPORTANTE DEL AÑO**. Ticket promedio alto. |
| **Día del Padre** | Junio (3er Domingo) | **30 días** (May 15) | Herramientas, Accesorios Auto, Tecnología, Afeitadoras, Gadgets | Regalos funcionales. Difícil sorprender, fácil vender utilidad. |
| **Prima de Mitad de Año** | Junio 15 - 30 | **15 días** | Tecnología (Audífonos, Smartwatch), Ropa, Caprichos | La gente tiene liquidez extra. Compras impulsivas aumentan. |

## 🟠 Q3: JULIO - SEPTIEMBRE (Vientos & Amor)

| Evento / Temporada | Fecha Aprox. | Ventana de Prep. (Días antes) | Categorías Clave (Keywords) | Notas Estratégicas |
| :--- | :--- | :--- | :--- | :--- |
| **Independencia / Vientos** | Julio 20 - Agosto | **30 días** | Cometas, Actividades aire libre, Chaquetas cortavientos | Temporada de vientos fuerte en el centro del país. |
| **Feria de las Flores** | Agosto (Inicios) | **30 días** | Ropa típica, Sombreros, Ponchos, Accesorios fiesta (Antioquia) | Muy regional pero fuerte en Medellín. |
| **Flores Amarillas** | Septiembre 21 | **20 días** (Sept 1) | Todo lo amarillo, Girasoles, Peluches, Flores eternas | **Micro-tendencia viral de TikTok** que explotó en 2023/24. |
| **Amor y Amistad** | Sept (3er Sab) | **45 días** (Ago 1) | Sex shop (Adultos), Peluches, Chocolates, Tecnología pareja, Juegos mesa | **EVENTO CLAVE**. El "San Valentín" real de Colombia. Amigo secreto. |

## 🔴 Q4: OCTUBRE - DICIEMBRE (La Mina de Oro)

| Evento / Temporada | Fecha Aprox. | Ventana de Prep. (Días antes) | Categorías Clave (Keywords) | Notas Estratégicas |
| :--- | :--- | :--- | :--- | :--- |
| **Halloween** | Octubre 31 | **60 días** (Sep 1) | Disfraces, Máscaras LED, Decoración, Lentes contacto, Maquillaje FX | Se empieza a buscar desde Septiembre. Alta viralidad en redes. |
| **Semana de Receso** | Octubre (Inicios) | **30 días** | Playa, Vestidos baño, Bloqueador, Juguetes viaje | Mini-temporada de vacaciones escolares. |
| **Black Friday / Cyber** | Noviembre (Final) | **30 días** | Tecnología High-Ticket, Electrodomésticos, Combos x2 x3 | La gente espera descuentos. Ideal para liquidar stock o lanzar ganadores. |
| **Navidad (Regalos)** | Diciembre 16-24 | **90 días** (Sep/Oct) | Juguetes (Tendencia del año), Ropa, Tecnología, Decoración Navidad | **EVENTO #1**. Todo se vende. La clave es tener stock y logística rápida. |
| **Prima de Navidad** | Dic 15 - 20 | **N/A** | Compras última hora, Regalos "Salvavidas" | Envíos express (Contraentrega local) ganan aquí. |

---

## ⚙️ CÓMO DEBE USAR ESTO EL SISTEMA (Lógica del Bot)

1.  **Check Diario:** El sistema revisa la fecha actual (ej: `2024-08-01`).
2.  **Look-Ahead:** Busca eventos cuya "Ventana de Prep." inicie en los próximos 7 días.
    *   *Ejemplo:* "Alerta: Se acerca la ventana de preparación para **Amor y Amistad (Sept)**".
3.  **Consulta Histórica (Retro-Trends):**
    *   El bot va a Google Trends y consulta: *"¿Qué keywords relacionadas con 'Regalos Pareja' tuvieron pico en Septiembre 2023 y Septiembre 2024?"*.
4.  **Recomendación Proactiva:**
    *   Genera un reporte: *"Usuario, estamos a 45 días de Amor y Amistad. Históricamente, estos productos suben de demanda. Te sugiero buscar en Dropi estos conceptos: [Lista Generada]"*.
