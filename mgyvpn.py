#!/usr/bin/python3.6
# -*- coding: utf8 -*-
"""mgyvpn.py
Ce script python permet d'automatiser l'installation d'OpenVPN avec chiffrement sous easy-rsa
entre un noeud serveur et des noeuds clients
Il a été réalisé et testé sous Ubuntu Server LTS 18.04
Il fait appel à un ficher de configuration yaml
"""

import sys
import signal
import subprocess
import os
import re
import yaml
from socket import inet_aton

#Redirection des messages d'erreur
logfile=open('./mgyvpn.log','w')

#Try Finally pour ce flux
try:
    sys.stderr=logfile

    def logmessage(msg,f=logfile):
        """Procédure de gestion des logs, et d'affichage sur la console"""
        print("    ===> INFO : ",msg)
        msg="    ===> INFO : "+ msg+"\n"
        f.write(msg)

    #lié à Signal
    def fermeture(signal, frame):
        """Cette fonction est appelée quand l'excécution du script est interrompue"""
	
        #Enregistrer un log de fermeture inopinée 
        logmessage("\nRequête d'arrêt du script reçue !!!")
        
        sys.exit(0) 

    #Assignation d'une fonction au signal SIGINT
    signal.signal(signal.SIGINT,fermeture)

    def checked_ip(ip_addr):
        """Cette fonction renvoie True quand l'adresse IP fournie est valide
        Elle crée une exception dans le cas d'une adresse invalide"""
        try:
            #socket.inet_aton(str(ip_addr))
            return True
        except:
            logmessage("l'adresse IP '{}' n'est pas valide".format(ip_addr))
            raise Exception("IP '{}' non valide".format(ip_addr))  


    def exec_command(macommande,titre=""):

        """Cette fonction exécute une commande système et retourne un résultat
        Les erreurs sont consignées dans le fichier error.log"""
        if not titre:
            titre=macommande
        else:
            titre+="\n"+macommande
	
	#Mise à jour du log
        logmessage(titre)

        res=subprocess.run(macommande, shell=True,  stdout=sys.stdout, stderr=sys.stderr, check=True)
        #Générer une exception en cas d'erreur
        #res.check_returncode()

     
    def EditEasyRsaVars(fichier,dict_param):
        """Modification du fichier de configuration easy-rsa/vars"""
        texte=''
        with open(fichier,'r') as f: #Ouvrir le fichier en lecture seule
            for ligne in f: #Parcourir les lignes du ficher vars
                remplacement=False
                for cle in dict_param: #Parcourir la liste des paramètres à customiser
                    p='^export ('+cle+'){1}='
                    if re.match(p,ligne): #Vérifier si la ligne correspond à un paramètre
                        texte+='export {}="{}"\n'.format(cle,dict_param[cle]) #Créer la ligne à remplacer
                        #Supprimer ce paramètre dans la liste des paramètres à vérifier
                        del dict_param[cle]
                        remplacement=True
                        break
                if not remplacement:
                    texte+=ligne	#Copier la ligne sans modification
#        print(texte)	
	#Enregistrer le fichier modifié
        with open("./vars",'w') as f:
            f.write(texte)
    

    def EditConfVpnServer(fichier):
        """Création du fichier de configuration ./server.conf
        Ce fichier est destiné à être copié dans /etc/openvpn/"""
        
        texte="""proto udp
dev tun
ca ca.crt
dh dh2048.pem
ifconfg-pool-persist ipp.txt
keepalive 10 120
tls-auth ta.key
persist-key
persist-tun
verb 3
status openvpn-status.log
explicit-exit-notify 1
"""

        with open(fichier,'r') as f: #Ouvrir le fichier en lecture seule
            config_entiere=yaml.load_all(f)
            listeClients=[]
            listeCcdFiles=[]
            listeFichiersConfig=[]
            for conf in config_entiere:
                for param,v in conf.items():
                    if param=="Easy-RSA":
                        EditEasyRsaVars("./vars",v)
                        listeFichiersConfig.append("{}/var2".format(os.getcwd()))
                    elif param=="Version":
                        if v !=1.0:
                            logmessage("Version du fichier de configuration non pris en charge")
                            exit()
                    elif param=="ServerName":
                       serverName=v
                    elif param=="Network":
                        texte+="server " + v["virtualNetwork"]+"\n"                      
                        if checked_ip(v["wanInterface"]):
                            texte+="local " + v["wanInterface"]+"\n"
                            port=str(v["ipPort"])
                        texte+="port " + str(port)+"\n"
                        texte+='push "route  '+ v["lanNetwork"]+'"\n'
                    elif param=="Clients":
                        if not os.path.isdir("./ccd"):
#                        if not os.path.isdir("/etc/openvpn/ccd"):
                            print('here')
                            logmessage("Création du répertoire CCD")
                            os.mkdir("./ccd")
