// Charlas de pasillo: cuando dos se cruzan caminando por la misma línea de la grilla, uno dice algo
// y el otro contesta un toque después (globos de una línea, ~35 caracteres como mucho).
//
// "Misma línea" (carril): los dos caminan (tienen ruta y no llegaron) en el mismo eje de la grilla
// (ambos por a, o ambos por b, según su facing) y:
//   - en sentido contrario: carriles a 0 o 1 casilla (de frente o pasando al lado), y se acercan a
//     <= reach casillas, o ya están a <= 1 (justo cruzándose);
//   - en el mismo sentido: el mismo carril y a <= reach casillas; habla el que va atrás.
// Cada encuentro se sortea una sola vez (al empezar), con enfriamiento global y por pareja.
// Nunca durante una escena especial (world.special) ni un guion, salvo el paseo (script.kind "wander").
//
// Choques: el que camina y espera porque otro le tapa la próxima casilla (blockedFor) le dice algo y el
// otro contesta (BUMP), con enfriamiento por pareja (bump.cooldown).
//
// Sofá: sentados un rato en el living (couch.seats: el sofá y el sillón individual de Leonard), si hay uno
// solo dice algo para sí (SOLO; también en solo_seats, como la banqueta de Penny); si hay dos o tres, dos
// se hablan (COUCH). Sorteo cada couch.every s. En la van no hay sofá: couch.group "rest" usa los lugares de reposo.
//
// Trabajo: al llegar al lugar de su rol (pensar, pizarrón, compu, cómic, telescopio) dice algo de la tarea
// (WORK), y cada work.every s en el mismo lugar, otra con probabilidad work.again. Sheldon con la manta
// (uso alto) tiene las suyas (BLANKET). Al entrar saluda (ENTER) y alguien que ya estaba contesta (GREET).
// Nadie habla si otro tiene un globo a <= work.near casillas, para que no se pisen.

/** Líneas por pareja ordenada "quien habla>quien contesta": [frase, respuesta]. */
export const LINES = {
  "leonard>penny": [
    ["Hola, Penny... ¿todo bien?", "Hola, Leonard."],
    ["¡Penny! Qué casualidad...", "Vivo enfrente, Leonard."],
    ["Lindo... eh, lindo día, ¿no?", "Está nublado, Leonard."],
    ["¿Cenamos? Digo, si querés. O no.", "Si hay comida tailandesa, sí."],
    ["Te queda bien... todo.", "Ay, gracias. Creo."],
  ],
  "penny>leonard": [
    ["¡Ey, Leonard!", "¡Ey! Digo... hola, Penny."],
    ["¿Me pasás la clave del wifi?", "Ya la usás, Penny."],
    ["Linda remera.", "¿En serio? ¡Gracias!"],
    ["¿Sheldon anda de buen humor?", "Definí «buen humor»."],
    ["¿Queda algo en la heladera?", "Lo que trajiste vos el jueves."],
  ],
  "sheldon>leonard": [
    ["Leonard, estás en mi trayectoria.", "Sheldon, es un pasillo."],
    ["Caminás a 0,8 m/s. Ineficiente.", "Gracias por la auditoría."],
    ["Recordá: hoy es noche de Halo.", "Ya sé. Me lo dijiste 4 veces."],
    ["Cedé el paso: va la derecha.", "Eso no es una ley, Sheldon."],
    ["¡Bazinga!", "Ni siquiera dijiste nada."],
  ],
  "leonard>sheldon": [
    ["Permiso, Sheldon.", "Permiso denegado."],
    ["¿Me dejás pasar?", "Según el acuerdo, sí."],
    ["Sheldon, correte un poco.", "Correte vos: llegué primero."],
    ["¿Otra vez con el tren a escala?", "No es un juguete, Leonard."],
    ["¿Vamos a la tienda de cómics?", "Es miércoles. Obviamente."],
  ],
  "sheldon>penny": [
    ["Penny.", "Sheldon."],
    ["Toc, toc, toc. Penny.", "Estoy acá adelante, Sheldon."],
    ["Vas por mi lado del pasillo.", "El pasillo no tiene lados."],
    ["¿Sabías que el 85 % de...?", "No. Y no quiero saber."],
    ["¡Bazinga!", "¿Qué? Si no dije nada."],
  ],
  "penny>sheldon": [
    ["Hola, cariño.", "No soy tu cariño. Hola."],
    ["Sheldon, ¿un abrazo?", "Absolutamente no."],
    ["¿Qué hacés, raro?", "Física teórica. Lo de siempre."],
    ["¿Te hago una sopita?", "Solo si estoy enfermo. No lo estoy."],
    ["¡Bazinga!", "Esa es mía. Tiene derechos."],
  ],
  // Breaking Bad (la van)
  "walter>jesse": [
    ["Jesse. Tenemos que cocinar.", "¡Ya voy, viejo, la puta madre!"],
    ["Pureza 99,1 %. Ni un punto menos.", "Sí, sí. ¡Ciencia, bitch!"],
    ["Jesse, nada de Chili P.", "¡Es mi firma, viejo!"],
    ["¿Cómo abrimos el depósito?", "¡Imanes, bitch! ¡Imanes!"],
    ["¿Te lavaste las manos?", "Llevo guantes, yo. Relajá."],
    ["Pinkman. Hacé silencio.", "Ni hablé, Señor White."],
  ],
  "jesse>walter": [
    ["¡Yo, Señor White!", "No me digas «yo». Hola, Jesse."],
    ["¿Ya podemos cobrar, viejo?", "Cuando la pureza lo diga."],
    ["¿Pollos Hermanos? Muero de hambre.", "Ahí no. Nunca más."],
    ["¿Y si lo cortamos un poquito?", "Jamás. Nosotros no cortamos."],
    ["Viejo, usted me da miedo.", "Bien. Así funciona esto."],
  ],
  "walter>saul": [
    ["Saul. Necesito un abogado.", "No: un abogado *criminal*."],
    ["Decí mi nombre.", "¿Heisenberg? ¡Bajá la voz!"],
    ["¿Lavaste el dinero?", "Más limpio que tu pelada, Walt."],
    ["¿Cuánto me cobrás por esto?", "Para vos, el doble. Amistad."],
  ],
  "saul>walter": [
    ["Tengo un tipo para eso.", "Siempre tenés un tipo."],
    ["¿Y si te vas a Nebraska?", "No me voy a ningún lado."],
    ["Walt, bajá un cambio.", "Yo no bajo nada. Yo golpeo."],
    ["¿Y el lavadero de autos?", "Lo maneja Skyler. Ni preguntes."],
    ["¡Mejor llamá a Saul!", "Te estoy viendo, Saul."],
  ],
  "jesse>saul": [
    ["Saul, me debés guita, bitch.", "Son honorarios, Pinkman."],
    ["¿Sos abogado de verdad?", "Diploma de Samoa. Vale igual."],
    ["¿Dónde está mi plata, yo?", "En un lugar seguro. Confiá."],
    ["¿Y Huell? ¿Lo dejaste afuera?", "Huell no se mueve. Nunca."],
  ],
  "saul>jesse": [
    ["Pinkman, ¿qué hiciste ahora?", "¡Nada, yo! Fue Badger."],
    ["Ey, Captain Cook.", "No me digas así, viejo."],
    ["¿Otra vez con Badger y Skinny?", "Son buenos pibes, yo."],
    ["Te consigo un abogado: yo.", "¿Y cuánto me sale, bitch?"],
  ],
};

