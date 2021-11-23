FAIL = -1
NOTATRIANGLE = 0
SCALENE = 1
ISOSCELES = 2
EQUILATERAL = 3


def triangle(s):
    if len(s) != 3:
        result = NOTATRIANGLE
    else:
        a = int(s[0])
        b = int(s[1])
        c = int(s[2])
        if a == b:
            if b == c:
                result = EQUILATERAL
            else:
                result = ISOSCELES
        else:
            if b == c:
                result = ISOSCELES
            else:
                if a == c:
                    result = ISOSCELES
                else:
                    result = SCALENE
    return result


def triangle3(s):
    if len(s) != 12:
        result = FAIL
    else:
        if int(s[0]) == 1:
            result = triangle(s[3:6])
        elif int(s[1]) == 1:
            result = triangle(s[6:9])
        elif int(s[2]) == 1:
            result = triangle(s[9:12])
        else:
            result = FAIL
    return result
