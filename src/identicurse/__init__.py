from identicurse import IdentiCurse
import random

SLOGANS = [
            "100% hippy-approved",
            "powered by hatred",
            "we don't get OAuth either",
            "don't drink and dent",
            "@psquid can't spell hippy",
            "Stupid sexy Flanders",
            "curry in the i-webs",
            "Got GNOME git commit access",
            "YOUR SOUL TO THE HOMOSEXUAL AGENDA",
            "Bullshit Bingo",
            "trying to do teh frees",
            "coming and coming and coming and coming"
          ]

def main():
    """
    Innit.
    """
    print "Welcome to IdentiCurse 0.3-dev - %s." % (random.choice(SLOGANS))
    IdentiCurse()


if __name__ == '__main__':
    main()