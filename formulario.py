# encoding: utf-8
# File: code.py

import web
import feedparser
import tweepy
from pymongo import MongoClient
from web import form
from web.contrib.template import render_mako
from datetime import date

consumer_key = 'b3GgjCThqLaCxnLKacZPg'
consumer_secret = 'u4BUfTKJHlADeaRj0AsZAqu2W2BJ5PWEF9i4BRyQ'
access_token = '264740225-Zjfw33W0B6ylm7r3o0TnXHCIh2jNoQSsox7G5xZQ'
access_token_secret = 'PMhH8vdJj0L3KIX5TdYVmdSy3sEldBx5fdd4EnsVk'

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

urls = (
        '/about(.*)', 'about',
        '/archives(.*)', 'archives',
        '/writing(.*)', 'writing',
        '/speaking(.*)', 'speaking',
        '/contact(.*)', 'contact',
        '/logout(.*)','logout',
        '/register(.*)','register',
        '/chart(.*)','chart',
        '/mash(.*)','mash',
        '/(.*)', 'index'
        )

app = web.application(urls, globals(), autoreload=True)

render = render_mako(
        directories=['templates'],
        input_encoding='utf-8',
        output_encoding='utf-8',
        )

if web.config.get('_session') is None:
    session = web.session.Session(app, web.session.DiskStore('sessions'),initializer={'user': 'anonymous','pag0' : 'vacio','pag1' : 'vacio','pag2' : 'vacio','pag3' : 'vacio'})
    web.config._session = session
else:
    session = web.config._session

client = MongoClient()
db = client.myDB

#Aunque se llama nuevo usuario,tambien se ha reciclado para actualizar los existentes
def newUser(nombre,apellidos,password,dni,correo,visa,fecha1,fecha2,fecha3,direccion,pago,clausulas):
    nombre=str(nombre)
    user={"nombre":nombre,
        "apellidos":str(apellidos),
        "pass":str(password),
        "correo":str(correo),
        "dni":str(dni),
        "visa":str(visa),
        "dia":str(fecha1),
        "mes":str(fecha2),
        "anyo":str(fecha3),
        "direccion":str(direccion),
        "pago":str(pago),
        "clausulas":str(clausulas)
    }
    if db.users.find_one({"nombre":nombre})==None:
        db.users.insert(user)
    else:
        db.users.update({"nombre":nombre}, {"$set": {"apellidos":str(apellidos),"pass":str(password),"correo":str(correo),"dni":str(dni),"visa":str(visa),"dia":str(fecha1),"mes":str(fecha2),"anyo":str(fecha3),"direccion":str(direccion),"pago":str(pago),"clausulas":str(clausulas)}})

def loadUser(nombre):
    nombre=str(nombre)
    Actualuser=db.users.find_one({"nombre":nombre})
    user=[None]*11
    #Esta conversion de diccionario a lista se hace para mantener la compatibilidad con el resto del codigo
    user[0]=Actualuser["nombre"]
    user[1]=Actualuser["apellidos"]
    user[2]=Actualuser["dni"]
    user[3]=Actualuser["correo"]
    user[4]=Actualuser["visa"]
    user[5]=Actualuser["dia"]
    user[6]=Actualuser["mes"]
    user[7]=Actualuser["anyo"]
    user[8]=Actualuser["direccion"]
    user[9]=Actualuser["pago"]
    user[10]=Actualuser["clausulas"]
    return user

def loadGraph():
    ActualGraph=db.users.find_one({"Dato":"dato"})
    graph=[None]*5
    if ActualGraph is not None:
        graph[0]=ActualGraph["Dato1"]
        graph[1]=ActualGraph["Dato2"]
        graph[2]=ActualGraph["Dato3"]
        graph[3]=ActualGraph["Dato4"]
        graph[4]=ActualGraph["Dato5"]
    else:
        graph[0]=1
        graph[1]=2
        graph[2]=3
        graph[3]=4
        graph[4]=5
    return graph

