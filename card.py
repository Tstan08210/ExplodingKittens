class Card:
    name = "Card"
    can_nope = False
    id = None
    def __str__(self):
        return self.name
    def __repr__(self):
        return self.name
    
class DefuseCard(Card):
    name = "Defuse"
    id = "CAACAgEAAxkBAAMGaikQnL8JyyekAi9trUlkgSVxflQAAtcGAAIca0BFBzVP3tICEuA7BA"

class ExplodingKitten(Card):
    name = "Exploding Kitten"
    id = "CAACAgEAAxkBAAMEaikQcIxrXpVBzwRKZQ43jjcePzoAAkIQAAItHUBFeCTCu9LrVHs7BA"

class ActionCard(Card):
    can_nope = True

class AttackCard(ActionCard):
    name = "Attack"
    id = "CAACAgEAAxkBAAMFaikQg2UCHaCmP5pPn-Jy6RaSvZ8AAk4JAAIljjhF14qqC1Ux15c7BA"


class SkipCard(ActionCard):
    name = "Skip"
    id = "CAACAgEAAxkBAAMHaikQwmEWpNbpIaEqi_wua7mubnQAAmsHAAKvKkBFXUv2lZVbnq87BA"


class ShuffleCard(ActionCard):
    name = "Shuffle"
    id = "CAACAgEAAxkBAAMDaikQQdDvs16RWcLSE9fyc7Z9nG8AAiEGAALwFkFFAo90ZIVGydo7BA"


class SeeTheFutureCard(ActionCard):
    name = "See The Future"
    id = "CAACAgEAAxkBAAMIaikQ2Wdk4qwIKy6sE_18vQAB8eMXAAKSCgAC9NRARd1NbOy7co0COwQ"


class FavorCard(ActionCard):
    name = "Favor"
    id = "CAACAgEAAxkBAAMJaikQ6kG6hXX5F22mOfv2ifVvUiQAAmsHAAInE0FFEx9N_NihWOg7BA"


class NopeCard(Card):
    name = "Nope"
    id = "CAACAgEAAxkBAAMKaikRA5g_fORXOm-gsbQ1DIO4ogcAAskIAAIMIkBFD91jIGlI30E7BA"

