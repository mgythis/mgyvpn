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

#Redirection des messages d'erreur
logfile=open('./mgyvpn.log','w')
#TODO: Try Finally pour ce flux
sys.stderr=logfile

def logmessage(msg,f=logfile):
	"""Procédure de gestion des logs, et d'affichage sur la console"""
	print(msg)
	f.write(msg+'\n')

#lié à Signal
def fermeture(signal, frame):
	"""Cette fonction est appelée quand l'excécution du script est interrompue"""
	#TODO Enregistrer un log de fermeture inopinée 
	logmessage("L'exécution du script a été interrompue !!!")
	sys.exit(0) 

#Assignation d'une fonction au signal SIGINT
signal.signal(signal.SIGINT,fermeture)

def exec_command(macommande,titre=""):
	"""Cette fonction exécute une commande système et retourne un résultat
	Les erreurs sont consignées dans le fichier error.log"""
	if not titre:
		#TODO: Gestion des caractères spéciaux
		titre=macommande
	else:
		titre+="\n"+macommande
	
	#Mise à jour du log
	logmessage(titre)
	
	try:
		res=subprocess.run(macommande, shell=True,  stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
		#print("Fin de l'opération !")
	except CalledProcessError as e:
		logmessage(e) #TODO Enregistrer l'erreur et quitter le programme
		raise e
		
def EditEasyRsaVars(fichier,dict_param):
	"""Modification du fichier de configuration easy-rsa/vars"""
	texte=''
	with open(fichier,'r') as f: #Ouvrir le fichier en lecture seule
		for ligne in f: #Parcourir les lignes du ficher vars
			remplacement=False
			for cle in dict_param: #Parcourir la liste des paramètres à customiser
				p='^export ('+cle+').='
				if re.match(p,ligne): #Vérifier si la ligne correspond à un paramètre
					texte+='export {}="{}"\n'.format(cle,dict_param[cle]) #Créer la ligne à remplacer
					#Supprimer ce paramètre dans la liste des paramètres à vérifier
					del dict_param[cle]
					remplacement=True
					break
			if remplacement:
				texte+=ligne	#Copier la ligne sans modification
					
	#Enregistrer le fichier modifié
	with open(fichier,'w') as f:
		f.write(texte)
		

def EditOpenVpn(fichier, serveur=True):
        """Modification du fichier de configuration /etc/openvpn/server.conf ou client.conf"""
        with open(fichier,'r') as f: #Ouvrir le fichier en lecture seule
                config_entiere=yaml.load_all(f)
                for conf in config_entiere:
                        for param,v in conf.items():
                                if param=="Easy-RSA":
                                        print(v)
                                        EditEasyRsaVars("./vars",v)
                                else:
                                        print(param,'->',v)
					
logmessage("Vérification du fichier de configuration")	
EditOpenVpn("./mgyvpn.server.yaml")


	
#TODO  
#Vérifier l'accès à Internet

try:

	#Mise à jour du système
	etape="Mise à jour du système"
	exec_command("apt-get -y update && apt-get -y upgrade",etape)

	#Installation d'OpenVPN
	etape="Installation d'OpenVPN"
	exec_command("apt-get install -y openvpn=2.4.4-2ubuntu1.3 -V",etape)

	#Installation de easy-rsa
	etape="Installation de easy-rsa"
	exec_command("apt-get install -y easy-rsa=2.2.2-2 -V",etape)

	os.mkdir("mkdir /etc/openvpn/easy-rsa/")
	
	exec_command("cp -r usr/share/easyrsa/* /etc/openvpn/easy-rsa/")
	exec_command("ln -s /etc/openvpn/openssl.cnf /etc/openvpn/openssl-1.0.0.cnf")

	#TODO: Editer le fichier "/etc/openvpn/easy-rsa/vars"

	#Changer de répertoire de travail
	os.chdir("/etc/openvpn/")

	etape="Générer le Master Authority Certificate (CA)"
	#exec_command(./source vars",etape) 
	#exec_command("./clean-all")
	#exec_command("./build-ca")

	etape="Générer la clé d'authentification TLS (TA)"
	exec_command("./openvpn --genkey --secret ./easy-rsa/keys/ta.key",etape)

	etape="Création d'un certificat et d'une clé privée pour le serveur"
	exec_command("/etc/openvpn/build-key-server {}".format(hote_local),etape) #TODO: Mettre à jour le nom d'hôte

	etape="Générer les paramètres DH"
	exec_command("./build-dh", etape) 

	etape="Copie des certificats dans le répertoire de travail"
	chdir("./easy-rsa/keys")
	exec_command("cp {}.crt {}.key ca.crt dh2048.pem ta.key /etc/openvpn/".format(hote_local,hote_local),etape) #TODO: Mettre à jour le nom d'hôte

	etape="Créer le certificat pour le client distant"

	os.chdir("/etc/openvpn/")
	exec_command("./build-key {}".format(hote_distant),etape) #TODO: Mettre à jour le nom d'hôte

	#TODO: copier sur VPNDistant les fichiers VPNDistant.crt, VPNDistant.key du dossier /etc/openvpn/easy-rsa/keys 
	#et aussi ta.key et ca.crt

	#TODO: Spécifier une adresse réseau pour les interfaces virtuelles à créer avec la directive :
	#server 194.0.0.0 255.255.255.248

	#TODO: Récupérer et modifier le fichier server.conf, notamment les paramètres CA, CRT, DH et KEY
	#Indiquer aux clients l'accès au LAN serveur

	#TODO: Activer le routage par le VPN vers le LAN distant avec les directives :
	#client-config-dir ccd
	#route 10.0.2.0 255.255.255.0

	logmessage("Créer le dossier .ccd")
	if not os.isdir:
		os.mkdir("./ccd") #TODO: Créer lo dossier si cela n'existe pas

	#TODO: Mettre à jour les variables ci-dessous
	exec_command("echo iroute {} {} > ./ccd/{}".format(lan_distant,masque_distant,hote_distant)) 

	etape="Redémarrage du serveur"
	exec_command("systemctl restart openvpn@server",etape)
	
	####Client
	
	#TODO: Récupérer et modifier le fichier client.conf, notamment les paramètres CA, CRT et KEY
	#TODO: Définissez l'adresse WAN du serveur en modifiant le mot clé Remote
	
	#TODO Récupérer sur le serveur les clés du client et au besoin les supprimer (faire de ceci un paramètre du module) sur le serveur
	
	etape="Redémarrage du client"
	exec_command("systemctl restart openvpn@client",etape)

except CalledProcessError:
	print("Le script s'est arrêté à cause d'une erreur fatale de type 'CalledProcessError'")
else:
  print("Le script s'est arrêté à cause d'une erreur indéterminée")
  
