# -*- coding: utf-8 -*-
from dataclasses import dataclass, field

FORCA_FASES = [
r"""
  +---+
  |   |
      |
      |
      |
      |
=========
""",
r"""
  +---+
  |   |
  O   |
      |
      |
      |
=========
""",
r"""
  +---+
  |   |
  O   |
  |   |
      |
      |
=========
""",
r"""
  +---+
  |   |
  O   |
 /|   |
      |
      |
=========
""",
r"""
  +---+
  |   |
  O   |
 /|\  |
      |
      |
=========
""",
r"""
  +---+
  |   |
  O   |
 /|\  |
 /    |
      |
=========
""",
r"""
  +---+
  |   |
  O   |
 /|\  |
 / \  |
      |
=========
""",
]

@dataclass
class Forca:
    palavra: str
    dica: str
    tentativas_max: int = 6
    certas: set = field(default_factory=set)
    erradas: set = field(default_factory=set)

    def __post_init__(self):
        self.palavra = self.palavra.strip().lower()
        if not (3 <= len(self.palavra) <= 30) or not self.palavra.isalpha():
            raise ValueError("A palavra deve ter entre 3 e 30 letras e conter apenas letras.")
        self.dica = self.dica.strip()

    @property
    def tentativas(self) -> int:
        return self.tentativas_max - len(self.erradas)

    def estado_palavra(self) -> str:
        return " ".join([c if c in self.certas else "_" for c in self.palavra])

    def boneco(self) -> str:
        idx = min(len(self.erradas), len(FORCA_FASES) - 1)
        return FORCA_FASES[idx]

    def terminou(self) -> bool:
        return self.venceu() or self.perdeu()

    def venceu(self) -> bool:
        return all((not ch.isalpha()) or (ch in self.certas) for ch in self.palavra)

    def perdeu(self) -> bool:
        return self.tentativas <= 0

    def tentar(self, letra: str) -> str:
        letra = letra.strip().lower()
        if len(letra) != 1 or not letra.isalpha():
            return "Entrada inválida: digite apenas 1 letra."
        if letra in self.certas or letra in self.erradas:
            return "Letra repetida."
        if letra in self.palavra:
            self.certas.add(letra)
            return "Acertou!"
        else:
            self.erradas.add(letra)
            return "Errou!"
