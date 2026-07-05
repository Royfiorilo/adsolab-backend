# 🧪 Guía de Testing - Módulo Cinético

> **Propósito:** Probar todos los endpoints del módulo cinético con datos experimentales reales  
> **Última actualización:** 2026-06-24

---

## 📋 Tabla de Contenidos

1. [Preparación](#preparación)
2. [Flujo Completo con PowerShell](#flujo-completo-con-powershell)
3. [Flujo Completo con Postman](#flujo-completo-con-postman)
4. [Script Python Automatizado](#script-python-automatizado)
5. [Convertir Datos de Excel a JSON](#convertir-datos-de-excel-a-json)
6. [Debugging](#debugging)
7. [Checklist de Testing](#checklist-de-testing)

---

## 🚀 Preparación

### Requisitos Previos

- Backend corriendo en `http://127.0.0.1:5000`
- PostgreSQL corriendo (vía `docker-compose up -d`)
- Datos experimentales del Excel extraídos

### Formato de Datos Esperado

De tu archivo Excel, necesitas extraer:

**Opción A: Datos directos**
- Columna A: Tiempo (min) → `[0, 5, 10, 20, 30, 60]`
- Columna B: qt (mg/g) → `[0.0, 3.2, 5.1, 6.8, 7.4, 7.8]`

**Opción B: Desde concentraciones**
- Columna A: Tiempo (min)
- Columna B: Concentración en solución (mg/L)
- Datos adicionales: C₀, volumen (L), masa adsorbente (g)

---

## 💻 Flujo Completo con PowerShell

### Paso 0: Iniciar Backend

```powershell
# Terminal 1 - Base de datos
docker-compose up -d

# Terminal 2 - Backend
.venv\Scripts\python.exe app/start.py
```

Verificar que esté corriendo:
```powershell
curl http://127.0.0.1:5000/health-check
```

**Respuesta esperada:**
```json
{"status": "ok"}
```

---

### Paso 1: Obtener Token de Autenticación

```powershell
$response = Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:5000/auth-token" `
  -ContentType "application/json" `
  -Body '{"email":"adsolab@dev.com","password":"password"}'

$token = $response.token
Write-Host "✅ Token obtenido: $($token.Substring(0,20))..."
```

---

### Paso 2: Obtener Materiales Disponibles

```powershell
$materials = Invoke-RestMethod -Uri "http://127.0.0.1:5000/adsorption-materials"

Write-Host "`n📦 Adsorbatos disponibles:"
$materials.adsorbates | Format-Table id, ion_name, formula

Write-Host "📦 Adsorbentes disponibles:"
$materials.adsorbents | Format-Table id, name
```

**Anota los IDs** que usarás para tu experimento (ej: `adsorbate_id: 1`, `adsorbent_id: 1`)

---

### Paso 3: Crear Muestra Cinética con Datos Reales

#### 3A. Con datos directos (time + qt)

```powershell
$body = @{
  time = @(0, 5, 10, 20, 30, 60)
  qt = @(0.0, 3.2, 5.1, 6.8, 7.4, 7.8)
  temperature = 298
  time_unit = "min"
  measure_unit = "mg/g"
  adsorbate_id = 1
  adsorbent_id = 1
  title = "Experimento Real - Excel 2026-06-24"
  description = "Datos de laboratorio"
} | ConvertTo-Json

$sample = Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:5000/kinetics/sample" `
  -Headers @{"Authorization"="Bearer $token"; "Content-Type"="application/json"} `
  -Body $body

$sampleId = $sample.kinetic_sample_id
Write-Host "✅ Muestra creada con ID: $sampleId"
Write-Host "   Título: $($sample.title)"
```

#### 3B. Con concentraciones (backend calcula qt)

```powershell
$body = @{
  time = @(0, 5, 10, 20, 30)
  concentration = @(50.0, 43.6, 38.4, 33.2, 30.1)
  initial_concentration = 50.0
  volume = 0.25
  adsorbent_mass = 0.5
  temperature = 298
  time_unit = "min"
  measure_unit = "mg/g"
  adsorbate_id = 1
  adsorbent_id = 1
  title = "Experimento desde Concentración"
} | ConvertTo-Json

$sample = Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:5000/kinetics/sample" `
  -Headers @{"Authorization"="Bearer $token"; "Content-Type"="application/json"} `
  -Body $body

$sampleId = $sample.kinetic_sample_id
Write-Host "✅ Muestra creada. qt calculado: $($sample.qt)"
```

---

### Paso 4: Listar Muestras Guardadas

```powershell
$samples = Invoke-RestMethod -Uri "http://127.0.0.1:5000/kinetics/samples"

Write-Host "`n📋 Muestras guardadas:"
$samples.samples | Format-Table kinetic_sample_id, title, temperature, time_unit
```

---

### Paso 5: Obtener Modelos Cinéticos Disponibles

```powershell
$models = Invoke-RestMethod -Uri "http://127.0.0.1:5000/kinetics/models"

Write-Host "`n🔬 Modelos disponibles:"
foreach ($model in $models.models) {
  Write-Host "  [$($model._id)] $($model.name)"
  Write-Host "      Fórmula: $($model.formula)"
  Write-Host "      Parámetros: $($model.parameters.Keys -join ', ')"
}
```

---

### Paso 6: Predecir Seeds (Valores Iniciales)

#### 6A. Seeds para UN modelo específico

```powershell
# Ejemplo: Solo modelo 1 (Weber-Morris)
$body = @{
  kinetic_sample_id = $sampleId
  models = @(@{model = 1})
  filter = @()
} | ConvertTo-Json -Depth 3

$seedsResponse = Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:5000/kinetics/predict-seeds" `
  -ContentType "application/json" `
  -Body $body

$seeds = $seedsResponse.results[0].seeds
Write-Host "`n🌱 Seeds calculadas para modelo 1 (Weber-Morris):"
$seeds | Format-Table name, value
```

#### 6B. Seeds para TODOS los modelos (recomendado)

```powershell
# Pedir seeds para los 3 modelos disponibles
$body = @{
  kinetic_sample_id = $sampleId
  models = @(
    @{model = 1},  # Difusión Intraparticular
    @{model = 2},  # Pseudo-Segundo Orden (PSO)
    @{model = 3}   # Pseudo-Primer Orden (PFO)
  )
  filter = @()
} | ConvertTo-Json -Depth 3

$seedsResponse = Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:5000/kinetics/predict-seeds" `
  -ContentType "application/json" `
  -Body $body

Write-Host "`n🌱 Seeds calculadas para todos los modelos:"
foreach ($result in $seedsResponse.results) {
  Write-Host "`n  Modelo ID $($result.kinetic_model_id) - $($result.model_name):"
  $result.seeds | Format-Table name, value -AutoSize
}

# Guardar seeds para usar después
$seedsModel1 = $seedsResponse.results[0].seeds
$seedsModel2 = $seedsResponse.results[1].seeds
$seedsModel3 = $seedsResponse.results[2].seeds
```

---

### Paso 7A: Ejecutar Linealización (Método Tradicional)

```powershell
$body = @{
  kinetic_sample_id = $sampleId
  models = @(@{
    model = 1
    linearizations = @(1)
  })
  filter = @()
} | ConvertTo-Json -Depth 3

Write-Host "`n⏳ Ejecutando linealización..."
$linResponse = Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:5000/kinetics/run-linearization" `
  -ContentType "application/json" `
  -Body $body

$linResult = $linResponse.results[0].linearizations[0]
Write-Host "✅ Linealización completada"
Write-Host "   R² = $($linResult.statistics.r_squared)"
Write-Host "   Pendiente = $($linResult.slope)"
Write-Host "   Intercepto = $($linResult.intercept)"
Write-Host "`n   Parámetros recuperados:"
$linResult.parameters | Format-Table name, value, std_err
```

---

### Paso 7B: Ejecutar Ajuste No Lineal (Método Completo)

#### 7B.1. Ajustar UN modelo

```powershell
# Ejemplo: Solo modelo 1
$body = @{
  kinetic_sample_id = $sampleId
  models = @(@{
    model = 1
    seeds = $seedsModel1
    iterations = 10000
    step = 0.1
  })
  filter = @()
} | ConvertTo-Json -Depth 4

Write-Host "`n⏳ Ejecutando ajuste no lineal (10-15 segundos)..."
$fitResponse = Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:5000/kinetics/run-no-linear-model" `
  -ContentType "application/json" `
  -Body $body

# Extraer mejor método
$result = $fitResponse.results[0]
$bestMethodName = $result.best_adjust
$bestMethod = $result.adjustment_methods | Where-Object {$_.name -eq $bestMethodName}

Write-Host "`n✅ Ajuste completado!"
Write-Host "   Mejor método: $bestMethodName"
Write-Host "   R² = $($bestMethod.statistics.r_squared)"
```

#### 7B.2. Ajustar TODOS los modelos simultáneamente (recomendado)

```powershell
# Ajustar los 3 modelos en una sola llamada para comparar
$body = @{
  kinetic_sample_id = $sampleId
  models = @(
    @{
      model = 1  # Difusión Intraparticular
      seeds = $seedsModel1
      iterations = 10000
      step = 0.1
    },
    @{
      model = 2  # Pseudo-Segundo Orden
      seeds = $seedsModel2
      iterations = 10000
      step = 0.1
    },
    @{
      model = 3  # Pseudo-Primer Orden
      seeds = $seedsModel3
      iterations = 10000
      step = 0.1
    }
  )
  filter = @()
} | ConvertTo-Json -Depth 4

Write-Host "`n⏳ Ejecutando ajuste no lineal para 3 modelos (30-45 segundos)..."
$fitResponse = Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:5000/kinetics/run-no-linear-model" `
  -ContentType "application/json" `
  -Body $body

# Mostrar comparación entre todos los modelos
Write-Host "`n✅ Ajuste completado para 3 modelos!"
Write-Host "`n📊 COMPARACIÓN DE MODELOS:"
Write-Host ("="*70)

foreach ($result in $fitResponse.results) {
  $bestMethodName = $result.best_adjust
  $bestMethod = $result.adjustment_methods | Where-Object {$_.name -eq $bestMethodName}
  
  Write-Host "`n🔬 Modelo $($result.kinetic_model_id): $($result.model_name)"
  Write-Host "   Mejor método: $bestMethodName"
  Write-Host "   R² = $($bestMethod.statistics.r_squared)"
  Write-Host "   R² ajustado = $($bestMethod.statistics.adjust_r_squared)"
  Write-Host "   RMSE = $($bestMethod.statistics.RMSE)"
  Write-Host "   AIC = $($bestMethod.statistics.AIC)"
  Write-Host "   BIC = $($bestMethod.statistics.BIC)"
  
  Write-Host "   Parámetros:"
  $bestMethod.parameters | ForEach-Object {
    Write-Host "     $($_.name) = $($_.value) ± $($_.std_err)"
  }
}

# Mostrar ranking de modelos
Write-Host "`n🏆 RANKING POR R²:"
$fitResponse.results | ForEach-Object {
  $best = $_.adjustment_methods | Where-Object {$_.name -eq $_.best_adjust}
  [PSCustomObject]@{
    Modelo = "$($_.kinetic_model_id): $($_.model_name)"
    "R²" = [math]::Round($best.statistics.r_squared, 4)
    RMSE = [math]::Round($best.statistics.RMSE, 4)
    AIC = [math]::Round($best.statistics.AIC, 2)
  }
} | Sort-Object "R²" -Descending | Format-Table -AutoSize

# Análisis detallado del mejor modelo general
$bestOverall = $fitResponse.results | Sort-Object {
  ($_.adjustment_methods | Where-Object {$_.name -eq $_.best_adjust}).statistics.r_squared
} -Descending | Select-Object -First 1

$bestMethodOverall = $bestOverall.adjustment_methods | Where-Object {$_.name -eq $bestOverall.best_adjust}

Write-Host "`n🎯 MEJOR MODELO GENERAL: $($bestOverall.model_name)"
Write-Host "`n📊 Estadísticas completas:"
Write-Host "   R² = $($bestMethodOverall.statistics.r_squared)"
Write-Host "   R² ajustado = $($bestMethodOverall.statistics.adjust_r_squared)"
Write-Host "   RMSE = $($bestMethodOverall.statistics.RMSE)"
Write-Host "   AIC = $($bestMethodOverall.statistics.AIC)"
Write-Host "   BIC = $($bestMethodOverall.statistics.BIC)"

Write-Host "`n🔢 Parámetros ajustados:"
$bestMethodOverall.parameters | Format-Table name, value, std_err -AutoSize

Write-Host "`n🔍 Análisis de residuos:"
$residuals = $bestMethodOverall.residuals.analysis
Write-Host "   Normalidad: $(if($residuals.passes_normality){'✅ PASA'}else{'❌ FALLA'}) (p=$($residuals.normality_pvalue))"
Write-Host "   Homocedasticidad: $(if($residuals.passes_homoscedasticity){'✅ PASA'}else{'❌ FALLA'}) (p=$($residuals.homoscedasticity_pvalue))"
Write-Host "   Independencia: $(if($residuals.passes_independence){'✅ PASA'}else{'❌ FALLA'}) (DW=$($residuals.durbin_watson))"
```

---

### Paso 8: Guardar Investigación

```powershell
$body = @{
  kinetic_sample_id = $sampleId
  kinetic_investigation_id = $null  # null = nueva investigación
  iterations = 10000
  steps = 0.1
  results = $fitResponse.results
  comparison = $fitResponse.comparison
} | ConvertTo-Json -Depth 10

$saveResponse = Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:5000/kinetics/investigation/save" `
  -Headers @{"Authorization"="Bearer $token"; "Content-Type"="application/json"} `
  -Body $body

Write-Host "`n💾 Investigación guardada exitosamente!"
Write-Host "   Investigation ID: $($saveResponse.kinetic_investigation_id)"
Write-Host "   Version ID: $($saveResponse.version_id)"

$investigationId = $saveResponse.kinetic_investigation_id
$versionId = $saveResponse.version_id
```

---

### Paso 9: Listar Investigaciones

```powershell
$investigations = Invoke-RestMethod -Uri "http://127.0.0.1:5000/kinetics/investigations?page=1&per_page=20"

Write-Host "`n📚 Investigaciones guardadas:"
$investigations.investigations | Format-Table kinetic_investigation_id, kinetic_sample_id, @{Name="Muestra"; Expression={$_.sample.title}}
Write-Host "   Total: $($investigations.total) | Páginas: $($investigations.pages)"
```

---

### Paso 10: Listar Versiones de una Investigación

```powershell
$versions = Invoke-RestMethod -Uri "http://127.0.0.1:5000/kinetics/investigation/$investigationId/versions"

Write-Host "`n📂 Versiones de la investigación $investigationId :"
$versions.versions | Format-Table version_id, iterations, steps, created_at
```

---

### Paso 11: Recuperar Versión Específica

```powershell
$version = Invoke-RestMethod -Uri "http://127.0.0.1:5000/kinetics/investigation/$investigationId/version/$versionId"

Write-Host "`n📄 Versión recuperada:"
Write-Host "   Creada: $($version.created_at)"
Write-Host "   Iteraciones: $($version.iterations)"
Write-Host "   Modelos ajustados: $($version.fitted_models.Count)"

foreach ($fm in $version.fitted_models) {
  Write-Host "`n   Modelo ID $($fm.kinetic_model_id):"
  Write-Host "     Mejor método: $($fm.best_adjust)"
  Write-Host "     Parámetros:"
  $fm.adjustment_methods[0].parameters | Format-Table name, value, std_err
}
```

---

### Paso 12: Eliminar Muestra (Opcional)

```powershell
# ⚠️ Soft-delete, no elimina físicamente
$deleteResponse = Invoke-RestMethod -Method DELETE `
  -Uri "http://127.0.0.1:5000/kinetics/sample/$sampleId" `
  -Headers @{"Authorization"="Bearer $token"}

Write-Host "🗑️ Muestra $($deleteResponse.kinetic_sample_id) eliminada"
```

---

## 📮 Flujo Completo con Postman

### Configuración Inicial

1. **Crear Colección:**
   - New Collection → `AdsoLab Kinetics Testing`

2. **Variables de Colección:**
   - `base_url`: `http://127.0.0.1:5000`
   - `token`: (se llenará después)
   - `sample_id`: (se llenará después)
   - `investigation_id`: (se llenará después)

3. **Configurar Autorización:**
   - Collection → Authorization → Type: `Bearer Token`
   - Token: `{{token}}`

---

### Requests

#### 1. Obtener Token

```
POST {{base_url}}/auth-token
Body (raw, JSON):
{
  "email": "adsolab@dev.com",
  "password": "password"
}

Tests (Script para guardar token):
pm.test("Status 200", function() {
    pm.response.to.have.status(200);
});
pm.collectionVariables.set("token", pm.response.json().token);
```

---

#### 2. Health Check

```
GET {{base_url}}/health-check

Tests:
pm.test("Backend running", function() {
    pm.response.to.have.status(200);
    pm.expect(pm.response.json().status).to.eql("ok");
});
```

---

#### 3. Obtener Materiales

```
GET {{base_url}}/adsorption-materials

Tests:
pm.test("Materials loaded", function() {
    const data = pm.response.json();
    pm.expect(data.adsorbates.length).to.be.above(0);
    pm.expect(data.adsorbents.length).to.be.above(0);
});
```

---

#### 4. Crear Muestra

```
POST {{base_url}}/kinetics/sample
Headers: Authorization: Bearer {{token}}
Body (raw, JSON):
{
  "time": [0, 5, 10, 20, 30, 60],
  "qt": [0.0, 3.2, 5.1, 6.8, 7.4, 7.8],
  "temperature": 298,
  "time_unit": "min",
  "measure_unit": "mg/g",
  "adsorbate_id": 1,
  "adsorbent_id": 1,
  "title": "Test Postman - Excel Data"
}

Tests:
pm.test("Sample created", function() {
    pm.response.to.have.status(201);
    const data = pm.response.json();
    pm.collectionVariables.set("sample_id", data.kinetic_sample_id);
    console.log("Sample ID: " + data.kinetic_sample_id);
});
```

---

#### 5. Listar Modelos

```
GET {{base_url}}/kinetics/models

Tests:
pm.test("Models available", function() {
    const data = pm.response.json();
    pm.expect(data.models.length).to.be.above(0);
});
```

---

#### 6. Predecir Seeds

```
POST {{base_url}}/kinetics/predict-seeds
Body (raw, JSON):
{
  "kinetic_sample_id": {{sample_id}},
  "models": [{"model": 1}],
  "filter": []
}

Tests:
pm.test("Seeds calculated", function() {
    const data = pm.response.json();
    pm.expect(data.results[0].seeds.length).to.be.above(0);
    // Guardar seeds para siguiente request
    pm.collectionVariables.set("seeds", JSON.stringify(data.results[0].seeds));
});
```

---

#### 7. Linealización

```
POST {{base_url}}/kinetics/run-linearization
Body (raw, JSON):
{
  "kinetic_sample_id": {{sample_id}},
  "models": [
    {
      "model": 1,
      "linearizations": [1]
    }
  ],
  "filter": []
}

Tests:
pm.test("Linearization successful", function() {
    const data = pm.response.json();
    const result = data.results[0].linearizations[0];
    pm.expect(result.status).to.eql("OK");
    pm.expect(result.statistics.r_squared).to.be.above(0.9);
    console.log("R² = " + result.statistics.r_squared);
});
```

---

#### 8. Ajuste No Lineal

```
POST {{base_url}}/kinetics/run-no-linear-model
Body (raw, JSON):
{
  "kinetic_sample_id": {{sample_id}},
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

Tests:
pm.test("Non-linear fit successful", function() {
    const data = pm.response.json();
    const result = data.results[0];
    pm.expect(result.best_adjust).to.exist;
    
    const bestMethod = result.adjustment_methods.find(m => m.name === result.best_adjust);
    pm.expect(bestMethod.success).to.be.true;
    pm.expect(bestMethod.statistics.r_squared).to.be.above(0.9);
    
    console.log("Best method: " + result.best_adjust);
    console.log("R² = " + bestMethod.statistics.r_squared);
    
    // Guardar para siguiente request
    pm.collectionVariables.set("fit_results", JSON.stringify(data));
});
```

---

#### 9. Guardar Investigación

```
POST {{base_url}}/kinetics/investigation/save
Headers: Authorization: Bearer {{token}}
Body (raw, JSON):
{
  "kinetic_sample_id": {{sample_id}},
  "kinetic_investigation_id": null,
  "iterations": 10000,
  "steps": 0.1,
  "results": {{fit_results.results}},
  "comparison": {{fit_results.comparison}}
}

Tests:
pm.test("Investigation saved", function() {
    pm.response.to.have.status(201);
    const data = pm.response.json();
    pm.collectionVariables.set("investigation_id", data.kinetic_investigation_id);
    pm.collectionVariables.set("version_id", data.version_id);
    console.log("Investigation ID: " + data.kinetic_investigation_id);
    console.log("Version ID: " + data.version_id);
});
```

---

#### 10. Listar Investigaciones

```
GET {{base_url}}/kinetics/investigations?page=1&per_page=20

Tests:
pm.test("Investigations retrieved", function() {
    const data = pm.response.json();
    pm.expect(data.investigations).to.be.an('array');
    pm.expect(data.total).to.be.above(0);
});
```

---

#### 11. Recuperar Versión

```
GET {{base_url}}/kinetics/investigation/{{investigation_id}}/version/{{version_id}}

Tests:
pm.test("Version retrieved", function() {
    pm.response.to.have.status(200);
    const data = pm.response.json();
    pm.expect(data.version_id).to.eql(parseInt(pm.collectionVariables.get("version_id")));
    pm.expect(data.fitted_models).to.be.an('array');
});
```

---

## 🐍 Script Python Automatizado

Guarda este script como `test_kinetics.py`:

```python
import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

# ========================================
# TUS DATOS DEL EXCEL AQUÍ
# ========================================
TIME = [0, 5, 10, 20, 30, 60]
QT = [0.0, 3.2, 5.1, 6.8, 7.4, 7.8]
TEMPERATURE = 298
TIME_UNIT = "min"
MEASURE_UNIT = "mg/g"
ADSORBATE_ID = 1
ADSORBENT_ID = 1

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def main():
    print_section("🧪 TESTING MÓDULO CINÉTICO")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ========================================
    # 1. AUTENTICACIÓN
    # ========================================
    print_section("1. Autenticación")
    response = requests.post(f"{BASE_URL}/auth-token", json={
        "email": "adsolab@dev.com",
        "password": "password"
    })
    response.raise_for_status()
    token = response.json()["token"]
    headers = {"Authorization": f"Token {token}"}
    print(f"✅ Token obtenido: {token[:30]}...")
    
    # ========================================
    # 2. MATERIALES
    # ========================================
    print_section("2. Obtener Materiales")
    materials = requests.get(f"{BASE_URL}/adsorption-materials").json()
    print(f"✅ Adsorbatos: {len(materials['adsorbates'])}")
    for ads in materials['adsorbates'][:3]:
        print(f"   [{ads['id']}] {ads['ion_name']} ({ads['formula']})")
    print(f"✅ Adsorbentes: {len(materials['adsorbents'])}")
    for ads in materials['adsorbents'][:3]:
        print(f"   [{ads['id']}] {ads['name']}")
    
    # ========================================
    # 3. CREAR MUESTRA
    # ========================================
    print_section("3. Crear Muestra Cinética")
    sample_response = requests.post(f"{BASE_URL}/kinetics/sample", 
        headers=headers,
        json={
            "time": TIME,
            "qt": QT,
            "temperature": TEMPERATURE,
            "time_unit": TIME_UNIT,
            "measure_unit": MEASURE_UNIT,
            "adsorbate_id": ADSORBATE_ID,
            "adsorbent_id": ADSORBENT_ID,
            "title": f"Test Python - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        }
    )
    sample_response.raise_for_status()
    sample_id = sample_response.json()["kinetic_sample_id"]
    sample_title = sample_response.json()["title"]
    print(f"✅ Muestra creada")
    print(f"   ID: {sample_id}")
    print(f"   Título: {sample_title}")
    print(f"   Puntos: {len(TIME)}")
    
    # ========================================
    # 4. MODELOS
    # ========================================
    print_section("4. Obtener Modelos")
    models = requests.get(f"{BASE_URL}/kinetics/models").json()
    print(f"✅ Modelos disponibles: {len(models['models'])}")
    for model in models['models']:
        print(f"   [{model['_id']}] {model['name']}")
        print(f"       Fórmula: {model['formula']}")
        print(f"       Parámetros: {', '.join(model['parameters'].keys())}")
    
    # ========================================
    # 5. PREDECIR SEEDS
    # ========================================
    print_section("5. Predecir Seeds")
    seeds_response = requests.post(f"{BASE_URL}/kinetics/predict-seeds",
        json={
            "kinetic_sample_id": sample_id,
            "models": [{"model": 1}],
            "filter": []
        }
    )
    seeds_response.raise_for_status()
    seeds = seeds_response.json()["results"][0]["seeds"]
    print(f"✅ Seeds calculadas:")
    for seed in seeds:
        print(f"   {seed['name']} = {seed['value']:.6f}")
    
    # ========================================
    # 6. LINEALIZACIÓN
    # ========================================
    print_section("6. Ejecutar Linealización")
    lin_response = requests.post(f"{BASE_URL}/kinetics/run-linearization",
        json={
            "kinetic_sample_id": sample_id,
            "models": [{"model": 1, "linearizations": [1]}],
            "filter": []
        }
    )
    lin_response.raise_for_status()
    lin_result = lin_response.json()["results"][0]["linearizations"][0]
    print(f"✅ Linealización completada")
    print(f"   R² = {lin_result['statistics']['r_squared']:.4f}")
    print(f"   Pendiente = {lin_result['slope']:.4f}")
    print(f"   Intercepto = {lin_result['intercept']:.4f}")
    print(f"   Parámetros recuperados:")
    for param in lin_result['parameters']:
        print(f"     {param['name']} = {param['value']:.4f} ± {param['std_err']:.4f}")
    
    # ========================================
    # 7. AJUSTE NO LINEAL
    # ========================================
    print_section("7. Ejecutar Ajuste No Lineal")
    print("⏳ Ejecutando (10-15 segundos)...")
    fit_response = requests.post(f"{BASE_URL}/kinetics/run-no-linear-model",
        json={
            "kinetic_sample_id": sample_id,
            "models": [{
                "model": 1,
                "seeds": seeds,
                "iterations": 10000,
                "step": 0.1
            }],
            "filter": []
        }
    )
    fit_response.raise_for_status()
    fit_data = fit_response.json()
    
    result = fit_data["results"][0]
    best_method_name = result["best_adjust"]
    best_method = next(m for m in result["adjustment_methods"] if m["name"] == best_method_name)
    
    print(f"✅ Ajuste completado")
    print(f"\n📊 RESULTADOS:")
    print(f"   Mejor método: {best_method_name}")
    print(f"   R² = {best_method['statistics']['r_squared']:.4f}")
    print(f"   R² ajustado = {best_method['statistics']['adjust_r_squared']:.4f}")
    print(f"   RMSE = {best_method['statistics']['RMSE']:.4f}")
    print(f"   AIC = {best_method['statistics']['AIC']:.2f}")
    print(f"   BIC = {best_method['statistics']['BIC']:.2f}")
    
    print(f"\n🔢 Parámetros ajustados:")
    for p in best_method["parameters"]:
        print(f"   {p['name']} = {p['value']:.4f} ± {p['std_err']:.4f}")
    
    print(f"\n🔍 Análisis de residuos:")
    res = best_method["residuals"]["analysis"]
    print(f"   Normalidad: {'✅ PASA' if res['passes_normality'] else '❌ FALLA'} (p={res['normality_pvalue']:.4f})")
    print(f"   Homocedasticidad: {'✅ PASA' if res['passes_homoscedasticity'] else '❌ FALLA'} (p={res['homoscedasticity_pvalue']:.4f})")
    print(f"   Independencia: {'✅ PASA' if res['passes_independence'] else '❌ FALLA'} (DW={res['durbin_watson']:.2f})")
    
    print(f"\n📈 Métodos probados:")
    for method in result["adjustment_methods"]:
        status = "✅" if method["success"] else "❌"
        r2 = method["statistics"]["r_squared"] if method["success"] else "N/A"
        print(f"   {status} {method['name']:15s} R²={r2}")
    
    # ========================================
    # 8. GUARDAR INVESTIGACIÓN
    # ========================================
    print_section("8. Guardar Investigación")
    save_response = requests.post(f"{BASE_URL}/kinetics/investigation/save",
        headers=headers,
        json={
            "kinetic_sample_id": sample_id,
            "kinetic_investigation_id": None,
            "iterations": 10000,
            "steps": 0.1,
            "results": fit_data["results"],
            "comparison": fit_data["comparison"]
        }
    )
    save_response.raise_for_status()
    save_data = save_response.json()
    investigation_id = save_data['kinetic_investigation_id']
    version_id = save_data['version_id']
    print(f"✅ Investigación guardada")
    print(f"   Investigation ID: {investigation_id}")
    print(f"   Version ID: {version_id}")
    
    # ========================================
    # 9. LISTAR INVESTIGACIONES
    # ========================================
    print_section("9. Listar Investigaciones")
    investigations = requests.get(f"{BASE_URL}/kinetics/investigations?page=1&per_page=5").json()
    print(f"✅ Total investigaciones: {investigations['total']}")
    print(f"   Mostrando {len(investigations['investigations'])} de {investigations['total']}")
    for inv in investigations['investigations'][:3]:
        print(f"   [{inv['kinetic_investigation_id']}] {inv['sample']['title'] if inv['sample'] else 'Sin título'}")
    
    # ========================================
    # 10. RECUPERAR VERSIÓN
    # ========================================
    print_section("10. Recuperar Versión")
    version = requests.get(
        f"{BASE_URL}/kinetics/investigation/{investigation_id}/version/{version_id}"
    ).json()
    print(f"✅ Versión recuperada")
    print(f"   Creada: {version['created_at']}")
    print(f"   Iteraciones: {version['iterations']}")
    print(f"   Modelos ajustados: {len(version['fitted_models'])}")
    
    # ========================================
    # RESUMEN FINAL
    # ========================================
    print_section("✅ TEST COMPLETADO EXITOSAMENTE")
    print(f"Sample ID: {sample_id}")
    print(f"Investigation ID: {investigation_id}")
    print(f"Version ID: {version_id}")
    print(f"Mejor ajuste: {best_method_name} (R² = {best_method['statistics']['r_squared']:.4f})")
    print("\n🎉 Todos los endpoints funcionando correctamente!")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.RequestException as e:
        print(f"\n❌ ERROR: {e}")
        print("\n⚠️  Verifica que el backend esté corriendo en http://127.0.0.1:5000")
    except KeyError as e:
        print(f"\n❌ ERROR en respuesta del servidor: campo {e} no encontrado")
    except Exception as e:
        print(f"\n❌ ERROR inesperado: {e}")
```

**Ejecutar:**
```powershell
python test_kinetics.py
```

---

## 📊 Convertir Datos de Excel a JSON

### Método 1: Con Python y pandas

```python
import pandas as pd
import json

# Leer Excel
df = pd.read_excel("tus_datos.xlsx", sheet_name="Sheet1")

# Opción A: Si tienes columnas "Tiempo" y "qt"
time = df["Tiempo"].tolist()
qt = df["qt"].tolist()

# Opción B: Si tienes columnas "Tiempo" y "Concentracion"
time = df["Tiempo"].tolist()
concentration = df["Concentracion"].tolist()

# Generar JSON para el request
sample_data = {
    "time": time,
    "qt": qt,  # O "concentration": concentration
    "temperature": 298,
    "time_unit": "min",
    "measure_unit": "mg/g",
    "adsorbate_id": 1,
    "adsorbent_id": 1,
    "title": "Datos Excel"
}

print(json.dumps(sample_data, indent=2))
```

### Método 2: Manualmente en Excel

1. Selecciona la columna de tiempos
2. Copia y pega en un archivo de texto
3. Reemplaza saltos de línea con comas
4. Rodea con corchetes: `[0, 5, 10, 20, 30, 60]`
5. Repite para columna de qt

### Método 3: Herramienta Online

1. Guarda Excel como CSV
2. Ve a https://www.convertcsv.com/csv-to-json.htm
3. Sube el CSV
4. Selecciona "Column Array"
5. Copia el resultado

---

## 🐛 Debugging

### Error: "Connection refused"

```powershell
# Verificar que el backend esté corriendo
Get-Process -Name python -ErrorAction SilentlyContinue

# Si no está corriendo, iniciarlo
.venv\Scripts\python.exe app/start.py
```

### Error: "Unauthorized" (401)

```powershell
# Regenerar token
$response = Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:5000/auth-token" `
  -ContentType "application/json" `
  -Body '{"email":"adsolab@dev.com","password":"password"}'
$token = $response.token
```

### Error: "Sample not found" (404)

```powershell
# Verificar que la muestra existe
Invoke-RestMethod -Uri "http://127.0.0.1:5000/kinetics/samples"
```

### Error: "Validation error" (400)

Causas comunes:
- Arrays `time` y `qt` con longitudes diferentes
- Valores negativos en los datos
- Menos de 2 puntos de datos
- Falta `initial_concentration` cuando usas `concentration`

```powershell
# Verificar longitudes
$time = @(0, 5, 10)
$qt = @(0.0, 3.2, 5.1)
Write-Host "Longitud time: $($time.Count), qt: $($qt.Count)"
```

### Ver Logs del Backend

Los logs aparecen en la terminal donde ejecutaste `python app/start.py`:

```
[kinetics] Inicio ajuste no lineal: 2026-06-24 15:30:00
[kinetics] Fin ajuste no lineal: 2026-06-24 15:30:12
```

### Reiniciar Base de Datos

Si algo sale mal con los datos:

```powershell
docker-compose down
docker-compose up -d
# Esto ejecuta migraciones automáticamente
```

---

## ✅ Checklist de Testing

Marca cada paso al completarlo:

### Configuración
- [ ] Backend corriendo en puerto 5000
- [ ] PostgreSQL corriendo (docker-compose)
- [ ] Datos del Excel extraídos

### Autenticación
- [ ] Token obtenido exitosamente
- [ ] Token guardado en variable

### Datos
- [ ] Materiales listados correctamente
- [ ] Muestra cinética creada
- [ ] Sample ID guardado

### Análisis
- [ ] Modelos listados
- [ ] Seeds predichas exitosamente
- [ ] Linealización ejecutada (R² > 0.9 esperado)
- [ ] Ajuste no lineal ejecutado (10-15 seg)
- [ ] Mejor método identificado
- [ ] Parámetros ajustados obtenidos
- [ ] Análisis de residuos completo

### Persistencia
- [ ] Investigación guardada
- [ ] Investigation ID y Version ID obtenidos
- [ ] Investigaciones listadas
- [ ] Versión específica recuperada

### Validación
- [ ] Todos los residuos pasan tests (normalidad, homocedasticidad, independencia)
- [ ] R² > 0.95 (ajuste excelente)
- [ ] AIC y BIC reportados
- [ ] Curva extendida tiene ~300 puntos

---

## 📚 Recursos Adicionales

- **OpenAPI Spec:** Ver archivo `openapi-spec.yml`
- **Flujo de Usuario:** Ver archivo `FLUJO_USUARIO_CINETICA.md`
- **Documentación Backend:** Ver archivo `README.md`
- **Arquitectura Módulo:** Ver archivo `KINETICS_MODULE.md`

---

## 🚀 Próximos Pasos

Después de validar que todo funciona:

1. **Probar con diferentes seeds** para ver cómo afecta la convergencia
2. **Probar con outliers** usando el parámetro `filter: [2, 5]`
3. **Crear múltiples versiones** de una investigación
4. **Comparar linealización vs ajuste no lineal** con los mismos datos
5. **Exportar resultados** para graficar en Excel/Python/R

---

**Última actualización:** 2026-06-24  
**Versión:** 1.0