/** Sentado solo en el sofá: frases para sí mismo. */
export const SOLO = {
  sheldon: [
    "Mi lugar. El punto cero del universo.",
    "Suave gatito, cálido gatito...",
    "Wil Wheaton... ¡Wheaton!",
    "Teoría de cuerdas, día 1.462.",
    "Hoy toca comida tailandesa.",
    "Nadie tocó mi asiento. Bien.",
    "Hoy es día de pizza. Es ley.",
    "Mamá dice que soy especial. Lo soy.",
  ],
  leonard: [
    "¿Le escribo a Penny? No. ¿Sí? No.",
    "Un doctorado y no sé qué decirle.",
    "Mi inhalador... ¿dónde quedó?",
    "¿Sheldon cambió la clave del wifi?",
    "Mamá no llamó. Típico.",
    "Mi sillón. El único sin cláusula.",
    "Debería ir al gimnasio. Mañana.",
    "¿Y si me mudo? Sheldon me encuentra.",
  ],
  penny: [
    "¿Un pizarrón en el living? Ñoños.",
    "Uy, me terminé su vino.",
    "Su wifi anda mejor que el mío.",
    "Si Sheldon me ve acá, me mata.",
    "Turno doble en el Cheesecake. Ugh.",
    "¿Comida tailandesa otra vez? Dale.",
    "Mañana audición. ¡Esta es la mía!",
  ],
  walter: [
    "Yo soy el que golpea la puerta.",
    "No estoy en peligro. Soy el peligro.",
    "Decí mi nombre.",
    "Todo esto, por mi familia.",
    "Gray Matter... me robaron todo.",
    "Lo hice por mí. Me gustaba.",
    "Un hombre provee. Y punto.",
    "Química: el estudio del cambio.",
  ],
  jesse: [
    "Yeah, ciencia, bitch!",
    "Quiero un kart. O un láser tag.",
    "Badger me debe guita, yo.",
    "Cocinar con este viejo... uf.",
    "Otro pucho y arranco.",
    "Esta van huele a muerte, yo.",
    "Mr. White está re loco, bitch.",
  ],
  saul: [
    "S'all good, man.",
    "¿Huell? ¿Dónde se metió?",
    "El teléfono no para. Bien.",
    "El de las aspiradoras... por si acaso.",
    "Cinnabon en Omaha... ni loco.",
    "Hoy no me demanda nadie. Raro.",
    "Mi oficina tiene columnas. Clase.",
  ],
};

/** Dos en el sofá, "quien habla>quien contesta": [frase, respuesta]. */
export const COUCH = {
  "sheldon>leonard": [
    ["Estás en mi zona de respiración.", "Es un sofá, Sheldon."],
    ["¿Jugamos Klingon Boggle?", "Paso. Otra vez no."],
    ["Revisemos el acuerdo de convivencia.", "¿Ahora? Estoy cansado."],
    ["Tu codo invade la cláusula 14.", "Mi codo no firmó nada."],
    ["Mañana: simulacro de incendio.", "Sheldon, es domingo."],
  ],
  "leonard>sheldon": [
    ["¿Pedimos pizza?", "Hoy toca tailandés."],
    ["¿Podés correrte un poco?", "No. Estoy en mi lugar."],
    ["¿Vemos algo?", "Firefly. Y no opines."],
    ["Sheldon, me estás mirando.", "Estudio tu conducta social."],
    ["¿Y si te sentás en otro lado?", "Esa frase no tiene sentido."],
  ],
  "sheldon>penny": [
    ["Estás casi en mi lugar.", "Estoy al lado, Sheldon."],
    ["¿Querés aprender física?", "¿Va a doler?"],
    ["Tus papas hacen ruido.", "Son papas, cariño."],
    ["Te traigo una bebida caliente.", "¿Por? Si estoy bien."],
    ["Ese cojín es para visitas.", "Soy visita."],
  ],
  "penny>sheldon": [
    ["¿Me hacés lugar?", "Hay 45 cm. Los medí."],
    ["Cantame Suave Gatito.", "Solo si estás enferma."],
    ["¿Qué estás mirando?", "Doctor Who. No preguntes."],
    ["¿Me prestás la manta?", "La manta tiene dueño."],
    ["¿Sos feliz, Sheldon?", "Estoy en mi lugar. Sí."],
  ],
  "leonard>penny": [
    ["¿Querés... ver una peli?", "Si no es de superhéroes, sí."],
    ["¿Cómo te fue en el trabajo?", "Dos dólares de propina."],
    ["¿Más vino?", "Siempre."],
    ["Penny, lo nuestro... ¿qué es?", "Hoy no, Leonard."],
    ["Te queda lindo el pelo así.", "No hice nada. Gracias."],
  ],
  "penny>leonard": [
    ["¿Me masajeás los pies?", "¡Sí! Digo... si querés."],
    ["Explicame tu trabajo. Fácil.", "Es física... con láseres."],
    ["¿Sheldon ya se durmió?", "No duerme. Se recarga."],
    ["Te robé el wifi otra vez.", "Nunca dejaste de hacerlo."],
    ["Leonard, ¿hay comida?", "Sobras de tailandés."],
    ["¿Por qué Sheldon es así?", "Su mamá dice que lo testearon."],
    ["Ese sillón es tuyo, ¿no?", "El único lugar sin dueño: Sheldon."],
  ],
  "walter>jesse": [
    ["¿Sabés qué es la química?", "¿Lo que hacemos? ¿Cocinar?"],
    ["Hoy cocinamos 50 libras.", "¿50? ¿Está loco, viejo?"],
    ["No fumes adentro de la van.", "Es un pucho normal, yo."],
    ["Respetá la química, Jesse.", "La respeto. Re la respeto."],
  ],
  "jesse>walter": [
    ["¿Y si dejamos esto, viejo?", "Esto termina cuando yo diga."],
    ["¿Extraña dar clases?", "Ni un poco. Bueno... un poco."],
    ["Señor White, ¿somos amigos?", "Somos socios. Es mejor."],
    ["Me aburro. ¿Jugamos a algo?", "La química no es un juego."],
  ],
  "walter>saul": [
    ["¿Cuánto ganamos hoy?", "Neto, después de mi 5 %: mucho."],
    ["Necesito un auto nuevo.", "Tengo un tipo en el lavadero."],
  ],
  "saul>walter": [
    ["Walt, ¿te pongo en mi aviso?", "Ni en tus sueños, Saul."],
    ["¿Querés un abogado o un amigo?", "Un abogado. Barato."],
    ["Esto me recuerda a Cicero.", "No sé qué es Cicero, Saul."],
  ],
  "jesse>saul": [
    ["¿Me hacés un descuento?", "Sí: 10 % extra. Cariño."],
    ["Vos sos re turbio, viejo.", "Turbio no. Creativo."],
  ],
  "saul>jesse": [
    ["Chico, invertí en un lavadero.", "Prefiero un láser tag, yo."],
    ["¿Viste mi aviso en la tele?", "El de la Constitución inflable."],
  ],
};

