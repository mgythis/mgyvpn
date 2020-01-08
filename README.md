<h1>Script Python pour le d&eacute;ploiement de OpenVPN sur des machines sous Ubuntu</h1>
<p>Ce script permet une installation automatique de Openvpn sous linux. Il a &eacute;t&eacute; test&eacute; sur Ubuntu 18.04 LTS avec la version 3 de Python.</p>
<h3><strong>Description de la configuration </strong></h3>
<p><em>mgyvpn</em> permet au LAN derri&egrave;re le client VPN d'acc&eacute;der au LAN derri&egrave;re le serveur et vice-versa. Pour ce faire, avant l'ex&eacute;cution du script, il est n&eacute;cessaire que les postes clients et le poste serveurs soient joignables l'un l'autre au travers de leurs interfaces WAN.</p>
<h3><strong>Conditions particuli&egrave;res : </strong></h3>
<ol>
<li>Le script doit &ecirc;tre ex&eacute;cut&eacute; en tant que root</li>
<li>Le poste sur lequel openvpn va &ecirc;tre install&eacute; doit &ecirc;tre connect&eacute; &agrave; Internet</li>
<li>Pour une ex&eacute;cution du script &agrave; distance via SSH, il est important de configurer le compte de l'utilisateur SSH pour ex&eacute;cuter les commandes en mode SUDO sans confirmation de mot de passe</li>
<li>Avant l'ex&eacute;cution du script sur un &eacute;ventuel client OpenVPN il convient de copier les cl&eacute;s de s&eacute;curit&eacute; g&eacute;n&eacute;r&eacute;es sur le serveur dans un dossier de la machine du client. Par d&eacute;faut le script cherchera les cl&eacute;s de s&eacute;curit&eacute;s dans /root/mgyvpn/</li>
<li>Les postes clients et serveurs doivent avoir leur nom d'h&ocirc;te configur&eacute; dans les fichiers /etc/hosts &agrave; moins d'&ecirc;tre enregistr&eacute;s sur un DNS. En effet les noms d'h&ocirc;tes serviront pour pour nommer les cl&eacute;s de s&eacute;curit&eacute;. Clients et serveur devront pouvoir &ecirc;tre joints leur nom d'h&ocirc;te sur le WAN.</li>
</ol>
<h3><strong>Installation</strong></h3>
<p>Pour mettre en place une ou plusieurs liaisons VPN impliquant un serveur VPN unique, proc&eacute;der comme suit :</p>
<h4>Sur le serveur VPN&nbsp;</h4>
<ol>
<li>Modifier le fichier <a href="https://github.com/mgythis/mgy-openvpn/mgyopenvpn.server.yaml">mgyvpn.server.yaml</a> pour correspondre &agrave; votre installation</li>
<li>Ex&eacute;cuter la commande ci-dessous en tant que super utilisateur :
<blockquote>#mgyvpn.py create server</blockquote>
</li>
<li>Copier depuis /etc/openvpn du serveur OpenVPN vers un dossier de votre choix sur les clients VPN les fichiers ci-dessous:
<ul style="list-style-type: square;">
<li>ta.key</li>
<li>ca.crt</li>
<li>NomDuClient.key</li>
<li>NomDuClient.crt</li>
<li>dh2048.pem</li>
<li>mgyvpn.client.yaml</li>
</ul>
</li>
</ol>
<h4>Sur chaque client VPN</h4>
<p style="padding-left: 30px;">Ex&eacute;cuter la commande :</p>
<blockquote>
<p style="padding-left: 30px;">#mgypvp.py add client <em>NomDelaMachineCliente</em> -d <em>DossierDesClesDeSecurite&nbsp;</em></p>
</blockquote>
<p style="padding-left: 30px;">Remplacer les mots-cl&eacute;s&nbsp;<em>NomDelaMachineCliente</em> et&nbsp;<em>DossierDesClesDeSecurite</em> par les informations correspondantes dans la commande ci-dessus</p>
<h3>Auteur</h3>
<p style="padding-left: 30px;">Berthis Mongouya : <a href="mailto:erthis@gmail">erthis@gmail.com</a></p>
<h3>Licence :</h3>
<p style="padding-left: 30px;"><a href="https://github.com/mgythis/mgy-openvpn/LICENCE.txt.txt">GNU GPL 3.0</a></p>
<hr />
<p><span style="color: #333333;"><em>mgyvpn Copyright 2020 Berthis Mongouya</em></span></p>
