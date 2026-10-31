# **Centro de Documentación Pública y Divulgación: Honey-Agent**

Bienvenido a la documentación pública oficial de **Honey-Agent**. Esta sección está diseñada para proporcionar explicaciones claras, conceptuales y accesibles para **clientes, directores de tecnología (CTOs/CISOs), evaluadores de proyectos, analistas de seguridad y público general**, sin requerir conocimientos profundos del código fuente interno.

---

## **¿Qué es Honey-Agent en Términos Sencillos?**

**Honey-Agent** es un sistema de **ciberdefensa activa** impulsado por Inteligencia Artificial. En lugar de limitarse a levantar un muro y esperar a que los atacantes intenten romperlo, Honey-Agent despliega un **servidor señuelo inteligente** que actúa como un laberinto en memoria:

1. **Atrae al intruso:** Simula ser un servidor corporativo real y vulnerable.
2. **Lo engaña con IA:** Emula una terminal Linux auténtica mediante Modelos de Lenguaje sin exponer un sistema operativo real que pueda ser hackeado.
3. **Desgasta su tiempo (Tarpit):** Introduce retrasos calculados para que el atacante y sus herramientas automáticas pierdan tiempo y recursos.
4. **Le entrega cebos rastreables (Canary Tokens):** Proporciona contraseñas y claves falsas que disparan alarmas inmediatas si intenta usarlas en otros sistemas de la empresa.
5. **Lo neutraliza automáticamente:** En cuanto el atacante intenta una acción destructiva, el sistema bloquea su dirección IP a nivel de firewall en menos de 5 milisegundos.

---

## **Índice de Documentos Públicos Disponibles**

| Documento | Enlace | Audiencia | Propósito |
| :--- | :--- | :--- | :--- |
| **01. Whitepaper y Explicación General** | [01_Whitepaper_Honey_Agent_Explicacion_General.md](01_Whitepaper_Honey_Agent_Explicacion_General.md) | Directores, Evaluadores, Clientes | Visión ejecutiva, propuesta de valor, retorno de inversión y beneficios estratégicos de la defensa activa. |
| **02. Infografía y Conceptos Visuales** | [02_Infografia_y_Conceptos_Visuales.md](02_Infografia_y_Conceptos_Visuales.md) | Estudiantes, Analistas, Público | Diagramas de flujo claros, analogías sencillas del funcionamiento y ciclo de vida de una amenaza. |
| **03. Guía de Usuario del SOC Dashboard** | [03_Guia_Usuario_SOC_Dashboard.md](03_Guia_Usuario_SOC_Dashboard.md) | Operadores del SOC, Analistas Jr | Cómo interpretar el panel de monitoreo, niveles del velocímetro de amenaza y respuesta ante incidentes. |
| **04. Preguntas Frecuentes y Legalidad (FAQ)** | [04_Preguntas_Frecuentes_y_Legalidad.md](04_Preguntas_Frecuentes_y_Legalidad.md) | Oficiales de Cumplimiento, Legales, TI | Legalidad de la decepción activa (no es contraataque), privacidad de datos y garantías de seguridad. |

---

## **Diferencia entre Documentación Pública e Interna**

* **`docs_publicos/` (Esta carpeta):** Lenguaje claro, enfoque en el valor de negocio, casos de uso, infografías y conceptos explicativos de alto nivel.
* **`docs/` (Carpeta técnica interna):** Especificaciones de arquitectura de software, tablas de inodos, contratos entre programadores, código fuente, regexes de MITRE ATT&CK y guías de compilación.
