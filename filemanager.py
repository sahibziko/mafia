# -*- coding: utf-8 -*-


def readfile(telegramapi.txt):
    """Leia o conteúdo de um arquivo.
    :param name:
    """
    file = open(name, 'r')
    content = file.read()
    file.close()
    return content


def writefile(name, content):
    """Grave algo em um arquivo, sobrescrevendo tudo o que estiver nele.
    :param name: Nome del file
    :param content: Contenuto del file
    """
    file = open(name, 'w')
    file.write(content)
    file.close()
