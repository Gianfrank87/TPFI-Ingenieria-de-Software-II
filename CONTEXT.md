# CONTEXT.md

El 4/11/2026 se utilizó Codex para corregir las advertencias de pdoc y coverage observadas durante la validación local. El usuario autorizó explícitamente actualizar pdoc a la versión 16 dentro del entorno virtual existente. Se mantuvieron los diagnósticos visibles y el alcance de medición de cobertura, sin modificar AWS.

## Uso de herramienta de IA

Se utilizó ChatGPT como apoyo para interpretar la consigna, proponer una estructura modular, revisar el código y preparar pruebas automatizadas.

### Prompts representativos

1. "Revisá la consigna del TPFI de Ingeniería de Software II y separá los entregables obligatorios."
2. "Diseñá una implementación Python de los patrones Singleton, Proxy y Observer respetando CorporateData y CorporateLog en DynamoDB."
3. "Prepará pruebas pytest que validen los patrones y la lógica sin modificar las tablas AWS reales."
4. "Revisá ruff, black, mypy, pyright, cobertura y bandit y corregí los problemas encontrados."

Las decisiones finales, ejecución en el entorno AWS provisto y evidencias de integración deben ser verificadas por el alumno.

En la preparación de la entrega se utilizó Codex para auditar archivos publicables, revisar exclusiones de Git, ejecutar pruebas y controles de calidad y preparar GitHub Actions. Se preservó la lógica funcional de conexión a DynamoDB y no se ejecutaron operaciones sobre las tablas reales.

El 3/11/2026 se solicitó a Codex mejorar la observabilidad de las tres terminales para la defensa oral, unificar los siete controles de calidad y agregar regresiones. Se conservaron los gateways DynamoDB y el Proxy, se añadieron eventos posteriores a confirmaciones reales y se documentaron los límites del contador de suscripciones y de la entrega TCP. Las pruebas usan sockets locales, mocks y gateways falsos; se preservó la configuración AWS. Se preparó la rama `fix/logging-defensa` para revisión por Pull Request, sin merge automático.
