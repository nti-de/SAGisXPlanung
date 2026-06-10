---
title: Textliche Festsetzungen
---

# Textliche Festsetzungen

XPlanung bietet die Möglichkeit, textlich formulierte Planinhalte (z. B. textliche Festsetzungen
oder Begründungen) dem gesamten Planungsbereich oder zusätzlich dazu bestimmten Teilflächen des Plangebiets zuzuordnen.
Zu empfehlen ist die Erfassung von textlichen Festsetzungen und deren Zuordnung zum entsprechenden geometrischen Planobjekt[^1].

[^1]: Leitfaden XPlanung, Leitstelle XPlanung (2020), https://xleitstelle.de/downloads/XPlanung_Leitfaden_1.pdf

## Textliche Festsetzung anlegen

Textliche Festsetzungen werden in XPlanung als eigenständige Objekte vom Typ
`XP_TextAbschnitt` (oder davon abgeleitete Typen) erfasst. Ein Textabschnitt kann anschließend einem oder mehreren
Planinhalten zugeordnet werden.

<div markdown="span" class="procedure">
    <h4>Neuen Textabschnitt erstellen</h4>
    <ol>
        <li>
            Im [Objektbaum](elements/plan-details.md#der-objektbaum) den gewünschten Planinhalt auswählen.
        </li>
        <li>
            Über das Kontextmenü <b>Neues Datenobjekt hinzufügen</b> die passende Relation auf eine TextAbschnitt-Klasse auswählen.
            Die Relation kann je nach zugehörigem XPlan-Objekt entweder <code>texte</code> (bei Plan und Bereich) oder <code>refTextInhalt</code> (bei Planinhalten) heißen.
        </li>
    </ol>

    <figure>
        <img src="../assets/add-text-section.png" alt="Textabschnitt hinzufügen"/>
    </figure>
</div>

Anschließend öffnet sich der Dialog zum Erstellen eines neuen Textabschnitts.

<figure markdown="span">
    ![Textabschnitt erstellen](../assets/create-text-section.png)
</figure>

Dabei können folgende Informationen erfasst werden:

<table>
    <tr>
        <th>schluessel</th>
        <td>Kurzbezeichnung oder Nummerierung der textlichen Festsetzung.</td>
    </tr>
    <tr>
        <th>gesetzlicheGrundlage</th>
        <td>Rechtsgrundlage, auf die sich die Festsetzung bezieht (z.&nbsp;B. § 9 Abs. 1 Nr. 2 BauGB).</td>
    </tr>
    <tr>
        <th>text</th>
        <td>Wortlaut der textlichen Festsetzung.</td>
    </tr>
    <tr>
        <th>refText</th>
        <td>Optionaler Verweis auf externe Dokumente oder Textquellen.</td>
    </tr>
    <tr>
        <th>Rechtscharakter</th>
        <td>Fachliche Einordnung des Textes, z.&nbsp;B. Festsetzung, Hinweis oder Nachrichtliche Übernahme.</td>
    </tr>
</table>

## Vorhandene Textabschnitte verwenden

Bereits erfasste Textabschnitte können mehrfach verwendet werden. Dadurch lassen sich
identische Festsetzungen verschiedenen Planinhalten zuordnen, ohne den Text erneut erfassen zu müssen.

<div class="procedure">
    <h4>Vorhandenen Textabschnitt zuordnen</h4>
    <ol>
        <li>
            Beim Anlegen eines Textabschnitts die Option <b>Vorhandene durchsuchen</b> auswählen.
        </li>
        <li>
            Gewünschte Textabschnitte über die Suchfunktion finden und auswählen.
        </li>
        <li>
            Mit der Auswahl bestätigen, um die Zuordnung zum aktuellen Planinhalt herzustellen.
        </li>
    </ol>

    <figure>
        <img src="../assets/select-text-section.png" alt="Vorhandene Textabschnitte auswählen"/>
    </figure>
</div>

!!! tip

    Textliche Festsetzungen sollten möglichst nur einmal erfasst und anschließend den
    allen betroffenen Planinhalten zugeordnet werden.