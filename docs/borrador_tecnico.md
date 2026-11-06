# Solvers híbridos generados por LLM: borrador técnico

> Copia exportada del documento vivo: https://claude.ai/artifact/NVRsT6xucJsirtnczZEBct (la versión de referencia es esa).

Nov 6, 2026 · Ignacio Araya

## Resumen

Presentamos un framework que construye solvers metaheurísticos y matheurísticos para problemas de optimización combinatoria a partir de una especificación mínima escrita por una persona. El humano aporta cuatro piezas por problema: el formato y un generador de instancias, una descripción en lenguaje natural, un conjunto de casos de prueba y un **oráculo** que define las violaciones por familia de restricciones y los términos del costo. A partir de ahí, un LLM escribe el modelo del problema en C++, los componentes de búsqueda (constructores, vecindarios, perturbaciones, operadores de path relinking y destrucciones), y la formulación MIP que usa la matheurística en sus sub-problemas. Todo lo que escribe el LLM pasa por una validación autónoma por capas contra el oráculo y los casos, y se corrige con el mismo LLM a partir del reporte de rechazo. El framework aporta seis esqueletos en C++ (SA, ILS, VNS, TS, PR y una matheurística híbrida, HYB) y elige la combinación de esqueleto, componentes y parámetros con irace.

En los cinco primeros problemas (flow shop de permutación con flowtime y con makespan, job shop, CVRP y lot sizing capacitado multi-ítem), los solvers generados quedan, según el problema, entre 0,16 % y 1,4 % de media de las mejores soluciones conocidas en benchmarks clásicos (con la excepción del flowtime en instancias de 200 y 500 trabajos), y en el CLSP encuentran soluciones mejores que las publicadas para dos instancias de Trigeiro et al. (G53 y G69). El costo de generación es de 1 a 4 USD de API por problema.

Con un protocolo único (v2), el pipeline generó modelo, 9 componentes y vista MIP para siete problemas, los cinco anteriores más la localización de centros con capacidad y fuente única (SSCFLP) y la mochila multidimensional (MKP): 63 de 63 componentes aceptados, 53 en la primera ronda, por 8,88 USD en total. El afinamiento de ese protocolo, una configuración por tipo de instancia, está en curso; sus resultados reemplazarán a los preliminares de la sección 9.1.

## 1. Introducción

Construir un buen solver para un problema combinatorio nuevo exige aún semanas de trabajo experto: modelar el problema, diseñar vecindarios y perturbaciones que exploten su estructura, implementarlos de forma eficiente, combinarlos en una metaheurística y ajustar sus parámetros. Los LLM ya escriben código de optimización razonable, pero usarlos de forma directa tiene tres problemas: el código generado puede ser incorrecto de maneras sutiles (un delta que no coincide con el costo, un movimiento que rompe la factibilidad), una sola heurística generada rara vez es competitiva, y no hay un criterio para elegir entre las variantes que produce.

Nuestra propuesta separa el trabajo en tres capas. El humano define *qué* es el problema con un oráculo ejecutable pequeño. El LLM escribe *cómo* resolverlo, en piezas acotadas con contratos explícitos, y cada pieza se valida contra el oráculo antes de aceptarse. El framework aporta lo que no depende del problema: los esqueletos de búsqueda, la matheurística, y la configuración automática que elige qué piezas usar y con qué parámetros.

**Contribuciones** (borrador):

1. Una división humano/LLM en la que lo humano por problema se reduce a la instancia, la descripción, los casos y el oráculo; el modelo C++, los componentes y la formulación MIP los escribe el LLM.
2. Una validación autónoma por capas (compilación, sintáctica, contractual, operacional, calidad y diversidad) que convierte cada rechazo en un reporte accionable para la corrección por ediciones.
3. Un espacio de configuración condicional (esqueleto → componentes por slot → parámetros) afinado con irace o con un tuner por etapas, con todo el código de búsqueda corriendo en C++.
4. Una matheurística genérica (HYB) que alterna búsqueda local en C++ con sub-MIP sobre la formulación que escribió el LLM, con destrucciones genéricas sobre grupos de variables.
5. Una evaluación en siete problemas con benchmarks de la literatura y con los conjuntos de test de los métodos de diseño de heurísticas con LLM (ReEvo, MCTS-AHD, CO-Bench, FrontierCO), y estudios de ablación sobre las decisiones de diseño (destrucciones generadas, vista MIP generada, prompts compactos).

## 2. Visión general

El pipeline tiene seis fases: tres en las que escribe el LLM (modelo, componentes, vista MIP), cada una cerrada por su validador, y tres del framework (catálogo, configuración, evaluación). La tabla resume quién escribe cada pieza y contra qué se valida.

```
Humano (por problema)        LLM, con validación                 Framework
---------------------        -------------------                 ---------
Instancia y generador        1. Modelo C++                       Catálogo
Descripción          ---->      (contra oráculo y casos)   ---->    |
Casos de prueba              2. Componentes C++                     v
Oráculo                         (validación por capas)           Configuración (irace o por etapas)
                             3. Vista MIP (Python)                  |
                                (validada por familia)              v
                                                                 Solver afinado

Cada pieza del LLM se valida en un proceso aparte; un rechazo vuelve al LLM como reporte y se corrige con ediciones.
```

El oráculo alimenta las tres fases del LLM: es la referencia contra la que se valida el modelo, los componentes (a través del modelo) y la vista MIP.

El algoritmo 0 une todas las fases y remite a los demás algoritmos: la generación del modelo (algoritmo 1) y de cada slot (algoritmo 2), la optimización de lo aceptado (algoritmo 5), la vista MIP y la configuración (irace o el tuner por etapas, algoritmo 4). HYB (algoritmo 3) es uno de los esqueletos entre los que elige el tuner.

```
Algoritmo 0: Construcción de un solver (visión general)
Entrada: especificación (S, C, O; sección 3), slots Σ, instancias de entrenamiento I
Salida: configuración θ* (esqueleto, componentes y parámetros), que corre en C++
  1 M ← GenerarModelo(S, C, O)                                ▷ Algoritmo 1
  2 M ← Optimizar(M)                                          ▷ Algoritmo 5
  3 V ← GenerarVistaMIP(S, C, O)                              ▷ opcional: habilita HYB
  4 K ← ComponentesBase(O, V)                                 ▷ partidas; destrucciones si hay V
  5 para cada σ ∈ Σ hacer
  6     K_σ ← GenerarSlot(σ, n, M, K_σ)                       ▷ Algoritmo 2
  7     K_σ ← Optimizar(K_σ)                                  ▷ Algoritmo 5
  8 K ← K ∪ {Compuesto(K_vec)}                                ▷ si hay dos o más vecindarios
  9 Θ ← EspacioCondicional(esqueletos, K)                     ▷ esqueleto → slots → parámetros
 10 θ* ← Tuner(Θ, I)                                          ▷ irace o Algoritmo 4
 11 devolver θ*                                               ▷ HYB: Algoritmo 3
```

| pieza | quién la escribe | lenguaje | se valida contra |
| --- | --- | --- | --- |
| instancia: formato (`to_text`) y generador | humano | Python | — |
| descripción del problema (`ModelSpec`) | humano | texto | — |
| casos de prueba (`cases.json`): respuestas factibles e infactibles con su costo | humano (o generados con el oráculo) | JSON | — |
| oráculo: violaciones por familia y términos del costo | humano | Python | — |
| modelo del problema | LLM | C++ | casos visibles y ocultos, oráculo en instancias al azar |
| componentes (constructor, vecindario, perturbación, relink, destrucción) | LLM | C++ | contrato del slot, modelo, micro-instancias, catálogo |
| vista MIP (variables, restricciones por familia, objetivo, grupos) | LLM | Python | oráculo y óptimos de los casos |
| esqueletos SA, ILS, VNS, TS, PR, HYB | framework | C++ (con referencia en Python) | — |
| configuración (esqueleto, componentes, parámetros) | irace / tuner por etapas | — | instancias de entrenamiento |

