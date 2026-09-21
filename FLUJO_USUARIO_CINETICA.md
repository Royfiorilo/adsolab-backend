# 🧪 Flujo de Usuario - Módulo Cinético de AdsoLab

> **Audiencia:** Desarrolladores de frontend y agentes de programación  
> **Propósito:** Especificación completa del flujo de usuario para implementar la interfaz del módulo cinético

---

## 📋 Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Autenticación](#autenticación)
3. [Flujo Completo Paso a Paso](#flujo-completo-paso-a-paso)
4. [Endpoints Detallados](#endpoints-detallados)
5. [Modelos de Datos](#modelos-de-datos)
6. [Casos de Uso](#casos-de-uso)
7. [Validaciones y Errores](#validaciones-y-errores)
8. [Ejemplos de Payloads](#ejemplos-de-payloads)

---

## 🎯 Resumen Ejecutivo

El **módulo cinético** permite a los usuarios:
1. Cargar datos experimentales de cinética de adsorción (tiempo vs cantidad adsorbida)
2. Ajustar modelos cinéticos a sus datos usando dos métodos:
   - **Linealización** (método tradicional, rápido pero menos preciso)
   - **Ajuste no lineal** (método moderno, más preciso con estadísticas completas)
3. Comparar múltiples modelos cinéticos
4. Guardar y recuperar investigaciones con versionado

**Backend base URL:** `http://127.0.0.1:5000` (desarrollo) | `https://api.adsolab.xyz` (producción)

---

## 🔐 Autenticación

### Obtener Token (para desarrollo/testing)

**Endpoint:** `POST /auth-token`

**Request:**
```json
{
  "email": "adsolab@dev.com",
  "password": "password"
}
```

**Response:**
```json
{
  "token": "WyIxIiwiJDJiJDEyJE5...",
  "user_id": 1,
  "email": "adsolab@dev.com"
}
```

**Uso:** Incluir en headers de requests autenticados:
```
Authorization: Token WyIxIiwiJDJiJDEyJE5...
```

---

## 🔄 Flujo Completo Paso a Paso

### **FASE 1: Preparación de Datos**

#### Paso 1.1: Obtener Materiales Disponibles

**Objetivo:** Poblar dropdowns de adsorbatos y adsorbentes

**Endpoint:** `GET /adsorption-materials`

**Response:**
```json
{
  "adsorbates": [
    {"id": 1, "ion_name": "Arsénico", "formula": "As(III)", "iupac_name": "..."},
    {"id": 2, "ion_name": "Plomo", "formula": "Pb(II)", "iupac_name": "..."}
  ],
  "adsorbents": [
    {"id": 1, "name": "Hidroxiapatita"},
    {"id": 2, "name": "Carbón Activado"}
  ]
}
```

**UI:** Renderizar selectores con estos datos.

---

#### Paso 1.2: Crear Muestra Cinética 🔒

**Objetivo:** Cargar datos experimentales del usuario

**Endpoint:** `POST /kinetics/sample`

**Requiere:** Autenticación (Bearer token)

**Opciones de entrada:**

##### **Opción A: Datos directos (time + qt)**
Usuario ya tiene valores de `qt` (cantidad adsorbida) calculados:

```json
{
  "time": [0, 5, 10, 20, 30, 60],
  "qt": [0.0, 3.2, 5.1, 6.8, 7.4, 7.8],
  "temperature": 298,
  "time_unit": "min",
  "measure_unit": "mg/g",
  "adsorbate_id": 1,
  "adsorbent_id": 1,
  "title": "Ensayo As-HAP temperatura ambiente",
  "description": "Experimento 2024-03-15"
}
```

##### **Opción B: Datos con concentración (time + concentration)**
Usuario tiene concentraciones en solución, backend calcula `qt` automáticamente:

```json
{
  "time": [0, 5, 10, 20, 30],
  "concentration": [50.0, 43.6, 38.4, 33.2, 30.1],
  "initial_concentration": 50.0,
  "volume": 0.25,
  "adsorbent_mass": 0.5,
  "temperature": 298,
  "time_unit": "min",
  "measure_unit": "mg/g",
  "adsorbate_id": 1,
  "adsorbent_id": 1
}
```

**Fórmula de cálculo backend:** `qt = (C0 - Ct) * V / m`

**Response:** Objeto `KineticSample` completo con ID asignado:
```json
{
  "kinetic_sample_id": 1,
  "time": [0, 5, 10, 20, 30, 60],
  "qt": [0.0, 3.2, 5.1, 6.8, 7.4, 7.8],
  "temperature": 298,
  "time_unit": "min",
  "measure_unit": "mg/g",
  "adsorbate_id": 1,
  "adsorbent_id": 1,
  "user_id": 1,
  "title": "admin-298K-cinetica-arsenico-hidroxiapatita-04-06-2026"
}
```

**Validaciones automáticas:**
- ✅ Arrays `time` y `qt` (o `concentration`) deben tener la misma longitud
- ✅ Valores no negativos
- ✅ Al menos 2 puntos de datos
- ✅ Si se usa `concentration`, requiere `initial_concentration`, `volume` y `adsorbent_mass`

**UI Sugerida:**
- Formulario con dos tabs: "Datos Directos" vs "Desde Concentración"
- Tabla editable para ingresar pares (time, qt) o (time, concentration)
- Opción de importar CSV
- Título auto-generado si el usuario deja el campo vacío

---

#### Paso 1.3: Listar Muestras del Usuario

**Endpoint:** `GET /kinetics/samples`

**Response:**
```json
{
  "samples": [
    {
      "kinetic_sample_id": 1,
      "title": "admin-298K-cinetica-arsenico-hidroxiapatita-04-06-2026",
      "temperature": 298,
      "time_unit": "min",
      "measure_unit": "mg/g",
      "user_id": 1
    }
  ]
}
```

**UI:** Lista/tabla de muestras guardadas, clic para seleccionar.

---

### **FASE 2: Selección de Modelos**

#### Paso 2.1: Obtener Modelos Cinéticos Disponibles

**Endpoint:** `GET /kinetics/models`

**Response:**
```json
{
  "models": [
    {
      "_id": 1,
      "name": "Difusión Intraparticular",
      "formula": "qt = kid * time**0.5 + C",
      "latex_formula": "q_t = k_{id} \\cdot \\sqrt{t} + C",
      "description": "Modelo de Weber-Morris para difusión intraparticular...",
      "parameters": {
        "kid": "constante de velocidad de difusión intraparticular (mg/g·min^0.5)",
        "C": "intercepto relacionado con la capa límite externa (mg/g)"
      },
      "linearizations": [
        {
          "linearization_id": 1,
          "name": "Linealización Intraparticular",
          "parameters": {
            "x": "time**0.5",
            "y": "qt",
            "m": "kid",
            "b": "C"
          }
        }
      ]
    }
  ]
}
```

**UI:** 
- Checkboxes o lista seleccionable de modelos
- Mostrar fórmula LaTeX renderizada (usar KaTeX o MathJax)
- Tooltip con descripción de cada parámetro

**Nota:** Actualmente solo está implementado **Difusión Intraparticular**. PFO y PSO están pendientes.

---

### **FASE 3: Análisis (Dos Caminos)**

El usuario puede elegir entre **Linealización** o **Ajuste No Lineal** (o ejecutar ambos para comparar).

---

## 🔵 CAMINO A: LINEALIZACIÓN (Método Tradicional)

### Paso 3A: Ejecutar Linealización

**Endpoint:** `POST /kinetics/run-linearization`

**Request:**
```json
{
  "kinetic_sample_id": 1,
  "models": [
    {
      "model": 1,
      "linearizations": [1]
    }
  ],
  "filter": []
}
```

**Parámetros:**
- `kinetic_sample_id`: ID de la muestra a analizar
- `models`: Array de modelos a ejecutar
- `linearizations`: IDs de linealizaciones (opcional, por defecto usa todas)
- `filter`: Array de índices de puntos a excluir (para outliers)

**Response:**
```json
{
  "kinetic_sample_id": 1,
  "results": [
    {
      "model": 1,
      "best_result": 1,
      "linearizations": [
        {
          "name": "Linealización Intraparticular",
          "id": 1,
          "status": "OK",
          "slope": 0.834,
          "intercept": 0.21,
          "statistics": {
            "r_squared": 0.9912
          },
          "transformed": {
            "x": [0.0, 2.236, 3.162, 4.472, 5.477, 7.746],
            "y": [0.0, 3.2, 5.1, 6.8, 7.4, 7.8]
          },
          "parameters": [
            {
              "name": "kid",
              "value": 0.834,
              "std_err": 0.021
            },
            {
              "name": "C",
              "value": 0.21,
              "std_err": 0.11
            }
          ]
        }
      ]
    }
  ]
}
```

**UI:**
- Graficar `transformed.x` vs `transformed.y` con Plotly/Chart.js
- Mostrar ecuación de la recta: `y = 0.834x + 0.21`
- Mostrar R² de forma prominente
- Tabla de parámetros recuperados con incertidumbre

**Ventajas:**
- ✅ Rápido (< 1 segundo)
- ✅ No requiere seeds
- ✅ Siempre converge

**Desventajas:**
- ❌ Menos preciso que ajuste no lineal
- ❌ Solo funciona con modelos linealizables

---

## 🔴 CAMINO B: AJUSTE NO LINEAL (Método Recomendado)

### Paso 3B.1: Predecir Seeds (Valores Iniciales)

**Endpoint:** `POST /kinetics/predict-seeds`

**Request:**
```json
{
  "kinetic_sample_id": 1,
  "models": [
    {"model": 1}
  ],
  "filter": []
}
```

**Response:**
```json
{
  "kinetic_sample_id": 1,
  "results": [
    {
      "id": 1,
      "name": "Difusión Intraparticular",
      "seeds": [
        {"name": "kid", "value": 1.006},
        {"name": "C", "value": 1.0}
      ]
    }
  ]
}
```

**Estrategia de cálculo:**
- `kid` → `max(qt) / √max(time)`
- `C` → `1.0` (valor por defecto)
- Otros parámetros siguen reglas similares

**UI:**
- Mostrar tabla editable con seeds calculadas
- Usuario avanzado puede modificar valores manualmente
- Botón "Restaurar seeds automáticas"

---

### Paso 3B.2: Ejecutar Ajuste No Lineal

**Endpoint:** `POST /kinetics/run-no-linear-model`

**Request:**
```json
{
  "kinetic_sample_id": 1,
  "models": [
    {
      "model": 1,
      "seeds": [
        {"name": "kid", "value": 1.006},
        {"name": "C", "value": 1.0}
      ],
      "iterations": 10000,
      "step": 0.1
    }
  ],
  "filter": []
}
```

**Parámetros:**
- `seeds`: Valores iniciales (del paso anterior o modificados)
- `iterations`: Máximo de iteraciones (opcional, default: 10000)
- `step`: Tamaño de paso para algoritmo brute (opcional)
- `filter`: Índices de puntos a excluir

**Response (COMPLETA):**
```json
{
  "kinetic_sample_id": 1,
  "results": [
    {
      "model": 1,
      "best_adjust": "leastsq",
      "adjustment_methods": [
        {
          "name": "leastsq",
          "success": true,
          "parameters": [
            {"name": "kid", "value": 0.821, "std_err": 0.018},
            {"name": "C", "value": 0.24, "std_err": 0.09}
          ],
          "statistics": {
            "r_squared": 0.9934,
            "adjust_r_squared": 0.9921,
            "RMSE": 0.089,
            "SSE": 0.047,
            "AIC": -31.2,
            "BIC": -30.4,
            "chi_squared": 0.012
          },
          "residuals": {
            "values": [0.01, -0.05, 0.03, -0.02, 0.04, -0.01],
            "analysis": {
              "passes_normality": true,
              "normality_pvalue": 0.312,
              "passes_homoscedasticity": true,
              "homoscedasticity_pvalue": 0.541,
              "passes_independence": true,
              "durbin_watson": 1.97
            }
          },
          "transformed": {
            "x": [0.0, 0.5, 1.2, 2.5, 3.8, 5.1, 6.4, ..., 60.0],
            "y": [0.0, 0.92, 1.84, 2.94, 3.78, 4.45, 5.01, ..., 7.79]
          }
        },
        {
          "name": "nelder",
          "success": true,
          "parameters": [...],
          "statistics": {...}
        }
      ]
    }
  ],
  "comparison": {
    "heuristic": {
      "best_model": 1,
      "results": [
        {"model": 1, "score": 0.874}
      ]
    },
    "ml": null
  }
}
```

**Métodos de optimización ejecutados:**
- `leastsq` (Levenberg-Marquardt) ⭐ Recomendado
- `nelder` (Nelder-Mead)
- `powell` (Powell)
- `lbfgsb` (L-BFGS-B)
- Y otros...

**UI - Elementos Clave:**

1. **Gráfico Principal:**
   - Puntos experimentales: scatter de `time` vs `qt`
   - Curva ajustada: línea con `transformed.x` vs `transformed.y` (300 puntos suavizados)
   - Leyenda: Datos experimentales + Modelo ajustado

2. **Estadísticas:**
   ```
   R² = 0.9934  ⭐⭐⭐⭐⭐ Excelente
   R² ajustado = 0.9921
   RMSE = 0.089
   AIC = -31.2
   ```

3. **Parámetros:**
   ```
   kid = 0.821 ± 0.018 mg/(g·min^0.5)
   C = 0.24 ± 0.09 mg/g
   ```

4. **Análisis de Residuos:**
   - Gráfico de residuos vs tiempo
   - Indicadores: ✅ Normalidad | ✅ Homocedasticidad | ✅ Independencia

5. **Métodos Probados:**
   - Tabla comparativa de todos los métodos
   - Destacar el mejor método

**Tiempo de ejecución:** ~5-15 segundos (prueba todos los métodos)

---

### **FASE 4: Guardar Investigación** 🔒

#### Paso 4.1: Guardar Resultados

**Endpoint:** `POST /kinetics/investigation/save`

**Requiere:** Autenticación

**Request (Primera vez):**
```json
{
  "kinetic_sample_id": 1,
  "kinetic_investigation_id": null,
  "iterations": 10000,
  "steps": 0.1,
  "results": [
    {
      "model": 1,
      "best_adjust": "leastsq",
      "seeds": [
        {"name": "kid", "value": 1.006},
        {"name": "C", "value": 1.0}
      ],
      "adjustment_methods": [
        {
          "name": "leastsq",
          "params": [
            {"name": "kid", "value": 0.821, "std_err": 0.018},
            {"name": "C", "value": 0.24, "std_err": 0.09}
          ],
          "statistics": {...},
          "residuals": {...}
        }
      ]
    }
  ],
  "comparison": {
    "heuristic": {
      "best_model": 1,
      "results": [{"model": 1, "score": 0.874}]
    }
  }
}
```

**Response:**
```json
{
  "status": "ok",
  "kinetic_investigation_id": 1,
  "version_id": 1
}
```

**Request (Nueva versión de investigación existente):**
```json
{
  "kinetic_sample_id": 1,
  "kinetic_investigation_id": 1,  // ← ID existente
  "iterations": 15000,
  "steps": 0.05,
  "results": [...],  // Nuevos resultados con seeds diferentes
  "comparison": {...}
}
```

**Response:**
```json
{
  "status": "ok",
  "kinetic_investigation_id": 1,
  "version_id": 2  // ← Nueva versión
}
```

**UI:**
- Botón "Guardar Investigación"
- Si es la primera vez: crear nueva
- Si ya existe: preguntar "¿Guardar como nueva versión?"

---

### **FASE 5: Recuperar Investigaciones**

#### Paso 5.1: Listar Investigaciones

**Endpoint:** `GET /kinetics/investigations?page=1&per_page=20&user_id=1`

**Query params:**
- `page`: Número de página (default: 1)
- `per_page`: Resultados por página (default: 20)
- `user_id`: Filtrar por usuario (opcional)

**Response:**
```json
{
  "investigations": [
    {
      "kinetic_investigation_id": 1,
      "kinetic_sample_id": 1,
      "user_id": 1,
      "sample": {
        "kinetic_sample_id": 1,
        "title": "admin-298K-cinetica-arsenico-hidroxiapatita-04-06-2026",
        "temperature": 298
      },
      "user": {
        "id": 1,
        "email": "admin@adsolab.com"
      }
    }
  ],
  "page": 1,
  "per_page": 20,
  "total": 1,
  "pages": 1
}
```

**UI:** Tabla paginada de investigaciones con filtros.

---

#### Paso 5.2: Listar Versiones de una Investigación

**Endpoint:** `GET /kinetics/investigation/{investigation_id}/versions`

**Response:**
```json
{
  "versions": [
    {
      "version_id": 1,
      "kinetic_investigation_id": 1,
      "iterations": 10000,
      "steps": 0.1,
      "created_at": "2026-06-04T15:30:00Z"
    },
    {
      "version_id": 2,
      "kinetic_investigation_id": 1,
      "iterations": 15000,
      "steps": 0.05,
      "created_at": "2026-06-04T16:45:00Z"
    }
  ]
}
```

**UI:** Timeline de versiones con fecha/hora.

---

#### Paso 5.3: Recuperar Versión Específica

**Endpoint:** `GET /kinetics/investigation/{investigation_id}/version/{version_id}`

**Response:** Objeto completo con todos los resultados guardados:
```json
{
  "version_id": 1,
  "kinetic_investigation_id": 1,
  "iterations": 10000,
  "steps": 0.1,
  "created_at": "2026-06-04T15:30:00Z",
  "fitted_models": [
    {
      "kinetic_fitted_model_id": 1,
      "kinetic_model_id": 1,
      "best_adjust": "leastsq",
      "seeds": [
        {"name": "kid", "value": 1.006},
        {"name": "C", "value": 1.0}
      ],
      "adjustment_methods": [
        {
          "name": "leastsq",
          "success": true,
          "parameters": [...],
          "statistics": {...},
          "residuals": {...},
          "transformed": {...}
        }
      ]
    }
  ],
  "comparison": {
    "heuristic": {
      "best_model": 1,
      "results": [{"model": 1, "score": 0.874}]
    }
  }
}
```

**UI:** Reconstruir visualización completa del análisis con este JSON.

---

### **FASE 6: Gestión de Datos**

#### Eliminar Muestra 🔒

**Endpoint:** `DELETE /kinetics/sample/{kinetic_sample_id}`

**Requiere:** Autenticación y ser propietario

**Response:**
```json
{"kinetic_sample_id": 1}
```

**Nota:** Soft-delete (no se elimina físicamente)

---

#### Eliminar Investigación 🔒

**Endpoint:** `DELETE /kinetics/investigation/{kinetic_investigation_id}`

**Requiere:** Autenticación y ser propietario

**Response:**
```json
{"kinetic_investigation_id": 1}
```

**Nota:** Elimina en cascada todas las versiones.

---

#### Eliminar Versión Específica 🔒

**Endpoint:** `DELETE /kinetics/investigation/{investigation_id}/version/{version_id}`

**Response:**
```json
{"status": "ok"}
```

---

## 📊 Modelos de Datos

### KineticSample
```typescript
interface KineticSample {
  kinetic_sample_id: number;
  time: number[];
  qt: number[];
  concentration?: number[];
  initial_concentration?: number;
  volume?: number;
  adsorbent_mass?: number;
  title?: string;
  description?: string;
  temperature: number;
  time_unit: string;
  measure_unit: string;
  adsorbate_id: number;
  adsorbent_id: number;
  user_id: number;
}
```

### KineticModel
```typescript
interface KineticModel {
  _id: number;
  name: string;
  formula: string;
  latex_formula: string;
  description: string;
  parameters: Record<string, string>;
  linearizations: KineticLinearization[];
}
```

### FittedParameter
```typescript
interface FittedParameter {
  name: string;
  value: number;
  std_err?: number;
}
```

### Statistics
```typescript
interface Statistics {
  r_squared: number;
  adjust_r_squared: number;
  RMSE: number;
  SSE: number;
  AIC: number;
  BIC: number;
  chi_squared: number;
}
```

### ResidualsAnalysis
```typescript
interface ResidualsAnalysis {
  passes_normality: boolean;
  normality_pvalue: number;
  passes_homoscedasticity: boolean;
  homoscedasticity_pvalue: number;
  passes_independence: boolean;
  durbin_watson: number;
}
```

---

## 🎬 Casos de Uso

### Caso 1: Usuario Básico - Análisis Simple

1. Usuario carga datos experimentales (Paso 1.2)
2. Selecciona modelo "Difusión Intraparticular" (Paso 2.1)
3. Ejecuta linealización (Paso 3A)
4. Ve gráfico y R² = 0.99
5. Guarda investigación (Paso 4.1)

**Tiempo total:** ~2 minutos

---

### Caso 2: Usuario Avanzado - Análisis Completo

1. Usuario carga datos (Paso 1.2)
2. Identifica 2 outliers en el gráfico
3. Solicita seeds (Paso 3B.1)
4. Modifica seed de `kid` a 0.8 (basado en experiencia)
5. Ejecuta ajuste no lineal con `filter: [2, 5]` (Paso 3B.2)
6. Compara 3 métodos de optimización
7. Analiza residuos (pasan todos los tests)
8. Exporta gráfico como PNG
9. Guarda versión 1 (Paso 4.1)
10. Prueba con diferentes seeds → Guarda versión 2

**Tiempo total:** ~10 minutos

---

### Caso 3: Investigador - Comparación de Modelos

1. Usuario tiene 1 muestra experimental
2. Ejecuta ajuste no lineal con:
   - Difusión Intraparticular
   - PFO (cuando se implemente)
   - PSO (cuando se implemente)
3. Backend devuelve `comparison.heuristic.best_model`
4. Usuario compara R², AIC, BIC entre modelos
5. Selecciona el mejor modelo según criterios estadísticos

**Tiempo total:** ~5 minutos

---

## ⚠️ Validaciones y Errores

### Errores Comunes

#### Error 400 - Bad Request
```json
{
  "message": "Validation error",
  "errors": {
    "time": "Time and qt arrays must have the same length",
    "qt": "All values must be non-negative"
  }
}
```

**Causas:**
- Arrays de diferente longitud
- Valores negativos
- Menos de 2 puntos de datos
- Falta `initial_concentration` cuando se usa `concentration`

#### Error 401 - Unauthorized
```json
{
  "message": "Unauthorized"
}
```

**Causa:** Token faltante o inválido en endpoints 🔒

#### Error 403 - Forbidden
```json
{
  "message": "You are not authorized to delete this sample"
}
```

**Causa:** Intentar eliminar muestra/investigación de otro usuario

#### Error 404 - Not Found
```json
{
  "message": "Sample not found"
}
```

**Causa:** ID inexistente o muestra eliminada (soft-delete)

---

## 📝 Ejemplos de Payloads Completos

### Ejemplo: Flujo Completo con Datos Reales

```javascript
// 1. Crear muestra
const createSampleResponse = await fetch('/kinetics/sample', {
  method: 'POST',
  headers: {
    'Authorization': 'Token ...',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    time: [0, 5, 10, 20, 30, 45, 60, 90, 120],
    qt: [0.0, 2.8, 4.5, 6.2, 7.1, 7.6, 7.9, 8.1, 8.2],
    temperature: 298,
    time_unit: "min",
    measure_unit: "mg/g",
    adsorbate_id: 1,
    adsorbent_id: 1,
    title: "Arsénico-HAP 25°C"
  })
});
const sample = await createSampleResponse.json();
// sample.kinetic_sample_id = 42

// 2. Predecir seeds
const seedsResponse = await fetch('/kinetics/predict-seeds', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    kinetic_sample_id: 42,
    models: [{model: 1}],
    filter: []
  })
});
const seedsData = await seedsResponse.json();
// seedsData.results[0].seeds = [{name: "kid", value: 0.95}, {name: "C", value: 1.0}]

// 3. Ajuste no lineal
const fitResponse = await fetch('/kinetics/run-no-linear-model', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    kinetic_sample_id: 42,
    models: [{
      model: 1,
      seeds: seedsData.results[0].seeds,
      iterations: 10000
    }],
    filter: []
  })
});
const fitResults = await fitResponse.json();
// fitResults.results[0].best_adjust = "leastsq"
// fitResults.results[0].adjustment_methods[0].statistics.r_squared = 0.9954

// 4. Guardar
const saveResponse = await fetch('/kinetics/investigation/save', {
  method: 'POST',
  headers: {
    'Authorization': 'Token ...',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    kinetic_sample_id: 42,
    kinetic_investigation_id: null,
    iterations: 10000,
    steps: 0.1,
    results: fitResults.results,
    comparison: fitResults.comparison
  })
});
const saved = await saveResponse.json();
// saved.kinetic_investigation_id = 15
// saved.version_id = 1
```

---

## 🎨 Recomendaciones de UI/UX

### Gráficos (Plotly.js recomendado)

```javascript
// Gráfico principal: datos experimentales + curva ajustada
const trace1 = {
  x: sample.time,
  y: sample.qt,
  mode: 'markers',
  name: 'Datos experimentales',
  marker: {size: 10, color: 'blue'}
};

const trace2 = {
  x: fitResults.results[0].adjustment_methods[0].transformed.x,
  y: fitResults.results[0].adjustment_methods[0].transformed.y,
  mode: 'lines',
  name: 'Modelo ajustado (Difusión Intraparticular)',
  line: {color: 'red', width: 2}
};

Plotly.newPlot('graph', [trace1, trace2], {
  title: 'Cinética de Adsorción',
  xaxis: {title: 'Tiempo (min)'},
  yaxis: {title: 'qt (mg/g)'}
});
```

### Indicadores de Calidad del Ajuste

```javascript
function getQualityRating(r_squared) {
  if (r_squared >= 0.99) return {rating: '⭐⭐⭐⭐⭐', text: 'Excelente', color: 'green'};
  if (r_squared >= 0.95) return {rating: '⭐⭐⭐⭐', text: 'Muy bueno', color: 'lightgreen'};
  if (r_squared >= 0.90) return {rating: '⭐⭐⭐', text: 'Bueno', color: 'yellow'};
  if (r_squared >= 0.80) return {rating: '⭐⭐', text: 'Regular', color: 'orange'};
  return {rating: '⭐', text: 'Pobre', color: 'red'};
}
```

### Manejo de Outliers

```html
<div class="outlier-manager">
  <h3>Puntos Experimentales</h3>
  <table>
    <tr>
      <th>Índice</th>
      <th>Tiempo</th>
      <th>qt</th>
      <th>Excluir</th>
    </tr>
    {#each sample.time as t, i}
      <tr>
        <td>{i}</td>
        <td>{t}</td>
        <td>{sample.qt[i]}</td>
        <td><input type="checkbox" bind:checked={filter[i]} /></td>
      </tr>
    {/each}
  </table>
</div>
```

---

## 🔄 Comparación con Módulo de Equilibrio

| Aspecto | Módulo Equilibrio (isotermas) | Módulo Cinético |
|---------|-------------------------------|-----------------|
| Variables | `ce` (concentración) / `qe` (equilibrio) | `time` (tiempo) / `qt` (adsorción) |
| Endpoints base | `/sample`, `/models`, `/investigation` | `/kinetics/sample`, `/kinetics/models`, `/kinetics/investigation` |
| Seeds | Requeridas para ajuste no lineal | Requeridas para ajuste no lineal |
| Linealización | Sí (tradicional) | Sí (tradicional) |
| Modelos disponibles | ~8 modelos (Langmuir, Freundlich, etc.) | 1 implementado (Difusión), 2 pendientes (PFO, PSO) |
| Comparación ML | Ridge regression | Pendiente implementar |

---

## 📚 Recursos Adicionales

### OpenAPI Specification

Ver archivo completo: `openapi-spec.yml`

Visualizar en: https://editor.swagger.io/

### Documentación Backend

- **README.md**: Instalación y configuración
- **KINETICS_MODULE.md**: Arquitectura del módulo cinético
- Código fuente:
  - `app/controller/kinetics_controller.py`: Todos los endpoints
  - `app/services/kinetics_no_linear_model_service.py`: Lógica de ajuste
  - `app/services/kinetics_linearization_service.py`: Lógica de linealización

### Testing Local

Base URL: `http://127.0.0.1:5000`

Credenciales dev:
- Email: `adsolab@dev.com`
- Password: `password`

---

## 🚀 Roadmap de Implementación Frontend

### Fase 1: MVP (Mínimo Viable)
- [ ] Formulario crear muestra (opción A: time/qt directo)
- [ ] Lista de modelos
- [ ] Ejecutar ajuste no lineal con seeds auto
- [ ] Gráfico básico con Plotly
- [ ] Mostrar R² y parámetros

### Fase 2: Completo
- [ ] Opción B: calcular qt desde concentración
- [ ] Editor de seeds
- [ ] Gráfico de residuos
- [ ] Tabla comparativa de métodos
- [ ] Guardar investigación
- [ ] Listar investigaciones guardadas

### Fase 3: Avanzado
- [ ] Manejo de outliers (filtro)
- [ ] Ejecutar linealización
- [ ] Comparación visual de múltiples modelos
- [ ] Exportar gráficos (PNG/SVG)
- [ ] Exportar resultados (Excel/CSV)
- [ ] Versionado de investigaciones (timeline)

---

## 📞 Contacto y Soporte

Para dudas sobre la implementación:

1. Revisar `openapi-spec.yml` para payloads exactos
2. Consultar código fuente en `app/controller/kinetics_controller.py`
3. Probar endpoints con Postman/Insomnia usando ejemplos de este documento

**Última actualización:** 2026-06-04
