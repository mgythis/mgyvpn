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
  print(titre)
  try:
    res=subprocess.run(macommande, shell=True,  stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    print("Fin de l'opération !")
  except CalledProcessError as e:
    print(e.message()) #TODO Enregistrer l'erreur et quitter le programme
    raise e

#TODO  
#Vérifier l'accès à Internet

try:

  #Mise à jour du système
  def exec_command("apt-get -y update && apt-get -y upgrade","Mise à jour du système")
  
  #Installation d'OpenVPN
  def exec_command("apt-get install -y openvpn=2.4.4-2ubuntu1.3 -V","Installation d'OpenVPN")

  #Installation de easy-rsa
  def exec_command("apt-get install -y easy-rsa=2.2.2-2 -V","Installation de easy-rsa")
 
 
except: 
  