Dos decisiones dan forma al resto. Primero, el oráculo es la única definición del problema: el modelo C++ y la vista MIP son *vistas* que tienen que coincidir con él, no especificaciones paralelas. Segundo, el LLM nunca escribe un solver entero: escribe piezas con un contrato pequeño, y el framework las combina. Así, una pieza mala se detecta y se descarta sola, y el tuner decide qué combinación sirve.

## 3. Especificación del problema

Un problema se especifica con cuatro piezas; ninguna describe cómo resolverlo.

### 3.1 Instancia

Una clase de Python inmutable con los datos, accesores derivados y tres responsabilidades: `to_text()` fija el formato de entrada del modelo C++, `parse`/`load` leen ese formato y los archivos del benchmark, y los generadores producen instancias al azar reproducibles por semilla. El pack del problema expone `make_instances(n, semilla, tamaño)` y cuatro tamaños: `micro_size` (validar componentes), `default_size` (sonda de diversidad, casos generados), `bench_size` (medir velocidad) y el de entrenamiento del tuner.

En el CLSP:

```python
@dataclass(frozen=True)
class CLSPInstance:
    demand: tuple[tuple[float, ...], ...]   # d[i][t]
    setup_cost: tuple[float, ...]           # s[i]
    holding_cost: tuple[float, ...]         # h[i]
    setup_time: tuple[float, ...]           # st[i]
    capacity: tuple[float, ...]             # cap[t]

    def to_text(self) -> str: ...   # "n T", la capacidad por período y, por ítem, "s h st" y su demanda
    @staticmethod
    def trigeiro(n, T, rng, utilization=0.9, tbo=2.0, ...): ...   # generador al estilo Trigeiro et al.
```

El generador `trigeiro` sigue el de la literatura: demanda normal truncada con alrededor de 20 % de ceros, costo de setup derivado de un tiempo entre pedidos (TBO) objetivo por la fórmula EOQ, tiempos de setup como fracción de la capacidad, y capacidad uniforme para una utilización objetivo, ajustada para que siempre exista un plan factible. Un caso de 2 ítems y 3 períodos en el formato de `to_text`:

```
2 3
113 113 113
186 4.0 8.3
0.0 31 0.0
1628 5.0 8.3
95 43 79
```

El generador es la pieza humana con más efecto en el resultado final: si no se parece al benchmark objetivo, el tuner afina para otras instancias (sección 10).

### 3.2 Descripción (`ModelSpec`)

Lo que el LLM lee del problema. Sus campos:

| campo | contenido | ejemplo en el CLSP |
| --- | --- | --- |
| `name` | nombre del problema | "Lot sizing capacitado multi-ítem (CLSP)" |
| `description` | datos, restricciones y objetivo, en lenguaje natural | setups, capacidad compartida, sin backlog, inventario inicial 0; minimizar setups más inventario |
| `instance_source` | el código de la clase de instancia (en el prompt compacto, solo campos, accesores y `to_text`) | la clase de arriba |
| `answer_format` | el formato neutral de una respuesta, con un ejemplo | matriz 0/1 ítem × período, `[[1, 0, 1], [1, 1, 0]]` |
| `families` | nombres y significado de las familias de restricciones y de los términos del costo | familia `demanda` (unidades no cubiertas); términos `setup` e `inventario` |
| `forbidden_modules` | módulos que el código generado no puede importar (no va al prompt; la generación de la vista MIP rechaza el código que los importa) | el oráculo y los casos (sería copiar la respuesta) |

La descripción no dice cómo resolver el problema; las pistas algorítmicas (por ejemplo, "vecindarios acotados en flowtime") van aparte, como indicación explícita del investigador (`--hint`), y quedan registradas en las estadísticas de la corrida.

Dos reglas de la descripción salieron de fallos de generación:

- **La respuesta es siempre una lista de listas**, aunque el problema tenga una sola secuencia o un solo vector (en el SSCFLP, `[[2, 0, 2, 2]]`: el centro de cada cliente). Con respuestas planas, el LLM escribía modelos que no coincidían con la forma `vector<vector<int>>` del contrato (corridas 158 y 159).
- **La descripción dice cuál es la solución trivial.** La coherencia (sección 4) compara la penalización del modelo con la del oráculo, que depende del costo de la trivial; si la descripción no la fija, el LLM elige otra y el modelo se rechaza aunque todo lo demás esté bien (SSCFLP, corrida 173). En el MKP la trivial es un greedy por beneficio sobre consumo; en el SSCFLP, cada cliente al centro más barato con capacidad libre y, si alguno no cabe, first fit decreasing.

### 3.3 Casos de prueba (`cases.json`)

Instancias muy chicas con respuestas etiquetadas, al estilo de los jueces de programación competitiva. Cada caso trae la instancia en el formato de `to_text`, varias respuestas en el formato neutral y, si se conoce, el óptimo:

```json
{"name": "clsp_0_2x3", "visible": true, "optimum": 5070.0,
 "instance": "2 3\n113 113 113\n186 4.0 8.3\n...",
 "solutions": [
   {"answer": [[1, 1, 1], [1, 1, 1]], "feasible": true,  "cost": 5442.0},
   {"answer": [[0, 1, 0], [1, 1, 1]], "feasible": true,  "cost": 5070.0},
   {"answer": [[1, 0, 0], [1, 0, 0]], "feasible": false, "violates": ["demanda"]}]}
```

Las respuestas cubren la solución trivial, soluciones razonables, el óptimo y soluciones infactibles con las familias que violan. En el CLSP hay 6 casos (de 2×3 a 4×3), 1 visible en el prompt y 5 ocultos; se generan con un script que etiqueta cada respuesta con el oráculo y calcula el óptimo por fuerza bruta (todos los planes de setups, cada uno con su LP de producción). Así, los casos no agregan una especificación nueva: fijan en ejemplos concretos lo que dice el oráculo, con respuestas que el generador de instancias no garantiza (infactibles etiquetadas y óptimos).

### 3.4 Oráculo

**Oráculo.** Seis funciones en Python (más una opcional, well\_formed) que definen el problema de forma ejecutable. Las dos centrales son las violaciones por familia (0 = cumple) y los términos del costo; una solución es factible si todas sus violaciones son 0, y su costo es la suma de los términos. El oráculo del CVRP completo tiene unas 50 líneas:

```python
def canonical(sol): ...                    # forma canónica (rutas ordenadas por su primer cliente)
def trivial_solution(inst): ...            # una ruta por cliente
def random_solution(inst, rng): ...        # para generar soluciones de prueba
def from_answer(inst, answer): ...         # formato neutral de los casos -> solución

def violations(inst, sol) -> dict[str, float]:
    seen = conteo de visitas por cliente
    visita = sum(|seen[c] - 1| for c in clientes) + visitas a nodos que no existen
    capacidad = sum(max(0, carga(r) - Q) for r in sol)
    return {"visita": visita, "capacidad": capacidad}

def cost_terms(inst, sol) -> dict[str, float]:
    return {"distancia": sum(dist(0 -> r -> 0) for r in sol)}
```

