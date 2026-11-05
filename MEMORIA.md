# Memoria del trabajo práctico final integrador

**Asignatura:** Ingeniería de Software II

**Alumno:** Gian Moreyra

**Proyecto:** acceso a datos corporativos con Singleton, Proxy y Observer

**Repositorio:** https://github.com/Gianfrank87/TPFI-Ingenieria-de-Software-II

## 1. Objetivo y alcance

El trabajo implementa un sistema cliente-servidor en Python que permite consultar,
listar y modificar registros de AWS DynamoDB. Integra los patrones Singleton, Proxy
y Observer, registra operaciones en una tabla de auditoría y notifica los cambios
a los clientes suscriptos mediante sockets TCP.

La solución separa el transporte, las validaciones, el acceso a datos y la gestión
de suscripciones. Esta organización permite probar el comportamiento con gateways
falsos, sin depender de credenciales ni modificar las tablas reales.

## 2. Arquitectura y responsabilidades

| Elemento | Archivo principal | Responsabilidad |
| --- | --- | --- |
| Servidor | `src/tpfi/server.py` | Recibir conexiones, coordinar solicitudes, auditoría y notificaciones. |
| Cliente | `src/tpfi/client.py` | Enviar solicitudes JSON y mostrar respuestas. |
| Cliente Observer | `src/tpfi/observer_client.py` | Suscribirse, recibir eventos y reconectar ante fallas. |
| Acceso a DynamoDB | `src/tpfi/aws_gateway.py` | Encapsular `CorporateData` y `CorporateLog`. |
| Proxy | `src/tpfi/proxy.py` | Validar operaciones antes de delegarlas al gateway. |
| Administrador Observer | `src/tpfi/observer.py` | Registrar suscriptores y distribuir modificaciones. |
| Protocolo | `src/tpfi/protocol.py` | Serializar y recibir JSON UTF-8 terminado en salto de línea. |
| Logging | `src/tpfi/logging_setup.py` | Configurar mensajes y ocultar campos sensibles habituales. |

Los programas `singletonproxyobserver.py`, `singletonclient.py` y
`observerclient.py` son los puntos de entrada. El servidor atiende las conexiones
con hilos y mantiene los sockets de las suscripciones para enviar eventos.

## 3. Aplicación de los patrones

### Singleton

`CorporateDataGateway` y `CorporateLogGateway` heredan de
`_SingletonTableGateway`. La clase base conserva una instancia por clase concreta;
un bloqueo protege su creación. Cada gateway encapsula el recurso de su tabla,
evitando que la lógica de aplicación tenga que construirlo en cada operación.
La instancia es local a cada proceso, no global entre distintos servidores.

### Proxy

`CorporateDataProxy` valida `ACTION` y acepta `get`, `list` y `set`. Exige un
identificador para `get` y `set`, verifica el objeto `DATA` y controla el caso de
registro inexistente. Después delega en el contrato `DataGateway`, lo que permite
reemplazar DynamoDB por una implementación falsa durante las pruebas.

### Observer

`SubscriptionManager` mantiene un registro de sockets por UUID. Una nueva
suscripción con el mismo UUID reemplaza la anterior. Después de una modificación,
el servidor comunica el registro resultante a los suscriptores. Los envíos que
fallan provocan la eliminación de la suscripción correspondiente.

El cliente Observer espera la confirmación de `subscribe` antes de anunciar que
está suscripto. Si pierde la conexión, reintenta y vuelve a suscribirse.

## 4. Flujo de las operaciones y persistencia

Las solicitudes incluyen `UUID`, `ACTION` y, cuando corresponde, `ID` y `DATA`.
`SESSION` identifica la sesión; el servidor genera un identificador si falta.

1. El cliente abre una conexión TCP y envía una solicitud JSON.
2. El servidor verifica que sea un objeto y que incluya UUID.
3. El Proxy valida y ejecuta `get`, `list` o `set` mediante el gateway.
4. El servidor registra la operación en `CorporateLog` y envía la respuesta.
5. Para `set`, después de enviar la respuesta, notifica a los Observers.

`get` consulta por la clave `id`. `list` recorre las páginas de resultados de
DynamoDB. `set` recupera el registro, combina los campos recibidos y escribe el
estado resultante; si no existe, lo crea. La auditoría incorpora un identificador,
UUID, sesión, acción, fecha UTC, estado e ID del registro cuando corresponde.

## 5. Ejecución y reproducción

Se requiere Python 3.11 o superior. La instalación, configuración y demostración
completa se describen en [README.md](README.md) y
[VALIDACION_LOCAL.md](VALIDACION_LOCAL.md).

