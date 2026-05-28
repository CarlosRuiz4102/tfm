-Podria estar interesante mostrar que para un futuropodriamos tener la opinion de analisatas profesionales para ver por un lado que tal analiza nuestro sistema y por otro que nos ayuden a refizorzar nuestros analisis.

-Darle una vuelta a lo de la motivación punto 1.2 , eso de mvp.... MAs que todo eso del MVP miralo bine porque no se si esta muy bine, si eso define en algun lado los diferentes MVP que tuvimos para que se sepa.

-Seria interesante mostrar los datos que obtenemos? tipo en el 3.1

-Como ves en el punto 3.2 cometar el proceso que hay que hacer para descargarnos los datos? contarlo y puedes unirlo con el punto 3.3 donde mostramos la estructiura de los csv

-Ten cuidado que en el punto 3.3 las tablas no corten frases, lo mismo en el 3.4

-lo del punto 3.6? es profesional comentar esas cosas??

-cada vez que menciones los modelos que vayan seguidos de sus citas

-ver el 5.3, que es y que sentido tiene

-hay que volver a ejeutar para ver que tal resultados obtenemos y poder poner bine la tabla del 8.8. Tambien seria interesante que los resultamos que obtengamos los pongamos en [evaluacion_amplitud_tfm_llms.md] y borremos los antiguos

-mirar los .md que hay en docs y comentar en la memoria la info que tienen, puede ser interesante

-darle una vuelta a lo de las salidas, si el usuario pide en el mensaje que le mostremos algo, nos ceñiremos a ello y se lo mostraremos junto lo que consideremos adicional

-revisar eso de lo que hemos hecho sobre elegir un buen analisis, citar de las fuentes donde nos hemos formado 

-mencionar tambine en la memoria el github donde estamos trabajando y como hemos organizado todo, un poco que se note que hemos realizado trabajo de MLops

-porcentahe de errores, benmarch, respuesta esperada vs respuesta que da, ver los intent, retrival, darle una vuelta

-estimar estas cosas a futuro como apis no gratuitas, oseaq comentar nuestras limitaciones y que estaria bien para un futuro

-crees que lo de anexos se deberia quedar ahi o lo deberiamos meter por otro lado de la memoria, me refiero a su contenido.

-a la que acabemos de hacer todo darle una vuelta a las conclusiones

-darle una vuelta a este mensaje 
Buen día, 

Les dejo a continuación el resumen de las métricas para la iteración 25b.

En general esta iteración presenta un mejor rendimiento con respecto a la anterior iteración 25a.

A resaltar de la iteración 25b con respecto a la 25a:
Accuracy global se mantiene mejorando ligeramente a nivel de decimales
Accuracy e2e se mantiene mejorando ligeramente a nivel de decimales también
En las detecciones erróneas empeora con respecto a la iteración 25a en Clarify pero mejora en Alfred
En cuanto a los casos donde ocurre desambiguación, se mantienen en 1%
Los errores por retrieval se mantienen mientras que los errores por description disminuyen en 24
Son más los e2e que mostraron una desmejora que los que mostraron mejora
A nivel de olas, son más las olas que mejoran su rendimiento que las que desmejoran
Se observó una ligero aumento en el accuracy de los intents destacados y los intents con peor accuracy tienen en general mejor accuracy que los peores intents de la 25a

Recomendamos revisar más en detalle para ver si han podido haber otras diferencias que puedan resultar de interés.

Resumen:

El accuracy global se mantiene con respecto al de la iteración anterior, presentando una leve mejora a nivel de decimales:

accuracy

ITERACIÓN 25a

0.94

ITERACIÓN 25b

0.94

En cuanto a los e2e, el accuracy se mantiene presentando leve mejora a nivel de decimales:

E2E

accuracy

ITERACIÓN 25a

0.91

ITERACIÓN 25b

0.91

Con respecto a la versión 25a, observamos: 

E2E que han empeorado: 
consulting.assistance.contactBbva
consulting.account.detail
operation.card.modifyDetail
consulting.financialHealth.frontPage
consulting.card.detail
contract.products.insurances
operation.bill.returnBill
service.insurance.assistance
E2E que han mejorado:
consulting.movements.generic
consulting.movements.specific
consulting.financialHealth.savings
contract.products.loans
En cuanto a las detecciones incorrectas empeoran en Clarify (11 más) pero mejoran en Alfred (11 menos) con respecto a la iteración 25a.

- Iteración 24b:

Alfred  63
Clarify  22
- Iteración 25a:

Alfred  90
Clarify  38
- Iteración 25b:

Alfred  79
Clarify  49
Desambiguación

La desambiguación ocurre en el 1% de los casos, estando el intent correcto en el top_k en el 82% de los casos de desambiguación, un porcentaje 3% mayor que en la anterior iteración 25a.

intents_disambiguation 0.01
intents_disambiguation_and_match_top_k 0.8

ANÁLISIS POR OLAS

