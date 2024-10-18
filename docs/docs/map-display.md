# Kartenanzeige

SAGis XPlanung enthält eine Sammlung an Standard-Darstellungsvorschriften zur Visualisierung von Planwerken nach 
den Vorlagen der Planzeichenverordnung. Eine Anpassung der individuelle Stile ist
in den [Einstellungen](../settings/symbology.md) möglich.

!!! tip

    Die Darstellungskonfiguration aus den [Einstellungen](../settings/symbology.md) wird auf alle Planwerke bei der 
    Kartenanzeige angewendet. Für die Anpassung der Darstellung einzelner Planwerke, können die üblichen QGIS-Darstellungseigenschaften
    projektbasiert verwendet werden. 


## Präsentationsobjekte

Zur Erweiterung der Darstellungsinformationen realisiert der Standard XPlanung das Konzept der Präsentationsobjekte.
Diese unterstützen oder ändern die Standard-Darstellung von Planinhalten, haben jedoch selbst keine fachliche Bedeutung.
Präsentationobjekte können graphische Annotationen, wie textliche Beschriftungen oder zusätzliche Symbole repräsentieren.

### Nutzungschablone

Ein typisches Präsentationsobjekt ist die Nutzungschablone.  Die Tabellenform der Nutzungschablone gibt einen 
einfachen Überblick auf die wichtigsten Festsetzungen einer Baufläche. 
Die Nutzungsschablone kann für alle Bauflächen innerhalb eines Bebauungsplans aktiviert werden 
(Objektklasse <code>BP_BaugebietsTeilFlaeche</code>). Die angezeigten Daten der Tabelle werden aus den Sachdaten des
entsprechenden XPlan-Objekts verwendet.
<figure markdown="span">
    ![Beispiel Nutzungschablone](../assets/template-example.png)
</figure>


<div class="procedure">
    <h4>Nutzungsschablone anzeigen</h4>
    <ul>
        <li>
            Im Objektbaum das Kontextmenü eines Objekts vom Typ <code>BP_BaugebietsTeilFlaeche</code> wählen und 
            mit Menüoption <i>Nutzungsschablone anzeigen</i> auf der Karte ein- oder ausblenden.
        </li>
        <li>
            Mit Option <i>Nutzungsschablone bearbeiten</i> können die angezeigten Inhalte der Nutzungsschablone angepasst
            werden
        </li>
        <figure>
            <img src="../assets/show-template.png" alt="Nutzungschablone Aktionen"/>
        </figure>
    </ul>
</div>

<div class="procedure" id="nutzungschablone-edit">
    <h4>Nutzungsschablone anpassen</h4>
    <ul>
        <li>
            Im Objektbaum das Kontextmenü eines Objekts vom Typ <code>BP_BaugebietsTeilFlaeche</code> wählen und 
            mit Menüoption <i>Nutzungsschablone bearbeiten</i> den Dialog zum Bearbeiten der Nutzungsschablone öffnen.
        </li>
        <li>
            Alternativ: Mit dem XPlan-Werkzeug eine Nutzungschablone auf der Karte auswählen. Im Kontextmenü des Werkzeug
            findet sich ebenfalls die Option <i>Nutzungsschablone bearbeiten</i>
        </li>
        <figure>
            <img src="../assets/edit-template.png" alt="Nutzungschablone Kartenwerkzeug"/>
        </figure>
    </ul>
    Im Dialog <i>Nutzungsschablone bearbeiten</i> besteht die Möglichkeit die Form und Inhalte anzupassen:
    <table markdown="span">
        <tr>
            <th>Form</th>
            <td>Anpassen der Tabellenform. Auswahl aus den drei vorgegebenen Formen.</td>
        </tr>
        <tr>
            <th>Zellwerte</th>
            <td>Bestimmt die Inhalte der Nutzungschablone. Jede Auswahlliste bestimmt den Inhalt einer Zelle in der
                Tabelle. Es kann aus den folgenden Optionen gewählt werden:
                <ul>
                    <li><b>Art d. baulichen Nutzung</b> (Punkt 1 PlanZV)</li>
                    <li><b>Anzahl der Vollgeschosse</b> (Punkt 2.7 PlanZV)</li>
                    <li><b>Grundflächenzahl</b> (Punkt 2.5 PlanZV)</li>
                    <li><b>Geschossflächenzahl</b> (Punkt 2.1 PlanZV)</li>
                    <li><b>Art der Bebbaung</b> (Punkt 3.1.1-3.1.4 PlanZV)</li>
                    <li><b>Bauweise</b> (Punkt 3.1-3.3 PlanZV)</li>
                    <li><b>Dachneigung</b>: Angabe aus zugeordnetem Objekt vom Typ <code>BP_Dachgestaltung</code></li>
                    <li><b>Dachform</b>: Angabe aus zugeordnetem Objekt vom Typ <code>BP_Dachgestaltung</code></li>
                    <li><b>Höhe baulicher Anlagen</b> (Punkt 2.8 PlanZV): Angabe aus zugeordnetem Objekt vom Typ <code>XP_Hoehenangabe</code></li>
                    <li><b>Baumasse / Baumassenzahl</b> (Punkt 2.3-2.4 PlanZV)</li>
                    <li><b>Grundfläche / Geschossfläche</b> (Punkt 2.2+2.6 PlanZV)</li>
                </ul>
            </td>
        </tr>
        <tr>
            <th>Allgemeine Darstellungsoptionen</th>
            <td>Mit dem Schieberegler kann die Größe der Kartendarstellung angepasst werden. Die Auswahl 
                <i>Drehwinkel</i> bestimmt die Ausrichtung auf der Karte</td>
        </tr>
    </table>
    <figure>
        <img src="../assets/edit-template-dialog.png" alt="Nutzungschablone Kartenwerkzeug"/>
    </figure>
</div>