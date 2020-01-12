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
import traceback
from socket import inet_aton
from copy import deepcopy

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
            #From socket module
            inet_aton(str(ip_addr))
            return True
        except:
            logmessage("l'adresse IP '{}' n'est pas valide".format(str(p_addr)))
            raise Exception("IP '{}' non valide".format(str(ip_addr)))  


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
        print(texte)	
	#Enregistrer le fichier modifié
        with open(fichier,'w') as f:
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
        rsaDict={}
        with open(fichier,'r') as f: #Ouvrir le fichier en lecture seule
            config_entiere=yaml.load_all(f)
            listeClients=[]
            listeCcdFiles=[]
            listeFichiersConfig=[]
            listeSshUsers={}
            for conf in config_entiere:
                for param,v in conf.items():
                    if param=="Easy-RSA":
                        rsaDict=deepcopy(v)
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
                            logmessage("Préparation du répertoire CCD")
                            os.mkdir("./ccd")
                        texte+="client-config-dir ccd\n"
                        
                        chemin=os.getcwd()

                        for param2,t in v.items():
                            logmessage("Création d'une route vers le LAN derrière le client '{}'".format(param2))
                            listeClients.append(param2)
                            
                            listeSshUsers[param2]=t["ssh-user"]
                            
                            exec_command('echo "iroute {}" > ./ccd/{}'.format(t["lanNetwork"],param2))
                            
                            listeCcdFiles.append("{}/ccd/{}".format(chemin,param2))

                            texte+="route " + t["lanNetwork"]+'\n'
                    else:
                        print("Le paramètre '{}' n'est pas reconnu !!!".format(param))
        
        texte+="cert {}.crt\nkey {}.key\n".format(serverName,serverName)

        fic='{}/server.conf'.format(os.getcwd())
        with open(fic,'w') as f:
            f.write(texte)
        listeFichiersConfig.append(fic)
        
        texte="""Version: 1.0
ServerName: {}
Port: {}""".format(serverName,port)
        
        fic='{}/mgyvpn.client.yaml'.format(os.getcwd())
        with open(fic,'w') as f:
            f.write(texte)
        listeFichiersConfig.append(fic)
        
        return serverName, listeClients, listeCcdFiles, listeFichiersConfig, rsaDict, listeSshUsers
    
    
    def EditConfVpnClient(fichier):
        """Création du fichier de configuration ./client.conf
        Ce fichier est destiné à être copié dans /etc/openvpn/"""
        texte="""
client
dev tun
proto udp
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

    
    def parse_arguments(arg):
        """Cette fonction détermine s'il est question de :
        - Créer un serveur OPENVPN
        - Déclarer un client OPENVPN sur le serveur
        - Créer un client OPENVPN"""

        fichiersACopier=[]
        mode_='m_none'
    
        if len(arg)<3:
            logmessage(print_help())
            return mode_, fichiersACopier
        
        #Dans le cas de l'exécution sur un client sans spécifier le dossier de récupération du fichier de configuration après l'option -d, indiquer un dossier par défaut
        if len(arg)==4:
            arg.append("-d")
            arg.append("~/mgyvpn/export")
            

        if arg[1]=='create':
            if arg[2]=='server':
                mode_='m_create_server'
                logmessage("Création d'un serveur OpenVpn")
            elif arg[2]=='client':
                if arg[3]:
                    if arg[4]=='-d' and arg[5]:
                        try:
                            fichiers=['ca.crt',"ta.key","dh2048.pem","{}.crt".format(arg[3]),'{}.key'.format(arg[3]),"mgyvpn.client.yaml"]
                            i=0
                            for f in fichiers:
                                fic="{}/{}".format(arg[5],f)
                                if not os.path.isfile(fic):
                                    logmessage("Le fichier '{}' est manquant".format(f))
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

    #Sauvegarder le chemin d'exécution du module afin de pouvoir récupérer les fichiers et dossiers qui y seront générés

    exec_path=os.getcwd()
    
    #Cette variable indique le contexte : création d'un serveur ou création d'un client 
    mode_='m_none'
    
    try:
        
        #Analyse des argurments du module
        mode_, fichiersACopierSurLeClient = parse_arguments(sys.argv)
        if mode_=='m_none':
            raise Exception()
    except:
        logmessage("L'installation est interrompue lors de l'analyse des arguments")
        exit()

    
    logmessage("Configuration d'OpenVPN")	
    
    if mode_=='m_create_server':
        serverName, listeClients, listeCcdFiles, listeFichiersConfig, rsaDict, listeSshusers = EditConfVpnServer("./mgyvpn.server.yaml")
    elif mode_=='m_create_client':
        clientName, clientConfFile=EditConfVpnClient("{}/mgyvpn.client.yaml".format(sys.argv[5]))
    

    #Mise à jour du système
    etape="Mise à jour du système"
#    exec_command("apt-get -y update && apt-get -y upgrade",etape)
    
    #Installation d'OpenVPN
    etape="Installation d'OpenVPN"
    exec_command("apt-get install -y openvpn",etape)
    #exec_command("apt-get install -y openvpn=2.4.4-2ubuntu1.3 -V",etape)

    #Installation de easy-rsa
    if mode_=='m_create_server':
        etape="Installation de easy-rsa"
        exec_command("apt-get install -y easy-rsa",etape)
        
        #exec_command("apt-get install -y easy-rsa=2.2.2-2 -V",etape)
        
        logmessage("Création du dossier easy-rsa")
        try:
            os.mkdir("/etc/openvpn/easy-rsa/")
        except:
            pass
        try:
            exec_command("cp -r /usr/share/easy-rsa/* /etc/openvpn/easy-rsa/")
        except:
            pass
        try:
            exec_command("ln -s /etc/openvpn/easy-rsa/openssl-1.0.0.cnf /etc/openvpn/easy-rsa/openssl.cnf")
        except:
            pass

        #Changer de répertoire de travail
        os.chdir("/etc/openvpn/easy-rsa/")

        #Editer le fichier "/etc/openvpn/easy-rsa/vars"
        EditEasyRsaVars("./vars",rsaDict)

        etape="Générer le Master Authority Certificate (CA)"
        exec_command(". ./vars && ./clean-all && ./build-ca --batch",etape)
        
        etape="Générer la clé d'authentification TLS (TA)"
        exec_command("openvpn --genkey --secret ./keys/ta.key",etape)

        etape="Création d'un certificat et d'une clé privée pour le serveur"
        exec_command(". ./vars && ./build-key-server --batch {}".format(serverName),etape)

        etape="Générer les paramètres DH"
        exec_command(". ./vars &&  ./build-dh", etape) 

        os.chdir("/etc/openvpn/easy-rsa/keys")
        etape="Copie des certificats dans le répertoire de travail"
        exec_command("cp {}.crt {}.key ca.crt dh2048.pem ta.key /etc/openvpn/".format(serverName,serverName),etape)

        os.chdir("/etc/openvpn/easy-rsa/")
        etape="Créer les certificats de sécurité pour les clients"
        for clientName in listeClients:
            exec_command(". ./vars && ./build-key --batch {}".format(clientName),etape) 

        os.chdir("/etc/openvpn/")
        logmessage("Créer le dossier ./ccd")
        if not os.path.isdir("./ccd"):
            os.mkdir("./ccd") #Créer lo dossier si cela n'existe pas
        
        for fic in listeCcdFiles:
            exec_command("cp {} ./ccd/".format(fic))

        #Copie des fichiers de configuration server.conf et mgyyvpn.server.yaml dans /etc/openvpn
        for fic in listeFichiersConfig:
            exec_command("cp {} ./".format(fic))

        
        #Création du dossier ./export dans le répertoire d'exécution du module mgyvpn
        #Ce répertoire contiendra des dossiers portant le nom de chaque client VPN
        #Dans chacun des dossiers on trouvera toutes les clés de sécurité nécessaires et un fichier de conviguration yaml
        if not os.path.isdir("{}/export".format(exec_path)):
            os.mkdir("{}/export".format(exec_path)) #Créer lo dossier si cela n'existe pas
        chemin="{}/export".format(exec_path)
        for fic in listeClients: #Parcourir la liste des clients VPN
            if not os.path.isdir("{}/{}".format(chemin,fic)):
                os.mkdir("{}/{}".format(chemin,fic)) #Créer un dossier pour chaque client
                try:
                    os.chdir("/etc/openvpn")
                    exec_command("cp -f ca.crt dh2048.pem ta.key mgyvpn.client.yaml {}/{}/".format(chemin,fic))
                    os.chdir("/etc/openvpn/easy-rsa/keys")
                    exec_command("cp -f ./{}.crt ./{}.key {}/{}/".format(fic,fic,chemin,fic))
                    
                except:
                    pass

        #Copier les fichiers par SSH sur les clients 
        #en utilisant le compte ssh indiqué dans le fichier de configuration
        for fic in listeClients:
            try:
                #exec_command("scp -r {}/{} {}@{}:/root".format(chemin,fic,listeSshusers[fic],fic))
                logmessage("scp -r {}/{} {}@{}:./mgyvpn".format(chemin,fic,listeSshusers[fic],fic))
            except:
                logmessag("Erreur dans l'exportation des clés sur le client '{}'".format(fic))
        
        etape="Redémarrage du server"
        #exec_command("systemctl restart openvpn@server",etape)
     
    else: #Cas d'une machine cliente
        os.chdir("/etc/openvpn/")
        
        #Récupérer sur le serveur les clés du client et au besoin les supprimer (faire de ceci un paramètre du module) sur le serveur
        for fic in fichiersACopierSurLeClient:
            exec_command("cp {} ./".format(fic))

        #Substitution du fichier de configuration
        exec_command("cp {} ./".format(clientConfFile))

        etape="Redémarrage du client"
        #exec_command("systemctl restart openvpn@client",etape)
    
    logmessage("Vous avez réussi, votre VPN est installé !!!")

except subprocess.CalledProcessError:
    logmessage("Le script s'est arrêté à cause d'une exception du type 'CalledProcessError'")
else:
    logmessage("Le script s'est arrêté à cause d'une erreur indéterminée")
    logmessage(traceback.format_exc())
finally:
    logmessage('Fin du script')
    logfile.close()
  