#TODO:                            os.mkdir("/etc/openvpn/ccd")
                        texte+="client-config-dir ccd\n"
                        
                        chemin=os.getcwd()

                        for param2,t in v.items():
                            logmessage("Création d'une route vers le LAN derrière le client '{}'".format(param2))
                            listeClients.append(param2)
                            
                            exec_command('echo "iroute {}" > ./ccd/{}'.format(t["lanNetwork"],param2))
                            
                            listeCcdFiles.append("{}{}".format(chemin,param2))

                            texte+="route " + t["lanNetwork"]+'\n'
                    else:
                        print("Le paramètre '{}' n'est pas reconnu !!!".format(param))
        
        texte+="cert {}.crt\nkey {}.key\n".format(serverName,serverName)
        
        print(texte)
        print(listeClients)
        print(listeCcdFiles)
        
        fic='{}/server.conf'.format(os.getcwd())
        with open(fic,'w') as f:
            f.write(texte)
        listeFichiersConfig.append(fic)
        
        
        texte="""Version: 1.0
ServerName: {}
Port: {}
ClientName: {}""".format(serverName,port)
        print(texte)
        
        fic='{}/mgyvpnserver.cnf.yaml'.format(os.getcwd())
        with open(fic,'w') as f:
            f.write(texte)
        listeFichiersConfig.append(fic)
        
        return serverName, listeClients, listeCcdFiles, listeFichiersConfig
    
    
    def EditConfVpnClient(fichier):
        """Création du fichier de configuration ./client.conf
        Ce fichier est destiné à être copié dans /etc/openvpn/"""
        texte="""
client
dev tun
proto utp
resolv-retry infinite
nobind
persist-key
persist-tun
remorte-cert-tls server
tls-auth ta.key 1
#cipher AES-256-CBC
verb 3
"""
        with open(fichier,'r') as f: #Ouvrir le fichier en lecture seule
            config_entiere=yaml.load_all(f)
            for conf in config_entiere:
                for param,v in conf.items():
                    if param=="Version":
                        if v !=1.0:
                            logmessage("Version du fichier de configuration non pris en charge")
                            exit()
                    elif param=="ServerName":
                       serverName=v
                    elif param=="Port":
                        port=str(v)
                    else:
                        print("Le paramètre '{}' n'est pas reconnu !!!".format(param))
        clientName=sys.argv[3]
        texte+="remote {} {}\nca ca.crt\n{}.key\n{}.crt\n".format(serverName,port,clientName,clientName)
        fic="{}/client.conf".format(os.getcwd())
        with open(fic,'w') as f:
            f.write(texte)

        return clientName, fic



    def show_config():
        """Cette fonction affiche le fichier de configuration"""
        print("./mgyvpn.server.yaml")

    def print_help():
        """Cette fonction affiche l'aide pou rle module"""
        print("""Syntaxe des commandes du module mgyvpn :

Pour installer un serveur openvpn:
    create server
        
Pour installer un client openvpn
    create client ClientName -d keysDirectory
                    
    - ClientName est le nom réseau (et non l'adresse ip) du client 
    - keysDirectory est le répertoire sont copiées les clés de sécurité sur le client Openvpn

Ces commandes doivent être exécutées en mode administrateur

        """)


    #TODO  
    #Vérifier l'accès à Internet

    
    print(sys.argv)
    
#    mode_status=('m_none','m_create_server','m_create_client','m_add_client')
    
    def parse_arguments(arg):
        """Cette fonction détermine s'il est question de :
        - Créer un serveur OPENVPN
        - Déclarer un client OPENVPN sur le serveur
        - Créer un client OPENVPN"""

        fichiersACopier=[]
        mode_='m_none'
        if sys.argv[1]=='create':
            if arg[2]=='server':
                mode_='m_create_server'
                logmessage("Création d'un serveur OpenVpn")
            elif arg[2]=='client':
                if arg[3]:
                    if arg[4]=='-d' and arg[5]:
                        #TODO: check either sys.argv[5] is a directory 
                        try:
                            fichiers=['ca.crt',"ta.key","dh2048.pem","{}.crt".format(arg[3]),'{}.key'.format(arg[3]),"mgyvpnserver.cnf.yaml"]
                            i=0
                            for f in fichiers:
                                fic="{}/{}".format(arg[5],f)
                                if not os.path.isfile(fic):
                                    logmessage("La clé '{}' est manquante".format(f))
                                else:
                                    i+=1
                                    fichiersACopier.append(fic)
                            if i!=len(fichiers):
                                raise Exception("Toutes les clés ne sont pas présentes")
                            mode_='m_create_client'
                            logmessage("Création du client OpenVpn nommé '{}'".format(arg[3]))
                            logmessage("Les clés de sécurité seront importées du dossier '{}'".format(arg[5]))
                        except:
                            pass
                    else:
                        print_help()
                else:
                    print_help()
            else: 
                print_help()
        else: 
            print_help()
        
        return mode_, fichiersACopier

    
    
    mode_='m_none'
    
    try:
        mode_, fichiersACopierSurLeClient = parse_arguments(sys.argv)
        if mode_=='m_none':
            raise Exception()
    except:
        logmessage("L'installation est interrompue à la suite d'erreurs")
        exit()

    
    logmessage("Configuration d'OpenVPN")	
    
    if mode_=='m_create_server':
        serverName, listeClients, listeCcdFiles, listeFichiersConfig = EditConfVpnServer("./mgyvpn.server.yaml")
    elif mode_=='m_create_client':
        clientName, clientConfFile=EditConfVpnClient("{}/mgyvpnserver.cnf.yaml".format(sys.argv[5]))
    

    #Mise à jour du système
    etape="Mise à jour du système"
