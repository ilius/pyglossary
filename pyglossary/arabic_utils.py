def recodeToWinArabic(u):
    replaceList = [
        ('ی', 'ي'),
        ('ک', 'ك'),
        ('ٔ', 'ء'),
        ('\xef\xbf\xbd', ''),
    ] + [(chr(i), chr(i+144)) for i in range(1632, 1642)]
    for item in replaceList:
        u = u.replace(item[0], item[1])
    return u.encode('windows-1256', 'replace')


