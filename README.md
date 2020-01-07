# mgy-openvpn
Script Python pour le déploiement de OpenVPN sur des machines sous Ubuntu

Ce script permet une installation automatique de Openvpn sous linux.
Il a été testé sur Ubuntu 18.04 LTS avec la version 3 de Python.

Description de la configuration OpenVPN
mgyvpn permet au LAN derrière le client VPN d'accéder au LAN derrière le serveur et vice-versa. Pour ce faire, avant l'exécution du script, il est nécessaire que les postes clients et le postes serveurs soient joignables l'un l'autre


Conditions particulières :
1- Il doit être exécuté en tant que root
2- Le poste sur lequel openvpn va être installé doit être connecté à Internet
3- Pour une exécution du script à distance via ssh, il est important de configurer le compte de l'utilisateur ssh pour une exécution des commandes en mode SUDO sans confirmation de mot de passe
4- Avant l'exécution du script sur un éventuel client OpenVPN il convient de copier les clés de sécurité générées sur le serveur dans un dossier de la machine du client.
Par défaut le script cherchera les clés de sécurités dans /root/mgyvpn/
5- Les postes clients et serveurs doivent avoir leur nom d'hôte configuré dans les fichiers /etc/hosts à moins d'être enregistrés sur un DNS. En effet les noms d'hôtes serviront pour pour nommer les clés de sécurité

Installation
modifier le fichier mgyvpn.server.yaml pour correspondre à votre installation

1- Pour installer le serveur openvpn, exécuter la commande ci-dessous :
  #mgyvpn.py create server

2-Pour installer un nouveau client openvpn, modifier le fichier de configuration ci-dessous en rajoutant les paramètres du client puis exécuter la commande ci-dessous sur le serveur openvpn :
  #mgyvpn.py create client
Ensuite copier depuis /etc/openvpn du serveur OpenVPN vers un dossier de votre choix sur le client VPN les fichiers ci-dessous:
  -ta.key
  -ca.crt
  -NomDuClient.key
  -NomDuClient.crt
  -dh2048.pem
  -mgyopenvpnserver.cnf
