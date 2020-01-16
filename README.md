<h1>Script Python pour le d&eacute;ploiement automatique d'un serveur Openvpn et plusieurs clients sous Ubuntu 18.04 LTS</h1>
<p>Ce script r&eacute;alise le d&eacute;ploiement automatique de Openvpn sous linux sur un serveur et plusieurs clients. Il a &eacute;t&eacute; test&eacute; sur Ubuntu 18.04 LTS avec la version 3.6 de Python.&nbsp;</p>
<h3><strong>Description</strong></h3>
<p><em>mgyvpn</em> permet au LAN derri&egrave;re le <em>client</em> VPN d'acc&eacute;der au LAN derri&egrave;re le <em>serveur</em> et vice-versa. Pour ce faire, avant l'ex&eacute;cution du script, il est n&eacute;cessaire que les postes <em>clients</em> et le poste <em>serveur</em> soient joignables l'un l'autre &agrave; travers leurs interfaces WAN gr&acirc;ce &agrave; leurs noms d'h&ocirc;te.</p>
<h3><strong>Conditions particuli&egrave;res : </strong></h3>
<ol>
<li>Le script doit &ecirc;tre ex&eacute;cut&eacute; en tant que <em>root</em> sur le <em>serveur VPN</em></li>
<li>L'utilisateur <em>root</em>&nbsp;<em>(sudo)</em> sur le <em>serveur</em> doit avoir un acc&egrave;s SSH par cl&eacute; sur chaque client VPN. Pour cet acc&egrave;s, utiliser un compte SUDO du client VPN</li>
<li>Le compte sudo qui sera utilis&eacute; sur la machine du client doit pouvoir ex&eacute;cuter des commandes sans confirmation de mot de passe</li>
<li>Les postes <em>clients</em> et le <em>serveur</em> doivent &ecirc;tre connect&eacute;s &agrave; Internet pour le t&eacute;l&eacute;chargement des paquets d'installation de OpenVPN et Easy-RSA</li>
<li>Les postes <em>clients</em> et <em>serveur</em>&nbsp;doivent avoir leur nom d'h&ocirc;te configur&eacute; dans les fichiers <em>/etc/hosts</em> &agrave; moins d'&ecirc;tre enregistr&eacute;s sur un DNS. Les noms d'h&ocirc;te serviront aussi au nommage des cl&eacute;s de s&eacute;curit&eacute;. <br /><em>Clients et serveur devront pouvoir &ecirc;tre joints sur le WAN avec leur nom d'h&ocirc;te</em>.</li>
<li>Le routage IPv4 doit &ecirc;tre activ&eacute; sur toutes les machines, <em>clients</em> et <em>serveur.</em></li>
</ol>
<h3><strong>Installation</strong></h3>
<p>Pour mettre en place une ou plusieurs liaisons VPN impliquant un serveur VPN unique, proc&eacute;der comme suit :</p>
<h4>Sur le serveur VPN&nbsp;</h4>
<ul>
<li>Cl&ocirc;ner le contenu du projet <em>mgyvpn</em> sur le serveur VPN.&nbsp;</li>
<li>Dans le dossier ainsi cr&eacute;&eacute;, modifier le fichier <a href="https://github.com/mgythis/mgyvpn/mgyvpn.server.yaml">mgyvpn.server.yaml</a> pour correspondre &agrave; votre installation</li>
<li>Ex&eacute;cuter la commande ci-dessous en tant que super utilisateur (<em>faire un sudo)</em> :
<blockquote>#mgyvpn.py create server</blockquote>
<ul>
<li>Un ficher <em>mgyvpn.log</em> est cr&eacute;&eacute;e dans le dossier et contient les logs de l'installation</li>
<li>Un dossier <em>export</em> est cr&eacute;&eacute;, il contient des sous-dossiers contenant chacun les certificats et param&egrave;tres pour un <em>client vpn</em></li>
</ul>
</li>
<li>Le script exportera par <em>ssh</em> sur chaque <em>client,</em> dans le <em>dossier d'accueil de l'utilisateur SSH</em>, un r&eacute;pertoire nomm&eacute; <em>mgyvpn</em>, contenant:
<ul>
<li>Un dossier portant le nom du&nbsp;<em>client vpn,&nbsp;</em>il contient :&nbsp;les certificats et les param&egrave;tres de configuration du client(<em>mgyvpn.client.yaml</em>).</li>
<li>Le script lui-m&ecirc;me</li>
</ul>
</li>
<li>En fin d'installation, le script lancera l'installation sur chaque <em>client&nbsp;Openvpn</em></li>
</ul>
<h4>Sur chaque client VPN</h4>
<p style="padding-left: 30px;">Ex&eacute;cuter la commande :</p>
<p style="padding-left: 60px;">#<span style="background-color: #ffff99;">mgypvp.py add client NomDelaMachineCliente</span></p>
<blockquote>
<p>ou&nbsp;</p>
</blockquote>
<p style="padding-left: 60px;">#<span style="background-color: #ffff99;">mgypvp.py add client NomDelaMachineCliente -d DossierDesClesDeSecurite&nbsp;</span></p>
<p style="padding-left: 30px;">Remplacer les mots-cl&eacute;s&nbsp;<em>NomDelaMachineCliente</em> et&nbsp;<em>DossierDesClesDeSecurite</em> par les informations correspondantes dans la commande ci-dessus.</p>
<p style="padding-left: 30px;">Comme sur l'installation du serveur, un fichier <em>mgyvpn.log</em> est &eacute;galement disponible.</p>
<h3>Auteur</h3>
<p style="padding-left: 30px;">Berthis Mongouya : <a href="mailto:erthis@gmail">erthis@gmail.com</a></p>
<h3>Licence :</h3>
<p style="padding-left: 30px;"><a href="https://github.com/mgythis/mgyvpn/LICENCE.txt">GNU GPL 3.0</a></p>
<hr />
<p><span style="color: #333333;"><em>mgyvpn Copyright 2020 Berthis Mongouya</em></span></p>
