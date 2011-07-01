import re

_bad_words = {
    r'arse': '****',
    r'arsehole': '********',
    r'asshole': '*******',
    r'bastard': '*******',
    r'beaner': '******',
    r'bitch': '*****',
    r'bj': '**',
    r'bjay': '****',
    r'blow job': '********',
    r'blowjob': '*******',
    r'boner': '*****',
    r'chink': '*****',
    r'chinky': '******',
    r'cock': '****',
    r'cocksucker': '**********',
    r'coon': '****',
    r'cracker': '*******',
    r'cum': '***',
    r'cunt': '****',
    r'dick': '****',
    r'dyke': '****',
    r'fag': '***',
    r'faggot': '******',
    r'fuck': '****',
    r'fucker': '******',
    r'fucking': '*******',
    r'god damn': '********',
    r'goddamn': '*******',
    r'gringo': '******',
    r'jap': '***',
    r'jizz': '****',
    r'motherfucker': '************',
    r'negro': '*****',
    r'nigga': '*****',
    r'nigger': '******',
    r'penis': '*****',
    r'prick': '*****',
    r'pussy': '*****',
    r'queer': '*****',
    r'sex': '***',
    r'shit': '****',
    r'slut': '****',
    r'son of a bitch': '**************',
    r'spunk': '*****',
    r'tits': '****',
    r'twat': '****',
    r'vag': '***',
    r'vagina': '******',
    r'veejay': '******',
    r'vj': '**',
    r'vjain': '*****',
    r'vjay': '****',
    r'wank': '****',
    r'wanker': '******',
    r'wetback': '*******',
    r'whore': '*****',
    }

_RE_FLAGS = re.MULTILINE | re.IGNORECASE | re.DOTALL

_compiled_patterns = [(re.compile(r'\b' + key + r'\b', _RE_FLAGS),
                       _bad_words[key]) for key in _bad_words]


def censor_text(text):
    for pattern, replacement in _compiled_patterns:
        text = pattern.sub(replacement, text)
    return text
