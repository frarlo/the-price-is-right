# Lógica de la parte cliente #
import socket, sys, random, time
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes
from pathlib import Path

# HOST y PUERTO como variables globales:
HOST = '127.0.0.1'  
PORT = 5000

# Inicializamos las variables de nuestra clave privada y la clave publica del servidor:
clave_privada_cliente = None
clave_publica_servidor = None

# Inicializamos las variables del cifrador y descifrador para ahorrar recursos:
cifrador_RSA = None
descifrador_RSA = None

# Función para "abrir" las claves asumiendo que están en el mismo directorio que este archivo e inicializar los objetos des/cifradores:
def abrir_claves():
    # Accedemos a las variables globales para cambiarlas:
    global clave_privada_cliente, clave_publica_servidor, cifrador_RSA, descifrador_RSA

    # Primero la privada de nuestro cliente:
    clave_privada_path = Path(__file__).parent / "privada_cliente.pem"
    clave_privada_cliente = RSA.import_key(open(clave_privada_path).read())

    # Luego la pública del servidor:
    clave_publica_path = Path(__file__).parent / "publica_servidor.pem"
    clave_publica_servidor = RSA.import_key(open(clave_publica_path).read())

    # Ahora inicializamos nuestro cifrador con la clave pública del servidor:
    cifrador_RSA = PKCS1_OAEP.new(clave_publica_servidor)
    # Lo mismo, pero con el descifrador con nuestra propia clave privada:
    descifrador_RSA = PKCS1_OAEP.new(clave_privada_cliente)

# Función que encripta el mensaje con simetría:        
def encripta_mensaje(mensaje):

    # Pasamos el mensaje recibido a binario:
    mensaje_binario = mensaje.encode()

    # Creamos una nueva clave simétrica de forma aleatoria:
    clave_simetrica = get_random_bytes(32) #AES 256 bits
    nonce_simetrico = get_random_bytes(32)
    sesion_simetrica = clave_simetrica + nonce_simetrico
        
    # La sesión simétrica la encriptamos con asimetría:
    sesion_encriptada = cifrador_RSA.encrypt(sesion_simetrica)
        
    # Ahora encriptamos el mensaje con simetría:
    cifrador_AES = AES.new(clave_simetrica, AES.MODE_EAX, nonce_simetrico)
    mensaje_simetrico = cifrador_AES.encrypt(mensaje_binario)
        
    # Juntamos la clave simétrica con el mensaje:
    mensaje_cifrado = sesion_encriptada + mensaje_simetrico
        
    # Devuelve el mensaje ya cifrado:
    return mensaje_cifrado

# Función que desencripta el mensaje con simetría:
def desencripta_mensaje(mensaje_cifrado):

    # La sesión simétrica son los primeros 256 bytes codificados con RSA:
    sesion_simetrica = mensaje_cifrado[:256]            # Si tuviésemos una clave RSA más grande deberíamos cambiar este valor por 512 o 1024

    # Desencriptamos con nuestra clave privada la sesión:
    sesion_desencriptada = descifrador_RSA.decrypt(sesion_simetrica)

    # Accedemos a la clave y al nonce (primeros y últimos 32 bytes respectivamente para AES 256 bits)
    clave_simetrica = sesion_desencriptada[:32]
    nonce_simetrico = sesion_desencriptada[32:]

    # El mensaje cifrado con simetría es todo lo que hay después de los primeros 256 bytes de codificación RSA:
    mensaje_binario = mensaje_cifrado[256:]

    # Desciframos el mensaje con la sesión simétrica recibida:
    descifrador_AES = AES.new(clave_simetrica, AES.MODE_EAX, nonce_simetrico)
    mensaje_descifrado = descifrador_AES.decrypt(mensaje_binario)

    # El mensaje aún está en binario, lo convertimos a formato legible:
    mensaje_descifrado = mensaje_descifrado.decode()

    # Devuelve el mensaje ya descifrado:
    return mensaje_descifrado

# Función del cliente:
def programa_cliente():

    # Antes de nada accedemos a las claves e inicializamos el par descrifrador/cifrador asimétrico:
    abrir_claves()

    # Creamos el socket cliente:
    try:
        socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('Socket cliente creado')
    except socket.error:
        print('Fallo en la creación del socket ciente')
        sys.exit()

    # Conectamos el socket cliente al socket servidor con las variables GLOBALES:
    socket_cliente.connect((HOST, PORT))
    # Mensaje informativo:
    print(f"Conectado con el socket-servidor de El Precio Justo {HOST}/{PORT}")
    # Inicializamos la variable (vacía) que recibirá el mensaje del servidor:
    servidor_dice = ''

    # Bloque with con el socket_cliente:
    with socket_cliente:

        """ La primera interacción con el servidor está fuera del bucle porque recoge el nombre del usuario"""
        
        # Recibimos información del Servidor:
        servidor_dice = socket_cliente.recv(1024)
        # La mostramos al cliente por pantalla:
        print(servidor_dice.decode())
        # Pedimos al usuario el nombre de usuario por teclado:
        usuario = input()
        # Si el usuario pulsa enter sin introducir nada (cadena vacía)...
        while usuario == '':
            print("Debes introducir un apodo de usuario. Prueba otra vez: ")
            usuario = input()
        # Lo enviamos al socket:
        socket_cliente.send(usuario.encode())

        # A partir de este punto el usuario entra en juego, por lo tanto toda la comunicación está encriptada:
        while True:
            # Esperamos a que nos diga algo el servidor de juego:
            servidor_dice = socket_cliente.recv(1024)
            # Lo desencriptamos:
            mensaje_servidor = desencripta_mensaje(servidor_dice)
            # Mostramos el mensaje del servidor al cliente:
            print(mensaje_servidor)
            # Comprobamos que la partida siga en marcha gracias a la frase de despedida:
            if mensaje_servidor == 'Gracias por jugar.':
                # Hemos recibido el mensaje que termina la ejecución, enviamos un mensaje de sincronización:
                cierre = "okfinish"
                # Lo encriptamos:
                cierre_encriptado = encripta_mensaje(cierre)
                # Lo enviamos:
                socket_cliente.sendall(cierre_encriptado)
                # Para finalmente recibir el resumen de nuestra partida:
                resumen_encriptado = socket_cliente.recv(1024)
                # Lo desencriptamos:
                resumen = desencripta_mensaje(resumen_encriptado)
                # Lo mostramos:
                print(resumen)
                # Salimos del bucle:
                break
            # El usuario introduce lo que le pide la parte servidor:
            mensaje = input()
            # Encriptamos el mensaje con la clave de sesión:
            mensaje_encriptado = encripta_mensaje(mensaje)
            # Mientras el usuario introduzca una cadena vacía no enviará ningún mensaje:
            while mensaje == '':
                print("No has introducido ningun valor. Por favor, introduce un valor:")
                mensaje = input()
            # Lo codifica y lo envía:
            socket_cliente.sendall(mensaje_encriptado) #Codificamos el mensaje a bytes y le indicamos que lo envie todo

    # Cerramos el socket:
    socket_cliente.close()

if __name__ == '__main__':
    # Ejecutamos el programa cliente desde el main:
    programa_cliente()
    # Mensaje de control para establecer que ha terminado la ejecución del cliente:
    print("Ejecución de la parte cliente terminada.")
    # Salimos:
    sys.exit()