Qué recibe y qué devuelve cada función (`inst` es una instancia; `sol`, una solución en la representación interna del oráculo, que debe ser hashable porque se memoriza):

| función | devuelve | ejemplo en el CVRP |
| --- | --- | --- |
| `canonical(sol)` | la misma solución en forma canónica, para que dos soluciones equivalentes sean iguales | tupla de rutas no vacías, ordenadas por su primer cliente |
| `trivial_solution(inst)` | una solución válida conocida; fija la escala de la penalización | `((1,), (2,), (3,))`: una ruta por cliente |
| `random_solution(inst, rng)` | una solución bien formada al azar (puede ser infactible) | clientes barajados, cortados en rutas |
| `from_answer(inst, answer)` | la solución que corresponde a una respuesta en el formato neutral de los casos (listas JSON) | `[[3, 1], [2]]` → `((2,), (3, 1))` |
| `violations(inst, sol)` | `dict[str, float]`: una entrada por familia de restricciones, con su magnitud ≥ 0; 0 = se cumple | `{"visita": 0.0, "capacidad": 12.0}` |
| `cost_terms(inst, sol)` | `dict[str, float]`: una entrada por término del costo; el costo es la suma | `{"distancia": 1534.2}` |

Una solución es factible si todas sus violaciones son 0 (con tolerancia 10⁻⁶). Las claves de los dos diccionarios son siempre las mismas para un problema, y son los nombres que usan la descripción, los casos, el modelo C++ y la vista MIP. La magnitud de una violación mide cuánto falta para cumplirla (unidades de carga sobrantes, clientes sin visitar): la búsqueda la usa para acercarse a la factibilidad, y la validación la compara contra el modelo C++ en instancias generadas. Los casos de prueba, en cambio, solo registran qué familias se violan.

**Forma de la solución (well\_formed).** Una séptima función, opcional, dice si una solución tiene la forma del problema: en el SSCFLP, una sola fila con un centro válido por cliente; en el MKP, una fila de índices de ítems distintos. Las violaciones no alcanzan para esto: un vector con otra forma puede no violar nada por casualidad, o ser evaluado por el modelo C++ leyendo fuera de rango. La validación la aplica a la trivial y a las soluciones al azar del oráculo y, desde la sección 5, a todo lo que devuelve un componente. El CVRP no la define (sus violaciones ya cubren cualquier forma).

El oráculo no tiene que ser eficiente: se usa solo para validar.

## 4. Generación y validación del modelo C++

El LLM escribe un único header `model.hpp` con un contrato genérico, igual para todo problema. La solución es siempre `std::vector<std::vector<int>>` con la forma de la respuesta del problema; el resto es libre (estructuras auxiliares, precomputaciones, evaluación incremental).

El prompt del modelo lleva, en este orden: la tarea, la descripción, la clase de la instancia con su formato, el formato de la respuesta, las familias y los términos, el contrato y los casos visibles. El contrato es idéntico para todo problema y se le muestra al LLM tal cual (encabezado de `native/include/hsf/generic.hpp`):

```cpp
// El contrato (el modelo va en `namespace gen` y se llama `Model`):
struct Model {
    using Solution = std::vector<std::vector<int>>;   // la solución con la forma de la respuesta del problema
    double penalty;                                   // peso de una unidad de violación en `objective`
    static Model parse(const std::string& text);      // la instancia en su formato de entrada
    Solution trivial() const;                         // la solución trivial (la de la descripción)
    Solution random(hsf::Rng& rng) const;             // una solución al azar bien formada
    // magnitud de cada familia de restricciones (0 = se cumple) y cada término del costo, con sus nombres
    void violations(const Solution& s, std::vector<std::pair<std::string, double>>& out) const;
    void cost_terms(const Solution& s, std::vector<std::pair<std::string, double>>& out) const;
    double objective(const Solution& s) const;        // Σ costo + penalty · Σ violaciones
    bool feasible(const Solution& s) const;           // todas las violaciones en 0
};
// `penalty` = 10 · (|costo de la solución trivial| + 1). Los esqueletos y los componentes solo usan
// `objective`, `feasible` y lo que el modelo exponga.

// en <hsf/core.hpp>:
namespace hsf {
struct Rng {
    std::mt19937_64 g;
    explicit Rng(uint64_t seed) : g(seed) {}
    double uniform();  // uniforme en [0, 1)
    int below(int n);  // entero uniforme en [0, n)
};
}
```

El mensaje de sistema fija cinco reglas:

1. Un solo bloque C++ con `model.hpp` completo: `#pragma once`, `#include <hsf/core.hpp>` y los headers estándar que use, todo en `namespace gen`.
2. Solo la biblioteca estándar. Si el costo o las violaciones dependen de resolver un subproblema de optimización, implementarlo de forma exacta (los casos lo verifican).
3. Sin entrada/salida ni variables globales mutables; la memoria de trabajo puede ir en miembros `mutable` (un modelo se usa en un solo hilo).
4. `objective` y `feasible` se llaman cientos de miles de veces por segundo: precalcular en `parse` lo que dependa solo de la instancia y no reservar memoria en cada llamada.
5. Usar exactamente los nombres de familias y términos indicados.

La regla 2 es la que exige el CLSP: el costo de un plan de setups depende de la producción óptima, que es un flujo de costo mínimo; la descripción de la familia \`demanda\` dice que la producción es la óptima dado el plan, y el LLM eligió por su cuenta calcularla como un flujo de costo mínimo en C++.

La penalización se fija igual que en el oráculo, penalty = 10 · (|costo de la solución trivial| + 1), así los esqueletos pueden recorrer soluciones infactibles con una función objetivo única.

Esta regla es la razón de que la descripción deba fijar la solución trivial (sección 3.2): el modelo y el oráculo tienen que llegar a la misma penalización.

**Espacios de trabajo.** Cada generación queda en un directorio propio (`generated/v2/<problema>` en el protocolo v2) con su modelo, su catálogo y su vista MIP. Si el directorio tiene un `model/model.hpp`, la generación de componentes y la optimización usan ese modelo y no el del paquete (`generation_for`), así varias generaciones del mismo problema conviven sin pisarse.

El algoritmo 1 resume el ciclo de generación y corrección:

```
Algoritmo 1: Generación del modelo con corrección por ediciones
Entrada: especificación S, casos C, oráculo O, rondas R
Salida: modelo M aceptado, o falla
  1 P ← PromptModelo(S, C_vis)
  2 para r ← 1 hasta R hacer
  3     y ← LLM(P)
  4     si r = 1 entonces M ← BloqueCpp(y)
  5     si no M ← AplicarEdiciones(M, y)                      ▷ bloques buscar/reemplazar
  6     ρ ← ValidarModelo(M, C, O)                            ▷ en un proceso aparte
  7     si ρ.aceptado entonces devolver M
  8     P ← PromptCorrección(M, ρ)
  9 devolver falla
