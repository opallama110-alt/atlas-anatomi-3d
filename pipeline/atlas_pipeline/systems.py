"""Assign each BodyParts3D element to one display system.

The rules run in order and the first match wins. Tissue type from the IS-A tree
(artery, vein, bone, muscle) comes before organ membership from the PART-OF tree,
so a pharyngeal muscle stays a muscle and a coronary artery stays an artery.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from .bp3d_tables import ElementConcepts

SystemId = Literal[
    "integumentary", "muscular", "skeletal", "connective", "digestive", "respiratory", "urinary",
    "reproductive", "endocrine", "lymphatic", "cardiac", "arterial", "venous", "nervous", "sensory",
]


@dataclass(frozen=True)
class Rule:
    rule_id: str
    system: SystemId
    isa: frozenset[str] = frozenset()
    partof: frozenset[str] = frozenset()
    name: re.Pattern[str] | None = None

    def matches(self, concepts: ElementConcepts, name_en: str) -> bool:
        if self.isa & concepts.isa or self.partof & concepts.partof:
            return True
        return bool(self.name and self.name.search(name_en))


def _names(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE)


RULES: tuple[Rule, ...] = (
    Rule("isa-artery", "arterial", isa=frozenset({"FMA50720"})),
    Rule("isa-vein", "venous", isa=frozenset({"FMA50723"})),
    Rule("partof-heart", "cardiac", partof=frozenset({"FMA7088"})),
    Rule("nervous", "nervous", isa=frozenset({"FMA65132", "FMA61284", "FMA5865", "FMA55676"}),
         partof=frozenset({"FMA7157"})),
    Rule("isa-bone", "skeletal", isa=frozenset({"FMA5018", "FMA12516"})),
    Rule("isa-muscle", "muscular", isa=frozenset({"FMA5022", "FMA32558"})),
    Rule("partof-respiratory", "respiratory", partof=frozenset({"FMA7158"})),
    Rule("partof-alimentary", "digestive", partof=frozenset({"FMA7152"})),
    Rule("partof-urinary", "urinary", partof=frozenset({"FMA7159"})),
    Rule("partof-genital", "reproductive", partof=frozenset({"FMA7160"})),
    Rule("partof-endocrine", "endocrine", partof=frozenset({"FMA9668"})),
    Rule("lymphatic", "lymphatic", partof=frozenset({"FMA9607"}), name=_names(r"spleen|lymph|tonsil|thymus")),
    Rule("sensory", "sensory", partof=frozenset({"FMA54450", "FMA54449"}),
         name=_names(r"eyeball|lens|cornea|retina|cochlea|vestibul|tympan")),
    Rule("integument", "integumentary", isa=frozenset({"FMA7163"}), partof=frozenset({"FMA74657", "FMA72979"})),
    Rule("connective", "connective", isa=frozenset({"FMA55107", "FMA10446", "FMA9721"})),
    Rule("name-urinary", "urinary", name=_names(r"kidney|ureter|bladder|urethra")),
    Rule("name-genital", "reproductive", name=_names(r"testis|prostat|penis|epididym|seminal|deferens|scrot")),
    Rule("name-endocrine", "endocrine",
         name=_names(r"adrenal|suprarenal gland|thyroid gland|parathyroid|pituitary|hypophysis|pineal")),
    Rule("name-digestive", "digestive", name=_names(
        r"stomach|esophag|liver|pancrea|gallbladder|intestin|colon|rectum|duoden|jejun|ileum|cecum|appendix"
        r"|tongue|salivary|parotid|submandibular gland|sublingual gland")),
    Rule("name-respiratory", "respiratory", name=_names(r"trachea|bronch|lung|laryn|nasal|pharyn")),
)

_DEFAULT: tuple[SystemId, str] = ("connective", "default")


def classify(concepts: ElementConcepts, name_en: str) -> tuple[SystemId, str]:
    for rule in RULES:
        if rule.matches(concepts, name_en):
            return rule.system, rule.rule_id
    return _DEFAULT