/** Choque: "el que espera>el que tapa": [frase, respuesta]. */
export const BUMP = {
  "sheldon>leonard": [
    ["Leonard. Colisión inminente.", "Ya chocamos, Sheldon."],
    ["Esto viola la cláusula 9.", "Sheldon, es un choque."],
    ["Correte. Ahora. Por favor.", "Dijiste «por favor». Progreso."],
    ["Calculé mi ruta. La arruinaste.", "Rodeame, Sheldon."],
    ["¿Sos un fermión? Ocupás mi lugar.", "Ni entendí, pero perdón."],
  ],
  "sheldon>penny": [
    ["Penny. Penny. Penny.", "¡Ya me corro!"],
    ["Tu órbita choca con la mía.", "¿Qué? Pasá, raro."],
    ["No me toques. Gérmenes.", "Ni te toqué, Sheldon."],
    ["Estás en mi espacio personal.", "Tu espacio es todo el depto."],
    ["Penny, eso fue un choque.", "Y esto un «perdón». Andá."],
  ],
  "leonard>sheldon": [
    ["Permiso... ¿Sheldon?", "No. Llegué primero."],
    ["Sheldon, correte, por favor.", "Recalculando... no."],
    ["¿Podés no frenar en el medio?", "Estoy pensando. Esperá."],
    ["Sheldon, me estás bloqueando.", "Vos me estás apurando."],
  ],
  "leonard>penny": [
    ["¡Perdón! Perdón, Penny.", "Tranqui, Leonard."],
    ["Ups. Hola. Perdón. Hola.", "Hola, Leonard. Respirá."],
    ["Pasá vos. Las damas primero.", "Qué caballero."],
    ["Choqué con vos. Literal.", "Sí, me di cuenta, cielo."],
  ],
  "penny>sheldon": [
    ["Permiso, cariño.", "No soy tu cariño. Pasá."],
    ["Sheldon, correte.", "Estás en MI pasillo."],
    ["¿Me dejás pasar, raro?", "Tras el debido protocolo."],
    ["¡Ey! ¡Casi me pisás!", "Casi. No hay contacto, no hay falta."],
  ],
  "penny>leonard": [
    ["Ay, Leonard, ¡perdón!", "¡No, perdón yo! Digo..."],
    ["Correte, enano. Es chiste.", "Ja. Ja. Muy graciosa."],
    ["Choque y fuga, Leonard.", "Te denuncio al edificio."],
    ["¿Me estás siguiendo?", "¡No! Bueno... un poco."],
  ],
  "walter>jesse": [
    ["Jesse. Estás en mi camino.", "Uy, perdón, Señor White."],
    ["Correte, imbécil.", "¡Tranqui, viejo! ¡Ya voy!"],
    ["Jesse, despejá el área.", "¿Qué área? ¡Es una van!"],
    ["No me toques el matraz.", "Ni lo toqué, yo."],
    ["Pisá con cuidado, Jesse.", "Ok, ok... qué intenso, bitch."],
  ],
  "jesse>walter": [
    ["¡Yo! ¿Me deja pasar?", "Cuando dejes de decir «yo»."],
    ["¡Viejo, casi tiro todo!", "Casi. Por eso cocino yo."],
    ["Correte, Heisenberg, bitch.", "Cuidado, Jesse. Pisá despacio."],
    ["¡La concha de...! ¡Me pisó!", "Fue un accidente. Seguí."],
  ],
  "walter>saul": [
    ["Saul. Afuera.", "Ok, ok. No toques el traje."],
    ["Correte, Goodman.", "Con gusto. Factura aparte."],
  ],
  "saul>walter": [
    ["¡Walt! Me arrugás el traje.", "Es un traje feo, Saul."],
    ["Permiso, cliente estrella.", "No soy tu cliente estrella."],
    ["Ojo, que esto es demanda.", "Demandame. Te pago yo."],
  ],
  "jesse>saul": [
    ["¡Correte, Saul, bitch!", "Esto te sale 50 dólares."],
    ["¡Yo! Me pisaste.", "Te recomiendo un abogado."],
  ],
  "saul>jesse": [
    ["Pinkman, ojo con el traje.", "Ese traje es horrible, yo."],
    ["Ey, chico, abrime paso.", "¿Y qué gano yo, viejo?"],
    ["Esto se arregla con plata.", "Todo con vos es plata."],
  ],
};