```

La validación corre en un proceso aparte, así un segfault del código generado rechaza el modelo sin tumbar la generación. Tiene cuatro capas en orden; la primera que falla define el reporte:

1. **Compilación** (g++ con pybind11): el error del compilador va al reporte.
2. **Casos** (visibles y ocultos): mismas familias violadas y mismo costo que la respuesta etiquetada.
3. **Casos generados**: en instancias del generador (micro y de tamaño realista), las mismas violaciones y el mismo costo que el oráculo, en la solución trivial, en soluciones al azar y en soluciones rotas a propósito.
4. **Coherencia**: `objective` = costo + penalty · violaciones, y `feasible` ⇔ sin violaciones.

El reporte de rechazo es concreto: el caso, la respuesta, el valor esperado y el obtenido, por término ("costo esperado 1534, obtenido 1490; término *inventario*: esperado 312, obtenido 268"). Con eso, en el job shop y el CVRP el modelo se aceptó a la primera; falta medir las rondas en los cinco problemas con el pipeline actual.

**Optimización.** Un segundo paso (`native_model_optimizer`) pide una versión más rápida con las mismas salidas. Se acepta si coincide con el modelo aceptado en todas las salidas (prueba diferencial) y alguna medida de velocidad (evaluaciones del objetivo por segundo, o la velocidad de los vecindarios del catálogo) mejora al menos 1,2× (1,1× en las pasadas siguientes).

## 5. Generación de componentes

Un componente es una clase C++ que implementa la interfaz de un *slot* sobre el modelo, más una cabecera JSON con su nombre y sus parámetros (con tipo y rango, para el tuner). El LLM genera *n* componentes estructuralmente distintos por slot en una sola llamada; cada uno se compila y se valida por separado.

| slot | interfaz | lo usan |
| --- | --- | --- |
| `constructor` | build(rng): una solución inicial factible, determinista dada la semilla | todos |
| `neighborhood` | `moves(s)`, `apply(s, m)`, `delta(s, m)`, `tabu_key(m)`, `estimate` opcional | SA, ILS, VNS, TS, PR, HYB |
| `perturbation` | `perturb(s, strength, rng)` | ILS, PR, HYB |
| `relink` | camino de una solución guía a otra | PR |
| `destruction` | `destroy(s, ratio, rng)` → índices de variables de la vista MIP que se liberan | HYB |

Un movimiento es un arreglo de enteros (`Move = std::array<int, 7>`, seis libres), así los esqueletos no dependen del problema. Las interfaces traen métodos por defecto (por ejemplo `tabu_key(m) = m`, correcto para movimientos auto-inversos, y `sample` sin gastar azar cuando caben todos).

### 5.1 Estructura de un componente

Un componente es un archivo C++ con tres partes: una cabecera JSON en un comentario, la clase que implementa la interfaz del slot sobre `Model`, y una fábrica `make_component` que lee los parámetros y construye la clase. Un vecindario del CLSP generado por el LLM, completo salvo detalles:

```cpp
// COMPONENT: {"name": "setup_toggle_flip", "slot": "neighborhood",
//             "params": {"sweep_items_first": {"type": "cat", "values": ["yes", "no"]}}}
class SetupToggleFlip : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    SetupToggleFlip(const Model& m, bool itemsFirst) : M(m), itemsFirst_(itemsFirst) {}

    void moves(const Sol& s, std::vector<Move>& out) override {   // un movimiento por (ítem, período)
        for (int i = 0; i < M.n; ++i)
            for (int t = 0; t < M.T; ++t) out.push_back(mk(i, t));   // o período primero, según el parámetro
    }
    Sol apply(const Sol& s, const Move& m) override {             // enciende o apaga el setup
        Sol r = s;
        r[m[0]][m[1]] = 1 - r[m[0]][m[1]];
        return r;
    }
    double delta(const Sol& s, const Move& m) override {          // objective(apply(s, m)) − objective(s)
        return M.objective(apply(s, m)) - base(s);                  // base(s): objetivo de s memorizado
    }
private:
    const Model& M;
    bool itemsFirst_;
    ...
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    bool f = params.text("sweep_items_first", "yes") == "yes";
    return std::make_unique<SetupToggleFlip>(model, f);
}
```

El framework compila todos los componentes de un catálogo junto con el modelo en un solo módulo; cada archivo queda en su propio espacio de nombres, así que `make_component` y las clases auxiliares no chocan. El componente recibe una referencia constante al modelo y puede guardar estado propio (memoria de trabajo, como el objetivo de la última solución en `base`), porque cada corrida crea sus propias instancias.

**Parámetros.** La cabecera declara cada parámetro con su tipo y su dominio; esa declaración es la que entra al espacio de configuración, como `<componente>.<parámetro>`, condicionada a que el componente esté elegido.

| tipo | declaración | lectura en la fábrica | valor por defecto |
| --- | --- | --- | --- |
| entero | `{"type": "int", "range": [1, 10]}` | `(int) params.get("max_len", 4)` | `default` si lo trae; si no, el punto medio del rango |
| real | `{"type": "float", "range": [0.01, 0.5], "log": true}` | `params.get("ratio", 0.1)` | `default`; si no, el punto medio (geométrico con `log`) |
| categórico | `{"type": "cat", "values": ["yes", "no"]}` | `params.text("sweep_items_first", "yes")` | `default`; si no, el primer valor |

`"log": true` le dice a irace que muestree en escala logarítmica (para tasas, temperaturas o tamaños que varían en órdenes de magnitud). El valor por defecto de la fábrica solo se usa si el parámetro no llega; las corridas reciben siempre el de la configuración. Los esqueletos declaran sus parámetros con el mismo formato (sección 7). La capa de aporte en combinación prueba configuraciones al azar dentro de estos rangos antes de concluir que un componente no aporta, porque algunos son inútiles con los valores por defecto y útiles con otros.

El algoritmo 2 resume la generación de un slot:

```
Algoritmo 2: Generación de un slot
Entrada: slot σ, cantidad n, modelo M, catálogo K_σ, rondas R
Salida: catálogo K_σ ampliado
  1 P ← PromptSlot(σ, n, Contrato(σ), Interfaz(M), K_σ)
  2 Q ← Parsear(LLM(P)) ∖ {c : nombre(c) ∈ K_σ}
  3 para cada c ∈ Q hacer
  4     para r ← 1 hasta R hacer
  5         ρ ← Compilar(M, K_σ ∪ {c})                        ▷ error del compilador, si falla
  6         si compiló entonces ρ ← Validar(c, M, K_σ)        ▷ validación por capas, proceso aparte
  7         si ρ.aceptado entonces
  8             K_σ ← K_σ ∪ {c}; pasar al siguiente c
  9         c ← AplicarEdiciones(c, LLM(PromptCorrección(c, ρ)))
 10 devolver K_σ
