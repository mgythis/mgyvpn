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
from os import chdir

#Redirection des messages d'erreur
errorlogfile=open('./mgyvpn.error.log','w')
sys.stderr=errorlogfile

#lié à Signal
def fermeture(signal, frame):
   """Cette fonction est appelée quand l'excécution du script est interrompue"""
  #TODO Enregistrer un log de fermeture inopinée 
  print("L'exécution du script a été interrompue !!!")
  sys.exit(0) 

#Assignation d'une fonction au signal SIGINT
signal.signal(signal.SIGINT,fermeture)

def exec_command(macommande,titre=""):
  if not titre:
    #TODO: Gestion des caractères spéciaux
    titre=macommande
   else:
    titre+="\n"+macommande"
  print(titre)
  try:
    res=subprocess.run(macommande, shell=True,  stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    #print("Fin de l'opération !")
  except CalledProcessError as e:
    print(e.message()) #TODO Enregistrer l'erreur et quitter le programme
    raise e

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
  
  exec_command("mkdir /etc/openvpn/easy-rsa/")
  exec_command("cp -r usr/share/easyrsa/* /etc/openvpn/easy-rsa/")
  exec_command("ln -s /etc/openvpn/openssl.cnf /etc/openvpn/openssl-1.0.0.cnf")
  
  #TODO: Editer le fichier "/etc/openvpn/easy-rsa/vars"
  
  #Changer de répertoire de travail
  chdir("/etc/openvpn/")
  
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
  chdir("/etc/openvpn/")
  exec_command("./build-key {}".format(hote_distant),etape) #TODO: Mettre à jour le nom d'hôte
  
  #TODO: copier sur VPNDistant les fichiers VPNDistant.crt, VPNDistant.key du dossier /etc/openvpn/easy-rsa/keys 
  #et aussi ta.key et ca.crt
  
  #TODO: Spécifier une adresse réseau pour les interfaces virtuelles à créer avec la directive :
	#server 194.0.0.0 255.255.255.248
  
  #TODO: Récupérer modifier le fichier server.conf, notamment les paramètres CA, CRT, DH et KEY
  #Indiquer aux clients l'accès au LAN serveur

  #TODO: Activer le routage par le VPN vers le LAN distant avec les directives :
	#client-config-dir ccd
	#route 10.0.2.0 255.255.255.0
  
  exec_command("mkdir ./ccd") #TODO: Créer lo dossier si cela n'existe pas
  
  #TODO: Mettre à jour les variables ci-dessous
  exec_command("echo iroute {} {} > ./ccd/{}".format(lan_distant,masque_distant,hote_distant)) 

  #exec_command("")
  #exec_command("")
  #exec_command("") 
  #exec_command("")
  #exec_command("")
  #exec_command("")
  #exec_command("")

  except CalledProcessError:
  #Echec chdir
  print("Le script s'est arrêté à cause d'une erreur fatale")
else:
  print("Le script s'est arrêté à cause d'une erreur indéterminée")
  
