def count(s):
    if len(s) > 10:
        return -1
    elif len(s) < 1:
        return 0
    else:
        prev_cnt = count(s[1:])
        if ord('a') <= ord(s[0]) and ord(s[0]) <= ord('z'):
            return prev_cnt + 1
        else:
            return prev_cnt

count_tup = (count, ["hello 456"])