/** Al llegar al lugar de su rol (y de vez en cuando mientras sigue ahí): personaje > rol > frases. */
export const WORK = {
  sheldon: {
    think: [
      "Hmm... interesante. Muy interesante.",
      "Necesito más datos. Y silencio.",
      "Esto requiere mi mente superior.",
      "Si fuera fácil, lo haría Leonard.",
      "Pensando. No respiren tan fuerte.",
    ],
    edit: [
      "Corrijo un error. No mío, claro.",
      "Ecuaciones: el idioma del universo.",
      "Así. Elegante. Como yo.",
      "Kripke jamás escribiría esto.",
      "Una línea más y llega el Nobel.",
    ],
    shell: [
      "Comando ejecutado. Con precisión.",
      "Mi computadora. Mi silla. Orden.",
      "Compilando... no me interrumpan.",
      "Si falla, es culpa del hardware.",
      "Terminal: mi otro lugar favorito.",
    ],
    read: [
      "Flash número 123. Primera edición.",
      "Este dibujante no sabe física.",
      "No es un cómic: es investigación.",
      "Batman no podría hacer esto.",
    ],
    web: [
      "Wikipedia se equivoca. Otra vez.",
      "Internet: 90 % gatos, 10 % datos.",
      "Confirmando que tengo razón...",
      "Ah. Tenía razón. Como siempre.",
    ],
  },
  leonard: {
    think: [
      "Ok, a ver... Leonard, pensá.",
      "Física experimental: probar y rezar.",
      "Si Sheldon ve esto, me mata.",
      "Respirá. Es solo un bug.",
    ],
    edit: [
      "Arreglado. Antes que Sheldon.",
      "No es elegante, pero anda.",
      "Un parche más... y listo.",
      "El pizarrón también es mío, eh.",
    ],
    shell: [
      "Corriendo el experimento...",
      "Por favor que compile. Por favor.",
      "OmniRoute, no me falles ahora.",
      "Mi silla, mi compu. Por fin.",
      "Láseres y terminales. Mi vida.",
    ],
    read: [
      "Este cómic es mío, Sheldon.",
      "Linterna Verde le gana a Aquaman.",
      "Leo tranquilo. Por una vez.",
    ],
    web: [
      "Calibrando el telescopio...",
      "Stack Overflow, salvame.",
      "Buscando... sin que Sheldon vea.",
      "Datos nuevos. ¡Funciona!",
    ],
  },
  penny: {
    think: [
      "Ok... ¿qué era esto?",
      "Pensar me da sed. ¿Hay vino?",
      "Ni idea, pero sonrío.",
      "Cariño, ¿cómo se hace esto?",
    ],
    edit: [
      "Le dibujo un bigote a Einstein.",
      "¿Esto es física o arte moderno?",
      "Sheldon va a odiar esto.",
      "Escribo... bueno, con el celu.",
    ],
    shell: [
      "Uso tu compu, Leonard. Gracias.",
      "Tecleo rápido. Con dos dedos.",
      "Comando enviado. Creo.",
      "Más fácil que el Cheesecake.",
      "La clave era «Penny es linda».",
    ],
    read: [
      "Horóscopo: hoy hago física. Ja.",
      "«Diez tips para entender a Sheldon».",
      "Shh, estoy leyendo... las fotos.",
    ],
    web: [
      "¿Este telescopio ve mi casa?",
      "Busco zapatos. Digo... datos.",
      "Wow, la luna. ¡Hola, luna!",
      "¿Hay wifi en el espacio?",
    ],
  },
  walter: {
    shell: [
      "No es cocinar. Es química.",
      "Respeten la química.",
      "Pureza: 99,1 %. Azul.",
      "Mi producto es el mejor. Punto.",
      "Temperatura justa. Como siempre.",
    ],
    edit: [
      "Anoto la reacción. Precisa.",
      "Un error y volamos todos.",
      "Notas de laboratorio. En orden.",
      "Gray Matter era mío también.",
    ],
    read: [
      "Whitman. «Para mi otro W. W.»",
      "Metilamina: alcanza. Por ahora.",
      "Revisando el inventario...",
      "Hojas de hierba... hermoso.",
    ],
    think: [
      "Necesito más metilamina.",
      "Si Gus sospecha... no.",
      "Sin medias tintas.",
      "¿Ricina? No. Todavía no.",
      "Pensá, Walter. Pensá.",
    ],
    web: [
      "¿Esa es la DEA? ¿Hank?",
      "Solo desierto. Bien.",
      "Ese auto otra vez...",
      "Nadie nos vio. Creo.",
    ],
  },
  jesse: {
    shell: [
      "¡Yeah, ciencia, bitch!",
      "Un toque de Chili P...",
      "Sale re azul, yo.",
      "¡Sí, Señor White! ¡Sí, ciencia!",
      "¿Esto va a explotar? No, ¿no?",
    ],
    edit: [
      "Dibujo un cómic. Re copado.",
      "Pinkman: rey de los apuntes.",
      "¿Esto lleva tilde? Bah.",
    ],
    read: [
      "¿Qué dice acá? Letra chica, uf.",
      "Manual de química... zzz.",
      "El viejo subraya todo, yo.",
    ],
    think: [
      "Ok, yo... ¿y ahora qué?",
      "Pensá, Pinkman. Pensá, bitch.",
      "¿Y si nos agarran? No, no.",
    ],
    web: [
      "¡Cuidado! ¿Es la DEA?",
      "Ahí afuera... ¿Tuco? Uf.",
      "Desierto y más desierto, yo.",
    ],
  },
  saul: {
    shell: [
      "¿Hola? Saul Goodman, diga.",
      "No, señora: ese es otro abogado.",
      "Francesca, cancelá todo.",
      "¿Huell? Traé el auto.",
      "Se lo cobro por minuto. Diga.",
    ],
    edit: [
      "Un contrato... sin letra chica.",
      "Firmá acá, acá y acá.",
      "Esto es 100 % legal. Casi.",
    ],
    read: [
      "El código penal: mi Biblia.",
      "Precedentes... tengo un tipo.",
      "Leer es caro. Cobro por hora.",
    ],
    think: [
      "¿Y si es fraude?... Me sirve.",
      "Tengo un plan. Siempre tengo.",
      "¿Y si la culpa es de otro?",
    ],
    web: [
      "Ese auto... ¿Mike?",
      "Si viene la DEA, yo no estuve.",
      "Linda vista. Sin testigos.",
    ],
  },
};

