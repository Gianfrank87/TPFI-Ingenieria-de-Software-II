# TPFI — Ingeniería de Software II

Proyecto integrador en Python: **Proxy, Singleton y Observer** mediante sockets TCP y AWS DynamoDB.

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
python singletonproxyobserver.py -p 8080 -v
```

**Terminal 2 — Observer**

```bash
python observerclient.py -s localhost -p 8080 -o observer_output.json --retry 3 -v
```

**Terminal 3 — Cliente**

Antes de ejecutar, reemplazar `REEMPLAZAR_POR_UUID_CPU` en los JSON de `examples/` con el identificador emitido por `python evidence/IS2-TPFI-uuid.py`. Configurar también IDs y datos válidos para el entorno de prueba.

```bash
python singletonclient.py -i examples/list.json -s localhost -p 8080 -v
python singletonclient.py -i examples/get.json -s localhost -p 8080 -v
python singletonclient.py -i examples/set.json -s localhost -p 8080 -v
```

Después de `set`, el Observer debe recibir una notificación JSON. Las operaciones registran auditoría en `CorporateLog`.

### Demostración de la caída del servidor

1. Mantener abierto el Observer.
2. Detener el servidor con `Ctrl+C`.
3. Observar los avisos de desconexión y el nuevo intento cada 3 segundos.
4. Reiniciar el servidor; el Observer vuelve a suscribirse automáticamente.
5. Ejecutar un `set` y comprobar que el Observer recibe la notificación nuevamente.

### Segundo servidor en el mismo puerto

Sin detener la Terminal 1, abrir una cuarta terminal y ejecutar `python singletonproxyobserver.py -p 8080`. Debe informar que no se puede vincular el puerto y finalizar con código de error, sin detener el primer servidor.

## Pruebas, cobertura y calidad

```bash
python -m pytest
black --check .
ruff check .
mypy src/tpfi
pyright src/tpfi
bandit -r src/tpfi
```

Las pruebas usan implementaciones falsas de DynamoDB y bloquean la lectura de credenciales y las llamadas AWS. El umbral obligatorio configurado de cobertura es 85%. En la revisión local del 3/11/2026: **41 pruebas aprobadas, cobertura de líneas 93,73%** (Python 3.14.3). Black, Ruff, Mypy, Pyright y Bandit forman parte de los controles locales y de CI.

## Documentación y CI

```bash
pdoc -o docs/html tpfi
```

Los diagramas PlantUML actualizados están en `docs/` y `uml/`. El código envía la respuesta de `set` antes de notificar a los suscriptores y registra cada operación una sola vez. Los PNG y DOT originales de `docs/` se conservan como evidencia conceptual previa; para el orden exacto de respuesta y notificación, consultar los `.puml` actualizados. El flujo `.github/workflows/ci.yml` ejecuta controles automáticamente con Python 3.11 al subir cambios a GitHub y conserva la documentación HTML como artefacto descargable.

Los archivos `input_*.json`, `observer_output*.json`, credenciales, entornos virtuales y reportes temporales se conservan localmente y se excluyen de Git. `examples/` contiene las plantillas publicables. Los scripts originales de `evidence/` se preservan como material de la cátedra y no se ejecutan en CI; algunos escriben en AWS y deben utilizarse únicamente con autorización para ese entorno.

Para un procedimiento de evaluación paso a paso consultar `VALIDACION_LOCAL.md`.