```

**Validación por capas.** Corre sobre micro-instancias (generadas, de 2 a 8 elementos) con semillas fijas, para que un fallo sea reproducible y el mensaje concreto:

1. **Compilación**: el componente se compila con el modelo y los aceptados del slot; el error del compilador vuelve al LLM.
2. **Sintáctica**: la cabecera JSON es válida (nombre, slot, parámetros con tipo y dominio) y la clase implementa la interfaz del slot.
3. **Contractual**: las propiedades del slot, como *property-based testing* ligero sobre soluciones de prueba (las triviales, las de los constructores y al azar), con semillas fijas.
4. **Operacional**: todo corre en un proceso aparte con un límite de tiempo; un segfault, un `abort` por índice fuera de rango (compilado con `_GLIBCXX_ASSERTIONS`) o un método que no termina es un rechazo con la señal o el tiempo.
5. **Calidad**: tiene sentido como pieza de búsqueda, con umbrales laxos (no elige el mejor, descarta lo inútil).
6. **Diversidad**: no duplica a uno ya aceptado del mismo slot, medido en una instancia de tamaño realista. La firma es lo que el componente *produce*, no su código: para un vecindario, el conjunto de soluciones alcanzables desde una solución fija (similitud de Jaccard, umbral 0,8); para perturbaciones y destrucciones, un perfil de forma del conjunto que tocan promediado sobre muchas semillas (comparar conjuntos exactos mide la sincronía del generador aleatorio, no la idea).

La tabla detalla qué se verifica en cada slot. Las propiedades contractuales detectan errores de implementación; las de calidad, piezas que no pueden aportar.

| slot | contractual | calidad | diversidad |
| --- | --- | --- | --- |
| `constructor` | `build` da una solución factible en cada micro-instancia y semilla; la misma semilla da la misma solución | factible también en la instancia de tamaño realista; no mucho peor que la solución de referencia | — |
| `neighborhood` | `moves` no es vacío en alguna solución de prueba; `delta(s, m)` = f(`apply`(s, m)) − f(s) con tolerancia; `sample(s, k)` devuelve k movimientos distintos; si hay `estimate`, es finita y ordena los movimientos como `delta` en la mayoría de los pares | algún movimiento muestreado mejora en alguna micro-instancia; desde la solución de partida del esqueleto hay movimientos que mejoran; parte de esas mejoras no las alcanza ningún par | conjunto de vecinos alcanzables (Jaccard) |
| `perturbation` | no devuelve la misma solución con todas las semillas y soluciones de prueba | más fuerza (strength 3) cambia al menos tanto como menos fuerza (strength 1), en la instancia realista | perfil de forma de lo que cambia |
| `relink` | `distance(a, a)` = 0, simétrica y > 0 entre soluciones distintas; cada `step` hacia la guía baja la distancia estrictamente y llega en a lo más `distance(a, b)` pasos | — | — |
| `destruction` | libera al menos una variable; las liberadas son variables estructurales de la vista MIP; la parte fija y la liberada cubren todas las variables sin solaparse | más razón libera más variables (0,1 contra 0,5) | perfil de forma de lo que libera |

La factibilidad después de un movimiento o de una perturbación no se exige: los esqueletos recorren soluciones infactibles con la penalización del modelo. El framework tiene una séptima capa, el **aporte en combinación** (una corrida corta dentro de cada esqueleto declarado, desde cada constructor de partida, contra un componente nulo, quitando los esqueletos donde no aporta), pero la generación nativa no la activa: el tuner hace ese descarte con más presupuesto.

**Chequeo de forma.** La capa contractual verifica además, con well\_formed del oráculo, que el constructor, el apply de un vecindario, la perturbación y el relink devuelvan soluciones con la forma del problema. Se agregó después de la corrida 163: una perturbación del SSCFLP devolvía una lista de clientes por centro (otra representación de la misma información) y pasaba todas las capas, porque el modelo la evaluaba sin quejarse. Con el chequeo, esa perturbación se rechaza con el reporte `perturbation.well_formed`. Para que el LLM no se equivoque de representación, el prompt de componentes trae ahora una sección "La solución" con el answer\_format de la descripción.

**Corrección por ediciones.** Las respuestas de corrección son bloques buscar/reemplazar sobre el componente rechazado, no el componente completo; esto reduce la salida y evita que el LLM reescriba lo que ya funcionaba.

**Optimización.** `native_optimizer` pide versiones más rápidas de los aceptados, con pruebas diferenciales: los mismos movimientos en el mismo orden, el mismo `apply`, el mismo `delta` (con tolerancia), la misma perturbación con la misma semilla. Se acepta con una mejora de al menos 1,2× en alguna medida (deltas por segundo, pasos de TS, pasos de caminata), y los aceptados se vuelven a optimizar en pasadas encadenadas (1,1× desde la segunda). La caminata también paga lo que no cambia, así que se le pide el 40 % de la mejora, con un piso de 1,1×: por debajo, la diferencia cabe en el ruido de medir 1 s en un runner compartido. Los resultados de este documento usan los umbrales anteriores (1,5× y 1,2×).

El algoritmo 5 es el mismo para el modelo y para los componentes; cambian las medidas (evaluaciones del objetivo por segundo en el modelo; deltas, pasos de TS y pasos de caminata en un vecindario; perturbaciones por segundo) y la prueba diferencial (las mismas salidas del modelo en los casos y en instancias generadas; los mismos movimientos, `apply`, `delta` y perturbaciones con la misma semilla). Al prompt se le agrega un perfil de dónde se va el tiempo en cada método del vecindario y, si existe, otro componente del mismo slot ya optimizado como ejemplo.

```
Algoritmo 5: Optimización de una pieza aceptada (modelo o componente)
Entrada: pieza x aceptada, umbrales γ_1 = 1,2 y γ = 1,1, pasadas q, rondas R
Salida: la versión más rápida de x con las mismas salidas
  1 para p ← 1 hasta q hacer
  2     μ ← Medir(x)                                          ▷ evaluaciones, deltas, pasos por segundo
  3     γ_p ← γ_1 si p = 1, si no γ
  4     P ← PromptOptimización(x, μ, γ_p, Perfil(x))
  5     para r ← 1 hasta R hacer
  6         x′ ← AplicarEdiciones(x, LLM(P))
  7         si MismasSalidas(x′, x) y ∃m: μ′_m ≥ γ_p μ_m entonces  ▷ prueba diferencial
  8             x ← x′; pasar a la siguiente pasada
  9         P ← PromptCorrección(x′, reporte)
 10     si ninguna ronda mejoró entonces devolver x
 11 devolver x
```

## 6. Vista MIP generada y la matheurística HYB

**Vista MIP.** El LLM escribe en Python la formulación lineal del problema como ocho funciones de módulo; el prompt incluye la descripción, la instancia, el código del oráculo (importable) y los casos con sus óptimos.

```python
def variables(inst) -> {nombre: (cota_inf, cota_sup, "binary" | "continuous")}
def structural_variables(inst) -> [nombres]       # las que describen la solución
def to_assignment(inst, sol) -> {nombre: valor}    # solución -> valores de las estructurales
def aux_values(inst, sol) -> {nombre: valor}       # auxiliares en el punto de sol (cargas, inventarios, tiempos)
def from_assignment(inst, x) -> sol                # inversa de to_assignment
def constraint_families(inst) -> {familia: [(coeficientes, sentido, lado derecho)]}
def objective_terms(inst) -> {término: (coeficientes, constante)}
def variable_groups(inst) -> {grupo: [nombres]}    # partición de las estructurales en bloques chicos
```

Las familias de restricciones y los términos del objetivo llevan los mismos nombres que en el oráculo. Eso permite validar *por familia*: para cada solución de prueba se compara, familia por familia, si el MIP la viola en el punto (to\_assignment + aux\_values) con lo que dice el oráculo, y se compara el valor de cada término del objetivo. Una segunda capa resuelve los casos con CBC y exige el óptimo conocido. El reporte de rechazo nombra la familia, la solución y el lado izquierdo contra el derecho ("la familia *capacidad* se viola en el MIP: 81,2 > 79,0 en una solución que el oráculo da por factible").

En el CLSP, el LLM agregó por su cuenta las desigualdades (l,S) de Barany, Van Roy y Wolsey (unas 4 200 restricciones más que la formulación que había escrito un humano), una formulación más fuerte.

**Algoritmo 3. HYB.** Alterna un ILS con recocido en C++ con sub-MIP en Python sobre la vista MIP:

```
Algoritmo 3: HYB: búsqueda local en C++ alternada con sub-MIP
Entrada: instancia I, presupuesto T, destrucción D, fracciones λ_ls y λ_mip, razón δ
Salida: mejor solución factible s*
  1 Π ← ConstruirMIP(I)                                       ▷ desde la vista MIP
  2 s ← ILS(Constructor(I), λ_ls T)                           ▷ en C++
  3 s* ← s si s es factible
  4 mientras quede tiempo hacer
  5     F ← D(s, δ)                                           ▷ variables que se liberan
  6     x ← ToAssignment(s)
  7     s′ ← Resolver(Π; x_v fijo para v ∉ F; arranque x; límite λ_mip T)
  8     si s′ existe y f(s′) ≤ f(s) entonces s ← s′
  9     s ← ILS(s, λ_ls T)
 10     si s es factible y f(s) < f(s*) entonces s* ← s
 11 devolver s*