Con las dependencias instaladas y AWS configurado localmente, se utilizan tres
terminales:

```bash
python singletonproxyobserver.py -p 8080
python observerclient.py -s localhost -p 8080 -o observer_output.json --retry 3
python singletonclient.py -i examples/list.json -s localhost -p 8080
```

Los tres comandos corresponden respectivamente al servidor, Observer y cliente.
En la tercera terminal también pueden ejecutarse las plantillas `get.json` y
`set.json`. Antes se reemplaza el UUID de ejemplo y se configura un ID propio;
GET y SET deben usar el mismo ID para observar el registro modificado.

La demostración de recuperación consiste en detener el servidor, observar los
reintentos del Observer, reiniciar el servidor y ejecutar otro SET. Esta memoria
describe el procedimiento; la preparación de la entrega no volvió a ejecutar
operaciones contra AWS.

## 6. Pruebas y resultados verificados

En la revisión para la entrega se ejecutó `scripts/run_quality.ps1` con Python
3.14.3 del entorno virtual existente. El resultado fue:

| Control | Resultado |
| --- | --- |
| Pytest | 56 pruebas aprobadas. |
| Cobertura | 97,64% de líneas; mínimo requerido por la configuración: 85%. |
| Black y Ruff | Sin cambios de formato requeridos ni errores de lint. |
| Mypy y Pyright | Sin errores; Pyright tampoco informó advertencias. |
| Bandit | Sin incidencias en `src/tpfi`. |
| pdoc | Documentación HTML generada correctamente. |

Las pruebas cubren Singleton, Proxy, suscripciones, protocolo, clientes, servidor,
recuperación, errores y logging. Usan dobles de DynamoDB y sockets locales; la
configuración de pruebas bloquea la obtención de credenciales y las llamadas AWS.
Por eso estos resultados verifican la lógica y el transporte local, sin acreditar
por sí solos una integración vigente con las tablas reales.

GitHub Actions ejecuta los mismos siete controles en Linux con Python 3.11 ante
push y Pull Request. La documentación HTML se conserva como artefacto de CI.

## 7. Seguridad y revisión de publicación

Se revisaron los archivos publicables y los 3 commits existentes antes de preparar
esta entrega. La búsqueda de patrones de claves AWS, tokens, claves privadas,
credenciales literales y URL con contraseña no encontró secretos reales. Las
coincidencias detectadas correspondían a valores ficticios en pruebas de
ocultamiento de campos sensibles. También se revisaron los seis JSON locales
excluidos, sin detectar secretos mediante esos patrones.

Las plantillas publicadas usan un UUID de reemplazo y un ID genérico. Credenciales,
archivos `.env`, claves privadas, entornos virtuales, resultados locales y JSON de
la demostración quedan excluidos por `.gitignore`. La revisión por patrones no
constituye una garantía absoluta de ausencia de secretos.

El cliente conserva la respuesta JSON en stdout y los eventos de logging en
stderr. La salida del Observer oculta campos sensibles habituales tanto en consola
como en su archivo de salida. La identificación por UUID no implementa
autenticación criptográfica y el transporte TCP de esta solución no incorpora TLS.

## 8. Límites y posibles mejoras

El contador de suscripciones representa sockets registrados: una desconexión se
detecta cuando falla un envío. Un envío TCP completado no confirma que la
aplicación remota haya procesado el evento. No se implementan persistencia de
notificaciones, reproducción de eventos perdidos ni confirmaciones de recepción.

La modificación de datos y la escritura de auditoría son operaciones separadas;
no existe una transacción conjunta entre ambas tablas. La actualización de un
registro mediante lectura y escritura tampoco ofrece control de versiones para
escrituras concurrentes. Estos puntos, junto con autenticación, TLS y límites de
tamaño de mensajes, son posibles mejoras fuera del alcance implementado.

## 9. Documentación y uso de IA

Los diagramas actualizados en PlantUML están en `docs/` y `uml/`. Los archivos PNG
y DOT originales se conservan como material conceptual previo; para el orden
exacto de respuesta y notificación deben consultarse los `.puml` actualizados.

[CONTEXT.md](CONTEXT.md) declara el apoyo de herramientas de IA en la estructura,
revisión, pruebas y preparación de la entrega. La validación académica y las
evidencias de ejecución en el entorno AWS corresponden al alumno.

La solución integra los tres patrones solicitados, dispone de pruebas
automatizadas reproducibles y documenta tanto su ejecución como sus límites.
