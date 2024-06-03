## Changelog

### [2.5.1] - 22.05.2024

#### Veränderungen

- Anpassungen zur Nutzung mit Python 3.12 (ab QGIS 3.34.6)
- verbesserte Package-Verifizierung beim Starten des Plugins

#### Fehlerbehebungen

- Nutzungsschablonen werden mit Plan-Gruppe korrekt ausgeblendet (17fd4cee, b77f36c9)
- Objekteigenschaften von Präsentationsobjekten nach Neuladen eines Plans (29310c48)

### [2.5.0] - 22.05.2024

#### Neue Funktionen

- Neuer Dialog zur Übersicht der gespeicherten Pläne
- Excel-Import für Sachdaten der Objektklassen XP/BP/FP/RP/LP_Plan
- Funktion zum Upgrade des Datenbankschemas nach Plugin-Aktualisierung
- Neue Objektklasse `BP_UeberbaubareGrundstuecksFlaeche`

#### Veränderungen

- Verbesserte Geometrieauswahl bei Layern mit vielen Features (8b83295b)

### [2.4.0] - 15.04.2024

#### Neue Funktionen

- Neue Objektklassen: 
  - `BP_KennzeichnungsFlaeche`, `FP_VerEntsorgung`
  
#### Veränderungen

- Überarbeitung der Geometreievalidierung: Verbesserte Fehlermeldungen, Tooltips, Thread-Safety
- Ausblenden von Objektklassen, die nicht zur gewählten XPlanGML-Version passen

#### Fehlerbehebungen

- Fehler in Datenbank-Revision bzgl. UUID in sqlalchemy (6c797b1b)
- Import von Boolean-Werten aus XPlanGML korrigiert (8208375c)
- Fehler beim Wechseln des Plantyps im 'Planinhalte konfigurieren'-Dialog behoben (b365e72f)


### [2.3.0] - 19.03.2024

#### Neue Funktionen

- Neue Objektklassen: 
  - `BP_NebenanlagenFlaeche`, `SO_Luftverkehrsrecht`, `XP_VerbundenerPlan`, `BP_GenerischesObjekt`, `FP_GenerischesObjekt`, `BP_Immissionsschutz`, `BP_AbgrabungsFlaeche`, `BP_AufschuettungsFlaeche`, `SO_SonstigesRecht`
- Automatische Geometriekorrektur beim Speichern von Objekten in der Datenbank: 
  - Anpassung des Umlaufsinns von Polygon-Stützpunkten auf CCW 
  - Entfernung doppelter Stützpunkte 
- Neue Funktion zum Überprüfen der Datenbank-Verbindung in den Einstellungen
- Warnung vor dem Überschreiben der Vollversion durch eine Installation aus dem QGIS-Plugin Repository

#### Veränderungen

- Verbesserte Darstellungsstile
  - `BP_SchutzPflegeEntwicklungsFlaeche`: Korrekte Orientierung der T-Symbole, bessere Schriftart (7a9df5c0, 630649dd)
  - `SO_Denkmalschutzrecht` (51557b7c)
- Erfassung neuer Planinhalte aus Geometrien mit Z-Dimension (3D) möglich (c8bef963)
- Dialog zur Zuordnung der XPlan-Objektklasse zeigt nur noch zum Geometrietyp passende Objekte

#### Fehlerbehebungen

- Fehler beim Erfassen von XPlan-Objekten aus Layern mit mehr als 100 Features behoben (64aa3aa1)
- GML-Export mit Codelisten-Werten korrigiert (8a86dc75)
- keine doppelten Einträge in der Stilkonfiguration bei mehrfachem Aufruf der Einstellungen mehr (5f56b885)
- Fehlerhafte Anzeige von Planinhalten auf der Karte in Kombination mit einfacher Erfassungstiefe behoben (19e4a6e2)

### [2.2.2] - 05.01.2024

#### Neue Funktionen

- Benutzerdefinierte Symbolisierung und Darstellungsreihenfolge für XPlanung-Objekte (Vollversion)
  - Neuer Einstellungsdialog zur Anpassung der Symbolisierung
  - Import/Export der Darstellungskonfiguration

#### Veränderungen

- Doppelte Stützpunkte werden beim Civil-Import automatisch entfernt (57af1da0)
- verbesserte Stilisierung für `BP_Plan`, `BP_Wegerecht`, `SO_Denkmalsschutz`, `BP_SchutzPflegeEntwicklungsFlaeche` (017e2268)
- Domainwechsel zu nti-group.com (85c1e027)

#### Fehlerbehebungen

