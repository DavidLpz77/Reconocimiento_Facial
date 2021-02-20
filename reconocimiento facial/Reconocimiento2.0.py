#David Ricardo Lopez A - 20161020505
#Importa las librerias necesarias
import os
import cv2
import face_recognition
import sqlite3
import datetime
import time
import os.path
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#Funcion para enviar el email de la llegada tarde
def enviar_correo(MY_ADDRESS,PASSWORD,mensaje,TO):
    s = smtplib.SMTP(host='smtp.gmail.com', port=587) # servidor y puerto
    s.starttls() # Conexion tls
    s.login(MY_ADDRESS, PASSWORD) # Iniciar sesion con los datos de acceso al servidor SMTP

    # Crear el Mensaje
    msg = MIMEMultipart()

    message = mensaje
    msg['From']=MY_ADDRESS
    msg['To']= TO
    msg['Subject']="EMPLEADO LLEGO TARDE"

    # Agregar el texto del mensaje al mensaje
    msg.attach(MIMEText(message, 'plain'))

    # Enviar el mensaje
    s.send_message(msg)
    del msg

    # Finaliar sesion SMTP
    s.quit()

#Funcion para crear el usuario en la base de datos
def crear_usuario(conexion, datos_empleados):
    sql = 'INSERT INTO datos_empleados (nombre,email, hora) VALUES (?,?,?);'

    cursor = conexion.cursor()
    cursor.execute(sql, datos_empleados)
    conexion.commit()

#Funcion para la coneccion a la base de datos
def conexion_bd(Empleados): 
    try:
        conexion= sqlite3.connect(Empleados)
        print ('conexion establecida')
        return conexion
    except sqlite3.Error as error:
        print('Error al crear la conexion con la Base de datos', error)

 #Funcion para consultar el email de los empleados        
def buscar(conexion,nombre):
    sql = "SELECT email FROM Usuarios WHERE (nombre = '{}')".format(nombre)

    cursor = conexion.cursor()
    cursor.execute(sql)
    conexion.commit()
    resultado=cursor.fetchone()
    return resultado

#Datos del correo que enviara el email Destino y remitente
MY_ADDRESS = 'proyectoteleinf1@gmail.com'
PASSWORD = '12345678prueba'
TO='proyectoteleinf1@gmail.com'


conexion = conexion_bd('Empleados')
i=True
#Define la hora de llegada tardia
hora_llegada='08: 15: 00'
#compara el rostro con los usuarios conocidos en el banco de fotos y BD
encodings_conocidos = []
nombres_conocidos =[]  
#Busca en el banco de fotos y compara el nombre de la foto con el nombre de usuario
for dirpath, dirnames, filenames in os.walk("imagenes/"):
    for filename in filenames:
        foto = face_recognition.load_image_file(os.path.abspath("imagenes/"+filename))
        foto_encodings = face_recognition.face_encodings(foto)[0]
        texto=filename.split('.')
        nombre_db=texto[0]
        encodings_conocidos.append(foto_encodings)
        nombres_conocidos.append(nombre_db)
webcam = cv2.VideoCapture(0)
 
font = cv2.FONT_HERSHEY_COMPLEX
#reduccion de la foto para su comparacion
reduccion = 7

print("\nPulsar 'ENTER' para cerrar.\n")
#bucle que compara rostros y verifica si es conocido o desconocido
while 1:
    loc_rostros = [] 
    encodings_rostros = []
    nombres_rostros = [] 
    nombre = "" 
    #lee la imagen de la camara    
    valido, img = webcam.read()

    if valido:
                
        img_rgb = img[:, :, ::-1]
        
        img_rgb = cv2.resize(img_rgb, (0, 0), fx=1.0/reduccion, fy=1.0/reduccion)
        #encuentra coincidencias en los rostros
        loc_rostros = face_recognition.face_locations(img_rgb)
        encodings_rostros = face_recognition.face_encodings(img_rgb, loc_rostros)
                
        for encoding in encodings_rostros:
            coincidencias = face_recognition.compare_faces(encodings_conocidos, encoding)
            #Compara las coincidencias con el nombre del usuario de la base de datos        
            if True in coincidencias:
                nombre = nombres_conocidos[coincidencias.index(True)]
            #No encuentra conincidencia en el rostro            
            else:
                nombre = "Desconocido"
                        
            nombres_rostros.append(nombre)
        for (top, right, bottom, left), nombre in zip(loc_rostros, nombres_rostros):        
            top = top*reduccion
            right = right*reduccion
            bottom = bottom*reduccion
            left = left*reduccion
            #Si es un rostro desconocido pinta un rectangulo rojo        
            if nombre != "Desconocido":
                color = (0,255,0)
                cv2.rectangle(img, (left, top), (right, bottom), color, 2)
                cv2.rectangle(img, (left, bottom - 20), (right, bottom), color, -1)
                cv2.putText(img, nombre, (left, bottom - 6), font, 0.6, (0,0,0), 1)
                #Reconoce un rostro conocido en el banco de fotos
                if i==True:
                    ahora = datetime.datetime.now()
                    hora_entrada= datetime.time(8,15,00)
                    hora_entrada=ahora.strftime('%H: %M: %S')
                    email=buscar(conexion,nombre_db) 
                    datos_empleados = (nombre_db,str(email),hora_entrada)
                    crear_usuario(conexion,datos_empleados)
                    print('Rostro reconocido presione la tecla (A) para la siguiente persona')
                    i=False
                    #cuerpo del mensaje del email enviardo
                    mensaje='El empleado : ' + nombre_db + ' llego tarde a las: ' + hora_entrada + ' ¡¡¡¡¡¡¡¡PASARLE MEMORANDO!!!!!!!!'
                    print('Su hora de llegada es: ' +hora_entrada)
                    #verifica si la hora de entrada es tardia 
                    if hora_entrada>hora_llegada:
                        print('¡¡¡¡¡¡ LLEGO TARDE !!!!!!')
                        enviar_correo(MY_ADDRESS,PASSWORD,mensaje,TO)


            else:
                color = (0,0,255)
            #Crea un rectangulo alrededor del rostro captado en camara       
            cv2.rectangle(img, (left, top), (right, bottom), color, 2)
            cv2.rectangle(img, (left, bottom - 20), (right, bottom), color, -1)
            cv2.putText(img, nombre, (left, bottom - 6), font, 0.6, (0,0,0), 1)
                
                    
        
        cv2.imshow('Output', img)
        #Define las teclas para cerrar el aplicativo y para capturar rostro
        k = cv2.waitKey(5) & 0xFF
        if k==97:
            i=True
        if k == 13:
            cv2.destroyAllWindows()
            break
        
webcam.release()
#cierra la conexion a la base de datos
if conexion:
    conexion.close()