#!/usr/bin/python3.6
# -*- coding: utf8 -*-
"""mgyvpn.py
Ce script python permet d'automatiser l'installation d'OpenVPN avec chiffrement sous easy-rsa
entre un noeud serveur et des noeuds clients
Il a été réalisé et testé sous Ubuntu Server LTS 18.04 et Python 3.6
Il doit être exécuté sur le serveur OPENVPN
Il est associé à un fichier de configuration nommé mgyvpn.server.yaml
Pour plus d'information, se rendre sur https://github.com/mgythis/mgyvpn
"""
###########################################################################
# This program is free software: you can redistribute it and/or modify it #
#    under the terms of the GNU General Public Licence as published by    #
#    the Free Software Foundation, either version 3 of the licence, or    #
#                          any later version.                             #
#                                                                         #
#      This program is distributed in the hope hat it will be usefull,    #
#      but WITHOUT ANY WARRANTY; without even the implied warranty of     #
#            MERCHANTABILIY or FITENSS FOR A PARTICUA PURPOSE.            #  
#            See the General Public Licence form more deatails            #
#                                                                         #
#                  Par Berthis Mongouya, erthis@gmail.com                 #
#                   Copyright (C) 2020 Berthis Mongouya                   #
#                         Licence GNU/GPL 3.0                             #
###########################################################################

