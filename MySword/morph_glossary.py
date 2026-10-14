"""Plain-English explanations of the grammar terms in Berean's parsing descriptions, for the morphology dictionary.

Written for this project (not copied from any grammar). Greek and Hebrew are kept apart because the same word
means different things in each (a Greek "perfect" is not a Hebrew "perfect").
Each entry: (pattern matched in Berean's description, heading shown, explanation).
"""
import re

GREEK = [
    # parts of speech
    (r"verb", "Verb", "An action or state. Greek verbs show tense, voice and mood, and (in finite forms) person and number."),
    (r"noun", "Noun", "A person, place, thing or idea. Greek nouns show case, gender and number."),
    (r"proper", "Proper noun", "A name of a person, place or people."),
    (r"adjective", "Adjective", "Describes a noun and agrees with it in case, gender and number. It can also stand alone as a noun (\"the good\" = good people/things)."),
    (r"article", "Article", "Greek has only a definite article (\"the\"); there is no word for \"a/an\". The article also points to something known, turns other words into nouns, and can act like a pronoun (\"the one who...\"). It is often left untranslated."),
    (r"personal / possessive pronoun", "Personal / possessive pronoun", "I, you, he, she, it, we, they; in the genitive it usually means my, your, his, their."),
    (r"personal / relative pronoun", "Personal / relative pronoun", "A pronoun used either as a personal pronoun or to begin a relative clause (\"who, which\")."),
    (r"personal / reciprocal pronoun", "Reciprocal pronoun", "\"One another, each other.\""),
    (r"relative", "Relative pronoun", "\"Who, which, that\": begins a clause that describes a noun in the main sentence."),
    (r"demonstrative pronoun", "Demonstrative pronoun", "\"This, that, these, those\": points something out."),
    (r"interrogative / indefinite pronoun", "Interrogative / indefinite pronoun", "\"Who? what? which?\" (with an accent) or \"someone, something, a certain\" (without)."),
    (r"reflexive pronoun", "Reflexive pronoun", "\"Myself, yourself, himself, themselves\": the action turns back on the subject."),
    (r"pronoun", "Pronoun", "Stands in place of a noun."),
    (r"adverb", "Adverb", "Describes how, when, where or how much an action happens."),
    (r"preposition", "Preposition", "Shows a relationship (in, into, from, with, through). Its exact sense depends on the case of the noun after it."),
    (r"conjunction", "Conjunction", "Joins words or clauses: and, but, for, therefore, so that, if."),
    (r"negative particle", "Negative particle", "\"Not.\" Greek ou usually denies a fact; mē usually denies something wished, commanded or supposed."),
    (r"particle", "Particle", "A small word that adds emphasis, contrast or nuance; often not translated directly."),
    (r"interjection", "Interjection", "An exclamation: behold! woe! O!"),
    (r"comparative", "Comparative", "\"More ...\" or \"-er\" (greater, better)."),
    (r"superlative", "Superlative", "\"Most ...\" or \"-est\"; in the New Testament it often just means \"very\"."),
    (r"indec", "Indeclinable", "A word whose form never changes, usually a foreign (often Hebrew) name or word."),
    # tense
    (r"present", "Present tense", "Pictures the action as ongoing or repeated: \"is doing, keeps doing\". In the indicative it usually refers to the present time."),
    (r"imperfect", "Imperfect tense", "Ongoing or repeated action in the past: \"was doing, used to do, kept doing\"; sometimes \"began to do\" or \"tried to do\"."),
    (r"future", "Future tense", "Action expected to happen: \"will do\". Can also express a command or a promise."),
    (r"aorist", "Aorist tense", "Views the action as a whole, as a simple event, without describing its duration. In the indicative it usually refers to the past (\"did\"); in other moods it does not by itself give the time."),
    (r"pluperfect", "Pluperfect tense", "A completed past action whose result was still in place at a past time: \"had done\"."),
    (r"perfect", "Perfect tense", "A completed action whose result still stands: \"has done, is done\". Often stresses the present state (\"it stands written\")."),
    # voice
    (r"middle or passive", "Middle or passive voice", "The middle and passive have the same form here; the context decides whether the subject acts for itself (middle) or is acted on (passive). Many such verbs are simply translated as active."),
    (r"active", "Active voice", "The subject does the action: \"he loosed\"."),
    (r"middle", "Middle voice", "The subject acts with reference to itself or for its own interest: \"he washed (himself)\", \"he chose for himself\". Some verbs are middle in form but active in meaning."),
    (r"passive", "Passive voice", "The subject receives the action: \"he was loosed\"."),
    # mood
    (r"indicative", "Indicative mood", "States something as a fact or asks a factual question."),
    (r"subjunctive", "Subjunctive mood", "Something possible, intended or expected: often after \"that, so that, if, whenever\", or as \"let us ...\"."),
    (r"optative", "Optative mood", "A wish or a remote possibility: \"may it be\", \"may it never be!\" Rare in the New Testament."),
    (r"imperative", "Imperative mood", "A command or request: \"do!\". A present imperative often means \"keep on doing\"; an aorist imperative presents the command as a single whole act."),
    (r"infinitive", "Infinitive", "\"To do\". A verbal noun; after a preposition it often gives a purpose, a cause or a time (\"in order to\", \"because\", \"while\")."),
    (r"participle", "Participle", "\"Doing, having done\". A verbal adjective: it describes a noun, acts as a noun (\"the one who ...\"), or adds a circumstance (when, because, although, by ...)."),
    # case
    (r"nominative", "Nominative case", "The subject of the sentence, or a word that renames the subject (\"he is the Christ\")."),
    (r"genitive", "Genitive case", "Usually \"of\": possession, source, relationship or description (\"the word of God\"). Can also mean \"from\" or give time and comparison."),
    (r"dative", "Dative case", "Usually \"to\" or \"for\" (indirect object, \"gave to him\"); also \"in, with, by\" (place, means, manner)."),
    (r"accusative", "Accusative case", "The direct object of the verb; also extent (\"for three days\") and the object of many prepositions."),
    (r"vocative", "Vocative case", "Direct address: \"O Lord\", \"brothers!\"."),
    # gender / number / person
    (r"masculine", "Masculine", "Grammatical gender. For people it usually means male (or a mixed group); for things it is a feature of the word."),
    (r"feminine", "Feminine", "Grammatical gender. For things it is a feature of the word, not about sex."),
    (r"neuter", "Neuter", "Grammatical gender, neither masculine nor feminine; used for many things and ideas."),
    (r"singular", "Singular", "One."),
    (r"plural", "Plural", "More than one."),
    (r"1st person", "1st person", "The speaker: I, we."),
    (r"2nd person", "2nd person", "The one spoken to: you."),
    (r"3rd person", "3rd person", "The one spoken about: he, she, it, they."),
]

