# TPFI — Ingeniería de Software II

Proyecto integrador en Python: **Proxy, Singleton y Observer** mediante sockets TCP y AWS DynamoDB.

La [memoria del trabajo](MEMORIA.md) presenta la arquitectura, los patrones, los resultados de validación y los límites de la solución.

## Estructura y patrones

| Patrón | Implementación | Responsabilidad |
| --- | --- | --- |
| Singleton | `src/tpfi/aws_gateway.py` | Una instancia por gateway para `CorporateData` y `CorporateLog` |
| Proxy | `src/tpfi/proxy.py` | Validar y delegar `get`, `list`, `set` |
| Observer | `src/tpfi/observer.py` | Administrar suscriptores y notificar cambios |

- `src/tpfi/server.py` y `singletonproxyobserver.py`: servidor TCP concurrente.
- `src/tpfi/client.py` y `singletonclient.py`: cliente de operaciones sobre datos.
- `src/tpfi/observer_client.py` y `observerclient.py`: cliente suscriptor con reconexión automática.
- `src/tpfi/protocol.py`: serialización de mensajes JSON por línea.
- `tests/`: pruebas automatizadas con gateways falsos (sin modificar AWS).
- `evidence/`: scripts de verificación provistos para el entorno AWS.
- `docs/`, `uml/`: diagramas de actividad y estado en PlantUML, DOT y PNG.

## Requisitos

Python 3.11 o superior, conectividad a AWS y credenciales habilitadas para las tablas `CorporateData` y `CorporateLog`. **No subir las credenciales al repositorio.**

```bash
python -m venv .venv
```

Activar el entorno: Windows PowerShell `.\.venv\Scripts\Activate.ps1`; Linux/macOS `source .venv/bin/activate`.

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

Ejecutar los comandos desde la raíz del proyecto. Para la integración manual se utiliza la configuración AWS local existente, sin modificar perfiles ni variables. Las pruebas y la generación de documentación no requieren credenciales AWS.

## Demostración en tres terminales

**Terminal 1 — Servidor**

```bash
python singletonproxyobserver.py -p 8080
```

**Terminal 2 — Observer**

```bash
python observerclient.py -s localhost -p 8080 -o observer_output.json --retry 3
```

**Terminal 3 — Cliente**

Antes de ejecutar, reemplazar `REEMPLAZAR_POR_UUID_CPU` en los JSON de `examples/` con el identificador emitido por `python evidence/IS2-TPFI-uuid.py`. Configurar también IDs y datos válidos para el entorno de prueba.

```bash
python singletonclient.py -i examples/list.json -s localhost -p 8080
python singletonclient.py -i examples/get.json -s localhost -p 8080
python singletonclient.py -i examples/set.json -s localhost -p 8080
```

Después de `set`, el Observer debe recibir una notificación JSON. Las operaciones registran auditoría en `CorporateLog`.

La demostración con AWS es manual: preparar GET y SET con el ID de un registro propio; SET modifica ese registro y cada operación audita en CorporateLog. El script de calidad usa dobles de prueba y no ejecuta esta demostración.

Las tres terminales muestran INFO sin `-v`, con prefijos `[SERVER]`, `[CLIENT]` y `[OBSERVER]`. `-v` habilita DEBUG para `tpfi`; Boto3, Botocore, urllib3 y s3transfer quedan en WARNING. Los mensajes van a stderr; el cliente conserva exclusivamente la respuesta JSON en stdout. El Observer imprime cada JSON inmediatamente y oculta campos sensibles habituales (password, secret, token, credenciales). No usar secretos como ID, UUID ni datos del registro de demostración.

El servidor identifica acción, UUID e ID, confirma la auditoría sólo después de escribir CorporateLog y muestra las notificaciones entregadas por TCP. Ese número no confirma lectura por la aplicación remota. El contador representa suscripciones registradas: las desconexiones de Observers se detectan al fallar un envío, sin agregar heartbeats ni cambiar el protocolo.

### Demostración de la caída del servidor

1. Mantener abierto el Observer.
2. Detener el servidor con `Ctrl+C`.
3. Observar los avisos de desconexión y el nuevo intento cada 3 segundos.
4. Reiniciar el servidor; el Observer vuelve a suscribirse automáticamente.
5. Ejecutar un `set` y comprobar que el Observer recibe la notificación nuevamente.

### Segundo servidor en el mismo puerto

Sin detener la Terminal 1, abrir una cuarta terminal y ejecutar `python singletonproxyobserver.py -p 8080`. Debe informar que no se puede vincular el puerto y finalizar con código de error, sin detener el primer servidor.

## Pruebas, cobertura y calidad

Ejecutar todos los controles con el Python de `.venv`, sin activar el entorno ni instalar dependencias:

```powershell
.\scripts\run_quality.ps1
```

Desde otra ubicación, invocar la ruta absoluta del script. Si la política de PowerShell exige firma, puede usarse una excepción sólo para el proceso:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_quality.ps1
```

En Linux: `bash scripts/run_quality.sh`. Ambos scripts ubican la raíz por su propia ruta, requieren `.venv`, ejecutan pytest con cobertura, Black, Ruff, Mypy, Pyright, Bandit y pdoc, continúan tras fallos y muestran PASS/FAIL con códigos de salida. Devuelven 1 si falla cualquier control; 0 si pasan todos. No instalan dependencias ni modifican el entorno virtual.

```bash
python -m pytest
black --check .
ruff check .
mypy src/tpfi
pyright src/tpfi
bandit -r src/tpfi
```

Las pruebas usan implementaciones falsas de DynamoDB y bloquean la lectura de credenciales y las llamadas AWS. El umbral obligatorio configurado de cobertura es 85%. En la revisión local del 3/11/2026: **56 pruebas aprobadas, cobertura de líneas 97,64%** (Python 3.14.3). Los siete controles aprobaron al invocar el script desde otra carpeta. Se comprobó también que una falla de pytest no impide ejecutar los seis controles restantes y devuelve código 1.

Se requiere pdoc 16 para resolver las anotaciones con Python 3.14. La cobertura mide la ruta `src/tpfi`, evitando la importación exploratoria del paquete antes de iniciar la medición. No se silencian advertencias ni se filtra la salida de las herramientas. CI usa Python 3.11 y ejecuta el mismo script Linux en una `.venv` propia.

## Documentación y CI

```bash
pdoc -o docs/html tpfi
```

Los diagramas PlantUML actualizados están en `docs/` y `uml/`. El código envía la respuesta de `set` antes de notificar a los suscriptores y registra cada operación una sola vez. Los PNG y DOT originales de `docs/` se conservan como evidencia conceptual previa; para el orden exacto de respuesta y notificación, consultar los `.puml` actualizados. El flujo `.github/workflows/ci.yml` ejecuta controles automáticamente con Python 3.11 al subir cambios a GitHub y conserva la documentación HTML como artefacto descargable.

Los archivos `input_*.json`, `observer_output*.json`, credenciales, entornos virtuales y reportes temporales se conservan localmente y se excluyen de Git. `examples/` contiene las plantillas publicables. Los scripts originales de `evidence/` se preservan como material de la cátedra y no se ejecutan en CI; algunos escriben en AWS y deben utilizarse únicamente con autorización para ese entorno.

Para un procedimiento de evaluación paso a paso consultar `VALIDACION_LOCAL.md`.