- Endlossschleife von Warnungsdialogen beim ersten Start der Anwendung behoben (9dc1e21d)
- Fehler beim Speichern von Objekten vom Typ XP_SpezExterneReferenz im Attribut refScan von XP_Bereich behoben (375a23f8, b1fd27ed)
- Korrektur des Civil-Imports bei mehreren XP_Bereich-Instanzen (70d905b0)
- SQL-Offline Revisionen zwischen Versionen 1.10 und 2.0 korrigiert (4864341f, ce9d8474)
- Fehler beim Export von Objekten des Typs `XP_GesetzlicheGrundlage` behoben (04e66bce)

### [2.2.1] - 02.10.2023

#### Veränderungen

- unbekannte Codelist-Werte werden nicht mehr in der Datenbank gespeichert (edcb6368)

#### Fehlerbehebungen

- Attribute abfragen bei Sortierung des Objektbaums nach Kategorie korrigiert (cfb9e064)
- fehlende Stilisierung für `BP_Wegerecht` hinzugefügt (a4739409)
- Dialog zum Hinzufügen von Planinhalten erscheint korrekt, wenn ein Landschaftsplan gewählt ist (b2e01840)
- Download von Codelisten aus der GDI Registry korrigiert (8e1779cc)
- fehlerhafte Anzeige von Attributen mit Boolean oder Enum-List Datentyp beim Bearbeiten eines Plans (189c666a)
- Fehler der Vorwärts/Zurück-Funktion nach Änderung von Attributen mit Enum-List Datentyp behoben (49e70202)

### [2.2.0] - 29.08.2023

#### Neue Funktionen

- Funktion zum Zurücksetzen der Geometrievaldierung
- Unterstützung von Codelist-Attributen:
  - Möglichkeit zum Herunterladen von Werten einiger XPlanung-Codelisten aus der GDI-DE Registry
- Neue Objektklassen: 
  - `XP_Hoehenangabe`, `BP_NutzungsartenGrenze`, `BP_BereichOhneEinAusfahrtTypen`, `BP_EinfahrtPunkt`

#### Veränderungen

- Ausblenden von Attributen betrifft nun auch die Dialoge zum Bearbeiten von Atrributen (vormals nur bei Erfassung neuer Planinhalte) (a69cde81)

#### Fehlerbehebungen

- Fehler behoben, bei dem das Speichern von Planinhalten keine Änderung im Objektbaum verursachte (580723e4)
- fehlerhafter GML-Export des Attributs `rechtscharakter` in der Version 5.3 korrigiert (6a0e1e7b)
- Bearbeiten von Plänen mit `BP_VeraenderungssperreDaten` möglich (24dab1e5)

### [2.1.1] - 16.08.2023

#### Fehlerbehebungen

- Speichern von Objekten mit Angabe des Attributs `rechtscharakter` korrigiert

### [2.1.0] - 01.08.2023

#### Neue Funktionen

- Funktion zum "Rückgängig machen" von Attribut-Änderungen und Löschen einzelner Planinhalte
- Überprüfung und Installation aller Python-Abhängigkeiten bei Start der Anwendung
- Funktion zum Anlegen einer XPlanung-Datenbank aus der Anwendung

- [internal] Backport-System zur parallelen Entwicklung verschiedener Versionsstände

#### Veränderungen

- Allgemeine Überarbeitung des Einstellungsdialog: bessere Strukturierung
- Verschieben von Präsentationsobjekte kann abgebrochen werden (3474b5d7)
- neue Tooltips für XPlan-Attribute der XPlanung-Version 6.0 (3dd603af)
- [refactor] Finden von zusammengehörigen Planinhalten (83e7c43f)
- [refactor] Aktualisieren des Objekt-Exploreres nach Erstellen des Flächenschluss lädt auschließlich veränderte Objekte neu (b1ebff3d)

#### Fehlerbehebungen

- fehlerhafter Aufruf des Civil3D-Imports durch Menüeintrag korrigiert (9213a4d0)
- Objektklassen, die nicht zur gewählten XPlanung-Version passen, werden nicht mehr exportiert (cc103025)
- fehlende Umsetzung des CR-039 im BPlan-Schema für XPlanung 6.0 (d352a4cb, 853bd728)
- fehlende Anzeige von Tooltips für XPlan-Attribute (82c53d7c)
- GML Import bricht nicht mehr bei leeren Tags ab, sondern ignoriert diese (da0884d1)
- GML Import von Nutzungsschablonen mit 2 oder 4 Zeilen (bd393433)
- fehlerhafte SQL-Revision in 2.0.0: Commit nötig nach Enum-Veränderungen (51c48377)

### [2.0.0] - 29.06.2023

#### Neue Funktionen

- Abbildung des Objektmodells in der XPlanung-Version 6
- Import/Export von XPlanGML 6.0