import sys
import signal
import subprocess
import os
import re
import yaml
import traceback
import ipaddress
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
        """Cette fonction produit une exception si l'adresse IP fournie n'est pas valide"""
        try:
            ipaddress.ip_address(ip_addr)
        except:
            logmessage("l'adresse IP '{}' n'est pas valide".format(ip_addr))
            raise  
    
    def check_net_ip(ipmask):
        try:
            ipmask=ipmask.strip()
            ipmask=ipmask.replace('  ',' ')
            ipmask=ipmask.replace(' ','/')
        
            ipaddress.ip_network(ipmask)
        except:
            logmessage("L'adresse de réseau '{}' n'est pas valide !".format(ipmask))
            raise

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
        
        for cle in dict_param:
            texte+='export {}="{}"\n'.format(cle,dict_param[cle])
        
	#Enregistrer le fichier modifié
        with open(fichier,'w') as f:
            f.write(texte)
    
    def check_entry(regStr,entry,errorMsg):
        """Cette fonction vérifie la valeur entry avec une expression régulière; en cas de non conformité une exception est générée avec enregistrement dans le journal"""
        if re.match(regStr,entry) is None:
            logmessage("'{}': ".format(entry) + errorMsg)
            raise Exception()

    def EditConfVpnServer(fichier):
        """Création du fichier de configuration ./server.conf
        Ce fichier est destiné à être copié dans /etc/openvpn/"""
        
        texte="""proto udp
dev tun
ca ca.crt
dh dh2048.pem
ifconfig-pool-persist /var/log/openvpn/ipp.txt
status /var/log/openvpn/openvpn-status.log
keepalive 10 120
tls-auth ta.key 0
cipher AES-256-CBC
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
            port=''
            for conf in config_entiere:
                for param,v in conf.items():
                    if param=="Easy-RSA":
                        rsaDict=deepcopy(v)
                    elif param=="Version":
                        if v !=1.0:
                            logmessage("Version du fichier de configuration non pris en charge")
                            exit()
                    elif param=="ServerName":
                        check_entry(r"\w?",v,"Nom de serveur invalide !") 
                        serverName=v
                    elif param=="Network":
                        checked_ip(v["wanInterface"])
                        texte+="local " + v["wanInterface"]+"\n"
                            
                        port=str(v["ipPort"])
                        check_entry(r"^\d+$",port,"Numéro de port invalide")                    
                        texte+="port " + port+"\n"
                        
                        check_net_ip(v['virtualNetwork'])
                        texte+="server {}\n".format(v["virtualNetwork"])
                        
                        check_net_ip(v["lanNetwork"])
                        texte+='push "route  {}"\n'.format(v['lanNetwork'])
                        print(texte)
                    elif param=="Clients":
                        if not os.path.isdir("./ccd"):
                            logmessage("Préparation du répertoire CCD")
                            os.mkdir("./ccd")
                        texte+="client-config-dir ccd\n"
                        
                        chemin=os.getcwd()

                        for param2,t in v.items():
                            
                            check_entry(r"\w?",param2,"Nom d'hôte invalide !") 
                            
                            logmessage("Création d'une route vers le LAN derrière le client '{}'".format(param2))
                            listeClients.append(param2)
                            
                            check_entry(r"\w?",t["ssh-user"],"Nom d'utilisateur invalide !") 
                            listeSshUsers[param2]=t["ssh-user"]
                            
                            
                            check_net_ip(t["lanNetwork"])
                            
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
Port: {}
""".format(serverName,port)
        
        fic='{}/mgyvpn.client.yaml'.format(os.getcwd())
        with open(fic,'w') as f:
            f.write(texte)
        listeFichiersConfig.append(fic)

        return serverName, listeClients, listeCcdFiles, listeFichiersConfig, rsaDict, listeSshUsers
    
    
    def EditConfVpnClient(fichier):
        """Création du fichier de configuration ./client.conf
        Ce fichier est destiné à être copié dans /etc/openvpn/"""
        texte="""client
dev tun
proto udp
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
tls-auth ta.key 1
cipher AES-256-CBC
;ns-cert-type server
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
        texte+="remote {} {}\nca ca.crt\nkey {}.key\ncert {}.crt\n".format(serverName,port,clientName,clientName)
        fic="{}/client.conf".format(os.getcwd())
        with open(fic,'w') as f:
            f.write(texte)

        return clientName, fic



    def print_help():
        """Cette fonction affiche l'aide pou rle module"""
        print("""
++++++++++++++++
AIDE SUR MGYVPN
++++++++++++++++

Syntaxe des commandes du module mgyvpn :

Pour installer un serveur openvpn:
    create server
        
Pour installer un client openvpn:
    create client ClientName -d keysDirectory
                    
    - ClientName est le nom réseau (et non l'adresse ip) du client 
    - keysDirectory est le répertoire ou sont copiées les clés de sécurité sur le client Openvpn

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

        if arg[1]=='create': #Création de OpenVpn Server
            if arg[2]=='server':
                mode_='m_create_server'
                logmessage("Création d'un serveur OpenVpn")
            elif arg[2]=='client': #Création de Openvpn Client
                #Gestion d'un dossier de recherche par défaut pour les paramètres d'installation du client openvpn, en l'occurrence c'est le dossier portant le nom réseau du client, dans le répertoire courant
                if len(arg)==3: #Si le nom du client n'est pas spécifié en arguments
                    print_help()
                    return mode_, fichiersACopier
                if len(arg)==4:
                    arg.append("-d")
                if len(arg)==5:
                    arg.append("{}/{}".format(os.getcwd(),arg[3]))
                if arg[3]: #Nom d'hôte du client
                    if arg[4]=='-d' and arg[5]:
                        try:
                            fichiers=['ca.crt',"ta.key","{}.crt".format(arg[3]),'{}.key'.format(arg[3]),"mgyvpn.client.yaml"]
                            i=0
                            for f in fichiers:
                                fic="{}/{}".format(arg[5],f)
                                if not os.path.isfile(fic):
                                    logmessage("Le fichier '{}' est manquant".format(f))
                                else:
                                    i+=1
                                    fichiersACopier.append(fic)
                            if i!=len(fichiers):
                                logmessage("Toutes les clés ne sont pas présentes !!!")
                                raise Exception()
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
    
    #Vérifier que Openvpn n'est pas déjà installé
    if os.path.isfile('/lib/systemd/system/openvpn.service'):
        logmessage("Openvpn est déjà présent sur ce système !")
        logmessage("L'installation ne peut pas se poursuivre !")
        raise Exception()
    
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

    
    logmessage("Préparation de la configuration d'OpenVPN")	
    
    if mode_=='m_create_server':
        serverName, listeClients, listeCcdFiles, listeFichiersConfig, rsaDict, listeSshUsers = EditConfVpnServer("./mgyvpn.server.yaml")
    elif mode_=='m_create_client':
        clientName, clientConfFile=EditConfVpnClient("{}/mgyvpn.client.yaml".format(sys.argv[5]))
      
    #Mise à jour du système
    #Décommenter les deux lignes suivantes si vous souhaitez une mise à jour de la bibliothèque des dépôts avant l'installation
#    etape="Mise à jour du système"
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
        
        logmessage("Configuration de Openvpn")

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
        logmessage("Edition du fichier VARS")
        EditEasyRsaVars("./vars",rsaDict)

        etape="""Générer le Master Authority Certificate (CA)"
        Et les cla et le certificat du serveur"""
        try:
            exec_command(". ./vars && ./clean-all && ./build-ca --batch && ./build-key-server --batch {}".format(serverName),etape)
        except:
            logmessage("Erreur dans la création du maître de certification et des clé et certificat du serveur")
            raise

        etape="Générer la clé d'authentification TLS (TA)"
        try:
            exec_command("openvpn --genkey --secret ./keys/ta.key",etape)
        except:
            logmessage("Erreur dans la création de la clé statique d'authentification TLS")
            raise

        etape="Générer les paramètres DH\nAttention, cette étape peut durer plusieurs minutes"
        try:
            exec_command(". ./vars &&  ./build-dh", etape) 
        except:
            logmessage("Erreur dans la création du paramètre DH")
            raise

        os.chdir("/etc/openvpn/easy-rsa/keys")
        
        etape="Copie des certificats dans le répertoire de travail"
        try:
            exec_command("cp {}.crt {}.key ca.crt dh2048.pem ta.key /etc/openvpn/".format(serverName,serverName),etape)
        except:
            logmessage("Erreur dans la copie des clés et certificat vers le répertoire /etc/openvpn")
            raise
        #Création des ceertificats pour les clients
        os.chdir("/etc/openvpn/easy-rsa/")
        logmessage("Créer les certificats de sécurité pour les clients")
        for clientName in listeClients:
            try:
                exec_command(". ./vars && ./build-key --batch {}".format(clientName),"Création du ceertificat pour {}".format(clientName))
            except:
                logmessage("La création du certificat a échoué")

        #Création du dossier ccd requis pour le routage vers les LANs clients
        
        os.chdir("/etc/openvpn/")
        
        logmessage("Créer le dossier ./ccd")
        if not os.path.isdir("./ccd"):
            os.mkdir("./ccd") #Créer lo dossier si cela n'existe pas
        
        #Copie des fichiers de routage dans le répertoire
        for fic in listeCcdFiles:
            exec_command("cp {} ./ccd/".format(fic))

        #Copie des fichiers de configuration server.conf et mgyyvpn.client.yaml dans /etc/openvpn
        logmessage("Copie des fichiers de configuration")
        for fic in listeFichiersConfig:
            exec_command("mv {} ./".format(fic))

        
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
                    exec_command("cp -f ca.crt ta.key mgyvpn.client.yaml {}/{}/".format(chemin,fic))
                    os.chdir("/etc/openvpn/easy-rsa/keys")
                    exec_command("mv ./{}.crt ./{}.key {}/{}/".format(fic,fic,chemin,fic))
                    
                except:
                    logmessage("Erreur dans la copie de certificats ou fichiers de configuration pour le client '{}'".format(fic))

        #Copier les fichiers par SSH sur les clients 
        #en utilisant le compte ssh indiqué dans le fichier de configuration
        #Puis exécuter le script sur le client
        for fic in listeClients:
            try:
                #Création du dossier d'accueil du logiciel sur le client
                logmessage("Création du dossier d'accueil sur le client '{}'".format(fic))
                exec_command("ssh {}@{} 'mkdir -p /home/{}/mgyvpn'".format(listeSshUsers[fic],fic,listeSshUsers[fic]))
                #Copie des fichiers sur le client
                exec_command("scp -r {}/{} {}@{}:/home/{}/mgyvpn/".format(chemin,fic,listeSshUsers[fic],fic,listeSshUsers[fic]),"Copie des fichiers")

                #Copie du script lui-même sur le client
                exec_command("scp {}/{} {}@{}:/home/{}/mgyvpn/".format(exec_path,sys.argv[0],listeSshUsers[fic],fic,listeSshUsers[fic]),"Déploiement du script sur le client")
                
            except:
                logmessage("Erreur dans l'exportation des clés sur le client '{}'".format(fic))
        
        etape="Démarrage du service"
        exec_command("systemctl start openvpn@server",etape)

        #Installation sur les clients
        for clientName in listeClients:
            try:
                logmessage("Installation du client Openvpn nommé '{}'".format(clientName))
                exec_command("ssh {}@{} 'cd ~/mgyvpn && sudo ./mgyvpn.py create client {}'".format(listeSshUsers[clientName],clientName,clientName))
            except:
                logmessage("Erreur dans l'installation du client VPN '{}'".format(clientName))
     
    else: #Cas d'une machine cliente
        os.chdir("/etc/openvpn/")
        
        #Récupérer sur le serveur les clés du client et au besoin les supprimer (faire de ceci un paramètre du module) sur le serveur
        for fic in fichiersACopierSurLeClient:
            exec_command("cp {} ./".format(fic),"copie de {}".format(fic))

        #Substitution du fichier de configuration
        exec_command("cp {} ./".format(clientConfFile))

        etape="Démarrage du service"
        exec_command("systemctl start openvpn@client",etape)
    

except subprocess.CalledProcessError:
    logmessage("Le script s'est arrêté à cause d'une exception de type CalledProcessError")
except NameError:
    logmessage("Le script s'est arrêté sur une Erreur de type NameError")
except SyntaxError:
    logmessage("Le script s'est arrêté sur une Erreur de type SyntaxError")
except TypeError:
    logmessage("Le script s'est arrêté sur une Erreur de type TypeError")
except FileNotFoundError:
    logmessage("Le script s'est arrêté sur une Erreur de type FileNotFound")
else:
    if mode_=='m_create_server':
        logmessage("Bravo, le serveur OpenVpn est installé et configuré !!!")
    else:
        logmessage("Bravo, le client Openvpn '{}' est installé et configuré !!!".format(clientName))
finally:
    logmessage('Fin du script')
    logfile.close()
  
