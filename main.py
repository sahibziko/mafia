from telegram.ext import Updater
import filemanager

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

token = filemanager.readfile('telegramapi.txt')
updater = Updater(token)


# Ruoli possibili per i giocatori
# Base di un ruolo
class Role:
    icon = "-"
    team = 'None'  # Squadra: 'None', 'Good', 'Evil'
    name = "UNDEFINED"
    haspower = False
    poweruses = 0

    def power(self):
        pass

    def onendday(self):
        pass


class Royal(Role):
    icon = "\U0001F610"
    team = 'Good'
    name = "Royal"


class Mifioso(Role):
    icon = "\U0001F47F"
    team = 'Evil'
    haspower = True
    poweruses = 1
    target = None
    name = "Mifioso"

    def power(self):
        # Imposta qualcuno come bersaglio
        pass

    def onendday(self):
        # Ripristina il potere
        self.poweruses = 1
        # Uccidi il bersaglio


class Investigatore(Role):
    icon = "\U0001F575"
    team = 'Good'
    haspower = True
    poweruses = 1
    name = "Investigatore"

    def power(self):
        # Visualizza il ruolo di qualcuno
        pass

    def onendday(self):
        # Ripristina il potere
        self.poweruses = 1


class Angelo(Role):
    icon = "\U0001F607"
    team = 'Good'
    haspower = True
    poweruses = 1
    name = "Angelo"

    def power(self):
        # Salva qualcuno dalla morte!
        pass

    def onendday(self):
        # Ripristina il potere
        self.poweruses = 1


# Classi per i giocatori
class Player:
    tid = int()
    tusername = str()
    role = Role()  # Di base, ogni giocatore è un ruolo indefinito
    alive = True
    votingfor = None  # Diventa un player se ha votato
    votes = 0  # Voti. Aggiornato da updatevotes()

    def message(self, bot, text):
        bot.sendMessage(self.tid, text)

    def kill(self):
        self.alive = False

    def __init__(self, tid, tusername):
        self.tid = tid
        self.tusername = tusername


# Classe di ogni partita
class Game:
    adminid = int()
    groupid = int()
    players = list()
    tokill = list()  # Giocatori che verranno uccisi all'endday
    phase = 'Join'  # Fase di gioco: 'Join', 'Voting', 'Ended'

    def __init__(self, groupid, adminid):
        self.groupid = groupid
        self.adminid = adminid

    def message(self, bot, text):
        bot.sendMessage(self.groupid, text)

    def adminmessage(self, bot, text):
        bot.sendMessage(self.adminid, text)

    def mifiamessage(self, bot, text):
        # Trova tutti i mifiosi nell'elenco dei giocatori
        for player in self.players:
            if isinstance(player.role, Mifioso):
                player.message(bot, text)
        # Inoltra il messaggio all'admin
        self.adminmessage(bot, text)

    def findplayerbyid(self, tid) -> Player:
        # Trova tutti i giocatori con un certo id
        for player in self.players:
            if player.tid == tid:
                return player
        else:
            return None

    def findplayerbyusername(self, tusername) -> Player:
        # Trova tutti i giocatori con un certo username
        for player in self.players:
            if player.tusername == tusername:
                return player
        else:
            return None

    def assignroles(self, mifia=2, investigatore=1, angelo=0):
        import random
        random.seed()
        playersleft = self.players.copy()
        random.shuffle(playersleft)
        # Seleziona 2 mifiosi
        while mifia > 0:
            try:
                selected = playersleft.pop()
            except IndexError:
                raise IndexError("Non ci sono abbastanza giocatori!")
            else:
                selected.role = Mifioso()
                mifia -= 1
        # Seleziona 1 detective
        while investigatore > 0:
            try:
                selected = playersleft.pop()
            except IndexError:
                raise IndexError("Non ci sono abbastanza giocatori!")
            else:
                selected.role = Investigatore()
                investigatore -= 1
        # Seleziona 1 angelo
        while angelo > 0:
            try:
                selected = playersleft.pop()
            except IndexError:
                raise IndexError("Non ci sono abbastanza giocatori!")
            else:
                selected.role = Angelo()
                investigatore -= 1
        # Assegna il ruolo di Royal a tutti gli altri
        for player in playersleft:
            player.role = Royal()

    def updatevotes(self):
        for player in self.players:
            player.votes = 0
        for player in self.players:
            player.votingfor.votes += 1

    def mostvotedplayer(self) -> Player:
        mostvoted = None
        self.updatevotes()
        for player in self.players:
            if (mostvoted is None and player.votes >= 1) or (player.votes > mostvoted.votes):
                mostvoted = player
            elif player.votes == mostvoted.votes:
                # Non sono sicuro che questo algoritmo sia effettivamente il più equo. Ma vabbè, non succederà mai
                import random
                mostvoted = random.choice([player, mostvoted])
        return mostvoted

    def endday(self, bot):
        # Se ce n'è bisogno, si potrebbe rendere casuale l'ordine nelle abilità
        for player in self.players:
            player.role.onendday()
        lynched = self.mostvotedplayer()
        if lynched is not None:
            self.message(bot, "{0} era il più votato ed è stato ucciso dai Royal.\n"
                              "Era un {1} {2}.".format(lynched.tusername, lynched.role.icon, lynched.role.name))
            lynched.kill()

