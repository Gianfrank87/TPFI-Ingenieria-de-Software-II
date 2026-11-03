# Validación local final del TPFI

Esta etapa debe ejecutarse en la PC configurada con las credenciales AWS provistas por la cátedra. No copie ni publique `IS2_TPFI_credentials.json`.

## 1. Crear ambiente virtual

### Windows PowerShell

```powershell
cd TPFI_IS2_Gian_Moreyra
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### Linux

```bash
cd TPFI_IS2_Gian_Moreyra
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

## 2. Verificar AWS provisto por la cátedra

Utilice la configuración local existente, sin modificar credenciales, perfiles ni variables. El siguiente diagnóstico original es manual y requiere autorización de acceso al entorno AWS; no forma parte de la validación automatizada:

```bash
python evidence/IS2_TPFI_test.py
```

Debe informar las fechas de creación de `CorporateData` y `CorporateLog` y finalizar con `Completed successfully`.

## 3. Calidad y seguridad

Ejecutar, en este orden:

```bash
pytest
black --check .
ruff check .
mypy src/tpfi
pyright src/tpfi
bandit -r src/tpfi
```

Criterios de aceptación:

- pytest: 100% de tests OK y cobertura >= 85%.
- black: sin archivos que requieran reformateo.
- ruff: sin errores.
- mypy: sin errores.
- pyright: sin errores.
- bandit: sin observaciones de seguridad en alcance.

## 4. Prueba de integración manual

Esta sección describe la integración previamente comprobada por el alumno. No ejecutarla como parte de la preparación de GitHub: `set` modifica `CorporateData` y las operaciones del servidor registran entradas en `CorporateLog`. Las evidencias con datos reales deben conservarse fuera del repositorio.

En tres terminales con el ambiente virtual activado:

### Terminal 1 - servidor

```bash
python singletonproxyobserver.py -p 8080 -v
```

### Terminal 2 - observer

```bash
python observerclient.py -s localhost -p 8080 -o observer_output.json -v
```

### Terminal 3 - cliente

Reemplace `REEMPLAZAR_POR_UUID_CPU` en los JSON de `examples/` por el valor obtenido con:

```bash
python evidence/IS2-TPFI-uuid.py
```

Luego:

```bash
python singletonclient.py -i examples/get.json -v
python singletonclient.py -i examples/list.json -v
python singletonclient.py -i examples/set.json -v
```

Verificaciones:

1. `get` devuelve el registro solicitado o un error controlado.
2. `list` devuelve un array JSON.
3. `set` devuelve el registro actualizado.
4. El observer recibe una notificación después del `set`.
5. `CorporateLog` recibe entradas de `subscribe`, `get`, `list` y `set`.

## 5. Evidencias para el informe

Guardar capturas de:

- Diagnóstico AWS exitoso.
- Resultado completo de `pytest` con cobertura.
- `black`, `ruff`, `mypy`, `pyright` y `bandit` sin errores.
- Servidor iniciado.
- Observer suscripto y notificación recibida.
- Ejecuciones get/list/set.
- Registros correspondientes en CorporateLog si se visualizan desde AWS.
