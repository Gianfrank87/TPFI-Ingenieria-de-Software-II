# Changelog

## Sin publicar - 2026-11-03

- Eventos INFO en servidor, cliente y Observer para la defensa, con stderr separado del JSON y dependencias limitadas a WARNING; `-v` conserva DEBUG.
- Registro de conexiones, acción/UUID/ID, auditoría confirmada, suscripciones y envíos TCP; reconexión con confirmación del nuevo SUBSCRIBE.
- Ocultamiento de campos sensibles del Observer y errores sin detalles de proveedores.
- Scripts de calidad equivalentes para PowerShell y Linux: `.venv`, siete controles, continuación ante fallos, resumen y código de salida agregado.
- Regresiones con gateways falsos, sin modificar operaciones DynamoDB, y procedimiento manual de defensa actualizado.

## 1.0.1 - 2026-11-03

- Pruebas automatizadas del reintento de Observer y conflicto de puerto TCP.
- Documentación ampliada para ejecución, defensa y validación final.
- Actualización de comandos de generación de documentación.
- Preparación de entrega privada en GitHub, exclusión de datos locales y auditoría de secretos.
- Bloqueo de credenciales y llamadas AWS durante las pruebas; documentación HTML como artefacto de CI.

## 1.0.0 - 2026-10-28

- Implementación inicial de SingletonClient, ObserverClient y SingletonProxyObserverTPFI.
- Acceso DynamoDB con singletons separados para CorporateData y CorporateLog.
- Proxy para get/set/list con pista auditable.
- Observer con subscripciones persistentes y notificación de cambios.
- Pruebas automatizadas, calidad, seguridad y documentación UML.
