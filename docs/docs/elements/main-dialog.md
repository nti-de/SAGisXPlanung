# Hauptdialog

Der **Hauptdialog** ist der zentrale Einstiegspunkt der Anwendung.
Das Fenster bietet Zugriff auf die meistgenutzten Funktionen des SAGis XPlanung und ist
untergliedert in die folgenden vier Sektionen:

<table markdown="span">
    <tr>
        <th>Werkzeuge</th>
        <td>Zugriff auf das XPlanung-Werkzeug zum [Zuweisen neuer Planinhalte](../add-plancontent.md) und 
            zur [Abfrage von XPlan-Daten]() auf der Karte</td>
    </tr>
    <tr>
        <th>Neuen Plan erfassen</th>
        <td>Funktion zum [Erstellen eines neuen XPlan](../new-plan.md)</td>
    </tr>
    <tr>
        <th>XPlanGML Import</th>
        <td>Funktion zum [Import bestehender XPlanGML-Dokumente](../plan-import.md) in die Datenbank</td>
    </tr>
    <tr>
        <th>Planwerk-Auswahl</th>
        <td>Funktion zur Auswahl eines erfassten Planwerks aus der Datenbank.
            Der im Dropdown-Menü gewählte Plan wird im Arbeitsbereich des [Planwerk-Detail Fenster](plan-details.md) geladen und 
            kann mit der Option <control>Auswahl exportieren</control> in ein 
            [XPlanGML-Dokument exportiert](../plan-export.md) werden</td>
    </tr>
</table>

## Starten der Anwendung

Beim Aufruf der Anwendung startet das SAGis XPlanung in der Ansicht des Hauptdialogs.

1. In der **SAGis Menüleiste** auf das SAGis XPlanung-Icon klicken um die Anwendung
        zu starten
2. Das Hauptfenster öffnet sich standardmäßig als QGIS-Bedienfeld an der rechten Seite, 
    kann jedoch auch per drag-and-drop an eine andere Position verschoben werden

!!! info

    Sollte das Icon nicht in der Werkzeugleiste zu finden sein, vergewissern Sie sich, dass die 
    **SAGis Menüleiste** aktiviert ist (**Ansicht | Werkzeugleisten | SAGis Toolbar**).  


## Planwerk-Auswahl

Über die **Planwerk-Auswahl** können Sie schnell zwischen den in der Datenbank verfügbaren Plänen wechseln. 
Die Pläne lassen sich dabei nach Planart filtern, durchsuchen, sortieren und als Favoriten anheften.

![Planauswahl](../assets/plan-selection.png#only-light)
![Planauswahl](../assets/plan-selection-dark.png#only-dark)

<table markdown="span">
    <tr>
        <th>Plan auswählen</th>
        <td>
            Klicken Sie auf das Auswahlfeld am oberen Rand, um die Planauswahl zu öffnen.
            In der Liste werden alle verfügbaren Pläne angezeigt. Klicken Sie auf einen Plan,
            um diesen zu öffnen. Der in der Auswahlliste gewählte Plan wird im Arbeitsbereich
            des [Planwerk-Detail Fenster](plan-details.md) geladen.
        </td>
    </tr>
    <tr>
        <th>Pläne suchen</th>
        <td>
            Über das <strong>Suchfeld</strong> können Sie die Liste der Pläne durchsuchen.
            Geben Sie einen Suchbegriff ein, beispielsweise einen Teil des Plannamens.
            Die Liste wird während der Eingabe entsprechend eingeschränkt.
            <div class="admonition tip">
                <p class="admonition-title">Tipp: Suche nach Gemeinde</p>
                <p> 
                    Die Liste der Planwerke kann auch nach dem Namen der planaufstellenden
                    Gemeinde im Suchfeld gefiltert werden.
                </p>
            </div>
        </td>
    </tr>
    <tr>
        <th>Nach Planart filtern</th>
        <td>
            Mit den Schaltflächen oberhalb der Planliste können Sie die angezeigten Pläne
            nach ihrer Planart filtern:
            <ul>
                <li><strong>BP_Plan</strong> – Bebauungspläne</li>
                <li><strong>FP_Plan</strong> – Flächennutzungspläne</li>
                <li><strong>LP_Plan</strong> – Landschaftspläne</li>
                <li><strong>RP_Plan</strong> – Regionalpläne</li>
            </ul>
            Durch erneutes Auswählen eines Filters können Sie die entsprechende
            Einschränkung wieder aufheben.
        </td>
    </tr>
    <tr>
        <th>Pläne sortieren</th>
        <td>
            Über <strong>Sortieren nach</strong> können Sie festlegen, in welcher Reihenfolge
            die Pläne angezeigt werden:
            <ul>
                <li><strong>Name</strong> – sortiert die Pläne alphabetisch nach ihrem Namen.</li>
                <li><strong>Letzte</strong> – zeigt die zuletzt verwendeten bzw. zuletzt relevanten
                    Pläne zuerst an.</li>
            </ul>
            Mehrfaches Anwählen der Buttons ändert die Reihenfolge der Sortierung
            (aufsteigend/absteigend).
        </td>
    </tr>
    <tr>
        <th>Favoriten</th>
        <td>
            Häufig benötigte Pläne können Sie als <strong>Favoriten</strong> markieren.
            Klicken Sie dazu auf das <strong>Stern-Symbol</strong> neben einem Plan.
            Favorisierte Pläne werden im Bereich <strong>Favoriten</strong> am Anfang
            der Liste angezeigt und können dadurch schneller wieder aufgerufen werden.
            <br><br>

            Um einen Plan aus den Favoriten zu entfernen, klicken Sie erneut auf
            das Stern-Symbol.
        </td>
    </tr>
</table>