/** Sheldon con la manta y la notebook (uso alto de Claude). */
export const BLANKET = {
  sheldon: [
    "Esfuerzo máximo. No molestar.",
    "Modo manta: activado.",
    "Suave gatito... compilando...",
    "Cálido gatito... bola de código.",
    "Ni Penny me saca de acá.",
    "Mi lugar, mi manta, mi código.",
  ],
};

/** Al entrar (ya visible del todo). */
export const ENTER = {
  sheldon: [
    "Hola. Nadie toque mi lugar.",
    "Toc toc toc... ah, es mi casa.",
    "Llegué. Que empiece la ciencia.",
    "Saludos, gente de menor CI.",
  ],
  leonard: [
    "Hola, chicos. Volví.",
    "Cuatro pisos. El ascensor...",
    "Llegué. ¿Hay comida?",
    "Sheldon, no toqué tu lugar.",
  ],
  penny: [
    "¡Hola, chicos!",
    "¿Qué hay de comer?",
    "Vengo a robar wifi. Hola.",
    "Toc toc. Ah no, eso es de Sheldon.",
  ],
  walter: [
    "Jesse, tenemos que cocinar.",
    "Yo soy el que golpea la puerta.",
    "Llegó Heisenberg.",
    "A trabajar. Ahora.",
  ],
  jesse: [
    "¡Yo! ¿Qué onda, bitch?",
    "Llegó Pinkman, yo.",
    "¿Ya se cocina? Uf.",
    "¡Yeah! A cocinar, bitch.",
  ],
  saul: [
    "¡Mejor llamen a Saul!",
    "Hola, hola. ¿Quién me necesita?",
    "Saul Goodman, a su servicio.",
    "¿Cómo están mis clientes?",
  ],
};

/** Quien ya estaba contesta al que entra: "quien contesta>quien entra". */
export const GREET = {
  "sheldon>leonard": ["Llegás 3 minutos tarde.", "Leonard. Limpiate los pies."],
  "sheldon>penny": ["Penny. No golpeaste.", "¿Viniste por comida o wifi?"],
  "leonard>sheldon": ["Hola, Sheldon.", "Ah, volvió el genio."],
  "leonard>penny": ["¡Penny! Hola. Hola... hola.", "¡Hola! Estás... linda. Hola."],
  "penny>sheldon": ["¡Hola, cariño!", "Hola, Shelly."],
  "penny>leonard": ["¡Hola, Leonard!", "Ey, ¿traés comida?"],
  "walter>jesse": ["Llegás tarde, Jesse.", "Jesse. Ponete el traje."],
  "walter>saul": ["Saul. ¿Qué querés ahora?", "Nadie te llamó, Saul."],
  "jesse>walter": ["¡Yo, Señor White!", "Ah, llegó el jefe. Genial."],
  "jesse>saul": ["¡Ey, Saul! ¿Y mi plata?", "Llegó el abogado trucho, yo."],
  "saul>walter": ["¡Walt! Mi cliente favorito.", "Heisenberg. Qué honor."],
  "saul>jesse": ["Pinkman, ¡qué sorpresa!", "Ey, chico. ¿Todo legal?"],
};

/** Al entrar sin nadie en el living: un comentario, no un saludo (y no saluda con la mano). */
export const ENTER_ALONE = {
  sheldon: [
    "Living vacío. Óptimo.",
    "Silencio. Por fin.",
    "Nadie en mi lugar. Bien.",
    "Ciencia sin público. Ideal.",
  ],
  leonard: [
    "¿Sheldon? ¿Penny? ...Nadie.",
    "Paz. Disfrutala, Leonard.",
    "Silencio. Raro en esta casa.",
    "Nadie. Mi sillón me espera.",
  ],
  penny: [
    "¿Nadie? Bueno, el wifi sí.",
    "Uy, ¿y los chicos?",
    "Vacío. Me sirvo vino.",
    "Ni Sheldon. Qué raro.",
  ],
  walter: [
    "Nadie. Mejor.",
    "La van vacía. Silencio.",
    "¿Jesse? Siempre tarde.",
    "Solo yo y la química.",
  ],
  jesse: [
    "¿Señor White? ...Nadie.",
    "Solo en la van. Re tranqui.",
    "¿Y el viejo? Mejor, yo.",
  ],
  saul: [
    "¿Nadie? Cobro igual.",
    "Vacío. Hora de facturar.",
    "¿Dónde están mis clientes?",
  ],
};

/** Al irse (en la puerta, saludando con la mano) si queda alguien. */
export const LEAVE = {
  sheldon: [
    "Me voy. No toquen nada.",
    "Adiós. Mi lugar sigue siendo mío.",
    "Me retiro. Fue... tolerable.",
    "Hasta luego. ¡Bazinga!",
  ],
  leonard: [
    "Me voy, chicos. ¡Chau!",
    "Chau. Sheldon, portate bien.",
    "Me voy antes de que hable Sheldon.",
    "Chau. Si llama mi mamá, no estoy.",
  ],
  penny: [
    "¡Chau, chicos!",
    "Me voy. Gracias por el wifi.",
    "Me voy al Cheesecake. ¡Chau!",
    "Chau, cerebritos.",
  ],
  walter: [
    "Me voy. Nadie toque nada.",
    "Me voy. Jesse, limpiá.",
    "Me voy a casa. Con mi familia.",
    "Mañana, a las 8. Puntuales.",
  ],
  jesse: [
    "Me voy, yo. ¡Chau!",
    "Me tomo el palo, bitch.",
    "Chau, viejo. Mañana sigo.",
  ],
  saul: [
    "Me voy, tengo un juicio.",
    "Chau. La factura llega mañana.",
    "¡Mejor llamen a Saul! Chau.",
    "Me voy, Huell me espera.",
  ],
};

