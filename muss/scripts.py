from muss import db, locks

class CreateObject(db.Event):
    """
    Class for scripted events which cause the creation of a new object
    """
    def __init__(self, name, emit, send=None, owner=None, disruptive=False):
        with lock.authority_of(locks.SYSTEM):
            self.emit = emit
            self.send = send
        super(CreateObject, self).__init__(name, owner=owner, disruptive=disruptive)

    def trigger(self, source, player, **kwargs):
        if self.say:
            source.emit(self.notice.format(obj=source.name, player=player.name), exceptions=[player])
            player.send(self.send.format(obj=source.name))
        else:
            source.emit(self.notice.format(obj=source.name, player=player.name))
        # TODO: Implement appropriate changes to world database
        super(CreateObject, self).trigger()

class SelfDestruct(db.Event):
    """
    Class for scripted events which destroy the object to which they are registered
    """
    def __init__(self, name, emit, send=None, owner=None):
        with lock.authority_of(locks.SYSTEM):
            self.emit = emit
            self.send = send
        super(SelfDestruct, self).__init__(name, owner=owner, disruptive=True)

    def trigger(self, source, player, **kwargs):
        if self.say:
            source.emit(self.notice.format(obj=source.name, player=player.name), exceptions=[player])
            player.send(self.send.format(obj=source.name))
        else:
            source.emit(self.notice.format(obj=source.name, player=player.name))
        with locks.authority_of(locks.SYSTEM):
            source.destroy()
            self.destroy()
        super(SelfDestruct, self).trigger()

class ApplyAttribute(db.Event):
    """
    Class for scripted events which apply a custom attribute to an object
    """
    def __init__(self, name, emit, send=None, owner=None, disruptive=False):
        with lock.authority_of(locks.SYSTEM):
            self.emit = emit
            self.send = send
        super(ApplyAttribute, self).__init__(name, owner=owner, disruptive=disruptive)

    def trigger(self, source, player, **kwargs):
        if self.say:
            source.emit(self.notice.format(obj=source.name, player=player.name), exceptions=[player])
            player.send(self.send.format(obj=source.name))
        else:
            source.emit(self.notice.format(obj=source.name, player=player.name))
        # TODO: Implement appropriate changes to world database
        super(ApplyAttribute, self).trigger()

class ChangeAttribute(db.Event):
    """
    Class for scripted events which modify a custom attribute on an object
    """
    def __init__(self, name, emit, send=None, owner=None, disruptive=False):
        with lock.authority_of(locks.SYSTEM):
            self.emit = emit
            self.send = send
        super(ChangeAttribute, self).__init__(name, owner=owner, disruptive=disruptive)

    def trigger(self, source, player, **kwargs):
        if self.say:
            source.emit(self.notice.format(obj=source.name, player=player.name), exceptions=[player])
            player.send(self.send.format(obj=source.name))
        else:
            source.emit(self.notice.format(obj=source.name, player=player.name))
        # TODO: Implement appropriate changes to world database
        super(ChangeAttribute, self).trigger()

class RemoveAttribute(db.Event):
    """
    Class for scripted events which remove a custom attribute from an object
    """
    def __init__(self, name, emit, send=None, owner=None, disruptive=False):
        with lock.authority_of(locks.SYSTEM):
            self.emit = emit
            self.send = send
        super(RemoveAttribute, self).__init__(name, owner=owner, disruptive=disruptive)

    def trigger(self, source, player, **kwargs):
        if self.say:
            source.emit(self.notice.format(obj=source.name, player=player.name), exceptions=[player])
            player.send(self.send.format(obj=source.name))
        else:
            source.emit(self.notice.format(obj=source.name, player=player.name))
        # TODO: Implement appropriate changes to world database
        super(RemoveAttribute, self).trigger()

disintegrate = SelfDestruct('disintegrate', 'The {obj} disintegrates!')
explode = SelfDestruct('explode', 'The {obj} explodes violently!')
absorb = SelfDestruct('absorb', 'The {obj} glows briefly, and absorbs into {player}', send='The {obj} glows bright, and absorbs into you!')
