# Python Scripts for the Android:Netrunner LCG definition for OCTGN
# Copyright (C) 2013  Craig P Jolicoeur

# This python script is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this script.  If not, see <http://www.gnu.org/licenses/>.

###=========================File Contents====================================###
# This file contains custom Python classes for game interations in ANR.
# - These classes will allow the ANR scripts to have a more OOP approache and
#   allow for easier maintainability and modularity
###==========================================================================###

import re

# This class represents an ANR Card object
class ANRCard(object):
  def __init__(self, aCard):
    self.card = aCard
    debugNotify("## Created a new ANRCard", 5)

  def name(self):
    return fetchProperty(self.card, 'name')

  def isAgenda(self):
    return self.card.Type == 'Agenda'

  def isIdentity(self):
    return self.card.Type == 'Identity'

  def agendaPoints(self):
    return num(self.card.Stat)

  def isCorpCard(self):
    return self.card.Type in CorporationCardTypes

  def isRunnerCard(self):
    return self.card.Type in RunnerCardTypes

  def hasInfluence(self):
    return self.card.Influence.strip() != ""

  def influenceCost(self, faction):
    if self.card.Faction != faction:
      return num(self.card.Influence)
    else:
      return 0

  def factionRestricted(self, faction):
    if self.card.Faction == "Neutral":
      return False
    else:
      return self.card.Faction != faction

# This class will check the validity of an ANR deck
#
# * an array of errors will be stored for invalid decks
class DeckValidator(object):
  def __init__(self, aDeck, aSide):
    self.deck       = aDeck
    self.side       = aSide
    self.isValid    = True
    self.errors     = []
    self.deckSize   = len(aDeck)
    self.identity   = None
    self.agendaCnt  = 0
    self.agendaPts  = 0.0
    self.influence  = 0
    debugNotify("### Created a new DeckValidator for {}".format(aSide), 5)

  # This method will perform validation on the deck
  def validate(self):
    if not self.side:
      whisper("Choose a side first...")
      return
    notify(" -> Checking deck of {} ...".format(me))
    debugNotify("### About to fetch identity card", 5)
    self.identity = getSpecial('Identity')

    debugNotify("### About to check identity minimum deck size.", 5)
    self.__verifyMinimumDeckSize()

    # animation bug hack
    if len(players) > 1: random = rnd(1,100)
    debugNotify("### About to move cards to trash.", 5)
    # Use hidden archives to opponent cant see card while we check it
    trash = me.piles['Archives(Hidden)']
    if len(players) > 1: random = rnd(1,100)
    for card in self.deck: card.moveTo(trash)

    debugNotify("### About to check each card in the deck", 5)
    for card in trash: self.__processCard(card)

    debugNotify("### About to move cards back from trash.", 5)
    for card in trash: card.moveToBottom(self.deck)

    if 'corp' == self.side: self.__verifyAgendaPoints()
    self.__verifyInfluencePoints()
    self.__setDeckStats()

    if self.isValid: notify("-> Deck of {} is OK!".format(me))
    debugNotify("<<< DeckValidator with return: {}, {}.".format(self.isValid, self.identity), 3)

  def isRunnerFaction(self):
    return self.identity.Faction in RunnerFactions

  def isCorpFaction(self):
    return self.identity.Faction in CorprateFactions

  # Make sure this deck meets the minimum deck size
  def __verifyMinimumDeckSize(self):
    debugNotify("## Deck size: {}. Required: {}".format(self.deckSize, self.identity.Requirement), 5)
    if self.deckSize < num(self.identity.Requirement):
      notify(":::ERROR::: Only {} cards in {}'s Deck but {} are required".format(self.deckSize, me, num(self.identity.Requirement)))
      self.errors.append("Deck does not meet minimum deck size for Idenity")
      self.isValid = False

  # Make sure this deck has enough agenda points to be valid
  def __verifyAgendaPoints(self):
    if self.agendaPts/self.deckSize < 2.0/5.0:
      notify(":::ERROR::: Only {} Agenda Points in {}'s Deck of {} cards.".format(self.agendaPts/1, me, self.deckSize))
      self.errors.append("Too few Agenda Points in Corporate Deck: {}".format(self.agendaPts/1))
      self.isValid = False

  # Make sure this deck doesn't use too much influence points
  def __verifyInfluencePoints(self):
    if self.influence > num(self.identity.Stat):
      notify(":::ERROR::: Too much rival faction influence in {}'s Deck. {} influence found with a max of {}".format(me, self.influence, num(self.identity.Stat)))
      self.errors.append("Too much rival faction influence in Deck. {} influence found with a max of {}".format(self.influence, num(self.identity.Stat)))
      self.isValid = False

  # Store the deck stats globally
  def __setDeckStats(self):
    deckStats = (self.influence, self.deckSize, self.agendaCnt)
    me.setGlobalVariable('Deck Stats', str(deckStats))

  # Process a single card in the deck
  def __processCard(self, aCard):
    card = ANRCard(aCard)
    debugNotify("## Processing card: {}".format(card.name()), 5)
    if card.isAgenda():
      if 'corp' == self.side:
        self.agendaPts += card.agendaPoints()
        self.agendaCnt += 1
      else:
        notify(":::ERROR::: Agenda card found in {}'s Stack: {}.".format(me, card.name()))
        self.errors.append("Agenda card found in Runner Deck: {}".format(card.name()))
        self.isValid = False

    elif card.isCorpCard() and self.isRunnerFaction():
      notify(":::ERROR::: Corporate Card found in {}'s Stack: {}".format(me, card.name()))
      self.errors.append("Corporate Card found in Runner Deck: {}".format(card.name()))
      self.isValid = False

    elif card.isRunnerCard() and self.isCorpFaction():
      notify(":::ERROR::: Runner Card found in {}'s Stack: {}".format(me, card.name()))
      self.errors.append("Runner Card found in Corporate Deck: {}".format(card.name()))
      self.isValid = False

    if card.hasInfluence():
      self.influence += card.influenceCost(self.identity.Faction)
    else:
      if card.isIdentity():
        notify(":::ERROR::: Extra Identity card found in {}'s Stack: {}".format(me, card.name()))
        self.errors.append("Extra Identity Card found in Deck: {}".format(card.name()))
        self.isValid = False
      elif card.factionRestricted(self.identity.Faction):
        notify(":::ERROR::: Faction-restricted card found in {}'s Stack: {}".format(me, card.name()))
        self.errors.append("Faction-restricted Card found in Deck: {}".format(card.name()))
        self.isValid = False

    del card