/** Los que quedan despiden al que se va: "quien contesta>quien se va". */
export const BYE = {
  "sheldon>leonard": ["Adiós. Llevate la basura.", "Chau. Volvé en horario."],
  "sheldon>penny": ["Adiós, Penny. Devolvé el wifi.", "Chau. Golpeá al volver."],
  "leonard>sheldon": ["Chau, Sheldon.", "Por fin... digo, ¡chau!"],
  "leonard>penny": ["¡Chau, Penny! Chau... chau.", "¡Chau! ¿Mañana venís?"],
  "penny>sheldon": ["¡Chau, cariño!", "Chau, Shelly."],
  "penny>leonard": ["¡Chau, Leonard!", "Chau, cielo. Cuidate."],
  "walter>jesse": ["Andá. Mañana a las 8.", "Chau. No hagas idioteces."],
  "walter>saul": ["Por fin.", "Chau, Saul. Esto no se cobra."],
  "jesse>walter": ["Chau, Señor White.", "¡Chau, viejo!"],
  "jesse>saul": ["Chau, abogado trucho.", "¡Chau, Saul, bitch!"],
  "saul>walter": ["Chau, Walt. Pagá a tiempo.", "Cuidate, Heisenberg."],
  "saul>jesse": ["Chau, chico. Nada de líos.", "Portate bien, Pinkman."],
};

/** Al irse sin nadie en el living: un comentario para sí. */
export const LEAVE_ALONE = {
  sheldon: [
    "Apago todo. Ahorro energía.",
    "Me voy. El living queda en orden.",
    "Nadie a quien despedir. Eficiente.",
  ],
  leonard: [
    "Bueno, me voy. Nadie me oye.",
    "Chau, living. Chau, sillón.",
    "Me voy. Ni Sheldon para quejarse.",
  ],
  penny: [
    "Me llevo una cerveza. Nadie ve.",
    "Me voy. Ni se van a enterar.",
    "Chau, departamento de nerds.",
  ],
  walter: [
    "Apago el mechero. Me voy.",
    "Me voy. Todo limpio.",
    "Nadie. Mejor así.",
  ],
  jesse: [
    "Chau, van. Te quiero, yo.",
    "Me voy antes que venga el viejo.",
    "Nadie me ve. Me llevo un poco.",
  ],
  saul: [
    "Me voy. Facturo igual.",
    "Nadie me despide. Típico.",
    "Saul abandonó el edificio.",
  ],
};

const DEFAULTS = { chance: 0.6, cooldown: 30, pair_cooldown: 75, seconds: 2.6, reply_after: 1.2, reach: 2 };
const COUCH_DEFAULTS = { group: "couch", every: 15, chance: 0.35, cooldown: 60, solo_cooldown: 120, settle: 8,
                         seats: ["armchair"], solo_seats: ["kitchen_stool"] };
const BUMP_DEFAULTS = { chance: 0.9, after: 0.3, cooldown: 25 };
const WORK_DEFAULTS = { chance: 0.75, delay: 1, cooldown: 10, every: 30, again: 0.5, near: 4, greet: 0.8, greet_within: 6 };
const WORK_ROLES = ["think", "edit", "shell", "read", "web"];
// world -> {next, pairs: {par: hora}, near: Set, pending: [], couch: hora, solo: {quien: hora},
//           work: {quien: {at, said, next, saidAt}}, greeted: Set, entered: {quien: hora}, last: {lista: última frase}}
const state = new WeakMap();

/** Puede charlar: está, se ve entero, camina y no está en una escena (salvo el paseo). */
function walking(c) {
  if (!c.present || c.alpha < 1 || c.fadeDir || c.costume) return false;
  if (c.script && c.script.kind !== "wander") return false;
  return !c.arrived && (c.step || c.route?.length);
}

/** Sentado en el sofá hace al menos settle s, entero, sin guion, sin globo y sin irse. */
function seated(c, couch, now, settle) {
  if (!c.present || c.alpha < 1 || c.fadeDir || c.costume || c.script || c.leaving || c.say) return false;
  return c.arrived && !c.step && couch.includes(c.targetKey) && now - c.arrivedAt >= settle;
}

/** Posición continua en casillas (a, b): a mitad de un paso cuenta la fracción recorrida. */
function pos(c) {
  const s = c.step;
  if (!s) return c.tile;
  return [0, 1].map((i) => s.fromTile[i] + (s.to[i] - s.fromTile[i]) * s.p);
}

/** Si x e y se cruzan en el mismo carril: null, o {speaker, other} (speaker null: cualquiera). */
export function crossing(x, y, grid, reach) {
  const dx = grid.facings[x.facing].step, dy = grid.facings[y.facing].step;
  const ax = dx[0] !== 0 ? 0 : 1;
  if ((dy[0] !== 0 ? 0 : 1) !== ax) return null;    // ejes distintos: se cruzan en cruz, no en carril
  const px = pos(x), py = pos(y);
  const li = 1 - ax;
  const gap = Math.abs(px[li] - py[li]);
  const along = py[ax] - px[ax];                     // cuánto adelante de x está y, sobre el eje
  if (dx[ax] !== dy[ax]) {
    if (gap > 1.01) return null;
    const closing = along * dx[ax] > 0;
    return (closing && Math.abs(along) <= reach) || Math.abs(along) <= 1 ? { speaker: null } : null;
  }
  if (gap > 0.01 || Math.abs(along) > reach) return null;
  return along * dx[ax] > 0 ? { speaker: x, other: y } : { speaker: y, other: x };
}

/** Facing más cercano para mirar de una casilla a otra (pasos de la grilla). */
function facingToward(grid, from, to) {
  const d = [to[0] - from[0], to[1] - from[1]];
  let best = null, bestDot = -Infinity;
  for (const [name, f] of Object.entries(grid.facings)) {
    const dot = f.step[0] * d[0] + f.step[1] * d[1];
    if (dot > bestDot) [best, bestDot] = [name, dot];
  }
  return best;
}

/** Una al azar, sin repetir la última que dijo (o contestó) ese personaje en esa lista. */
function pick(pool, rand, st, tag) {
  if (pool.length < 2) return pool[0];
  let i = Math.floor(rand() * pool.length);
  if (pool[i] === st.last[tag]) i = (i + 1) % pool.length;
  return (st.last[tag] = pool[i]);
}

