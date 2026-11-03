# CONTEXT.md

## Uso de herramienta de IA

Se utilizó ChatGPT como apoyo para interpretar la consigna, proponer una estructura modular, revisar el código y preparar pruebas automatizadas.

### Prompts representativos

1. "Revisá la consigna del TPFI de Ingeniería de Software II y separá los entregables obligatorios."
2. "Diseñá una implementación Python de los patrones Singleton, Proxy y Observer respetando CorporateData y CorporateLog en DynamoDB."
3. "Prepará pruebas pytest que validen los patrones y la lógica sin modificar las tablas AWS reales."
4. "Revisá ruff, black, mypy, pyright, cobertura y bandit y corregí los problemas encontrados."

Las decisiones finales, ejecución en el entorno AWS provisto y evidencias de integración deben ser verificadas por el alumno.

En la preparación de la entrega se utilizó Codex para auditar archivos publicables, revisar exclusiones de Git, ejecutar pruebas y controles de calidad y preparar GitHub Actions. Se preservó la lógica funcional de conexión a DynamoDB y no se ejecutaron operaciones sobre las tablas reales.
