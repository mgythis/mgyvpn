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
#errorlogfile=open('./mgyvpn.error.log','w')
#sys.stderr=(errorlogfile)

#lié à Signal
def fermeture(signal, frame):
   """Cette fonction est appelée quand l'excécution du script est interrompue"""
  #TODO Enregistrer un log de fermeture inopinée 
  sys.exit(0) 
  

#TODO  
#Vérifier l'accès à Internet

try:
  #Mise à jour du système
  res=subprocess.run("apt-get install update -y && apt-get upgrade -y", capture_output=True, text=True, check=True)
  try:
    res.return_code() #Génère une exception de type CalledProcessError en cas d'absence d'erreur 
  except CalledProcessError:
    pass #TODO Enregistrer l'erreur et quitter le programme
  
  #Installation d'OpenVPN
  res=subprocess.run("apt-get install openvpn=2.4.4-2ubuntu1.3 -V -y", capture_output=True, text=True, check=True)
  try:
    res.return_code() #Génère une exception de type CalledProcessError en cas d'absence d'erreur 
  except CalledProcessError:
    pass #TODO Enregistrer l'erreur et quitter le programme

  #Installation de easy-rsa
  res=subprocess.run("apt-get install easy-rsa=2.2.2-2 -V -y", capture_output=True, text=True, check=True)
  try:
    res.return_code() #Génère une exception de type CalledProcessError en cas d'absence d'erreur 
  except CalledProcessError:
    pass #TODO Enregistrer l'erreur et quitter le programme
  apt-get install easy-rsa=2.2.2-2 -V -y
 
except: 
  