/** Alguien más tiene un globo (o una respuesta en camino) a <= r casillas: mejor no pisarlo. */
function crowded(world, st, c, r) {
  if (st.pending.some((p) => p.to === c || p.who === c)) return true;
  return world.chars.some((o) => o !== c && o.present && o.say
    && Math.abs(o.tile[0] - c.tile[0]) + Math.abs(o.tile[1] - c.tile[1]) <= r);
}

/** Libre para hablar solo: entero, sin globo, sin disfraz y sin guion (salvo el paseo). */
function free(c) {
  return c.present && c.alpha >= 1 && !c.fadeDir && !c.costume && !c.say && !c.leaving
    && (!c.script || c.script.kind === "wander");
}

/** Un cuadro: respuestas pendientes y búsqueda de cruces nuevos. Se llama después de mover a todos. */
function getState(world) {
  let st = state.get(world);
  if (!st) state.set(world, (st = { next: 0, pairs: {}, near: new Set(), pending: [], couch: 0, solo: {},
                                    work: {}, greeted: new Set(), entered: {}, last: {} }));
  return st;
}

/**
 * Entrada o salida por la puerta (character.js, kind "enter" | "leave"): con alguien en el living saluda
 * (ENTER / LEAVE) y todos los demás le contestan de a uno (GREET / BYE); solo, un comentario (ENTER_ALONE /
 * LEAVE_ALONE). Siempre habla, aunque haya otro globo cerca. Devuelve si había alguien (para saludar con la mano).
 */
export function greetTalk(world, c, kind, rand = Math.random) {
  const cfg = { ...DEFAULTS, ...(world.config.chatter || {}) };
  const others = world.chars.filter((o) => o !== c && o.present && !o.leaving && o.alpha > 0);
  if (cfg.enabled === false) return others.length > 0;
  const st = getState(world);
  const now = world.now;
  st.greeted.add(c.id);   // workTalk ya no lo saluda otra vez
  const [lines, alone, replies] = kind === "enter" ? [ENTER, ENTER_ALONE, GREET] : [LEAVE, LEAVE_ALONE, BYE];
  const pool = others.length ? lines[c.id] : alone[c.id];
  if (pool) {
    c.say = { text: pick(pool, rand, st, `${kind}:${others.length ? "" : "alone:"}${c.id}`), until: now + cfg.seconds };
    st.work[c.id] = { ...(st.work[c.id] || { at: null, said: true, next: 0 }), saidAt: now };
  }
  others.filter((o) => replies[`${o.id}>${c.id}`]).forEach((o, i) => {
    // Uno atrás del otro; si el que contesta está ocupado (otro globo), espera hasta reply_wait s
    const at = now + cfg.reply_after + i * cfg.seconds * 0.7;
    st.pending.push({ who: o, to: c, text: pick(replies[`${o.id}>${c.id}`], rand, st, `${kind}:${o.id}>${c.id}`),
                      at, until: at + (cfg.reply_wait ?? 4), face: !world.isSeat(o.targetKey) });
  });
  return others.length > 0;
}

export function chatter(world, rand = Math.random) {
  const cfg = { ...DEFAULTS, ...(world.config.chatter || {}) };
  if (cfg.enabled === false) return;
  const st = getState(world);
  const now = world.now;
  if (world.special) {
    st.pending = [];
    st.near.clear();
    return;
  }

  // Respuestas: si quien contesta sigue libre (sin globo, sin escena), contesta y mira al otro si está quieto
  st.pending = st.pending.filter((r) => {
    if (now < r.at) return true;
    const c = r.who;
    if (c.present && !c.say && (!c.script || c.script.kind === "wander")) {
      c.say = { text: r.text, until: now + cfg.seconds };
      if (r.face !== false && !c.step && !c.script && r.to.present) {
        const f = facingToward(world.grid, c.tile, r.to.tile);
        if (f) c.facing = f;
      }
      return false;
    }
    return c.present && r.until !== undefined && now < r.until;   // ocupado: los saludos esperan un poco
  });

  const chars = world.chars;
  const near = new Set();
  for (let i = 0; i < chars.length; i++) {
    for (let j = i + 1; j < chars.length; j++) {
      const x = chars[i], y = chars[j];
      if (!walking(x) || !walking(y)) continue;
      const hit = crossing(x, y, world.grid, cfg.reach);
      if (!hit) continue;
      const pair = [x.id, y.id].sort().join("+");
      near.add(pair);
      if (st.near.has(pair)) continue;               // el mismo encuentro: ya se sorteó
      if (now < st.next || now < (st.pairs[pair] ?? 0) || x.say || y.say || st.pending.length) continue;
      if (rand() >= cfg.chance) continue;
      let [a, b] = hit.speaker ? [hit.speaker, hit.other] : rand() < 0.5 ? [x, y] : [y, x];
      if (!LINES[`${a.id}>${b.id}`]) [a, b] = [b, a];
      const pool = LINES[`${a.id}>${b.id}`];
      if (!pool) continue;
      const [line, reply] = pick(pool, rand, st, `cross:${a.id}>${b.id}`);
      a.say = { text: line, until: now + cfg.seconds };
      st.pending.push({ who: b, to: a, text: reply, at: now + cfg.reply_after });
      st.next = now + cfg.cooldown;
      st.pairs[pair] = now + cfg.pair_cooldown;
    }
  }
  st.near = near;
  bumpTalk(world, st, cfg, rand);
  couchTalk(world, st, cfg, rand);
  workTalk(world, st, cfg, rand);
}

