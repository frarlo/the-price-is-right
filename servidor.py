# Lógica de la parte servidor #
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP
from pathlib import Path
import socket, sys, threading, random

# Inicializamos la variable global de la clave privada del servidor:
clave_privada_servidor = None
clave_publica_cliente = None

# Constructor de partidas:
class hilo_Partida(threading.Thread):         
    # Init:                                                              
    def __init__(self, nombre_jugador, socket_atiende, addr_cliente):
        super().__init__()
        # Inicializamos las variables de la clase de nombre de jugador, de socket y de si la instancia debe cerrarse (ahora no)
        self.nombre_jugador = nombre_jugador
        self.socket_atiende = socket_atiende
        self.addr_cliente = addr_cliente
        self.cerrar_instancia = False
        self.juegos_totales = 0                                         # Creamos una variable para saber cuántos juegos ha jugado el usuario y luego mostrarlo.
        self.resultados_partidas = []                                   # Creamos una variable en forma de lista para guardar la información de cada partida.
        self.cifrador_RSA = PKCS1_OAEP.new(clave_publica_cliente)       # Cada hilo de partida tiene su propio cifrador con la clave publica del cliente.
        self.descifrador_RSA = PKCS1_OAEP.new(clave_privada_servidor)   # Cada hilo de partida tiene su propio descifrador con la clave privada del propio servidor

    # Run:                                    
    def run(self):                              
        # Mensaje de depuración que nos comunica que se ha comunicado un jugador con X nombre:
        print(f"Conexión exitosa con el cliente {self.nombre_jugador} desde {self.addr_cliente}.")
        # Mientras el valor de cerrar instancia no sea False:
        while not self.cerrar_instancia:
            # Seguirá jugando
            self.jugar()
    
    # Función para enviar mensajes al cliente:
    def enviar_mensaje(self, mensaje):
        try:
            # Encriptamos:
            mensaje_encriptado = self.encriptar_mensaje(mensaje)
            # Lo enviamos:
            self.socket_atiende.sendall(mensaje_encriptado)
        # Manejamos la excepción de que el usuario cierre la comunicación sin previo aviso:
        except BrokenPipeError:
            # Mensaje de depuración:
            print("El mensaje no se pudo entregar ya que el cliente cerró.")
            # Ya que se ha cortado la conexión, cerramos conexión del socket:
            socket_atiende.close()
            self.cerrar_instancia = True

    # Función para recibir mensajes del cliente:
    def recibir_mensaje(self):
        # Recibe un mensaje el mensaje encriptado desde el cliente:
        mensaje_cifrado = self.socket_atiende.recv(1024)
        # Desencriptamos el mensaje llamando a la función:
        mensaje = self.desencriptar_mensaje(mensaje_cifrado)
        # Lo devuelve:
        return mensaje
    
    def encriptar_mensaje(self, mensaje):
        
        # Pasamos el mensaje recibido a binario:
        mensaje_binario = mensaje.encode()

        # Creamos una nueva clave simétrica de forma aleatoria:
        clave_simetrica = get_random_bytes(32) #AES 256 bits
        nonce_simetrico = get_random_bytes(32)
        sesion_simetrica = clave_simetrica + nonce_simetrico
        
        # La sesión simétrica la encriptamos con asimetría:
        sesion_encriptada = self.cifrador_RSA.encrypt(sesion_simetrica)
        
        # Ahora encriptamos el mensaje con simetría:
        cifrador_AES = AES.new(clave_simetrica, AES.MODE_EAX, nonce_simetrico)
        mensaje_simetrico = cifrador_AES.encrypt(mensaje_binario)
        
        # Juntamos la clave simétrica con el mensaje:
        mensaje_cifrado = sesion_encriptada + mensaje_simetrico
        
        # Devuelve el mensaje ya cifrado:
        return mensaje_cifrado

    # Función para desencriptar el mensaje:
    def desencriptar_mensaje(self, mensaje_cifrado):

        # La sesión simétrica son los primeros 256 bytes:                           Para leer X primeros bytes: https://stackoverflow.com/a/20002667/14441036
        sesion_simetrica = mensaje_cifrado[:256]                                    # Los puntos nos dicen si son al principio como aquí...

        # Desencriptamos con nuestra clave privada la sesión:
        sesion_desencriptada = self.descifrador_RSA.decrypt(sesion_simetrica)

        # Accedemos a la clave y al nonce:
        clave_simetrica = sesion_desencriptada[:32]
        nonce_simetrico = sesion_desencriptada[32:]                                # O al final, los últimos 32 bytes, como aquí.

        # El mensaje binario son todo lo que exista en el mensaje a partir del byte 256:
        mensaje_binario = mensaje_cifrado[256:]

        # Desciframos el mensaje con la sesión simétrica recibida:
        descifrador_AES = AES.new(clave_simetrica, AES.MODE_EAX, nonce_simetrico)
        mensaje_descifrado = descifrador_AES.decrypt(mensaje_binario)

        # El mensaje aún está en binario, lo convertimos a formato legible:
        mensaje_descifrado = mensaje_descifrado.decode()

        # Devuelve el mensaje ya descifrado:
        return mensaje_descifrado
    
    # Función para terminar la partida y el hilo de juego:
    def fin_partida(self):
        # Envia al cliente el mensaje "Gracias por jugar" que actuará como cierre en la parte idem:
        self.enviar_mensaje(f"Gracias por jugar.")
        # Esperamos sincronización:
        self.recibir_mensaje()
        # Inicializamos el mensaje de resumen como una cadena vacía:
        resumen = ""
        # Recorremos cada item de la lista como "resultado":
        for resultado in self.resultados_partidas:
            # Vamos concatenando el resultado con la string resumen:
            resumen += resultado
        # Enviamos de vuelta la información de la partida
        self.enviar_mensaje(resumen)
        # El usuario quiere terminar la partida con el servidor, lo mostramos como mensaje de depuración en el servidor:
        print(f"Fin de sesión de juego con el cliente {self.nombre_jugador}.")
        # El hilo está declarado como que tiene que cerrar la instancia propia:
        self.cerrar_instancia = True

    # Función para crear un diccionario de objetos y sus precios:
    def crea_diccionario(self):
        # Declaramos un diccionario vacío:
        diccionario_productos = {}
        # Llenamos el diccionario con tuplas (producto - valor)
        diccionario_productos["Televisión de 65 pulgadas"] = 499
        diccionario_productos["Escáner portátil"] = 150
        diccionario_productos["Bolígrafo de una marca conocida"] = 70
        diccionario_productos["Motocicleta roja"] = 29999
        diccionario_productos["Picadora eléctrica"] = 69
        diccionario_productos["Juego de skis"] = 499
        diccionario_productos["Telescopio"] = 120
        diccionario_productos["Juego de toallas"] = 40
        diccionario_productos["Botella de vino cosecha 'añeja'"] = 10 
        diccionario_productos["Patinete eléctrico"] = 599 
        diccionario_productos["Viaje de lujo a Tokio para dos personas"] = 12000
        diccionario_productos["Gafas Realidad Virtual"] = 499
        diccionario_productos["Libro con evidentes signos de uso"] = 4000
        diccionario_productos["Coche clásico"] = 80000
        diccionario_productos["Participación en el Rally Dakar"] = 30000
        diccionario_productos["Katana del siglo XVIII"] = 150000
        diccionario_productos["Roca lunar"] = 300
        diccionario_productos["Juego de mancuernas"] = 119
        diccionario_productos["Ordenador"] = 1800
        diccionario_productos["Videoconsola retro"] = 400
        diccionario_productos["Traje de fallero"] = 7500
        diccionario_productos["Pelapatatas"] = 12
        # Devolvemos el diccionario ya creado:
        return diccionario_productos    

    # Función para devolver un objeto de forma aleatoria de nuestro diccionario:
    def get_objeto(self):
        # Creamos el diccionario con su función:
        diccionario_productos = self.crea_diccionario()
        # Elegimos de forma aleatoria un producto usando random.choice:
        producto_diccionario = random.choice(list(diccionario_productos.items()))       # https://stackoverflow.com/a/4859322/14441036
        # Devolvemos un producto del diccionario:
        return producto_diccionario

    # Función para jugar (mostrar todo):
    def jugar(self):
        # Invocamos el producto del diccionario usando la función:
        producto_juego = self.get_objeto()
        # Extraemos los valores del objeto (su tupla):
        producto, valor = producto_juego
        # Mensaje saludo comienzo de juego:
        self.enviar_mensaje(f"Tienes tres oportunidades para acertar el precio de este objeto '{producto}', pero sin pasarte.\nIntroduce tu primera puja: ")
        # Inicializamos el número de pujas y si ha ganado:
        pujas = 1
        ganado = False
        # Inicializamos la condición de salida del while a False                                                                     
        salir = False
        # Mientras hayan 3 o menos pujas realizadas y no se haya cambiado el valor de salir se jugará:
        while pujas <= 3 and not salir:
            # Usamos el método obtener_entero para asegurarnos de que el usuario introduce un entero con la opción "1" precio
            precio = self.obtener_entero(1)

            # El usuario ha introducido un valor menor al precio real del producto:      // Sigue jugando
            if precio < valor:
                # Comprobamos si ya se han realizado tres pujas y si el precio adivinado no ha superado el valor real del producto:
                if pujas == 3:
                    # Lo consideramos ganador:
                    ganado = True
                    # Salimos del bucle
                    salir = True
                    # Invocamos función de fin de juego:
                    self.fin_juego(valor, precio, pujas, ganado)
                # El jugador no ha hecho tres pujas aún:
                else:
                    # Mensaje informativo:
                    self.enviar_mensaje("\nTe has quedado corto, ¿qué quieres hacer?\n\n1. Me planto / 2. Sigo jugando\n\nIntroduce el número de la opción: ")
                    # Volvemos a utilizar el método obtener_entero, pero esta vez con la opción "2" menú:
                    opcion = self.obtener_entero(2)
                    # El jugador elige plantarse:
                    if opcion == 1:
                        # Lo consideramos ganador:
                        ganado = True
                        # Declaramos el while como que tiene que salir:
                        salir = True
                        # Invocamos función de fin de juego:
                        self.fin_juego(valor, precio, pujas, ganado)
                    # Elige seguir jugando:
                    elif opcion == 2:   
                        # Mensaje para que el usuario puje otra vez:
                        self.enviar_mensaje(f"\nPuja otra vez por {producto}: ")
                        # Incrementamos una puja más
                        pujas += 1

            # Si el precio introducido es igual al valor:                               // Gana
            elif precio == valor:
                # Ha ganado:
                ganado = True
                salir = True
                self.fin_juego(valor, precio, pujas, ganado)  

            # Si el precio introducido es mayor al valor:                               // Pierde
            elif precio > valor:
                ganado = False
                # Método de fin de juego:
                salir = True
                self.fin_juego(valor, precio, pujas, ganado)

        # Ya no hay breaks, solo condiciones de salida para el while #                             

    # Función de fin de juego (recoge las variables del valor real del producto, el último precio que adivinó el usuario, el número de pujas y si ha ganado)
    def fin_juego(self, valor, precio, pujas, ganado):
        # Establecemos la diferencia a la que se ha quedado del precio justo:
        diferencia = valor - precio
        
        # Primero incrementamos el juego actual (recordemos que empieza a 0):
        self.juegos_totales += 1
        # Ahora agregamos lo que ha hecho el jugador en esta partida nuestra lista:
        resultado_partida = f"Partida {self.juegos_totales}: "
        # Si ha ganado lo añadimos a la string de una forma:
        if ganado:
            # Ponemos que se ha quedado a X para el precio justo seguido de un salto de línea:
            resultado_partida += f"Faltan {diferencia} para el precio justo.\n"
        # Si ha perdido de otra:
        else:
            # Ponemos simplemente que se ha pasado, seguido de un salto de línea:
            resultado_partida += f"Te pasaste.\n"
        # Una vez hemos completada la string con la información de la partida la añadimos como elemento a nuestra lista:
        self.resultados_partidas.append(resultado_partida)

        # Ha ganado:
        if ganado:
            # Mostramos el mensaje de victoria:
            self.enviar_mensaje(f"\nHas ganado. Has hecho {pujas} puja/s y te has quedado a {diferencia}€ del precio justo.\n¿Otra partida? 1. Sí 2. No - Introduce el número de la opción: ")
            # Invocamos el método para obtener el valor:
            opcion = self.obtener_entero(2)
            # Si devuelve 1 quiere jugar:
            if opcion == 1:
                # Volvemos a invocar la función de juego:
                self.jugar()
            # Si devuelve otra cosa (2) no quiere seguir jugando:
            else:
                # Sale del programa:
                self.fin_partida()
        # No ha ganado:
        else:
            # Mensaje de derrota:
            self.enviar_mensaje(f"\nHas perdido. Has hecho {pujas} pujas y te has pasado del precio justo. Otra vez será.\n¿Otra partida? 1. Sí 2. No - Introduce el número de la opción: ")
            opcion = self.obtener_entero(2)
            if opcion == 1:
                self.jugar()
            else:
                self.fin_partida()

    # Función para obtener un entero del usuario:
    def obtener_entero(self, opcion):
        # Bucle que pedirá un entero:
        while True:
            # Usamos la función de recibir el mensaje para asignar la variable:
            valor_recibido = self.recibir_mensaje()
            # Bloque try - except:
            try:
                # Convertimos la cadena a int:
                valor_entero = int(valor_recibido)
                # Opción 1 - Manejamos precio introducido por el usuario:
                if opcion == 1:
                    return valor_entero
                # Opcion 2 - Manejamos opción introducida por el usuario:
                elif opcion == 2:
                     # Si el valor está fuera de rango (menor a 1 o mayor a 2) lo manejamos
                    if valor_entero < 1 or valor_entero > 2:
                        self.enviar_mensaje("\nIntroduce una opción correcta.")
                        # En caso contrario el valor está en rango...
                    else:
                         # ... y lo devuelve:
                        return valor_entero
                # Manejamos la posible excepción de introducir decimales, letras, en vez de enteros:
            except ValueError as e:
                print(f"El cliente no insertó un número -> Excepción: {e}")
                self.enviar_mensaje("\nError. No has introducido un valor entero. Por favor, introduce un valor entero: ")