En cuanto al análisis incorporado por OLA podemos observar los siguientes puntos a resaltar (comparado con 25a): 

Mejores resultados: 


OLA 8

accuracy

PREVIOUS EXECUTION

0,96

CURRENT EXECUTION

0,97

Peores resultados:


OLA E2E

accuracy

PREVIOUS EXECUTION

0,91

CURRENT EXECUTION

0,91

En general, mejora con respecto a la iteración 25a la ola e2e, 1, 2, 4, 5, 6-1, y 8 mientras que empeoran las olas 3 y 7 .

TOTAL ERRORES POR CAUSA

Wrong retrieval: 58 errores (vs 58 errores en la versión 25a)

Wrong description: 350 errores (vs 374 errores en la versión 25a)

INTENTS CON PEOR ACCURACY 24b


EXPECTED INTENT	ACCURACY	MOST FREQUENT WRONG INTENT	MAIN ERROR REASON
consulting.stocks	0.67	consulting.communicationsPreferences
consulting.movements.generic
operation.contributeEquity
operation.documents.statement
---
experience.invest
contract.products.securitiesAccount
operation.contributeEquity
consulting.communicationsPreferences
clarify
operation.fundsTransfers

wrong retrieval
---
wrong description
consulting.financialHealth.savings	0.69	consulting.financialHealth.frontPage
consulting.financialHealth.expenseControl
consulting.account.global.balance	wrong description
operation.card.manageLinkedServices	0.75	alfred
consulting.card.detail
consulting.movements.specific
---
operation.cards.mobilePayments
clarify
operation.generic.restrictOnlineOperation	wrong retrieval
---
wrong description
contract.products.loans	0.77	clarify
operation.overdraft
---
operation.overdraft
contract.products.mortgages
experience.home.buying

wrong retrieval
---
wrong description
consulting.bills	0.78	operation.bill.returnBill
---
clarify
experience.bringToBbva.bringMyBills
operation.bill.returnBill
operation.card.modifyDetail
operation.payments.payDirectDebit	wrong retrieval
---
wrong description

INTENTS CON PEOR ACCURACY 25a


EXPECTED INTENT	ACCURACY	MOST FREQUENT WRONG INTENT	MAIN ERROR REASON
consulting.financialHealth.savings	0.56	consulting.financialHealth.frontPage
consulting.financialHealth.expenseControl
alfred
wrong description
consulting.stocks	0.64	operation.documents.statement
operation.contributeEquity
consulting.movements.generic
consulting.communicationsPreferences
---
contract.products.securitiesAccount
operation.contributeEquity
experience.invest
alfred	wrong retrieval
---
wrong description
contract.products.loans	0.77	clarify
operation.overdraft
---
operation.overdraft
experience.home.buying	wrong retrieval
---
wrong description
operation.card.manageLinkedServices	0.79	clarify
consulting.card.detail
consulting.movements.specific
---
operation.cards.mobilePayments
operation.generic.restrictOnlineOperation	wrong retrieval
---
wrong description
consulting.movements.specific	0.80	consulting.movements.generic
consulting.pensionPlan
---
alfred
clarify
consulting.bills
consulting.accountRetentions
consulting.deposits
consulting.movements.generic	wrong retrieval
---
wrong description

INTENTS CON PEOR ACCURACY 25b


EXPECTED INTENT	ACCURACY	MOST FREQUENT WRONG INTENT	MAIN ERROR REASON
consulting.stocks	0.67	consulting.movements.generic
operation.contributeEquity
---
experience.invest
alfred
operation.contributeEquity
contract.products.securitiesAccount	wrong retrieval
---
wrong description
operation.card.manageLinkedServices	0.75	consulting.card.detail
consulting.movements.specific
---
operation.cards.mobilePayments
operation.generic.restrictOnlineOperation
clarify	wrong retrieval
---
wrong description
consulting.financialHealth.expenseControl	0.80	consulting.financialHealth.savings
consulting.financialHealth.frontPage	wrong description
consulting.insurance.renewalAgenda	0.80	alfred
consulting.insurances.detail
experience.financial.aggregator
service.insurance.insuranceSpace	wrong description
operation.load.card	0.80	operation.transferToCard (9)
contract.products.cards.kids	wrong description

RENDIMIENTO DE INTENTS DESTACADOS


EXPECTED INTENT	ACCURACY	MOST FREQUENT WRONG INTENT	MAIN ERROR REASON
consulting.movements.generic	0.92	consulting.movements.specific
clarify	wrong description
consulting.movements.specific	0.85	
consulting.movements.generic
consulting.pensionPlan
---
clarify (7)
alfred
consulting.accountRetentions
consulting.account.bankCharges
consulting.movements.generic
consulting.loans
experience.bringToBbva.bringMyBills
fallback-out_of_scope
wrong retrieval
---
wrong description
operation.bill.returnBill	0.94	consulting.bills
consulting.assistance.fraud	                    wrong description
