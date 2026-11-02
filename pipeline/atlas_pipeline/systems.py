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
    # Arterial and venous segments, trunks, zones, and sets as well as whole vessels.
    Rule("isa-artery", "arterial", isa=frozenset({"FMA50720", "FMA86187", "FMA30313", "FMA49918", "FMA63812",
                                                 "FMA66332"})),
    Rule("isa-vein", "venous", isa=frozenset({"FMA50723", "FMA86188", "FMA30314", "FMA22917", "FMA63814"})),
    # Veins before arteries: "palmar venous arch" is a vein, "palmar arch" an artery.
    # Whole word only: "hepatovenous segment" is liver tissue, not a vein.
    Rule("name-vein", "venous", name=_names(r"\bveins?\b|\bvenous\b|vena cava")),
    Rule("name-artery", "arterial", name=_names(
        r"arter|aorta|celiac trunk|pulmonary trunk|costocervical trunk|thyrocervical trunk|palmar arch|plantar arch")),
    Rule("partof-heart", "cardiac", partof=frozenset({"FMA7088"})),
    # Nerves, brain segments, and the gray and white matter, nuclei and clusters of the neuraxis.
    Rule("nervous", "nervous", isa=frozenset({"FMA65132", "FMA61284", "FMA5865", "FMA55676", "FMA83143", "FMA83929",
                                              "FMA67242", "FMA223151", "FMA83840", "FMA83686", "FMA11195"}),
         partof=frozenset({"FMA7157"})),
    Rule("isa-bone", "skeletal", isa=frozenset({"FMA5018", "FMA12516"})),
    # Muscles, and the heads and zones of muscles (quadriceps heads, deltoid parts, levator ani).
    Rule("isa-muscle", "muscular", isa=frozenset({"FMA5022", "FMA32558", "FMA85453", "FMA10474", "FMA19089"})),
    Rule("partof-respiratory", "respiratory", partof=frozenset({"FMA7158"})),
    Rule("partof-alimentary", "digestive", partof=frozenset({"FMA7152"})),
    Rule("partof-urinary", "urinary", partof=frozenset({"FMA7159"})),
    Rule("partof-genital", "reproductive", partof=frozenset({"FMA7160"})),
    Rule("partof-endocrine", "endocrine", partof=frozenset({"FMA9668"})),
    Rule("lymphatic", "lymphatic", partof=frozenset({"FMA9607"}), name=_names(r"spleen|lymph|tonsil|thymus")),
    Rule("sensory", "sensory", partof=frozenset({"FMA54450", "FMA54449"}),
         name=_names(r"eyeball|lens|cornea|retina|corona ciliaris|cochlea|vestibul|tympan|\bear\b|auricle")),
    Rule("integument", "integumentary", isa=frozenset({"FMA7163"}), partof=frozenset({"FMA74657", "FMA72979"}),
         name=_names(r"hair|eyebrow|eyelash|\bnails?\b")),
    # Laryngeal cartilages and ligaments belong with the airway, not with joint tissue.
    Rule("name-larynx", "respiratory", name=_names(
        r"thyroid cartilage|cricoid|arytenoid|corniculate|cuneiform cartilage|epiglott|vocal|conus elasticus")),
    Rule("connective", "connective", isa=frozenset({"FMA55107", "FMA10446", "FMA9721", "FMA7591", "FMA7538",
                                                    "FMA21496"})),
    Rule("name-nervous", "nervous", name=_names(
        r"nerve|ganglion|chiasm|plexus|optic tract|amygdala|caudate nucleus|putamen|pallid|thalam|fornix|callosum"
        r"|commissure|collicul|geniculate|mammillary|lamina terminalis|interpeduncular|peduncle|stria"
        r"|interventricular foramen|brain|cerebr|cerebell|medulla|pons|midbrain|spinal cord|hippocamp")),
    Rule("name-heart", "cardiac", name=_names(r"wall of ventricle|atrium|cardiac|papillary|valve")),
    Rule("name-muscle", "muscular", name=_names(r"trapezius|deltoid|pectoralis|biceps|triceps")),
    Rule("name-urinary", "urinary", name=_names(r"kidney|ureter|bladder|urethra")),
    Rule("name-genital", "reproductive", name=_names(r"testis|prostat|penis|epididym|seminal|deferen|scrot")),
    Rule("name-endocrine", "endocrine",
         name=_names(r"adrenal|suprarenal gland|thyroid gland|parathyroid|pituitary|hypophysis|pineal")),
    Rule("name-digestive", "digestive", name=_names(
        r"stomach|esophag|liver|hepat|pancrea|gallbladder|intestin|colon|rectum|duoden|jejun|ileum|cecum|appendix"
        r"|tongue|salivary|parotid|submandibular gland|sublingual gland|\blips?\b")),
    Rule("name-respiratory", "respiratory", name=_names(r"trachea|bronch|lung|laryn|nasal|pharyn")),
    Rule("name-skeletal", "skeletal", name=_names(r"sternum|manubrium|xiphoid")),
    Rule("name-connective", "connective", name=_names(
        r"tendon|tendinous|ligament|membrane|raphe|tract|fascia|aponeuro|linea alba|retinacul")),
)

_DEFAULT: tuple[SystemId, str] = ("connective", "default")


def classify(concepts: ElementConcepts, name_en: str) -> tuple[SystemId, str]:
    for rule in RULES:
        if rule.matches(concepts, name_en):
            return rule.system, rule.rule_id
    return _DEFAULT