## FIN LÓGICA JUEGO ##

## Funciones principales del servidor ##

# Pequeña función para el protocolo de bienvenida:
def protocolo_bienvenida(socket_atiende):
    # Mensaje de bienvenida:
    mensaje = "Bienvenido al Precio Justo - Introduce tu apodo:"
    # Lo enviamos al cliente:
    socket_atiende.sendall(mensaje.encode())
    # Recibimos el apodo del jugador:
    nombre_jugador = socket_atiende.recv(1024).decode()
    # Lo devolvemos como parte de la función:
    return nombre_jugador

# Función para acceder a las claves al principio de la sesión:
def acceso_claves():
    global clave_privada_servidor, clave_publica_cliente

    path = Path(__file__).parent / "privada_servidor.pem"
    with open(path, 'rb') as file:
        clave_privada_servidor = RSA.import_key(file.read())

    pathf = Path(__file__).parent / "publica_cliente.pem"
    with open(pathf, 'rb') as file:
        clave_publica_cliente = RSA.import_key(file.read())


# Función principal
if __name__ == "__main__":
    
    # Abrimos ambas claves asimétricas y las dejamos declaradas de forma global:
    acceso_claves()

    # Establecemos IP y puerto del servidor:
    HOST = '127.0.0.1'
    PORT = 5000       

    # Creamos el socket:
    try:
        socket_escucha = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('¡Servidor-socket El Precio Justo creado!')
    except socket.error as ex:
        print(f"Fallo en la creación del socket servidor: {ex}")
        sys.exit()
    
    # Conectamos el socket:
    try:
        # El socket empieza a escuchar en la IP y PUERTO establecidos:
        socket_escucha.bind((HOST, PORT))
    except socket.error as ex:
        print('Error socket: %s' %ex)
        sys.exit()
    
    # El servidor, en caso de estar saturado, pone a hasta a 10 jugadores en espera antes de atenderlos (al 11 lo rechazará).
    socket_escucha.listen(10)
    # Lista de hilos
    instancias = []

    # Bucle:
    while True:
        # El Servidor queda bloqueado en esta línea esperando a que un cliente se CONECTE a su IP/PUERTO.
        socket_atiende, addr_cliente = socket_escucha.accept()
        # Asignamos el nombre del jugador con su función:
        nombre_jugador = protocolo_bienvenida(socket_atiende)
        # Cuando se conecte un cliente se iniciará un nuevo hilo con la instancia de juego (se pasan como parámetros el apodo, el socket y la dirección)
        partida_jugador = hilo_Partida(nombre_jugador, socket_atiende, addr_cliente)
        # Añadimos el hilo creado a la lista de instancias de juego:
        instancias.append(partida_jugador)
        # Se inicializa el hilo con la clase partida:
        partida_jugador.start()
    