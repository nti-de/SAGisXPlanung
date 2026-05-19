---
icon: lucide/message-circle-question-mark
---

# Häufige Fragen 

## Installation 

### Warum müssen für die Installation externe Python-Softwarepakete installiert werden? { id="python-pakete" }

SAGis XPlanung erweitert QGIS um spezialisierte Funktionen zur Erfassung, Bearbeitung und Verwaltung von XPlanGML-Daten.
Da einige hierfür benötigte Technologien nicht Bestandteil der Standard-QGIS-Installation sind, müssen zusätzliche 
Python-Pakete über den Python-Paketmanager (`pip`) installiert werden. Alle externen Abhängigkeiten sind unter 
einer OpenSource-Lizenz verfügbar.

Die externen Pakete übernehmen folgende Aufgaben innerhalb der Anwendung:

- **[SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy)**  
  Dient als objektorientierte Datenbankschnittstelle und ermöglicht die strukturierte Anbindung an  
  PostgreSQL/PostGIS-Datenbanken zum Zugriff auf das XPlan-Datenmodell.

- **[GeoAlchemy2](https://github.com/geoalchemy/geoalchemy2)**  
  Erweitert SQLAlchemy um räumliche Funktionen und unterstützt die Speicherung sowie Verarbeitung geografischer Objekte.

- **[asyncpg](https://github.com/MagicStack/asyncpg)**  
  Ein leistungsfähiger asynchroner PostgreSQL-Datenbanktreiber, der insbesondere bei datenintensiven Operationen und  
  größeren Datenmengen eine verbesserte Performance als der Standard-Datenbanktreiber im QGIS (`psycopg`) ermöglicht.

- **[qasync](https://github.com/CabbageDevelopment/qasync)**  
  Bindet asynchrone Python-Prozesse in die Qt-/QGIS-Oberfläche ein. Dadurch können datenbank- oder netzwerkintensive  
  Prozesse im Hintergrund ausgeführt werden, ohne die Benutzeroberfläche zu blockieren.

!!! note "Hinweis für Kunden der Vollversion"
    Für Kunden der Vollversion stellen wir auf Wunsch auch eine vollständig gebündelte Installationsversion mit  
    sämtlichen benötigten Python-Abhängigkeiten bereit. Diese Variante eignet sich insbesondere für IT-Umgebungen mit  
    eingeschränkten Benutzerrechten, in denen keine eigenständige Installation externer Python-Pakete möglich ist.