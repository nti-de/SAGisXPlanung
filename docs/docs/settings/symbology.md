# Darstellung

Zur Symbolisierung erfasster Planinhalte auf der QGIS-Karte wird durch die Anwendung eine Stilvorgabe für viele 
XPlan-Objektklassen bereitgestellt. Zusätzlich wird 

In den _Darstellung_-Einstellungen kann sowohl die Darstellungsreihenfolge als auch die einzelnen Stilvorgaben angepasst
werden. Die Darstellungsreihenfolge leitet sich dabei aus der Position der Einträge in der Liste ab. Eine höhere
Position in der Liste wird beim Anzeigen eines Plans weiter oben angezeigt, während untere Einträge in der Liste auf der
Karte in den Hintergrund rücken. 

<div class="procedure" markdown="1">
<h4>Symbolisierung bearbeiten</h4>
- Mit Doppelklick auf einen beliebigen Eintrag in der Liste der XPlan-Objektklassen öffnet sich ein Dialog zum Anpassen
  der Darstellungseinstellungen. Hier können alle üblichen QGIS-Konfigurationsmöglichkeiten angewandt werden um einen
  Stil zu laden oder anzupassen.

!!! note

    Viele XPlan-Objektklassen können mit unterschiedlichem Geometetriebezug auftreten (Punkt, Linie oder Polygon).
    Für entsprechende Klassen existiert ein Eintrag pro Geometrietyp in der Liste der Objektklassen.
</div>

<div class="procedure" markdown="1">
<h4>Darstellungsreihenfolge anpassen</h4>
- Nach Markieren eines Eintrags in der Liste der XPlan-Objektklassen kann der gewählte Eintrag mit den Pfeilsymbolen in
  der Aktionsleiste nach oben oder unten versschoben werden. Alternativ kann jeder Eintrag auch per drag-and-drop in
  der Liste verschoben werden.
</div>

<div class="procedure" markdown="1">
<h4>Weitere Aktionen</h4>

- Aufruf weiterer Aktionen über das Menü (Button mit drei vertikalen Punkten in der Aktionsleiste)
<table>
    <tr>
        <th>Einstellungen zurücksetzen</th>
        <td>Setzt die Darstellungskonfiguration auf den von SAGis XPlanung bereitgestellten Standard zurück</td>
    </tr>
    <tr>
        <th>Einstellungen exportieren/importieren</th>
        <td>Funktion zum Export der konfigurierten Stilvorgaben. Eine exportierte Datei kann mit der Option 
            <i>Einstellungen importieren</i> eingelesen werden</td>
    </tr>
</table>
</div>