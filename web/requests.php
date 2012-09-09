<?php

$output = shell_exec('ab -n 50000 -c 50 http://10.194.173.8/index.php/login');
echo "<pre>$output</pre>";

?>