```

La búsqueda local encuentra rápido buenas soluciones; el sub-MIP reoptimiza de forma exacta una parte, con las restricciones y el costo completos, y sale de óptimos locales que ningún movimiento alcanza. CBC recibe al menos 0,2 s y un error del solver cuenta como "sin solución".

**Destrucciones genéricas.** El framework aporta dos sobre `variable_groups`, sin código del problema: `group_window` libera una ventana de grupos consecutivos (con grupos por período, una ventana de tiempo) y `random_variables` libera una fracción de las variables al azar. El LLM también puede escribir destrucciones en C++ (slot `destruction`), pero en el CLSP, el job shop y el CVRP no les ganaron a las genéricas (sección 9), así que por defecto el tuning usa solo las genéricas.

## 7. Esqueletos y configuración automática

**Esqueletos.** Seis, en C++ (`native/include/hsf/core.hpp`), con una versión de referencia en Python de la misma semántica que usa la validación por combinación. Cada uno declara sus slots y sus parámetros con tipo y rango.

| esqueleto | slots | parámetros principales |
| --- | --- | --- |
| SA | constructor, vecindario | T0, enfriamiento (por tiempo o iteraciones), T\_end, alpha, evaluación por objetivo o por delta |
| ILS | constructor, vecindario, perturbación | fuerza, primera o mejor mejora, muestra o vecindario completo, aceptación (mejora o recocido relativo) |
| VNS | constructor, vecindario (el shake usa todos los del catálogo) | fuerza del shake, fracción de tiempo de la búsqueda local |
| TS | constructor, vecindario | tenencia, tamaño de la lista de candidatos, filtrado por estimación, élite y saltos atrás |
| PR | constructor, vecindario, relink (perturbación opcional) | tamaño de la población, mejora tabú o ILS, candidatos por camino, banda de selección |
| HYB | constructor, vecindario, perturbación, destrucción | fracciones de tiempo de la búsqueda local y del sub-MIP, fracción destruida |

SA, ILS, VNS y TS comparten un control de penalización: el peso de las violaciones puede empezar más bajo que el del modelo y ajustarse para visitar una fracción objetivo de soluciones factibles, como en HGS.

**Espacio de configuración.** Condicional: el esqueleto activa sus slots; cada slot elige entre los componentes compatibles del catálogo; cada componente activa sus parámetros declarados (`<componente>.<parámetro>`), y el esqueleto los suyos. Se exporta como parámetros condicionales de irace. Una configuración completa corre entera en C++, sin cruzar a Python, salvo los sub-MIP de HYB.

**Algoritmo 4. Tuner por etapas** (`--tuner staged`). Afinar todo en un solo espacio repartía el presupuesto de irace entre estructuras muy distintas, y el resultado dependía de la réplica.

```
Algoritmo 4: Tuner por etapas
Entrada: catálogo K, instancias de entrenamiento I, presupuesto B, cantidad k
Salida: configuración θ*
    ▷ Etapa 1: carrera estructural, con parámetros por defecto
  1 E ← {Default(e)} ∪ {Default(e) con un componente cambiado}  ▷ e esqueleto
  2 E ← E ∪ {por esqueleto, el mejor componente de cada slot}
  3 S ← las k mejores de E en I, de esqueletos distintos
    ▷ Etapa 2: irace en el espacio reducido
  4 Θ′ ← esqueletos de S + componentes no peores que el default
  5 L ← Irace(Θ′, I, B − |E|, iniciales = S)
    ▷ Etapa 3: validación con semillas nuevas
  6 devolver argmin_θ ∈ L ∪ S CostoMedio(θ, I)
