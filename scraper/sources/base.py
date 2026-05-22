"""Interface commune a toutes les sources de donnees."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from ..models import Listing


class ListingSource(ABC):
    """Une source d'annonces de Ferrari 458.

    Implementer une nouvelle source = sous-classer et definir ``fetch``.
    ``fetch`` ne doit jamais lever d'exception : en cas d'echec reseau ou
    de changement de structure du site, renvoyer une liste vide.
    """

    name: str = "base"

    @abstractmethod
    def fetch(self) -> List[Listing]:
        """Renvoie les annonces 458 actuelles de la source."""
        raise NotImplementedError