- Mehrfachauswahl zum Löschen von Objekten im Objektbaum (8a3d2112)
- Fortschrittsindikator beim Import von XPlanGML-Dateien (65cf9b2e)

#### Veränderungen

- Geometrievalidierung funktioniert mit Curved-Geometries (d10e0869)
- Performance-Verbesserungen der Geometrievalidierung (d10e0869)
- Kleine Performace-Verbesserungen beim Import von XPlanGML-Dateien (3eff74ba)

#### Fehlerbehebungen

- Datenbankinhalte werden beim ersten Start der Anwendung korrekt angezeigt (99b93aec)
- Import funktioniert auch, wenn Attribut `srsName` nicht auf dem äußerten Elememt vorliegt (8438b4e6)
- Multiplizität des Attributs `zweckbestimmung` der Klasse `FP_Gemeinbedarf` korrigiert (18417f4b)
- Korrektur der Werte `AnlageBundLand` und `BetriebOeffentlZweckbestimmung` der Enumklasse `XP_ZweckbestimmungGemeinbedarf` (0dff22e9)

### [1.10.2] - 12.05.2023

#### Veränderungen

- Datenmodell unterstützt das Speichern und Anzeigen von Objekten mit unterschiedlicher Geometriedimension (c6c7a721)
- Auswahllisten zur Bauweise und Bebaungsart sind nicht mehr Pflichtattribute (b77a2cd0)
- Zwischenspeichern des zuletzt genutzten Ordners beim Exportieren (76068599)
- Verbesserung der Fehlermeldungen beim Prüfen der Konformitätsbedingungen von Baugebieten (51403247)
- Umbennung des Basisverzeichnis und Python-Moduls in `SAGisXPlanung` (44b0cc0e)


- [Installer] Installationsprogramm lädt alle Abhängigkeiten aus lokalen Paketen (eff32a66)
- [Installer] Installationsprogramm prüft, ob Pythons Paketmanager installiert ist (05e6a10c)

#### Fehlerbehebungen

- Import von XPlanGML mit Objekten vom Typ `XP_SPEMassnahmenDaten` produziert keine Fehlermeldung mehr (287cf661)
- Fehler behoben, durch den bestimmte Attributwerte nicht gelöscht werden konnten (8da7221a)
- Crash bei Anzeige von Objekten des Typs `SO_Denkmalschutzrecht` unter QGIS >= 3.24 (7a9d3acf)
- fehlendes Kontextmenü im Objektbaum für Klasse `BP_SchutzPflegeEntwicklung` (c50961c9)
- fehlende Attributformulare für Datenobjekte (0b461799)
- fehlende Möglichkeit zur Dialog-Konfiguration für Klassen `XP_Bereich` und `XP_Objekt` (510011b2)

### [1.10.1] - 13.04.2023

#### Veränderungen

- Geometrievalidierung funktioniert mit Curved-Geometries (d10e0869)
- Performance-Verbesserungen der Geometrievalidierung (d10e0869)

#### Fehlerbehebungen

- fehlendes Attribut `flaechenschluss` bei Objektklassen, die von *P_Flaechenschlussobjekt abgeleitet sind (c353674f)
- Fehler bei der Anzeige von Geometriefehlern behoben, wenn es sich um eine Multi-Geometrie handelt (2ef3fa02)
- Auswahl der korrekten Seite im Einstellungs-Dialog (bdf6d65f)

### [1.10.0] - 28.03.2023

#### Neue Funktionen

- Unterstützung für Geometrien nach SQL/MM Spatial Part 3 (Curved Geometries)
  - benötigt mindestens GDAL 3.6.3
- Einstellungen zur Konfiguration der Sachdatendialoge:
  - Ausblenden von irrelevanten XPlanung-Attributen
- Überarbeitung des Dialogs zum Konfigurieren der Planinhalte:
  - Konfigurieren mehrerer gleicher Planinhalte in einem Schritt möglich
  - Auswahl von Geometrien über QGIS-Abfrageausdrücke
- neuer Dialog zum nachträglichen Bearbeiten der Sachdaten eines Plans
  - Zuweisung eines neuen Geltungsbereichs aus einem Layer möglich

#### Veränderungen

- Nutzung des GML-Drivers von OGR/GDAL, anstatt der GML-API von QGIS 
- Nutzung des Geometriemodells von GDAL anstatt shapely zur flexiblen Unterstützung verschiedenster Geomtrietypen
- Geometrien von neu angelegten Planinhalten werden nicht mehr segmentiert (f01ab139)
- Neue Menüeinträge in der SAGis-Menüleiste zum schnelleren Abruf der Verarbeitungswerkzeuge (3fd2a47f)
- Installationsprogramm erzwingt Installation von sqlalchemy in der Version 1.4
- Import-Button bleibt deaktviert, solange keine Datei angegeben ist
- bessere Bezeichnung des Tabellenkopfes beim Bearbeiten von Attributen

