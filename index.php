<?php
// Hostinger Web Entrypoint Fallback
// Serves index.html directly
if (file_exists(__DIR__ . '/index.html')) {
    include_once(__DIR__ . '/index.html');
} else {
    header("HTTP/1.1 200 OK");
    echo "<h1>Autonomous RFx Intelligence Engine</h1><p>Application ready.</p>";
}
exit;
?>