/** Choque: quien lleva bump.after s esperando porque otro le tapa la próxima casilla le habla. */
function bumpTalk(world, st, cfg, rand) {
  const bc = { ...BUMP_DEFAULTS, ...(cfg.bump || {}) };
  const now = world.now;
  if (bc.enabled === false || st.pending.length) return;
  for (const a of world.chars) {
    if (!walking(a) || a.say || a.blockedFor < bc.after || !a.route?.length) continue;
    const [t0, t1] = a.route[0];
    const b = world.chars.find((o) => o !== a && o.present && !o.costume
      && ((o.tile[0] === t0 && o.tile[1] === t1) || (o.step && o.step.to[0] === t0 && o.step.to[1] === t1)));
    const pool = b && BUMP[`${a.id}>${b.id}`];
    if (!pool || b.say) continue;
    const pair = `bump:${[a.id, b.id].sort().join("+")}`;
    if (now < (st.pairs[pair] ?? 0)) continue;
    st.pairs[pair] = now + bc.cooldown;              // se sortea una vez por choque
    if (rand() >= bc.chance) continue;
    const [line, reply] = pick(pool, rand, st, `bump:${a.id}>${b.id}`);
    a.say = { text: line, until: now + cfg.seconds };
    st.pending.push({ who: b, to: a, text: reply, at: now + cfg.reply_after, face: !b.arrived || !world.isSeat(b.targetKey) });
    return;
  }
}

/** Living: uno solo habla para sí, dos (o tres) se hablan. Cuenta el sillón individual de Leonard. */
function couchTalk(world, st, cfg, rand) {
  const cc = { ...COUCH_DEFAULTS, ...(cfg.couch || {}) };
  const couch = world.b.seats?.[cc.group];
  const now = world.now;
  if (cc.enabled === false || !couch || now < st.couch || st.pending.length) return;
  st.couch = now + cc.every;
  const lounge = [...couch, ...cc.seats];
  const soloSeats = [...lounge, ...cc.solo_seats];
  const inLounge = world.chars.filter((c) => c.present && lounge.includes(c.targetKey)).length;
  const near = (c) => !crowded(world, st, c, (cfg.work?.near ?? WORK_DEFAULTS.near));   // sin pisar otra escena
  const sat = world.chars.filter((c) => seated(c, lounge, now, cc.settle) && near(c));
  if (rand() >= cc.chance) return;
  if (sat.length >= 2) {
    const i = Math.floor(rand() * sat.length);
    const j = (i + 1 + Math.floor(rand() * (sat.length - 1))) % sat.length;
    let [a, b] = [sat[i], sat[j]];
    if (!COUCH[`${a.id}>${b.id}`]) [a, b] = [b, a];
    const pool = COUCH[`${a.id}>${b.id}`];
    if (!pool) return;
    const [line, reply] = pick(pool, rand, st, `couch:${a.id}>${b.id}`);
    a.say = { text: line, until: now + cfg.seconds };
    st.pending.push({ who: b, to: a, text: reply, at: now + cfg.reply_after, face: false });
    st.couch = now + cc.cooldown;
    return;
  }
  // Solo: el único del living, o alguien sentado aparte (la banqueta) con el living vacío o lejos
  const alone = world.chars.filter((c) => seated(c, soloSeats, now, cc.settle) && SOLO[c.id] && near(c)
    && now >= (st.solo[c.id] ?? 0) && (lounge.includes(c.targetKey) ? inLounge === 1 : true));
  if (!alone.length) return;
  const a = alone[Math.floor(rand() * alone.length)];
  a.say = { text: pick(SOLO[a.id], rand, st, `solo:${a.id}`), until: now + cfg.seconds };
  st.solo[a.id] = now + cc.solo_cooldown;
  st.couch = now + cc.cooldown;
}

/** Trabajo, manta y entrada: cada uno comenta lo que está haciendo; al que entra lo saludan. */
function workTalk(world, st, cfg, rand) {
  const wc = { ...WORK_DEFAULTS, ...(cfg.work || {}) };
  const now = world.now;
  if (wc.enabled === false) return;
  for (const c of world.chars) {
    if (!c.present) {
      st.greeted.delete(c.id);   // la próxima vez que entre vuelve a saludar
      delete st.entered[c.id];
      continue;
    }
    st.entered[c.id] ??= now;
    const w = st.work[c.id] ??= { at: null, said: true, next: 0, saidAt: -Infinity };

    // Manta (uso alto): es un guion, pero puede hablar desde el sillón
    if (c.blanketOn && c.anim === "blanket_type" && BLANKET[c.id] && !c.say) {
      if (now >= w.next && !crowded(world, st, c, wc.near)) {
        w.next = now + wc.every * 0.6;
        if (rand() < wc.again + 0.2) c.say = { text: pick(BLANKET[c.id], rand, st, `blanket:${c.id}`), until: now + cfg.seconds };
      }
      continue;
    }
    if (!free(c) || c.script) continue;

    // Entró: saluda una vez en sus primeros greet_within s (si no, ya no), y alguien que ya estaba contesta
    if (!st.greeted.has(c.id)) {
      st.greeted.add(c.id);
      if (ENTER[c.id] && now - st.entered[c.id] <= wc.greet_within && rand() < wc.greet && !crowded(world, st, c, wc.near)) {
        c.say = { text: pick(ENTER[c.id], rand, st, `enter:${c.id}`), until: now + cfg.seconds };
        w.saidAt = now;
        const others = world.chars.filter((o) => o !== c && free(o) && !o.script && GREET[`${o.id}>${c.id}`]);
        if (others.length) {
          const o = others[Math.floor(rand() * others.length)];
          st.pending.push({ who: o, to: c, text: pick(GREET[`${o.id}>${c.id}`], rand, st, `greet:${o.id}>${c.id}`),
                            at: now + cfg.reply_after, face: !world.isSeat(o.targetKey) });
        }
        continue;
      }
    }

    // Llegó al lugar de su rol: una frase de la tarea; después, de vez en cuando otra
    const role = c.targetRole;
    const pool = WORK[c.id]?.[role];
    if (!pool || !c.arrived || c.step || c.displaced || c.targetKey?.startsWith("@") || !WORK_ROLES.includes(role)) continue;
    const stay = `${c.targetKey}:${role}:${c.arrivedAt}`;
    if (w.at !== stay) [w.at, w.said] = [stay, false];
    const first = !w.said;
    // La primera: a delay s de llegar y a cooldown s de su última frase; las demás, cada every s
    if (now - c.arrivedAt < wc.delay || now < (first ? w.saidAt + wc.cooldown : w.next)) continue;
    if (crowded(world, st, c, wc.near)) continue;
    w.said = true;
    w.next = now + wc.every;
    if (rand() < (first ? wc.chance : wc.again)) {
      c.say = { text: pick(pool, rand, st, `work:${c.id}`), until: now + cfg.seconds };
      w.saidAt = now;
    }
  }
}