HEBREW = [
    # parts of speech and prefixes
    (r"conjunctive waw", "Conjunctive waw", "The prefix וְ (we-), \"and\". It can also mean but, then, so, or so that."),
    (r"preposition-b", "Preposition ב (be-)", "Prefix meaning in, at, with, by, among or when."),
    (r"preposition-l", "Preposition ל (le-)", "Prefix meaning to, for, toward, belonging to; before an infinitive, \"to, in order to\"."),
    (r"preposition-k", "Preposition כ (ke-)", "Prefix meaning like, as, according to; with an infinitive, \"when, as soon as\"."),
    (r"preposition-m", "Preposition מ (mi-)", "Prefix meaning from, out of, because of; after an adjective, \"more than\"."),
    (r"preposition", "Preposition", "Shows a relationship such as in, on, to, from, under, with."),
    (r"article", "Article", "The prefix הַ (ha-), \"the\". Hebrew has no word for \"a/an\"."),
    (r"direct object marker", "Direct object marker", "אֵת / אֶת־ ('et) marks a definite direct object. It has no English equivalent, so it is usually left untranslated (shown as \"-\")."),
    (r"interrogative", "Interrogative", "Marks a question; the prefix הֲ (ha-) turns a statement into a yes/no question."),
    (r"negative particle", "Negative particle", "\"Not, no\": לֹא for facts and absolute commands, אַל for \"do not\" and wishes."),
    (r"verb", "Verb", "An action or state. Hebrew verbs show the stem (pattern), conjugation, person, gender and number."),
    (r"noun", "Noun", "A person, place, thing or idea. Hebrew nouns show gender, number and state."),
    (r"proper", "Proper noun", "A name of a person, place or people."),
    (r"adjective", "Adjective", "Describes a noun; it follows its noun and agrees with it in gender, number and definiteness."),
    (r"personal / possessive pronoun", "Personal / possessive pronoun", "I, you, he...; as a suffix on a noun it means my, your, his... (\"his hand\"), on a verb it is the object (\"he saw him\")."),
    (r"relative", "Relative", "אֲשֶׁר / שֶׁ: \"who, which, that\"; begins a clause describing a noun."),
    (r"demonstrative pronoun", "Demonstrative pronoun", "\"This, that, these, those\"."),
    (r"pronoun", "Pronoun", "Stands in place of a noun; in Hebrew often written as a suffix."),
    (r"adverb", "Adverb", "Describes how, when or where an action happens."),
    (r"conjunction", "Conjunction", "Joins words or clauses: because, if, that, when (e.g. כִּי, אִם)."),
    (r"particle", "Particle", "A small function word (e.g. \"please\", \"behold\", \"there is\")."),
    (r"interjection", "Interjection", "An exclamation: behold! alas! woe!"),
    (r"ordinal", "Ordinal number", "First, second, third ..."),
    (r"number", "Number", "A numeral: one, two, ten, hundred ..."),
    # stems
    (r"qalpassparticiple", "Qal passive participle", "The simple meaning, passive, as a verbal adjective: \"written, blessed, cursed\"."),
    (r"qalpass", "Qal passive", "An old passive of the simple stem: \"was taken, was made\". Rare."),
    (r"qal", "Qal stem", "The simple, basic stem: the plain meaning of the verb (\"he broke, he wrote\")."),
    (r"nifal", "Niphal stem", "Usually the passive or reflexive of the Qal: \"was broken, hid himself\"."),
    (r"piel", "Piel stem", "Often intensive or causing a state: \"smashed, broke to pieces\"; for some verbs the normal active meaning (\"spoke\", \"sought\")."),
    (r"pual", "Pual stem", "The passive of the Piel: \"was smashed, was made to ...\"."),
    (r"hifil", "Hiphil stem", "Causative: \"caused to ..., made someone do\" (\"brought\" = caused to come)."),
    (r"hofal", "Hophal stem", "The passive of the Hiphil: \"was caused to ..., was brought\"."),
    (r"hitpael", "Hithpael stem", "Reflexive or reciprocal: the subject acts on itself or repeatedly (\"sanctified himself\", \"walked about\")."),
    (r"nithpael", "Nithpael stem", "A late variant of the Hithpael: reflexive or passive."),
    # conjugations
    (r"consecutive imperfect", "Consecutive imperfect (wayyiqtol)", "Form with וַ (wa-) prefixed: the main narrative past tense, \"and he did, then he did\". It moves a story forward step by step."),
    (r"conjunctive perfect", "Conjunctive perfect (weqatal)", "Perfect with וְ (we-): usually continues a future, a command or a habit, \"and he will do, and you shall do\"."),
    (r"conjunctive imperfect", "Conjunctive imperfect", "Imperfect with a plain \"and\" וְ (we-): often purpose or result, \"so that he may ...\", or a wish."),
    (r"perfect", "Perfect (qatal)", "Views the action as complete: usually past (\"he did\"); with verbs of state, present (\"he knows, he is great\"); in prophecy it can present a future as certain."),
    (r"imperfect", "Imperfect (yiqtol)", "Views the action as not complete: future (\"he will do\"), habitual (\"he used to do\"), or possible/desired (\"he may, he should\")."),
    (r"imperative", "Imperative", "A direct command: \"do!\"."),
    (r"jussive", "Jussive", "A wish or indirect command in the 3rd (or 2nd) person: \"let him do\", \"may he do\"; with אַל, \"do not\"."),
    (r"cohortative", "Cohortative", "A wish or resolve in the 1st person: \"let me do, let us do\". \"If contextual\" means the form alone cannot show it; the context decides."),
    (r"infinitive construct", "Infinitive construct", "A verbal noun: \"to do, doing\". With prefixes: לְ \"in order to\", בְּ/כְּ \"when, while\". Can take a subject or object."),
    (r"infinitive absolute", "Infinitive absolute", "Often doubles the main verb for emphasis (\"you shall surely die\"); can also stand for a command or a finite verb."),
    (r"participle", "Participle", "\"Doing\", or \"one who does\": ongoing action, a description, or a noun (\"the one who creates\")."),
    (r"paragogic nun", "Paragogic nun", "An extra נ (n) added to the end of the verb; it does not change the basic meaning (sometimes emphatic or stylistic)."),
    # person / gender / number / state
    (r"first person", "1st person", "The speaker: I, we."),
    (r"second person", "2nd person", "The one spoken to: you."),
    (r"third person", "3rd person", "The one spoken about: he, she, it, they."),
    (r"masculine", "Masculine", "Grammatical gender; for people usually male or a mixed group."),
    (r"feminine", "Feminine", "Grammatical gender; for things it is a feature of the word."),
    (r"common", "Common", "The same form for masculine and feminine."),
    (r"singular", "Singular", "One."),
    (r"plural", "Plural", "More than one."),
    (r"dual", "Dual", "Exactly two, or things in pairs (hands, eyes, feet)."),
    (r"construct", "Construct state", "The noun is joined to the following word: \"X of Y\" (\"the word of the LORD\")."),
    (r"determinate", "Determinate (Aramaic)", "The Aramaic \"emphatic\" state: \"the ...\" (definite)."),
]


