# Detailansicht Planwerk

Im Fenster **Planwerk Details** lassen sich verschiedenen Funktionen und Inhalte
abrufen, die einen einzelnen Plan in der Datenbank betreffen. Dabei wird immer
der Plan in den Arbeitsbereich geladen, der im [Hauptdialog](main-dialog.md) in der Liste der Planwerke
ausgewählt wurde.

Das Fenster **Planwerk Details** besteht aus den beiden Sektionen **Geometrieprüfung** und
dem **Objektbaum**. Im oberen Bereich finden sich allgemeine Aktionen zum 
Anzeigen, Bearbeiten und Löschen des vorliegenden Plans.

<div class="procedure">
    <h4>Detailansicht für ein Planwerk öffnen</h4>
    <ol>
        <li>Gewünschtes Planwerk aus Liste im <a href="main-dialog.md">Hauptdialog</a> wählen</li>
        <li>Neben der Liste der Planwerke auf das Info-Symbol klicken</li>
    </ol>
    <figure>
        <img src="../../assets/open-plan-details.png" alt="Plan Details öffnen"/>
    </figure>
</div>

## Kartenanzeige 

Jeder in der Datenbank erfasste Datensatz kann auf der QGIS-Karte visualisiert werden. Dabei wird eine standardmäßig 
konfigurierte Stilvorgabe und Layerreihenfolge des SAGis XPlanung angewendet. Eine Anpassung der individuelle Stile ist
in den [Einstellungen](#) möglich.

<div class="procedure">
    <h4>Plan auf Karte anzeigen</h4>
    <ul>
        <li>Mit dem Kartensymbol lässt sich der aktuell gewählte Plan auf der QGIS-Karte anzeigen</li>
    </ul>
    <figure>
        <img src="../../assets/display-map.png" alt="Plan Details öffnen"/>
    </figure>
</div>

## Geometrieprüfung

Zur Erfassung eines qualitativ hochwertigen Planwerks ist topologisch korrektes Anlegen der Geometrien unerlässlich. 
XPlanung definiert hierfür einige Qualitätsvorgaben, die bei der Validierung einer XPlanGML-Datei geprüft werden. 
Mit der Geometrieprüfung unterstützt SAGis XPlanung die Einhaltung der Vorgaben zur korrekten geometrischen Erfassung.

Dies betrifft die folgenden Bedingungen:

- Geometrien sind valide nach [OGC Simple Feature Access](https://www.ogc.org/standard/sfa/) Standard
- Geometrien enthalten keine doppelten Stützpunkte
- Einhaltung des Flächenschlusskonzepts

!!! info

    Flächenschluss: Bei der vollvektoriellen Erfassung muss der Zusammenschluss aller erfassten Flächen mit der Fläche 
    des Geltungsbereichs übereinstimmen. Es dürfen keine Überlappungen oder Lücken zwischen den Flächen auftreten und 
    keine Fläche darf den Umring des Geltungsbereichs übertreten.


<div class="procedure">
    <h4>Ausführen der Geometrieprüfung</h4>
    <ol>
        <li>
            Mit dem Button <b>Geometrieprüfung starten</b> den Prozess starten. Je nach Menge der erfassten 
            Flächenschlussobjekte kann der Prozess einige Zeit in Anspruch nehmen
        </li>
        <li>
            Sollte die Geometrieprüfung Fehler identifiziert haben, werden diese im Anschluss im Protokoll-Fenster 
            angezeigt. Jede Fehlermeldung, kann durch einen Doppelklick auf die Fehlernachricht auf der Karte 
            visualisiert werden.
        </li>
        <figure>
            <img src="../../assets/geometry-validation.png" alt="Geometrieprüfung"/>
        </figure>
        <li>
            Zum Beheben von Geometriefehlern können die <a href="https://docs.qgis.org/3.34/de/docs/user_manual/working_with_vector/editing_geometry_attributes.html">
            QGIS-Bearbeitungswerkzeuge</a> verwendet werden.
        </li>
    </ol>
</div>

<div class="procedure">
    <h4>Flächenschluss erzwingen</h4>
    <ul>
        <li>
            Die Funktion <b>Flächenschluss erzwingen</b> ermöglicht es, Flächen, die mit keiner Festsetzung 
            konfiguriert sind, mit einem Objekt des Typ <code>BP_FlaecheOhneFestsetzung</code> zu füllen. Dies ist 
            hilfreich, um die Flächenschlussbedingung zu erfüllen, wenn nicht die komplette Fläche des Geltungsbereichs 
            mit vektoriell erfassten Planinhalten gefüllt werden kann. 
        </li>
    </ul>
</div>


## Der Objektbaum

Der Objektbaum spiegelt die baumartige Struktur eines XPlanGML-Dokuments wider.
Jeder XPlan-Datensatz besteht zunächst aus dem Grundobjekt <code>BP_Plan</code>/<code>FP_Plan</code>/etc. Diesem sind dann weitere Planinhalte
zugeordnet. Dabei können einzelne Planinhalte wiederum anderen Inhalte zugeordnet sein, wodurch eine die Baumstruktur entsteht.

Über den Objektbaum werden die folgenden Funktionen abgebildet:

- <a href="#filtern-und-sortieren"> Filtern und Sortieren der Planinhalte</a>
- <a href="#bearbeiten-von-sachdaten" summary="">Bearbeiten von Sachdaten</a>
- <a href="../../add-plancontent/#datenobjekte-hinzufugen">Hinzufügen neuer Datenobjekte</a>
- <a href="#loschen-von-inhalten">Löschen von einzelnen Inhalten</a>


### Filtern und Sortieren 

Zur Navigation im Objektbaum, können alle erfassten Objekte sortiert und gefiltert werden.
Zur Sortierung stehen die drei Optionen **Nach Objekthierarchie**, **Alphabetisch** und **Nach Kategorie** sortieren 
zur Verfügung (in Reihenfolge von links von rechts). Die standardmäßige Sortierung **Nach Objekthierarchie** spiegelt 
den Aufbau des XPlan-Datensatzes in der Struktur einer XPlanGML-Datei wider.

Mit dem Lupen-Symbol öffnet sich ein Suchfeld, das zum **Filtern** der angezeigten Objekte nach _Namen der Objektart_ und 
_XPlanung-ID_ genutzt werden kann.

<figure markdown="span">
    ![Filtern und Sortieren](../../assets/filter-plancontents.png)
</figure>


### Bearbeiten von Sachdaten
<div><span class="full-label">Vollversion</span></div>

!!! warning

    Bearbeiten von Attributen ist in der Community-Version nur für Basisobjekte möglich.


1. Doppel-Klick auf einen Eintrag Objektbaum öffnet die Attribut-Ansicht
2. Doppel-Klick in eine Zelle der Spalte **Wert** öffnet einen Dialog zum Bearbeiten des gewählten Attributs
3. Gewünschte Anpassung am Attributwert eintragen und mit **Speichern** bestätigen 
    <figure markdown="span">
        ![Attribut bearbeiten](../../assets/edit-attribute.png)
    </figure>

!!! tip

    Mit der Rückgängig-Funktion können letzte Änderungen an Attributen wieder gelöscht werden um den Datensatz in einen
    früheren Zustand zu versetzen.
    <figure markdown="span">
        ![Attributänderung zurücksetzen](../../assets/edit-undo.png)
    </figure>

### Löschen von Inhalten

=== "Plan löschen"

    * Mit dem Mülleimer-Symbol im oberen Abschnitt des Fensters wird der gesamte Plan gelöscht
        <figure markdown="span">
            ![Attribut bearbeiten](../../assets/delete-plan.png)
        </figure>
        
=== "Planinhalte löschen"

    1. Objekte zum Löschen im Objektbaum auswählen (++ctrl++ zur Mehrfachauswahl oder gesamten Bereich durch Ziehen 
     der Maus markieren)
    2. Mit der rechten Masustaste das Kontextmenü aufrufen
    3. Mit **Planinhalt Löschen** werden gewählte Inhalte entfernt.
        <figure markdown="span">
            ![Attribut bearbeiten](../../assets/delete-plan-content.png)
        </figure>
   

### Weitere Planinhalt-Aktionen

Der Objektbaum bietet weitere Funktionen, die auf einzelne erfasste Planinhalte angewendet werden können.
Viele der Planinhalt-Aktionen können nur auf Objekten bestimmter XPlanung-Objektklassen oder Kategorien von Planinhalten
ausgeführt werden.

1. Aufruf der Planinhalt-Aktionen über das Kontextmenü der Einträge im Objektbaum (Rechtsklick)
    <figure markdown="span">
       ![Planinhalt-Aktionen](../../assets/plan-content-actions.png)
    </figure>

<table>
   <tr>
      <th>Planinhalte</th>
      <td>
         <ul>
            <li>
               <i><a href="#loschen-von-inhalten">Planinhalt löschen</a></i>: Planinhalt aus der Datenbank entfernen 
               (Bei Mehrfachauswahl werden alle gewählten Objekte gelöscht)
            </li>
            <li>
               <i>Planinhalt auf Karte hervorheben</i>: Wenn der <a href="#kartenanzeige">Plan im Arbeitsbereich/Karte geladen</a>
               ist, wird die Geometrie auf der Karte aufleuchten
            </li>
            <li>
               <i><a href="../../add-plancontent/#datenobjekte-hinzufugen">Datenobjekt hinzufügen</a></i>
            </li>
            <br>
            Bei Mehrfachauswahl: 
            <li>
               <i><a href="">Gewählte Objekte bearbeiten</a></i>
            </li>
         </ul>
      </td>
   </tr>
   <tr>
      <th><code>BP_BaugebietsTeilFlaeche</code></th>
      <td>
         <ul>
            <li>
               <i>Nutzungsschablone anzeigen</i>: Gibt an, ob für die diese Fläche eine Nutzungsschablone auf der Karte
               angezeigt werden soll
            </li>
            <li>
               <i><a href="">Nutzungsschablone bearbeiten</a></i>: Öffnet einen Dialog zur Konfiguration der Nutzungschablone
            </li>
         </ul>
      </td>
   </tr>
</table>