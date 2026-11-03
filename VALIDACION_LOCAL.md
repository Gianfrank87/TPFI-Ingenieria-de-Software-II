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

Con el entorno virtual existente, ejecutar todos los controles (no requiere AWS):

```powershell
.\scripts\run_quality.ps1
```

Desde otra carpeta, usar la ruta absoluta. Si se bloquean scripts sin firma: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_quality.ps1`; la excepción afecta sólo a ese proceso. En Linux: `bash scripts/run_quality.sh`.

Los scripts usan exclusivamente el Python de `.venv`, no instalan ni cambian dependencias, continúan aunque una herramienta falle y generan un resumen PASS/FAIL de los siete controles, incluido pdoc en `docs/html`. El código final es 1 ante cualquier fallo. No se ejecutan scripts de `evidence/`.

Equivalentes individuales:

```bash
pytest
black --check .
ruff check .
mypy src/tpfi
pyright src/tpfi
bandit -r src/tpfi
pdoc -o docs/html tpfi
```

Criterios de aceptación:

- pytest: 100% de tests OK y cobertura >= 85%.
- black: sin archivos que requieran reformateo.
- ruff: sin errores.
- mypy: sin errores.
- pyright: sin errores.
- bandit: sin observaciones de seguridad en alcance.

Resultado local del 3/11/2026 (Python 3.14.3): 56 tests aprobados, cobertura 97,64%; Black, Ruff, Mypy, Pyright, Bandit y pdoc PASS. Se ejecutó el script desde `scripts/` para verificar la independencia del directorio actual. pdoc generó los HTML con advertencias de compatibilidad `ForwardRef` en Python 3.14; no se actualizaron dependencias. CI ejecuta el script Linux con Python 3.11. No se revalidó la integración AWS real en esta intervención.

## 4. Prueba de integración manual

Esta sección describe la integración previamente comprobada por el alumno. No ejecutarla como parte de la preparación de GitHub: `set` modifica `CorporateData` y las operaciones del servidor registran entradas en `CorporateLog`. Las evidencias con datos reales deben conservarse fuera del repositorio.

En tres terminales con el ambiente virtual activado:

### Terminal 1 - servidor

```bash
python singletonproxyobserver.py -p 8080
```

### Terminal 2 - observer

```bash
python observerclient.py -s localhost -p 8080 -o observer_output.json --retry 3
```

### Terminal 3 - cliente

Reemplace `REEMPLAZAR_POR_UUID_CPU` en los JSON de `examples/` por el valor obtenido con:

```bash
python evidence/IS2-TPFI-uuid.py
```

Luego:

```bash
python singletonclient.py -i examples/list.json
python singletonclient.py -i examples/get.json
python singletonclient.py -i examples/set.json
```

Verificaciones:

1. `get` devuelve el registro solicitado o un error controlado.
2. `list` devuelve un array JSON.
3. `set` devuelve el registro actualizado.
4. El observer recibe una notificación después del `set`.
5. `CorporateLog` recibe entradas de `subscribe`, `get`, `list` y `set`.

Preparar los ejemplos GET/SET con el ID de un registro propio. El servidor debe mostrar conexión TCP con IP/puerto, acción, UUID, ID, validación/ejecución, escritura confirmada en CorporateLog y cierre del cliente. Después de SET muestra modificación y cantidad de envíos TCP completados. El Observer debe mostrar conexión, SUBSCRIBE enviado, confirmación, espera, ID modificado y JSON de la notificación, sin `-v`. El cliente mantiene stdout como JSON y escribe eventos en stderr.

6. Detener el servidor con Ctrl+C y verificar el aviso de desconexión del Observer y reintentos cada 3 segundos.
7. Reiniciar el servidor en el mismo puerto y verificar reconexión TCP y nueva confirmación SUBSCRIBE.
8. Manualmente, modificar otra vez el registro propio y verificar la notificación tras la reconexión.

La reconexión TCP se anuncia al conectar; la suscripción se confirma únicamente al recibir un ACK válido. Las suscripciones registradas no prueban presencia: el servidor elimina un Observer caído cuando falla un envío. La entrega TCP no equivale a confirmación de lectura del evento. No incorporar secretos a UUID/ID ni datos de prueba. Los campos sensibles habituales del JSON del Observer se ocultan también en su archivo de salida.

## 5. Evidencias para el informe

Guardar capturas de:

- Diagnóstico AWS exitoso.
- Resultado completo de `pytest` con cobertura.
- `black`, `ruff`, `mypy`, `pyright` y `bandit` sin errores.
- Servidor iniciado.
- Observer suscripto y notificación recibida.
- Ejecuciones get/list/set.
- Registros correspondientes en CorporateLog si se visualizan desde AWS.