#### Fehlerbehebungen

- fehlerhaftes Layout in den Sachdaten-dialogen behoben (98a353df)
- Fehler behoben, bei dem ein Planwerk aus Civil3D nicht importiert werden konnte, wenn sich noch kein Plan in der Datenbank befindet (c10916b0)
- keine Fehlermeldung mehr, wenn SAGis XPlanung vor den internen QGIS-Plugins geladen wurde (31f8dae3)
- Fehler beim Import von XPlanGML-Dokumenten mit fehlenden `xlink`-Verweisen behoben (31195ced)
- Installationsprogramm öffnet nun auch QGIS-LTR nach der Installation von SAGis XPlanung (628c63d6)

### [1.9.0] - 06.01.2023

#### Neue Funktionen

- Neues Verarbeitungswerkzeug zum Importieren von BPlan-Daten aus Civil3D

#### Veränderungen

- API für gemeinsame Menüs und Toolbars aller SAGis-Lösungen im QGIS (a288dd47)
- Überarbeitung der Funktionen zum Annotatieren von Planwerken (v2):
  - neuer Dialog zum Anlegen und Konfigurieren von Annotationen (0c2f5789)
  - Präsentationsobjekte werden nun einem bestimmten Planinhalt zugeordnet (nicht mehr dem gesamten Plan)
  - neue Präsentationsobjekte erscheinen sofort auf der Karte
  - Nutzung der korrekten Objektklasse `XP_PTO` statt `XP_TPO` für punktförmige Textannotationen (a916c05d)
  - XPlanGML-Import/Export von Präsentationsobjekten

- Kartenanzeige von Objekten der Klasse `SO_Denkmalschutzrecht` verbessert (e12f75a8)
- Weitere Tooltips beim Bearbeiten von Attributen (cce65474)
- Vererbungshierarchie für externe Referenzen angepasst, um das XPlanung-Schema besser abzubilden (a9debc85)
  
#### Fehlerbehebungen

- Attribute mit dem Datentyp `Angle` erlauben gebrochene Zahlen wie in GML-Spezifikation vorgegeben (e289a41c) 
- Falsche Default-Werte bei den Zeilen/Spalten von Nutzungsschablonen behoben (f6c7dfeb)
- Tooltips mit langem Textinhalt überdecken nicht mehr die gesamte Bildschirmbreite (24c2b4dd)
- fehlende Hervorhebung von Pflichtattributen beim Erstellen von Plänen hinzugefügt (24c2b4dd)

### [1.8.0] - 06.01.2023

#### Neue Funktionen

- Überprüfung der Konformitätsbedingungen für Flächennutzungspläne
- neue Objektklassen für nachrichtliche Übernahmen im FNP:
  - `SO_Denkmalschutzrecht`, `SO_Schienenverkehrsrecht`, `SO_SchutzgebietWasserrecht`

#### Veränderungen

