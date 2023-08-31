## Anweisungen zum Update

0. Zur Sicherheit zunächst ein Backup der existierenden Datenbank durchführen. 
1. Im QGIS-Erweiterungsmanager SAGis XPlanung suchen und `Erweiterung deinstallieren` wählen. Im Anschluss QGIS schließen.
2. Verbindung zur Datenbank herstellen bspw. in pgAdmin und das SQL-Skript zur Migration ausführen.
3. Nach erfolgreichem Update der Datenbank das Installationsprogramm ausführen.
> [!NOTE]  
> Darauf achten, dass der Installationspfad im QGIS-Plugin-Verzeichnis mit `../SAGisXPlanung` endet.
> (Nicht nur `../XPlanung`, wie es in früheren Versionen der Fall war)
