def crashme(s):
    if len(s) > 0 and s[0] == "b":
        if len(s) > 1 and s[1] == "a":
            if len(s) > 2 and s[2] == "d":
                if len(s) > 3 and s[3] == "!":
                    raise Exception("Deep bug!")


def crashme3(s):
    if len(s) != 15:
        raise Exception("Wrong input.")
    if s[0] == "1":
        crashme(s[3:7])
    elif s[1] == "1":
        crashme(s[7:11])
    elif s[2] == "1":
        crashme(s[11:15])
    else:
        raise Exception("Wrong input.")