def updateGraph(dato1,dato2,dato3,dato4,dato5):
    graph={"Dato":"dato",
        "Dato1":dato1,
        "Dato2":dato2,
        "Dato3":dato3,
        "Dato4":dato4,
        "Dato5":dato5,
    }
    if db.users.find_one({"Dato":"dato"})==None:
        db.users.insert(graph)
    else:
        db.users.update({"Dato":"dato"},{"$set": {"Dato1":dato1,"Dato2":dato2,"Dato3":dato3,"Dato4":dato4,"Dato5":dato5}})


signin_form = form.Form(
    form.Textbox('username',form.notnull,description='Username:'),
    form.Password('password',form.notnull, description='Password:'),
    validators = [form.Validator("Username and password didn't match.",lambda x: str(x.password)==db.users.find_one({"nombre":str(x.username)})["pass"])]
    )

arrayDiasMeses=[None]*31
arrayAnios=[None]*100
d=date.today()
for i in range(31):
    arrayDiasMeses[i]=[i+1,i+1]
for i in range(100):
    arrayAnios[i]=[d.year-i,d.year-i]

registerForm = form.Form( 
    form.Textbox("nombre", form.notnull,description = "Nombre:"),
    form.Textbox("apellidos",form.notnull ,description = "Apellidos:",),
    form.Textbox("dni",form.notnull, description = "DNI:"),
    form.Textbox("correo",form.notnull,form.regexp('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,3})$',"Correo incorrecto"), description = "Correo electronico:"),
    form.Dropdown('dia', arrayDiasMeses),
    form.Dropdown('mes', arrayDiasMeses[0:12]),
    form.Dropdown('anyo', arrayAnios),#Problemas con la codificacion de la Ñ,arreglar si sobre tiempo
    form.Textarea("direccion",form.notnull, description = "Direccion:"),
    form.Password("pass1",form.notnull,form.Validator('El password tiene que tener mas de 7 caracteres',lambda x: int(x)>7), description = "Password:"),
    form.Password("pass2",form.notnull,form.Validator('El password tiene que tener mas de 7 caracteres',lambda x: int(x)>7), description = "Repita su password:"),
    form.Radio("pago", ["Contrareembolso", "Con tarjeta"],description="Forma de pago"),
    form.Checkbox("condiciones",form.Validator('Tiene que aceptar las condiciones',lambda x: x=='acepto'),description="Acepto las condiciones",value='acepto'),
    form.Textbox("visa",form.regexp('([0-9]{4}[\s-]){3}[0-9]{4}',"Visa incorrecta"),description = "Numero de VISA:"),
    validators=[form.Validator("Los password no coinciden",lambda x:x.pass1 == x.pass2),form.Validator("Fecha incorrecta",lambda i:(((int(i.mes) == 2) and ((int(i.dia) <= 28) and ((int(i.anyo) % 4) != 0) or (int(i.dia) <= 29) and ((int(i.anyo) % 4) == 0))) or ((int(i.dia) <= 30) and ((int(i.mes) == 4) or (int(i.mes) == 6) or (int(i.mes) == 9) or (int(i.mes) == 11))) or ((int(i.mes) == 1) or(int(i.mes) == 3) or(int(i.mes) == 5) or(int(i.mes) == 7) or (int(i.mes) == 8) or (int(i.mes) == 10) or (int(i.mes) == 12) )))]
)

graphForm = form.Form( 
    form.Textbox("Dato1",form.notnull,description = "Dato 1:"),
    form.Textbox("Dato2",form.notnull,description = "Dato 2:"),
    form.Textbox("Dato3",form.notnull,description = "Dato 3:"),
    form.Textbox("Dato4",form.notnull,description = "Dato 4:"),
    form.Textbox("Dato5",form.notnull,description = "Dato 5:"),
)