def _compile(entries):
    # longest phrases first, so "consecutive imperfect" wins over "imperfect", "middle or passive" over "middle"
    entries = sorted(entries, key=lambda e: -len(e[0]))
    return re.compile(r"\b(%s)\b" % "|".join("(%s)" % e[0] for e in entries), re.I), entries


_GREEK = _compile(GREEK)
_HEBREW = _compile(HEBREW)


def explain(description, hebrew):
    """Terms found in Berean's description, in order, without repeats: [(heading, explanation)]."""
    rx, entries = _HEBREW if hebrew else _GREEK
    out, seen = [], set()
    for m in rx.finditer(description):
        i = next(n for n, g in enumerate(m.groups()[1:]) if g is not None)
        heading, text = entries[i][1], entries[i][2]
        if heading not in seen:
            seen.add(heading)
            out.append((heading, text))
    return out



# suffix -> (who, possessive "my", object "me")
PRONOUN = {"1cs": ("I", "my", "me"), "2ms": ("you, one man", "your", "you"), "2fs": ("you, one woman", "your", "you"),
           "3ms": ("he / it", "his / its", "him / it"), "3fs": ("she / it", "her / its", "her / it"),
           "1cp": ("we", "our", "us"), "2mp": ("you, men or a mixed group", "your", "you"),
           "2fp": ("you, women", "your", "you"), "3mp": ("they, men or a mixed group", "their", "them"),
           "3fp": ("they, women", "their", "them"), "3cp": ("they", "their", "them"), "2cp": ("you, plural", "your", "you")}


def suffix(code):
    """Explanation of a Hebrew pronoun suffix at the end of a code (e.g. N-msc+2ms), or None."""
    m = re.search(r"\+([123][mfc][sp])$", code)
    if not m or m.group(1) not in PRONOUN:
        return None
    who, poss, obj = PRONOUN[m.group(1)]
    return ("Attached pronoun +%s" % m.group(1),
            "A pronoun (%s) joined to the end of the word. On a noun it means \"%s\"; on a verb it is the object, "
            "\"%s\"; on a preposition, \"to %s, with %s\"." % (who, poss, obj, obj, obj))
