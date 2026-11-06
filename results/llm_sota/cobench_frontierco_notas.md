# CO-Bench / FrontierCO: lo que no se pudo confirmar

Fuentes: arXiv 2504.04310v3 y 2505.16952v3 (las últimas versiones), el repo CO-Bench (HEAD 2f6620b, 2026-05-17) y los `config.py` del dataset en HF. Los PDFs y los textos extraídos están en `pdfs/`.

## CO-Bench
- **LLM por problema.** Las tablas del apéndice (Tablas 7, 17, 21, 24 y 36) no dicen qué LLM se usó. Asumo o3-mini-medium por dos razones: así lo indican la sección de implementación (p.4) y el pie de la Fig. 3, y los promedios de las tablas coinciden con la Fig. 3.
- **EoH no cuadra.** El promedio de las 36 tablas del apéndice da 0.8007, pero la Fig. 3 dice 0.840. Los demás métodos sí coinciden (diferencia < 0.001). No sé cuál de los dos valores es el correcto.
- **Solver clásico de cada problema.** No se dice cuál es. El paper solo da ejemplos (LKH para TSP, CPLEX para scheduling, Gurobi para MIS). Que JSSP y FSSP usen CPLEX es una inferencia mía. Tampoco se publican la configuración ni el código de esos solvers.
- **Fórmula del score.** El paper usa min/max (Ec. 6), así que el score quedaría acotado en 1. El código usa una razón sin acotar, y por eso aparecen valores > 1 (MKP, GAP, HRSS).
- **Referencia de JSSP y FSSP.** No es la BKS: es la cota inferior del encabezado de los archivos de Taillard. Por eso un óptimo puede dar un score < 1. Esto lo leí en el código, no en el paper.
- **Promedio por archivo.** Primero se promedia dentro de cada archivo y después entre archivos. Esto también sale del código.
- **Partición dev/test.** La saqué del `config.py` actual en HF. No puedo garantizar que sea la misma que se usó en el paper. Tamaños de test resultantes: CWL 37, MKP 163, JSSP 40, FSSP 60, PVRP 5.
- **Presupuesto.**
  - Sí se reportan las 64 iteraciones.
  - No se reportan tokens, número de llamadas ni costo.
  - El timeout de la evaluación en dev no aparece en el paper (el README usa 10 s).
- **Sin valores por problema.** "Self-Refine" no existe en CO-Bench; lo más parecido es Greedy Refine. Chain of Experts y los LLM sin agente solo tienen valores agregados (Fig. 3).
- **Definición de "Above Classical".** La Fig. 3 lo define por instancias y el texto (p.3) por problemas.
- **Ruteo.** El único problema de vehicle routing es el period VRP (Tabla 36). En ese problema el solver clásico obtiene 0.124 y ReEvo, MCTS y EoH obtienen 0.0.

## FrontierCO
- **LLM de FunSearch y ReEvo.** No se indica. Solo Self-Refine dice explícitamente "o4-mini, medium". Que los otros dos usen lo mismo es una inferencia mía.
- **Asterisco en HGS hard.** En la Tabla 7 (CVRP), HGS hard tiene "*" solo en el tiempo y no en el gap (6.74 %). No está claro si quiere decir que hubo alguna instancia infactible o con timeout.
- **Instancias de validación de CVRP.** El paper (B.4) dice que son 20/100/500 ciudades; en HF aparecen 20/50/100.
- **Instancias FJSP hard.** La Tabla 1 dice 20 y el apéndice B.7 dice "24 of the largest".
- **BKS de CVRP Bélgica.** En `config.py` son enteros (CVRPLib, distancias redondeadas), pero el evaluador calcula distancias euclídeas sin redondear. Puede haber un pequeño sesgo en el gap; no lo verifiqué.
- **Golden 1-8.** Se descartó la restricción de largo de ruta y la BKS de config cambia en consecuencia (p.ej. Golden_1 = 5370.55). No comprobé de dónde sale esa BKS sin la restricción.
- **Las ± no son iguales.** Para el gap son desviación estándar. Para el tiempo son media geométrica ×/÷ desviación geométrica.
- **No hay seeds ni varias corridas.** Se reporta una sola corrida por agente.