```

Partir de las estructuras de la etapa 1 garantiza que el resultado no queda peor que un default. Con irace en un solo espacio (`--tuner irace`), el ganador se compara en instancias de test contra el default de cada esqueleto y contra una variante por componente.

## 8. Prompts compactos

Por defecto, lo que el LLM solo *usa* va en el prompt como prototipos (declaraciones, firmas y comentarios), y lo que tiene que *modificar* va completo.

| en el prompt de | va como prototipo | va completo |
| --- | --- | --- |
| componentes y destrucciones | el modelo C++, los componentes ya en el catálogo, `Rng` y `Config` | la interfaz del slot (sus métodos por defecto son contrato) |
| modelo y vista MIP | la clase de la instancia: campos, accesores y `to_text` (sin generadores ni `parse`) | el oráculo (es la especificación) y los casos |
| corrección y optimización | el modelo, si el componente solo lo usa | el componente o el modelo que se modifica |

El contrato del framework está escrito para esto: en `core.hpp`, `Rng` y `Config` tienen sus declaraciones arriba y sus definiciones (funciones inline) en una sección marcada, que el modo completo agrega y el compacto omite. El código que escribe el LLM, en cambio, se recorta con un parser: quita los cuerpos de las funciones (reconocidos por la `)` que precede a la llave), conserva clases, miembros y comentarios, incluido el de la línea de la firma. No se pide al LLM separar header e implementación porque los componentes llaman al modelo en los bucles internos y la compilación en un solo header permite inlining.

En el CLSP, el prompt de componentes baja de 22,2 a 9,4 mil caracteres, el de destrucciones de 18,2 a 7,6 y el del modelo de 9,9 a 5,2. El efecto en la generación se mide en la sección 9.

## 9. Evaluación experimental

Siete problemas, todo generado (modelo, componentes y, donde hay HYB, vista MIP). Los números salen de `results/README.md`; los protocolos difieren por problema y faltan réplicas en algunos (ver sección 10).

**Protocolo v2.** Para que los problemas sean comparables entre sí, los siete se regeneraron con el mismo protocolo (`generated/v2/<problema>`): modelo C++, 3 constructores, 3 vecindarios y 3 perturbaciones (hasta 3 rondas de corrección) y la vista MIP (no en los flow shop), con prompts compactos, la representación de la solución en el prompt de componentes y el chequeo de forma. Corridas 168–187 de `generate.yml`.

| problema | rondas del modelo | componentes | aceptados en la 1.ª ronda | rechazos | USD |
| --- | --- | --- | --- | --- | --- |
| flow shop, flowtime | 1 | 9/9 | 8/9 | 2 | 0,77 |
| flow shop, makespan | 1 | 9/9 | 9/9 | 0 | 0,62 |
| job shop | 1 | 9/9 | 8/9 | 1 | 1,31 |
| CLSP | 1 | 9/9 | 8/9 | 2 | 1,16 |
| CVRP | 1 | 9/9 | 8/9 | 2 | 2,50 |
| SSCFLP | 1 | 9/9 | 8/9 | 1 | 1,18 |
| MKP | 1 | 9/9 | 4/9 | 6 (3 de compilación) | 1,34 |
| total |  | 63/63 | 53/63 | 14 | 8,88 |

El modelo se aceptó en la primera ronda en los siete. No se cuenta un intento fallido del modelo del SSCFLP (0,54 USD), anterior a la regla de la solución trivial (sección 3.2).

**Benchmarks y referencias.** Todos los conjuntos están en el repositorio con su script de descarga (`fetch.py`) y sus valores de referencia con la fuente:

| problema | benchmark | referencia |
| --- | --- | --- |
| flow shop (ambos objetivos) | Taillard, 120 instancias | mejores conocidas publicadas |
| job shop | 162 instancias: Taillard ta01–ta80, la, swv, orb, abz, ft, yn | Weise (2020); las de JSPLIB tenían errores en ta11, ta15, ta19 y ta20 |
| CVRP | Uchoa X completo (100); FrontierCO (Golden y Arnold, 45); test de ReEvo (3×64) y de MCTS-AHD (2×64) | X: mejores conocidas de CVRPLIB; FrontierCO: las suyas; ReEvo y MCTS-AHD: HGS (PyVRP), mejor de 3 semillas |
| CLSP | Trigeiro, Thomas y McClain (G y F) | Degraeve y Jans; Belvaux y Wolsey |
| SSCFLP | 217 instancias: Holmberg (71), Díaz y Fernández (57), Yang (20), TB4 (45), cap de la OR-Library en versión de fuente única (24); capa–c y TBED1 con `--large` | Guastaroba y Speranza (2014), Kong (2021), óptimos de Holmberg; CBC donde no hay tabla |
| MKP | OR-Library (mknap1, mknap2 y las 270 de Chu y Beasley); test de ReEvo/MCTS-AHD (MKP100 y MKP200, 64 cada uno) | publicadas; CBC para los de ReEvo (óptimos) |

Tres fuentes tenían errores que encontró la propia validación de los datos: las cap de CO-Bench no son factibles con fuente única (se usaron las versiones de OR-Brescia), JSPLIB tenía mejores conocidas por debajo de las cotas, y el mknap2 de CO-Bench trae la matriz de consumos traspuesta.

**Resultados publicados de métodos con LLM.** Transcritos de los papers con tabla y página (`results/llm_sota/`), sin ejecutar nada. En los conjuntos sin óptimo publicado calculamos una referencia propia:

| conjunto | nuestra referencia | publicado (gap contra nuestra referencia) |
| --- | --- | --- |
| CVRP50 de MCTS-AHD | HGS: 8,014 | MCTS-AHD 9,286 (+15,9 %), ReEvo 9,327 (+16,4 %), EoH 9,359 (+16,8 %) |
| CVRP100 de MCTS-AHD | HGS: 12,838 | MCTS-AHD 15,782 (+22,9 %), ReEvo 16,092 (+25,3 %), EoH 15,681 (+22,1 %) |
| MKP100 de ReEvo/MCTS-AHD | óptimo: 23,346 | MCTS-AHD 23,269 (−0,33 %), ReEvo 23,245, EoH 23,139 |
| MKP200 | óptimo: 42,939 | MCTS-AHD 42,498 (−1,03 %), ReEvo 42,416, EoH 41,994 |

Las comparaciones tienen cuidados: MCTS-AHD reporta el gap contra el mejor método de cada columna, no contra un solver; sus test de CVRP no son los de ReEvo (otro orden del generador), los de MKP sí; CO-Bench usa 10 s por instancia y en scheduling compara contra la cota inferior de Taillard; FrontierCO permite hasta 3600 s, y su CFLP es de demanda divisible, otro problema que nuestro SSCFLP.

**Afinamiento: una configuración por tipo de instancia.** irace devuelve una configuración para la distribución de instancias de entrenamiento; con tamaños muy distintos en el mismo entrenamiento, elige una que no es buena en ninguno. Por eso se afina una configuración por problema y tipo de instancia, y se entrena con instancias del generador, no del benchmark, que queda para la evaluación:

- tipos: flow shop 50×10, 100×20 y 200×20; job shop 15×15 y 20×15; CLSP 20×20; CVRP como las X (100, 200 y 250 clientes) y en el cuadrado unitario como ReEvo (50 y 100); SSCFLP 20×100, 30×200 y 60×200; MKP como Chu y Beasley (100×5, 250×5, 250×10) y normalizado como ReEvo (100×5, 200×5, 500×5);
- presupuesto: 80 configuraciones × 6 instancias de entrenamiento, con `firstTest` 5 y `sampleInstances`, así irace ve todas las instancias en distinto orden; 6 instancias de test generadas;
- tiempo por corrida proporcional al tamaño (`--scale-budget`): cada problema declara un `budget_scale` (por ejemplo, centros × clientes / 2000 en el SSCFLP), así un tipo más grande recibe más tiempo;
- 2 réplicas por tipo; se elige la de menor gap en el test generado, sin mirar el benchmark.

**Protocolo de evaluación.** `scripts/bench_eval.py` corre la configuración elegida en el benchmark con tiempos que crecen con el tamaño, como en la literatura de cada problema: n·m/2·t ms en el flow shop (Taillard; Ruiz y Stützle) con el análogo de n·m en los demás (operaciones, ítems × períodos, centros × clientes, ítems × restricciones), t = 60; en el CVRP, n·t/100 s con t = 240, el 2,4·n s de Vidal (2022). Para compararse con CO-Bench o FrontierCO se usa su tiempo fijo (`--budget`). El gap se mide contra |referencia|, para que valga también en la maximización del MKP (su costo es el beneficio con signo negativo).

**9.1 Resultados preliminares en benchmarks (cinco problemas, protocolos anteriores al v2).** Gap medio contra la mejor solución conocida, con la mejor configuración afinada.

| problema | benchmark | tiempo | gap medio | referencia de la literatura |
| --- | --- | --- | --- | --- |
| flow shop, makespan | Taillard, 120 instancias | n·m/2·60 ms | 0,155 % | IGirms60: 0,20 %; IGirms240: 0,16 % |
| flow shop, flowtime | Taillard, hasta 100 trabajos | n·m/2·60 ms | 0,21–0,49 % por clase | ALGirtct60: 0,45–0,99 %; MRSILS: 0,22–0,63 % |
| flow shop, flowtime | Taillard, 200 y 500 trabajos | n·m/2·60 ms | 1,9–2,8 % | MRSILS y ALGirtct, 2–4 puntos mejores |
| job shop | Taillard ta01–ta10 (15×15) / ta11–ta20 (20×15) | 30 s | 0,36 % / 1,39 % | — (por completar) |
| CVRP | Uchoa X, 43 instancias de 101 a 298 clientes | 30 s | 1,04 % (0,32 % en 101–149) | HGS: \~0,1–0,3 % |
| CLSP | Trigeiro G (sin G30) / F | 60 s | 0,40 % / 0,26 % | Degraeve y Jans (B&P): 0,47 %; Belvaux y Wolsey (B&C, 900 s): 0,18 % |

En makespan, contra las cotas de EoH (heurísticas evolucionadas con LLM), el gap es −0,15 % frente a 0,23 %. En el CLSP, configuraciones distintas encontraron soluciones por debajo de la mejor publicada en G53 (74 729 < 74 799) y G69 (131 110 < 131 234).

**9.2 Ablaciones.** Cada fila compara una decisión de diseño con su alternativa, con el resto igual.

| decisión | comparación | resultado |
| --- | --- | --- |
| destrucciones de HYB | generadas por el LLM contra genéricas, CLSP / job shop / CVRP, una variante por destrucción (tunings 87, 88, 90) | las genéricas son la mejor o casi la mejor en los tres; lo que mueve a HYB es la búsqueda local |
| vista MIP | generada contra escrita a mano, mismas instancias y semillas (tunings 92–97) | iguales dentro del ruido: CLSP 231 803 contra 234 295, job shop 1 233,0 contra 1 232,2, CVRP 13 511,8 contra 13 528,8 |
| prompts | compactos contra completos, 3 generaciones por modo en CLSP y job shop (runs 145–156) | misma aceptación (27/27 y 18/18), ningún rechazo por diversidad; CLSP 42 % más barato y mejor configuración 1,67 % contra 2,08 %; job shop 13 % más caro, misma calidad |
| tuner | por etapas contra irace en un espacio (job shop, tunings 82 y 83) | encuentra solo la estructura que había que imponer a mano (PR), pero no le gana a imponerla |

**9.3 Costo.** Generar el modelo cuesta de 0,07 a 0,9 USD, los componentes de un problema de 1 a 4 USD, la vista MIP unos 0,35 USD, y optimizar los componentes de 0,5 a 5 USD. El tuning cuesta solo cómputo (alrededor de una hora por réplica en un runner de GitHub Actions).

## 10. Discusión, limitaciones y trabajo futuro

**Lo que muestran los resultados.** Con un oráculo de unas 50 líneas por problema, el pipeline produce solvers al nivel de metaheurísticas publicadas en makespan, flowtime hasta 100 trabajos y CLSP, y a 1 punto en el CVRP. La validación por capas es la que hace esto posible: casi todo lo que llega al catálogo funciona, y lo que no funciona se descarta con un reporte que el LLM sabe corregir. Las ablaciones apuntan a que el valor está en la búsqueda local en C++ y en la elección de la estructura, no en las piezas más exóticas (destrucciones específicas del problema).

**Limitaciones.**

- **Réplicas.** Muchas comparaciones usan una réplica de tuning o una generación por catálogo; varias diferencias están dentro del ruido. Para el paper hace falta un protocolo único con réplicas y pruebas estadísticas.
- **Protocolos mezclados.** Los resultados de 9.1 vienen de corridas en distintos momentos del desarrollo: algunos con el modelo escrito a mano o con la vista MIP de referencia (por ejemplo, el CLSP del tune 79), y en el job shop los dos tamaños salen de configuraciones distintas. El protocolo v2 (sección 9) los repite con el pipeline actual; hasta que termine su afinamiento, los números de 9.1 son preliminares.
- **Dónde no llega.** Flowtime con 200 y 500 trabajos (2–4 puntos detrás de MRSILS): el LLM no encontró aceleraciones específicas del costo de una inserción, ni con una indicación explícita del investigador. En el job shop 20×15 y el CVRP falta la estructura de los métodos de estado del arte (HGS en el CVRP).
- **Elección de las instancias de entrenamiento.** En el CLSP, las configuraciones afinadas en instancias 20×20 generadas se quedan en 1,3 % en Trigeiro G, contra 0,4–0,55 % de las afinadas en tamaños de Trigeiro: el tuner es tan bueno como las instancias que ve.
- **El oráculo sigue siendo humano.** Define el problema y no se puede generar sin circularidad; también la descripción y los casos. Una formulación mal escrita en el oráculo se propaga a todo.
- Referencias propias. En los test de CVRP de MCTS-AHD no hay óptimos publicados; nuestra referencia es HGS con 10 s y 3 semillas, buena pero no óptima, así que los gaps contra ella son una cota. Lo mismo para las Díaz-Fernández del SSCFLP que CBC no resolvió (sin referencia).
- Comparaciones con métodos con LLM con otro presupuesto. ReEvo, MCTS-AHD y EoH buscan una heurística dentro de un ACO con un LLM pequeño; CO-Bench y FrontierCO fijan tiempos (10 s y hasta 3600 s). Una comparación justa reporta también el costo de generación y usa su tiempo, no el nuestro.

**Pistas de dominio que el LLM no recibió.** Las especificaciones del CLSP, el job shop y el CVRP tenían tres campos más, heredados de una versión anterior del generador: la representación de la solución y cómo evaluarla, notas de implementación ("la producción óptima dado un plan es un LP"; "el orden en una máquina se modela con binarias de precedencia") y una pista para la vista constructiva. En el pipeline actual ningún generador los ponía en el prompt, así que todos los resultados de este documento se obtuvieron sin ellos, y se quitaron del código. Es un dato a favor: el LLM dedujo esas estructuras de la descripción, las familias y los casos. Queda abierto si pasarle pistas de dominio explícitas mejora los componentes, a costa de más trabajo humano por problema.

**Constructor completo o solo el puntaje.** Una versión anterior ofrecía dos slots de partida: `constructor` (el LLM escribe `build(rng)` entero) y `greedy_score` (el LLM escribe solo el puntaje de una acción, y un greedy genérico del framework hace el bucle con reglas greedy, RCL o ruleta). El segundo exigía que el modelo expusiera una vista constructiva (estado parcial, acciones candidatas, aplicar, completar), que ningún modelo generado escribió, y se quitó. Los datos no apoyaban la intuición de que el constructor completo falla más: los 12 constructores pedidos (CVRP, flow shop con makespan y con flowtime, job shop) se aceptaron en la primera ronda, con 58 a 105 líneas, menos que muchos vecindarios. Y los mejores (NEH, ahorros de Clarke-Wright, barrido con 2-opt) no son de la forma "elegir la acción de menor puntaje": reinsertan, fusionan o mejoran al final.

**Trabajo futuro.**

1. Un protocolo experimental uniforme con el pipeline final y réplicas (generación y tuning).
2. Reemplazar irace por una carrera de estructuras más barata, y medir cuánto se pierde.
3. Problemas nuevos sin experiencia previa del equipo, para medir el tiempo humano total.
4. Comparación directa con métodos de diseño de heurísticas con LLM (EoH, FunSearch, ReEvo, MCTS-AHD, CO-Bench, FrontierCO): los conjuntos de test y sus resultados publicados ya están en el repositorio; falta correr los solvers del protocolo v2 con sus tiempos.

## Referencias (por completar)

Citas mencionadas en el texto; faltan los datos bibliográficos completos y verificarlos.

- Taillard (1993): benchmarks del flow shop y del job shop.
- Trigeiro, Thomas y McClain (1989): instancias del CLSP.
- Uchoa et al. (2017): instancias X del CVRP.
- Degraeve y Jans: branch-and-price para el CLSP (tabla 9, mejores conocidas de las G).
- Belvaux y Wolsey: branch-and-cut para lot sizing.
- Barany, Van Roy y Wolsey: desigualdades (l,S).
- López-Ibáñez et al.: irace.
- Vidal et al.: HGS para el CVRP.
- Algoritmos de flow shop citados: IGA, ALGirtct, MRSILS, IGirms.
- Diseño de heurísticas con LLM: EoH, FunSearch, ReEvo.
- Weise (2020): mejores conocidas del job shop (jsspInstancesAndResults).
- Vidal (2022): HGS-CVRP; tiempo de 2,4·n s en las X.
- Wouda, Lan y Kool (2024): PyVRP.
- Holmberg, Rönnqvist y Yuan (1999): instancias del SSCFLP.
- Díaz y Fernández (2002); Yang et al. (2012): instancias del SSCFLP.
- Guastaroba y Speranza (2014): kernel search para el SSCFLP (mejores conocidas).
- Kong et al. (2021): resultados del SSCFLP en TB4 y TBED1.
- Beasley (1990): OR-Library (cap, mknap).
- Chu y Beasley (1998): algoritmo genético e instancias del MKP.
- Ruiz y Stützle (2007): tiempo n·m/2·t ms en el flow shop.
- Liu et al. (2024): EoH. Ye et al. (2024): ReEvo. Zheng et al. (2025): MCTS-AHD. Dat et al. (2025): HSEvo.
- Sun et al. (2025): CO-Bench. Feng et al. (2025): FrontierCO.
