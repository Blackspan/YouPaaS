<!DOCTYPE Html>
<Html>
<head>
<meta http-equiv="Content-type" content="text/html; charset=utf8"/>
<title></title>
</head>
<div>
<h2>Les instances <h2>
</div>
</Html>

<?php
try
{
$db = new PDO('sqlite:../youpaas.db');
$result = $db->query('SELECT * FROM mysql');

print "<table border=1>";
print "<tr><td>Nom de l'instance</td><td>Adresse IP</td><td>Etat</td></tr>";

foreach($result as $row)
{
print "<td>".$row['hostname']."</td>";
print "<td>".$row['hostip']."</td>";
print "<td>".$row['state']."</td>";
}

print "</table>";
$db = NULL;
}

catch(PDOException $e)

{
print 'Exception : '.$e->getMessage();
}
?>
<br></br>
<?php
try
{
$db = new PDO('sqlite:../youpaas.db');
$result = $db->query('SELECT * FROM apache');

print "<table border=1>";
print "<tr><td>Nom de l'instance</td><td>Adresse IP</td><td>Etat</td></tr>";

foreach($result as $row)
{
print "<td>".$row['hostname']."</td>";
print "<td>".$row['hostip']."</td>";
print "<td>".$row['state']."</td>";
}

print "</table>";
$db = NULL;
}

catch(PDOException $e)

{
print 'Exception : '.$e->getMessage();
}
?>
<br></br>
<?php
try
{
$db = new PDO('sqlite:../youpaas.db');
$result = $db->query('SELECT * FROM nginx');

print "<table border=1>";
print "<tr><td>Nom de l'instance</td><td>Adresse IP</td><td>Etat</td></tr>";

foreach($result as $row)
{
print "<td>".$row['hostname']."</td>";
print "<td>".$row['hostip']."</td>";
print "<td>".$row['state']."</td>";
}

print "</table>";
$db = NULL;
}

catch(PDOException $e)

{
print 'Exception : '.$e->getMessage();
}
?>
<hr></hr>
<br></br>
<h2>Les instances supplementaires</h2>
<?php
try
{
$db = new PDO('sqlite:../youpaas.db');
$result = $db->query('SELECT * FROM seconde_apache');

print "<table border=1>";
print "<tr><td>Nom de l'instance</td><td>Adresse IP</td><td>Etat</td></tr>";

foreach($result as $row)
{
print "<td>".$row['hostname']."</td>";
print "<td>".$row['hostip']."</td>";
print "<td>".$row['state']."</td>";
}

print "</table>";
$db = NULL;
}

catch(PDOException $e)

{
print 'Exception : '.$e->getMessage();
}
?>
<br></br>
<?php
try
{
$db = new PDO('sqlite:../youpaas.db');
$result = $db->query('SELECT * FROM seconde_nginx');

print "<table border=1>";
print "<tr><td>Nom de l'instance</td><td>Adresse IP</td><td>Etat</td></tr>";

foreach($result as $row)
{
print "<td>".$row['hostname']."</td>";
print "<td>".$row['hostip']."</td>";
print "<td>".$row['state']."</td>";
}

print "</table>";
$db = NULL;
}

catch(PDOException $e)

{
print 'Exception : '.$e->getMessage();
}
?>




</head>
<h2> Les requetes</h2>
<?php
try
{
$db = new PDO('sqlite:../youpaas.db');
$result = $db->query('SELECT * FROM request');

print "<table border=1>";
print "<tr><td>Serveur web 1</td><td>serveur web 2</td><td>tous les serveurs web</td> </tr>";
foreach($result as $row)
{
print "<td>".$row['nombre']."</td>";
}
print "</table>";
$db = NULL;
}

catch(PDOException $e)

{
print 'Exception : '.$e->getMessage();
}
?>