# Partite in corso
inprogress = list()


# Trova una partita con un certo id
def findgamebyid(gid) -> Game:
    for game in inprogress:
        if game.groupid == gid:
            return game


# Comandi a cui risponde il bot
def ping(bot, update):
    bot.sendMessage(update.message.chat['id'], "Pong!")


def newgame(bot, update):
    if update.message.chat['type'] != 'private':
        g = Game(update.message.chat['id'], update.message.from_user['id'])
        inprogress.append(g)
        bot.sendMessage(update.message.chat['id'], "Partita creata: " + repr(g))
    else:
        bot.sendMessage(update.message.chat['id'], "Non puoi creare una partita in questo tipo di chat!")


def join(bot, update):
    game = findgamebyid(update.message.chat['id'])
    if game is not None:
        if game.phase == 'Join':
            p = game.findplayerbyid(update.message.from_user['id'])
            if p is None:
                p = Player(update.message.from_user['id'], update.message.from_user['username'])
                game.players.append(p)
                bot.sendMessage(update.message.chat['id'], "Unito alla partita: " + repr(p))
            else:
                bot.sendMessage(update.message.chat['id'], "Ti sei già unito alla partita: " + repr(p))


def status(bot, update):
    game = findgamebyid(update.message.chat['id'])
    if game is None:
        bot.sendMessage(update.message.chat['id'], "In questo gruppo non ci sono partite in corso.")
    else:
        text = "Gruppo: {0}\n" \
               "Creatore: {1}\n" \
               "Stato: {2}\n" \
               "Giocatori partecipanti:\n".format(game.groupid, game.adminid, game.phase)
        # Aggiungi l'elenco dei giocatori
        for player in game.players:
            if player.votingfor is not None:
                text += "{0} {1} ({2})\n".format(player.role.icon, player.tusername, player.votingfor.tusername)
            else:
                text += "{0} {1}\n".format(player.role.icon, player.tusername)
        bot.sendMessage(update.message.chat['id'], text)


def endjoin(bot, update):
    game = findgamebyid(update.message.chat['id'])
    if game is not None and game.phase is 'Join' and update.message.from_user['id'] == game.adminid:
        game.phase = 'Voting'
        bot.sendMessage(update.message.chat['id'], "La fase di join è terminata.")
        game.assignroles(1, 0, 0)
        bot.sendMessage(update.message.chat['id'], "I ruoli sono stati assegnati.")


def vote(bot, update):
    game = findgamebyid(update.message.chat['id'])
    if game is not None and game.phase is 'Voting':
        player = game.findplayerbyid(update.message.from_user['id'])
        if player is not None:
            target = game.findplayerbyusername(update.message.text.split(' ')[1])
            if target is not None:
                player.votingfor = target
                bot.sendMessage(update.message.chat['id'], "Hai votato per uccidere {0}.".format(target.tusername))
            else:
                bot.sendMessage(update.message.chat['id'], "Il nome utente specificato non esiste.")
        else:
            bot.sendMessage(update.message.chat['id'], "Non sei nella partita.")
    else:
        bot.sendMessage(update.message.chat['id'], "Nessuna partita in corso trovata.")


def endday(bot, update):
    game = findgamebyid(update.message.chat['id'])
    if game is not None and game.phase is 'Voting' and update.message.from_user['id'] == game.adminid:
        game.endday(bot)


updater.dispatcher.addTelegramCommandHandler('ping', ping)
updater.dispatcher.addTelegramCommandHandler('newgame', newgame)
updater.dispatcher.addTelegramCommandHandler('join', join)
updater.dispatcher.addTelegramCommandHandler('status', status)
updater.dispatcher.addTelegramCommandHandler('endjoin', endjoin)
updater.dispatcher.addTelegramCommandHandler('vote', vote)
updater.dispatcher.addTelegramCommandHandler('endday', endday)
updater.start_polling()
updater.idle()
