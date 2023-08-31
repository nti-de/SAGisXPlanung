from dataclasses import dataclass

from qgis.core import QgsWkbTypes


@dataclass
class XPlanungItem:
    """ Container für ein XPlanung-Objekt. Beeinhaltet die XPlanung-ID des Objekts und die Objektart.
        Hält bei Bedarf zusätzlich Referenzen auf den zugehörigen Plan und Bereich.
        Nützlich als Parameter zur Übergabe von XPlanung-Objekt, um nicht auf den Datenbank-Objekten zu operieren."""
    xid: str
    xtype: type
    plan_xid: str = None
    bereich_xid: str = None
    parent_xid: str = None
    geom_type: QgsWkbTypes.GeometryType = None
