# Changelog

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
