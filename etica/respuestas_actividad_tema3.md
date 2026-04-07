## ACTIVIDAD CLASE TEMA 3 - Respuestas breves

### 1. Breve descripcion del caso de estudio elegido

El caso de estudio es un sistema de IA para analisis financiero historico-descriptivo mediante una arquitectura multiagente. El TFM todavia esta en proceso de desarrollo, pero ya cuenta con una base funcional suficiente como para realizar esta actividad a partir de lo que se ha implementado hasta ahora. En su estado actual, el sistema recibe una entrada estructurada con la consulta, la intencion, los tickers, el periodo y las rutas a los CSV, y a partir de ahi valida la entrada, selecciona el analisis, genera codigo Python, lo ejecuta y devuelve una respuesta interpretable.

Por ahora, el TFM soporta seis tipos de analisis: crecimiento de precio, comparacion de activos, vision general de un activo, analisis de retornos, analisis de riesgo historico y analisis tecnico. No realiza prediccion futura ni toma decisiones automaticas sobre personas.

### 2. El sistema IA del caso de estudio: ¿es de alto riesgo? ¿es un GPAIS?

En su estado actual, no parece un sistema de alto riesgo segun el Reglamento de IA, porque no se usa en ambitos como empleo, credito, biometria, justicia, educacion, infraestructuras criticas o servicios esenciales. Su funcion es analizar datos historicos de mercado y mostrar resultados descriptivos.

Tampoco es un GPAIS propio, porque el TFM no desarrolla ni comercializa un modelo de IA de proposito general. Ahora mismo funciona con reglas y plantillas programaticas, no con un modelo fundacional propio.

La implicacion de esto es que no le aplican las obligaciones especificas de los sistemas de alto riesgo ni las de proveedor de un GPAIS, aunque si debe respetar principios generales de seguridad, trazabilidad y buen uso de los datos.

### 3. Analisis de la tipologia de datos que se van a tratar

Los datos principales del TFM son datos financieros historicos de mercado: precios, volumen, fechas y series temporales de activos cotizados. Estos datos no son datos personales, porque no pertenecen a personas fisicas identificadas o identificables.

Ademas, el sistema trata datos tecnicos del propio flujo, como la consulta estructurada, la intencion, los tickers, las rutas de los CSV, el codigo generado y los logs de ejecucion. En principio, estos datos tampoco son personales, salvo que un usuario introduzca informacion identificativa en la consulta o que aparezcan datos personales de forma incidental en los logs.

Por tanto, el tratamiento principal es de datos no personales, y el posible tratamiento de datos personales seria accesorio y residual.

### 4. Datos especialmente protegidos

Con la informacion disponible, no se tratan categorias especiales de datos del articulo 9 RGPD. El sistema no trabaja con datos de salud, ideologia, religion, origen etnico, biometria, genetica, vida sexual o afiliacion sindical.

Por eso, en el estado actual del TFM no puede decirse que se traten datos sensibles. Aun asi, conviene aplicar medidas basicas como minimizacion de datos, control de acceso a los logs, limitacion del tiempo de conservacion y evitar que las consultas incluyan datos personales innecesarios.

### 5. Legitimacion del tratamiento de datos personales

La mayor parte del sistema trabaja con datos no personales, por lo que en esa parte no seria aplicable el RGPD. Si de forma accesoria se trataran datos personales, la base juridica mas razonable dependeria de la fase:

En desarrollo y pruebas internas, podria justificarse por interes legitimo del responsable, ya que el tratamiento seria necesario para desarrollar, depurar y asegurar el sistema.

En la fase de uso del sistema, si el usuario introduce datos personales dentro de una consulta para obtener el servicio, podria justificarse por la ejecucion de la relacion de servicio o por interes legitimo, siempre aplicando minimizacion y proporcionalidad.

En los logs tecnicos y la gestion de errores, la base mas razonable seria tambien el interes legitimo, porque esos registros sirven para seguridad, trazabilidad y mantenimiento del sistema.

### 6. Deberes del responsable: analisis de riesgo

Los principales riesgos del caso de estudio son los siguientes:

1. Inclusion accidental de datos personales en consultas o logs.  
Probabilidad media. Impacto medio.  
La medida principal es minimizar la informacion recogida y filtrar o borrar datos personales innecesarios.

2. Acceso no autorizado a logs, payloads o resultados de ejecucion.  
Probabilidad media. Impacto medio-alto.  
Las medidas principales son control de accesos, almacenamiento seguro y limitacion del tiempo de conservacion.

3. Ejecucion insegura del codigo generado.  
Probabilidad media. Impacto alto.  
Las medidas principales son ejecucion en entorno controlado, limites de tiempo y validacion del codigo antes de ejecutarlo.

4. Confianza excesiva en los resultados del sistema.  
Probabilidad media. Impacto medio-alto.  
La medida principal es dejar claro que el sistema ofrece analisis historico y apoyo interpretativo, pero no asesoramiento financiero automatico.

### 7. Conclusion final

En conclusion, el TFM presenta un riesgo moderado y controlable desde el punto de vista de proteccion de datos, porque trabaja sobre todo con datos financieros historicos no personales. No parece un sistema de alto riesgo ni un GPAIS propio, y tampoco se aprecia tratamiento de datos sensibles.

Por ello, el tratamiento puede considerarse viable siempre que se apliquen medidas basicas de minimizacion, seguridad, control de acceso, gestion de logs y transparencia sobre los limites reales del sistema.

### 8. Referencias normativas utiles

- RGPD, articulo 6.
- RGPD, articulo 9.
- RGPD, articulo 35.
- RGPD, articulo 37.
- LOPDGDD, articulo 34.
- Reglamento (UE) 2024/1689 de IA, articulo 6 y Anexo III.
- Reglamento (UE) 2024/1689 de IA, articulos sobre GPAI.