def rss():
    feed = feedparser.parse( "http://feeds.weblogssl.com/genbetadev" )
    myFeed=[None]*3
    myFeed[0]=[None]*2
    myFeed[1]=[None]*2
    myFeed[2]=[None]*2
    myFeed[0][0]=feed['items'][0]['title']
    myFeed[0][1]=feed['items'][0]['link']
    myFeed[1][0]=feed['items'][1]['title']
    myFeed[1][1]=feed['items'][1]['link']
    myFeed[2][0]=feed['items'][2]['title']
    myFeed[2][1]=feed['items'][2]['link']
    return myFeed


class index:
    def GET(self,name):
        myFeed=rss()
        form=signin_form()
        if session.user!='anonymous':
            session.pag3=session.pag2
            session.pag2=session.pag1
            session.pag1=session.pag0
            session.pag0='index.html'
        return render.index(formLogin=form.render(),user=session.user,pag1=session.pag1,pag2=session.pag2,pag3=session.pag3,feed=myFeed)

    def POST(self,name):
        myFeed=rss()
        form=signin_form()
        if form.validates(): 
            session.user = form['username'].value
        return render.index(formLogin=form.render(),user=session.user,pag1=session.pag1,pag2=session.pag2,pag3=session.pag3,feed=myFeed)

class about:
    def GET(self,name):
        myFeed=rss()
        form=signin_form()
        if session.user!='anonymous':
            session.pag3=session.pag2
            session.pag2=session.pag1
            session.pag1=session.pag0
            session.pag0='about.html'
        return render.about(formLogin=form.render(),user=session.user,pag1=session.pag1,pag2=session.pag2,pag3=session.pag3,feed=myFeed)


class archives:
    def GET(self,name):
        myFeed=rss()
        form=signin_form()
        if session.user!='anonymous':
            session.pag3=session.pag2
            session.pag2=session.pag1
            session.pag1=session.pag0
            session.pag0='archives.html'
        return render.archives(formLogin=form.render(),user=session.user,pag1=session.pag1,pag2=session.pag2,pag3=session.pag3,feed=myFeed)

class writing:
    def GET(self,name):
        myFeed=rss()
        form=signin_form()
        if session.user!='anonymous':
            session.pag3=session.pag2
            session.pag2=session.pag1
            session.pag1=session.pag0
            session.pag0='writing.html'
        return render.writing(formLogin=form.render(),user=session.user,pag1=session.pag1,pag2=session.pag2,pag3=session.pag3,feed=myFeed)


class speaking:
    def GET(self,name):
        myFeed=rss()
        form=signin_form()
        if session.user!='anonymous':
            session.pag3=session.pag2
            session.pag2=session.pag1
            session.pag1=session.pag0
            session.pag0='speaking.html'
        return render.speaking(formLogin=form.render(),user=session.user,pag1=session.pag1,pag2=session.pag2,pag3=session.pag3,feed=myFeed)

class contact:
    def GET(self,name):
        myFeed=rss()
        form=signin_form()
        if session.user!='anonymous':
            session.pag3=session.pag2
            session.pag2=session.pag1
            session.pag1=session.pag0
            session.pag0='contact.html'
        return render.contact(formLogin=form.render(),user=session.user,pag1=session.pag1,pag2=session.pag2,pag3=session.pag3,feed=myFeed)

class register:
    def GET(self,name):
        myFeed=rss()
        form=signin_form()
        regis=registerForm()
        if session.user!='anonymous':
            session.pag3=session.pag2
            session.pag2=session.pag1
            session.pag1=session.pag0
            session.pag0='register.html'
            data=loadUser(session.user)
            regis['nombre'].value=data[0]
            regis['apellidos'].value=data[1]
            regis['dni'].value=data[2]
            regis['correo'].value=data[3]
            regis['visa'].value=data[4]
            regis['dia'].value=int(data[5])
            regis['mes'].value=int(data[6])
            regis['anyo'].value=int(data[7])
            regis['direccion'].value=data[8]
            regis['pago'].value=data[9]
            regis['condiciones'].value=data[10]
        return render.register(formLogin=form.render(),user=session.user,pag1=session.pag1,pag2=session.pag2,pag3=session.pag3,register=regis.render(),feed=myFeed)

    def POST(self,name):
        myFeed=rss()
        form=signin_form()
        regis=registerForm()
        if regis.validates(): 
            session.user = regis['nombre'].value
            newUser(regis['nombre'].value,regis['apellidos'].value,regis['pass1'].value,regis['dni'].value,regis['correo'].value,regis['visa'].value,regis['dia'].value,regis['mes'].value,regis['anyo'].value,regis['direccion'].value,regis['pago'].value,regis['condiciones'].value)
        return render.register(formLogin=form.render(),user=session.user,pag1=session.pag1,pag2=session.pag2,pag3=session.pag3,register=regis.render(),feed=myFeed)
       