#    exec_command("apt-get install -y squid",etape)
    exec_command("apt-get -y update && apt-get -y upgrade",etape)
    
    exit()

    #Installation d'OpenVPN
    etape="Installation d'OpenVPN"
    exec_command("apt-get install -y openvpn=2.4.4-2ubuntu1.3 -V",etape)

    #Installation de easy-rsa
    if mode_=='m_create_server':
        etape="Installation de easy-rsa"
        exec_command("apt-get install -y easy-rsa=2.2.2-2 -V",etape)

        os.mkdir("mkdir /etc/openvpn/easy-rsa/")

        exec_command("cp -r usr/share/easyrsa/* /etc/openvpn/easy-rsa/")
        exec_command("ln -s /etc/openvpn/openssl.cnf /etc/openvpn/openssl-1.0.0.cnf")

        #TODO: Editer le fichier "/etc/openvpn/easy-rsa/vars"

        #Changer de répertoire de travail
        os.chdir("/etc/openvpn/")

        etape="Générer le Master Authority Certificate (CA)"
        exec_command("./source vars",etape) 
        exec_command("./clean-all")
        exec_command("./build-ca")

        etape="Générer la clé d'authentification TLS (TA)"
        exec_command("./openvpn --genkey --secret ./easy-rsa/keys/ta.key",etape)

        etape="Création d'un certificat et d'une clé privée pour le serveur"
        exec_command("/etc/openvpn/build-key-server {}".format(serverName),etape)

        etape="Générer les paramètres DH"
        exec_command("./build-dh", etape) 

        etape="Copie des certificats dans le répertoire de travail"
        os.chdir("./easy-rsa/keys")
        exec_command("cp {}.crt {}.key ca.crt dh2048.pem ta.key /etc/openvpn/".format(serverName,serverName),etape)

        etape="Créer les certificats pour les client distant"

        os.chdir("/etc/openvpn/")
        exec_command("./build-key {}".format(clientName),etape) #TODO: Mettre à jour les noms d'hôte dans une boucle

    #TODO: copier sur VPNDistant les fichiers VPNDistant.crt, VPNDistant.key du dossier /etc/openvpn/easy-rsa/keys 
    #et aussi ta.key et ca.crt

        logmessage("Créer le dossier ./ccd")
        if not os.isdir:
            os.mkdir("./ccd") #Créer lo dossier si cela n'existe pas
        
        for fic in listeCcdFiles:
            exec_command("cp {} ./ccd".format(fic))

        #Mise à jour des fichiers de configuration vars server et mgyyvpnserver.cnf
        for fic in listeFichiersConfig:
            exec_command("cp {} ./".format(fic))

        for fic in listeClients:
            etape="Génération de la clé de sécurité pour le client {}".format(fic)
            exec_command("./easy-rsa/build-key {}".format(fic),etape) #Mettre à jour les noms d'hôte dans une boucle
        
        etape="Redémarrage du serveur"
#        exec_command("systemctl restart openvpn@server",etape)
    
    
    else: #Cas d'une machine cliente
        os.chdir("/etc/openvpn/")
        
        for fic in fichiersACopierSurLeClient:
            exec_command("cp {} ./".format(fic))

        #Substitution du fichier de configuration
        exec_command("cp {} ./".format(clientConfFile))

    #TODO Récupérer sur le serveur les clés du client et au besoin les supprimer (faire de ceci un paramètre du module) sur le serveur

    etape="Redémarrage du client"
    #exec_command("systemctl restart openvpn@client",etape)
    
    logmessage("Vous avez réussi, votre VPN est installé !!!")

except subprocess.CalledProcessError:
    logmessage("Le script s'est arrêté à cause d'une exception du type 'CalledProcessError'")
except ZeroDivisionError:
    logmessage("Erreur de division par 0")
else:
    logmessage("Le script s'est arrêté à cause d'une erreur indéterminée")
finally:
    logmessage('Fin du script')
    logfile.close()
  
