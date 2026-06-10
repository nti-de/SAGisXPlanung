# Allgemeine Einstellungen

Auf der Startseite der Einstellungen lassen sich die folgenden allgemeinen Einstellungen treffen:

## Exportoptionen

<table>
    <tr>
        <th>Pfad für externe Referenzen</th>
        <td>Beim <a href="../../plan-export">XPlanGML-Export</a> als ZIP-Archiv werden alle Externen Referenzen im angegebenen 
            Unterordner gespeichert. Mit Option <i>Referenzen im Hauptordner speichern</i> werden alle Referenzen auf gleicher
            Ebene mit der XPlanGML-Datei verpackt</td>
    </tr>
    <tr>
        <th>XPlanung-Version</th>
        <td>Auswahlliste zum Wechseln der XPlanung-Version. Die festgelegte XPlanung-Version beeinflusst alle 
            verfügbaren Objektklassen, Attribute und Auswahllisten in der Anwendung <br>
            <div class="admonition info">
                <p class="admonition-title">Info</p>
                <p>Beim Wechsel der Version werden keine Daten aus der Datenbank entfernt. Es findet jedoch keine
                    Migration statt.</p>
            </div>
        </td>
    </tr>
    <tr>
        <th>Schema für XPlanGML-Dateiname</th>
        <td markdown="span">
            Definiert das Namensschema der beim Export erzeugten XPlanGML-Datei.
            Der Dateiname kann aus festen Texten und Platzhaltern zusammengesetzt werden.
            <div class="admonition example">
                <p markdown="span"> 
                    <b>Schema:</b>
                    ```text
                    {ags}_{planArt}_{nummer}_{name}
                    ```
                    <b>Aufgelöster Dateiname:</b>
                    ```text
                    09162000_BP_2026-001_Wiesenstraße.gml
                    ```
                </p>
            </div>

            <details markdown="span" class="note" open="open">
                <summary>Verfügbare Platzhalter</summary>
                <table>
                    <tr>
                        <th>Platzhalter</th>
                        <th>Beschreibung</th>
                    </tr>
                    <tr>
                        <td><code>{ags}</code></td>
                        <td>Amtlicher Gemeindeschlüssel</td>
                    </tr>
                    <tr>
                        <td><code>{gemeindeName}</code></td>
                        <td>Name der Gemeinde</td>
                    </tr>
                    <tr>
                        <td><code>{planArt}</code></td>
                        <td>Art des Plans (z.&nbsp;B. BP, FP, RP)</td>
                    </tr>
                    <tr>
                        <td><code>{nummer}</code></td>
                        <td>Plannummer</td>
                    </tr>
                    <tr>
                        <td><code>{name}</code></td>
                        <td>Name des Plans</td>
                    </tr>
                    <tr>
                        <td><code>{datum}</code></td>
                        <td>Aktuelles Datum des Exports</td>
                    </tr>
                    <tr>
                        <td><code>{version}</code></td>
                        <td>XPlan-Version der XPlanGML-Datei</td>
                    </tr>
                </table>
            </details>
        </td>
    </tr>
</table>

## Validierung

<table markdown="span">
    <tr>
        <th>Geometrien automatisch bereinigen</th>
        <td markdown="span">Zum Erfüllen der <a href="../../elements/plan-details#geometrieprufung">Geometrieprüfung</a> kann SAGis
            XPlanung zwei Fehlerquellen bei der Datenerfassung automatisch korrigieren. Dies betrifft den _korrekten 
            Umlaufsinn von Polygongeometrien_ und die Erfassung von _doppelten Stützpunkten_. <br><br>
            Wenn die Option <i>Geometrien automatisch bereinigen</i> aktiviert ist, werden alle Geometrien, die neu in 
            der Datenbank erfasst werden automatisch korrigiert. Dieser Prozess kann durch die folgenden Optionen 
            konfiguriert werden:
            <ul>
                <li>
                    Topologie erhalten: Die Geometriebereinigung erhält die topologische Struktur der Geometrien. Es 
                    werden nur doppelte, aufeinanderfolgende Stützpunkte entfernt.
                </li>
                <li>
                    bessere Erkennung doppelter Stützpunkte: Die Geometriebereinigung entfernt auch doppelte Stützpunkte, 
                    die nicht aufeinanderfolgend sind. Dies kann jedoch zu Änderungen in der Topologie führen. 
                </li>
            </ul>
        </td>
    </tr>
</table>

## Objektformulare und Aktionen

<table markdown="span">
    <tr>
        <th>Attributdualog durch SAGis XPlanung ersetzen</th>
        <td markdown="span">Beim Öffnen des Objektformulars, nach Abfrage eines Einzelobjekts auf der Karte, wird statt 
            dem nativen QGIS-Dialog die Attributansicht vom SAGis XPLanung automatisch geöffnet.
        </td>
    </tr>
</table>