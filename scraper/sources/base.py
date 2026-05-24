"""Interface commune a toutes les sources de donnees."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from ..catalog import Model
from ..models import Listing


class ListingSource(ABC):
    """Une source d'annonces pour un modele donne.

    Implementer une nouvelle source = sous-classer et definir ``fetch``.
    ``fetch`` ne doit jamais lever d'exception : en cas d'echec reseau ou
    de changement de structure du site, renvoyer une liste vide.

    Le modele courant est accessible via ``self.model``.
    """

    name: str = "base"

    def __init__(self, model: Model):
        self.model = model

    @abstractmethod
    def fetch(self) -> List[Listing]:
        """Renvoie les annonces actuelles du modele depuis la source."""
        raise NotImplementedError