class logout:
    def GET(self,name):
        session.kill()
        raise web.seeother('/index.html')

class chart:
    def GET(self,name):
        myFeed=rss()
        form=signin_form()
        graph=graphForm()
        if session.user!='anonymous':
            session.pag3=session.pag2
            session.pag2=session.pag1
            session.pag1=session.pag0
            session.pag0='chart.html'
        data=loadGraph()
        graph['Dato1'].value=data[0]
        graph['Dato2'].value=data[1]
        graph['Dato3'].value=data[2]
        graph['Dato4'].value=data[3]
        graph['Dato5'].value=data[4]
        return render.chart(formLogin=form.render(),user=session.user,pag1=session.pag1,pag2=session.pag2,pag3=session.pag3,feed=myFeed,gr=graph.render(),dat1=data[0],dat2=data[1],dat3=data[2],dat4=data[3],dat5=data[4])

    def POST(self,name):
        myFeed=rss()
        form=signin_form()
        graph=graphForm()
        if graph.validates():
            updateGraph(graph['Dato1'].value,graph['Dato2'].value,graph['Dato3'].value,graph['Dato4'].value,graph['Dato5'].value)
        return render.chart(formLogin=form.render(),user=session.user,pag1=session.pag1,pag2=session.pag2,pag3=session.pag3,gr=graph.render(),feed=myFeed,dat1=graph['Dato1'].value,dat2=graph['Dato2'].value,dat3=graph['Dato3'].value,dat4=graph['Dato4'].value,dat5=graph['Dato5'].value)

class mash:
    def GET(self,name):
        myFeed=rss()
        form=signin_form()
        if session.user!='anonymous':
            session.pag3=session.pag2
            session.pag2=session.pag1
            session.pag1=session.pag0
            session.pag0='mash.html'
        tweets = api.search(q='sheridan_Gr', count=5)
        geolat=[None]*5
        geolon=[None]*5
        if tweets[0].coordinates is not None:
            geolat[0]=tweets[0].coordinates.values()[1][1]
            geolon[0]=tweets[0].coordinates.values()[1][0]
        else:
            geolat[0]=1000
            geolon[0]=1000
        if tweets[1].coordinates is not None:
            geolat[1]=tweets[1].coordinates.values()[1][1]
            geolon[1]=tweets[1].coordinates.values()[1][0]
        else:
            geolat[1]=1000
            geolon[1]=1000
        if tweets[2].coordinates is not None:
            geolat[2]=tweets[2].coordinates.values()[1][1]
            geolon[2]=tweets[2].coordinates.values()[1][0]
        else:
            geolat[2]=1000
            geolon[2]=1000
        if tweets[3].coordinates is not None:
            geolat[3]=tweets[3].coordinates.values()[1][1]
            geolon[3]=tweets[3].coordinates.values()[1][0]
        else:
            geolat[3]=1000
            geolon[3]=1000
        if tweets[4].coordinates is not None:
            geolat[4]=tweets[4].coordinates.values()[1][1]
            geolon[4]=tweets[4].coordinates.values()[1][0]
        else:
            geolat[4]=1000
            geolon[4]=1000
        return render.mash(formLogin=form.render(),user=session.user,pag1=session.pag1,pag2=session.pag2,pag3=session.pag3,feed=myFeed,twe=tweets,geolatw=geolat,geolonw=geolon)

if __name__ == "__main__":
    app.run()