- Überarbeitung der Funktionen zum Annotatieren von Planwerken:
  - neues Widget zum Ändern des SVG-Symbols einer Annotation (#35)
  - verbesserte Sortierung der Symbolbibliothek (7824d697, 1a672240)
  - neue Funktion zum Verschieben von Annotationen auf der Karte (#34)
  - neue Funktion zum Abfragen von Annotationen auf der Karte

- Überarbeitung der Geometrievalidierung (#42): 
  - vollständig asynchrone Ausführung der Validierung (QGIS bleibt für andere Funktionen bedienbar)
  - Starke Verbesserung der Geschwindigkeit der Validierung durch
    - Nutzung von R-Tree Spatial Index zur Vermeidung von leistungsintensiven Geometrievergleichen
    - Weniger und besser optimierte SQL-Abfragen
    - -> 80% schneller auf kleinen Planwerken (ca. 100 Objekte), bis zu 93% schneller auf großen Planwerken (ca. 1000 Objekte)

- Tooltips zur Erklärung aller XPlanung-Attribute in sämtlichen Formularen (34b536f4)
- neues Framework für Enum-Werte, die erlauben, keine Auswahl zu treffen (b992a597)
  
#### Fehlerbehebungen

- Falsche Kardinalität des Attributs `sondernutzung` behoben (94d8da63)

### [1.7.0] - 28.10.2022

#### Neue Funktionen

- Neue Objektklassen für Flächennutzungspläne
- Abfrage-Tool ermöglicht das Identifizieren von Präsentationsobjekten auf dem Kartencanvas

#### Veränderungen

- Performance:
  - Dateiinhalte werden nur bei Bedarf aus der Datenbank geladen (2ea67614)
  - Datenbankabfragen laden nur noch benötigte Spalten (c0c79ada)
  - Dateireferenzen größer als 100MB werden nicht mehr erlaubt (63562b5a)

- Usability:
  - bessere Beschreibungen der Attribute (17dc8efb)
  - Objektbearbeitung im Objektbaum kann mit Doppelclick aufgerufen werden (c4da5383)
  - Datenobjekte werden asynchron gespeichert, UI bleibt bedienbar (b947081d)
  - Anzeige von unnötigen Attributen entfernt (042f58e5)
  - Aussehen des Fensters beim Zeigen von Planwerken mit langem Namen verbessert (f2a3ae13, 37352e14)

- Kartensymbole vergrößert (3ea4ef57)
- Unterstützung für QGIS-Versionen unter 3.22 aufgehoben (63f5b598)
- größere Auswahl an SVG-Symbolen zum Annotieren der Planwerke (e83f7827)

#### Fehlerbehebungen

- Fehler beim Anzeigen von Fenstern mit horizantalem Scroll behoben (a272236a)
- Änderungen von Plannamen werden überall korrekt angezeigt (a768c63a)
- Rasterlayer werden beim Neuladen des Projekts auch neu gerendert (1c028492)
- Export von Enum-Listen ins XPlanGML korrigiert (91b28c2e)
- fehlende Layer-Felder zur korrekten regelbasierten Anzeige bestimmter Layer hinzugefügt (c52c3809)
- Tippfehler im Attributnamen `sondernutzung` behoben (191c57b3)
- Tippfehler in Werten des Enums `FP_ZweckbestimmungStrassenverkehr` behoben (5bd30cbb)
- Fehlende Attribute von Hinzugefügten Datenobjekten werden sofort neugeladen (482baeb4)
- Fehler beim Import von XPlanGML-Dokumenten mit Top-Level-Namespace behoben (3068a8e2)
- fehlende Dokumente beim Export ins ZIP-Archiv (389f9d9c)
- Ladeanimation stoppt bei Fehlern im Prozess des Hinzufügens von Datenobjekten (58421ebe)
- XPlanung MeasureTypes (Winkel, Volumen, etc.) mit korrektem Datentyp in der Datenbank gespeichert (8542387d)


- Komplieren von UI-Files mit custom top level widgets ermöglicht (8594099d)
- Fehler beim Generieren von Datenbank Revisionen mit Geometrie-Spalten behoben (2709a36f)

### [1.6.0] - 29.08.2022

#### Neue Funktionen

- Darstellung von Baunutzungsschablonen (`XP_Nutzungsschablone`):
    - Möglichkeit zum Aktivieren/Deaktivieren der Nutzungschablone für Baugebietsflächen
    - Bearbeiten von Form, Größe und Anordnung der tabellarischen Darstellung
    - Identifikation und beliebige Positionierung auf der Karte über das Abfrage-Werkzeug
    - XPlanGML-Export angelegter Baunutzungsschablonen
- Neue Option zum Bearbeiten/Zuweisen der Gemeinde eines Planwerks aus dem Detail-Fenster
- Neues QGIS-Verarbeitungswerkzeug zum Export aller Bauleitpläne (Batch-Export)

#### Veränderungen

- Abfrage-Werkzeug lässt sich mit Hotkey öffnen (d46c2912)
- Auswahl des Planwerks bleibt über verschiedene Fenster synchronisiert (85fda4cd)
- Geltungsbereich-Validierung beim Zuweisen von Geometrien zu einzelnen Planinhalten (c1471e17)
- Interne Verarbeitung von `XP_Gemeinde`-Objekten überarbeitet, Nutzung des Attributs `ortsteilName` wird dadurch 
  ermöglicht (06c086f9, 73e8a043)
- Interface für die Übernahme von XPlanung-Daten aus Civil (79b57bed)
- Überprüfung des korrekten Datenbank-Schemas bei Verbindungsaufbau (15767bef)

#### Fehlerbehebungen

- Fehler beim Export von Planwerken mit Sonderzeichen behoben (a3ea1f22)
- XPlanung-Kennzeichen wird auch beim Verschieben der Layer in Gruppen erhalten (0ffb3e86)
- Fehler behoben, durch den Knoten nicht sofort im Objektbaum erschienen (08a2b6fc)
- Fehler beim Import von XPlanGML, die das `wirdDargestelltDurch`-Attribut enthalten, behoben (b642c86c)
- Unglückliche Bezeichnung der Bereichs-Layer bei Nutzung mehrerer Bereiche behoben (80279eda)
- Auswahl des Features beim Zuweisen von Geometrien (`QgsFeaturePickerWidget`) führt nicht mehr dazu, 
  dass Eingabeelemente größer als das Fenster anwachsen (14218bb5)
- leere Attributgruppen erscheinen nicht mehr im Dialog zum Erstellen von Planinhalten (1129b97e)
- Auswahlliste der Planwerke wechselt nicht mehr zum ersten Objekt beim Verlieren des Fokus (0ddf379a)
- Dialog zum Bearbeiten der Stammdaten kann nicht mehr ohne Datenbanl-Verbindung geööfnet werden (f2aa326)
- Fehlender Titel des Fenster zum Bearbeiten von XPlanung-Objekten hinzugefügt (1acce23)


- Falsches Wurzelverzeichnis beim Generieren eines Release (de1cb31)
- xsd-Files werden zur Schema-Validierung nicht mehr online-abgerufen, damit können Tests auch ohne Internet
  durchgeführt werden (1baf763b)


### [1.5.2] - 29.06.2022

#### Neue Funktionen

- Bearbeiten von Datenobjekten wie `XP_Gemeinde` und `XP_Plangeber`:
  - neuer Dialog zum Erstellen, Bearbeiten und Löschen von Datenobjekten 
  - Kontextmenu zum Bearbeiten und Löschen beim Erstellen eines Planwerks
- Neue 'SAGis'-Toolbar, die alle SAGis-Werkzeuge gruppiert

#### Veränderungen

- Installationsprogramm führt Prozesse im Hintergrund aus (b8ab4f0f)
- Fehlende Konformitätsbedingung 3.2.5.1 hinzugefügt (42729e62)

#### Fehlerbehebungen

- Fehler behoben, durch den das Abfragewerkzeug nicht das Attributfenster öffnen konnte (8ed3c71e)

### [1.5.1] - 17.06.2022

#### Neue Funktionen

- Objektbaum unterstützt Sortieren (nach Objekthierarchie, Alphabet und Kategorie) und Filtern 

#### Veränderungen

- mehr Tooltips (d5c0f2a5)
- bessere Eingabefelder für `Boolean` Werte (a2b2d593)
- bessere Eingabefelder für Datumslisten (c3e71c18)
- bessere Eingabefelder für Datumswerte, die auch leere Eingaben erlauben (59767fba)
- verbessertes Aussehen der Formulare durch gleiche Ausrichtung und Breite aller Eingabeelemente (2df91316)
- neu hinzugefügte Objekte werden im Objektbaum markiert (7f578267)
- weniger auffälliger Farb-Effekt beim Auswählen von Objekten im Objektbaum + Hervorheben der Objekte beim Hovern (6da89a98)

#### Fehlerbehebungen

- kleine Fehlerbehebungen der in 1.5.0 überarbeiteten Eingabeformulare:
  - Fehler beim Einlesen von Datumswerten und `MeasureTypes` behoben (fb17429b)
  - Validierung wird nun auch beim Bearbeiten von Attributen korrekt angewendet (324f4fb3)
  - neuer visueller Stil wird auch auf alte Elemente korrekt angewendet (db6a9bca)
- Default-Werte erscheinen beim Bearbeiten einzelner Attribute (10737af8)
- Fehler behoben, bei dem leere Eingabeformulare angezeigt wurden (415f6f55)
- Fehler durch nicht geschlossenen Dateizugriff behoben (5da6cba0)
- Funktionalität des _Verwerfen_-Buttons beim Bearbeiten von Attributen wiederhergestellt (f5409d45)
- Fehler bei der `RegEx`-Validierung behoben (24cabdec)
- Fehler behoben, durch den Beschriftungen breiter als das Fenster erschienen (24cabdec)
- Fehler behoben, durch den das Abfragewerkzeug nicht das Attributfenster öffnen konnte (08b94152)
- Löschen von mehreren aufeinanderfolgenden Objekten im Objektbaum korrigiert (460491db)

### [1.5.0] - 11.05.2022

#### Neue Funktionen

- `Darstellungsoptionen`: Neues Fenster zum Anpassen von Größe und Drehwinkel von Präsentationsobjekten
- Neue Objektarten:
  - `BP_SchutzPflegeEntwicklungsFlaeche`, `BP_Wegerecht`, `RP_Plan`, `LP_Plan`

#### Veränderungen

- Verbesserung der Nutzungsfreundlichkeit aller Eingabeformulare:
  - Beschreibung und Link zum Navigieren zu abhängigen Objekten
  - Fehlerhafte Eingaben in Formularen werden alle gleichermaßen visuell hervorgehoben
  - Eingabeformulare fokussieren automatisch fehlerhafte Eingaben
- Planinhalte mit fehlenden oder fehlerhaften Geometrien werden nicht mehr importiert (33fe00f8)

#### Fehlerbehebungen

- Planwerk-Details schließt nun wenn kein Planwerk mehr vorhanden ist (358b5883)
- Präsentationsobjekte werden nach Erfassung dem Objektbaum hinzugefügt (6944054b)
- Einige Beziehung zwischen Objektklassen von XPlanung korrigiert (Multiplizitäten, korrekte Vererbungshierarchie, etc.)
- fehlerhafter Zustand der Schaltfläche zum Speichern der Einstellungen behoben (a0ef802c)
- Schaltflächen werden korrekt deaktiviert, wenn kein Plan vorhanden ist (07833818)
- fehlerhafte Platzierung von Symbolen außerhalb der zugehörigen Planflächen behoben (c0e05de5)
- Fehler behoben, durch den auf manchen Rechnern keine Log-Datei geschrieben wurde (77cff8b4)
- Das Hervorheben von Präsentationsobjekten auf der Karte funktioniert nun richtig (0153daaf)

#### Verschiedenes

- Ab Version 1.5.0 existiert nun ein Installationsprogramm, welches das QGIS Plugin und alle Python-Abhängigkeiten installiert.

### [1.4.3] - 11.03.2022

#### Neue Funktionen

- Import von ZIP-Archiven mit Plandokumenten und externen Referenzen 
- Import von Punktgeometrien in Plandokumenten
- [build] SAGis XPlanung kann mit dem Cython-Compiler in C-Programmcode übersetzt werden

#### Veränderungen

- Das Wechseln zwischen Planwerken blockiert nicht mehr die Benutzeroberfläche (150f3e6)
- Performance-Verbesserungen bei der Geometrievalidierung (5a8f4d1)
- Dockwidget-Fenster lassen sich nur Rechts und Links andocken (cce598a)
- Nutzung des `pyqtSlot`-Dekorator für alle Slot-Funktion bringt leichte Performanceverbesserung (95aaa76)
- Animation beim Ladevorgang des Detail-Fensters (44a2175)
- Neues Icon für das Plugin (9d3f876)
- Geometrien lassen sich nicht mehr im Attribut-Fenster bearbeiten (5c50718)

#### Fehlerbehebungen

- Button zum Speichern erscheint nicht mehr ungwünscht beim Verschieben des Detail-Fensters (36bc8ad)
- Das Detail-Fenster wächst nicht mehr größer als die gesamte QGIS-Anwendung (4c34a81)
- fehlendes Vorschaubild für Klasse `BP_AnpflanzungBindungErhaltung` hinzugefügt (87ebf86)
- Objektbaum wird nach dem Hinzufügen neuer Objekte korrekt aktualisiert (d9288ac)
- fehlerhafte Validierung der Gemeinde-Auswahl korrigiert (4b974a9)
- Fehler behoben, durch den es möglich war, die Fenstergröße kleiner als den Inhalt anzupassen (d4aa56a)

### [1.4.2] - 07.02.2022

#### Neue Funktionen

- berechnungsintensive Funktionen blockieren nicht mehr die Benutzeroberfläche
- Exportfunktion unterstützt auch Punktgeometrien
- neue Einstellungs-Option zum Anpassen des Exportpfades für externe Referenzen

#### Veränderungen

- XPlanung - Map Tool lässt sich besser deaktivieren (c55fa60c)
- Nutzung der QGIS - Einstellungen zum Speichern von Datenbankinformationen etc.
- Dialog für Einstellungen überarbeitet (bessere Beschriftungen von Labels und Buttons, besserer Gruppierung der Menüpunkte)
- Exportfunktion überprüft Dateiname auf unerlaubte Zeichen und entfernt diese (e481e512)

#### Fehlerbehebungen

- bei sich überlagernden Geometrien wird die korrekte Auswahl identifiziert (dd2e09bd)
- Attribut `flaechenschluss` ist nicht mehr sichtbar beim Erfassen von Punktgeometrien (c1c78c8e)
- Planwerke werden beim Wechseln der Datenbank aktualisiert (4ef0551)
- PostGIS Verbindungen werden in bestimmten Fällen besser erkannt  (da091820)

### [1.4.1] - 21.01.2022

#### Neue Funktionen

- Kartenwerkzeug zum Konfigurieren und Abfragen von Planinhalten

#### Veränderungen

- keine Temporärlayer-Warnung für XPlanung-Layer (46ceba9)
- Auswahl von Objekten aus sich überschneidenden Layer möglich (897c36d)

#### Fehlerbehebungen

- Fehler beim Erstellen von Planwerken wenn kein Layer vorhanden war behoben (2379b5e)
- fehlerhafte Vorschauwerte bei der Bearbeitung von Auswahllisten entfernt (4ef0551)
- Fehler beim Import von FNP's behoben (2336652)

### [1.4.0] - 21.01.2022

#### Neue Funktionen

- neue Objektarten:
    - `BP_BauLinie`, `BP_BesondererNutzungszweckFlaeche`, `BP_GemeinbedarfsFlaeche`, 
      `BP_SpielSportanlagenFlaeche`, `BP_GruenFlaeche`, `BP_LandwirtschaftsFlaeche`,
      `BP_WaldFlaeche`, `BP_StrassenVerkehrsFlaeche`, `BP_GewaesserFlaeche`, 
      `BP_StrassenbegrenzungsLinie`, `BP_VerkehrsflaecheBesondererZweckbestimmung`, 
      `BP_VerEntsorgung`, `BP_AnpflanzungBindungErhaltung`

#### Veränderungen

- Import von XPlanGML-Dokumenten für Multipart-Geometrien `MultiSurface` und `MultiCurve` (728dc80)
- Darstellung aller Objektarten überarbeitet: Symbolisierung passt sich der Zweckbestimmung von Objekten an

#### Fehlerbehebungen

- Attribut `flaechenschluss` ist nicht mehr sichtbar beim Erfassen von Liniengeometrien (971aa5e)
- Fehler behoben, der bewirkte, dass das Detail-Fenster nicht erschien (a566df4)
- Fehler beim Abbruch der Bestätigung zum Löschen von Objekten behoben (0063126)

### [1.3.1] - 07.01.2022

#### Neue Funktionen

- Geometrievalidierung:
    - Prüfung doppelter Stützpunkte
    - Prüfung des Flächenschluss (Überschneidungen von Planinhalten, Geometrien außerhalb des Geltungsbereich und fehlende Flächen)
    - alle Geometriefehler können auf der Karte markiert werden
- Funktion zum Erzwingen des Flächenschluss (füllt Flächen ohne geplante Nutzung)
- Anpassungen von Geometrien der Planinhalte über QGIS-Funktionen wird in die Datenbank übernommen
- Funktion zum Erfassen von Datenobjekten (bspw. `XP_ExterneReferenz`) aus dem Objektbaum

#### Veränderungen

- Dialoge für einzelne Pläne sind jetzt ein `DockWidget` wie das Hauptfenster (5c56991)
- Größere Eingabefelder für mehrzeilige Kommentare (f840f88)
- Geometrie wird als besser lesbares WKT anstatt WKB angezeigt (6f859d3)

#### Fehlerbehebungen

- `rechtscharakter` ist jetzt eine notwendige Angabe (5c25f5d)
- Anzeige von Auswahlwerten korrigiert (df4555f)
- Indikatoren im Layerbaum werden beim verschieben der Knoten erhalten (18d9c3d)

### [1.3.0] - 29.11.2021

#### Neue Funktionen

- Schaltfläche zum Aktualisieren eines geladenen Planwerks im LayerTree

#### Veränderungen

- bessere Validierung bei der Zuordnung von Planinhalten zu Planwerken ohne Bereich
- Auswahl von Geometrien erlaubt neben 'normalen' Geometrien, jetzt auch `CurvePolygon`, `CompoundCurve` und `MultiCurve` 

#### Fehlerbehebungen

- Falsche Anzeige von Layer-Symbolisierungen, bei Layern mit unterschiedlichen XPlanung-Typen
- kritischer Fehler behoben, der Abstürze beim (zweiten) Speichern von Projekten verursachte
- Fehler behoben, bei dem nur abwechselnd Symbole oder Text-Annotationen angezeigt wurden

### [1.2.0] - 22.11.2021 

> Version enthält einen kritischen Fehler, der QGIS beim Speichern von Projekten zum Absturz bringt!
> Alle geänderten Projektinhalte gehen dabei verloren!

#### Neue Funktionen

- vollvektorielle Erfassung von Planinhalten
- Bearbeiten und Löschen von erfassten Planinhalten
- Planwerk mit Präsentationsobjekten (Text oder Symbole) annotieren

#### Veränderungen

- weitere Validierung der Konformitätsbedingungen
- einige Verbesserungen der Benutzeroberfläche durch passendere Widgets, mehr Tooltips und Hinweise
- bessere Validierung von fehlerhaften Eingaben

#### Fehlerbehebungen

- Fehler beim Exportieren von Enum-Werten
- Anzeigefehler beim Laden von Liniengeometrien
- fehlerhafte Deaktivierung von Schaltflächen
- Doppeltes Laden von Rasterbildern
- Absturz beim Rendern von FNP's

### [1.1.0] - 24.08.2021

#### Neue Funktionen

- teilvektorielle Erfassung von Planinhalten für BPläne und FNP
- Verknüpfung von externen Referenzen mit Planwerken
- Anzeige erfasster Planwerke auf der QGIS-Karte
