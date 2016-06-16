from muss import db, locks

class CreateObject(db.Event):
    """
    Class for scripted events which cause the creation of a new object
    """
    def __init__(self, name, emit, send=None, owner=None, disruptive=False):
        with locks.authority_of(locks.SYSTEM):
            self.emit_string = emit
            self.send_string = send
            self.disruptive = disruptive
        super(CreateObject, self).__init__(name, owner=owner, disruptive=disruptive)

    def trigger(self, source, player, **kwargs):
        try:
           player.send(self.send_string.format(obj=source.name))
           source.emit(self.emit_string.format(obj=source.name, player=player.name), exceptions=[player])
        except AttributeError:
            source.emit(self.emit_string.format(obj=source.name, player=player.name))
        # TODO: Implement appropriate changes to world database
        super(CreateObject, self).trigger()

class SelfDestruct(db.Event):
    """
    Class for scripted events which destroy the object to which they are registered
    """
    def __init__(self, name, emit, send=None, owner=None):
        super(SelfDestruct, self).__init__(name, owner=owner, disruptive=True)
        with locks.authority_of(locks.SYSTEM):
            self.emit_string = emit
            self.send_string = send

    def trigger(self, source, player, **kwargs):
        try:
           player.send(self.send_string.format(obj=source.name))
           source.emit(self.emit_string.format(obj=source.name, player=player.name),
                   exceptions=[player])
        except AttributeError:
            source.emit(self.emit_string.format(obj=source.name, player=player.name))
        with locks.authority_of(locks.SYSTEM):
            source.destroy()
        super(SelfDestruct, self).trigger()

class ApplyAttribute(db.Event):
    """
    Class for scripted events which apply a custom attribute to an object
    """
    def __init__(self, name, emit, send=None, owner=None, disruptive=False):
        with locks.authority_of(locks.SYSTEM):
            self.emit_string = emit
            self.send_string = send
            self.disruptive = disruptive
        super(ApplyAttribute, self).__init__(name, owner=owner, disruptive=disruptive)

    def trigger(self, source, player, **kwargs):
        try:
           player.send(self.send_string.format(obj=source.name))
           source.emit(self.emit_string.format(obj=source.name, player=player.name), exceptions=[player])
        except AttributeError:
            source.emit(self.emit_string.format(obj=source.name, player=player.name))
        # TODO: Implement appropriate changes to world database
        super(ApplyAttribute, self).trigger()

class ChangeAttribute(db.Event):
    """
    Class for scripted events which modify a custom attribute on an object
    """
    def __init__(self, name, emit, send=None, owner=None, disruptive=False):
        with locks.authority_of(locks.SYSTEM):
            self.emit_string = emit
            self.send_string = send
            self.disruptive = disruptive
        super(ChangeAttribute, self).__init__(name, owner=owner, disruptive=disruptive)

    def trigger(self, source, player, **kwargs):
        try:
           player.send(self.send_string.format(obj=source.name))
           source.emit(self.emit_string.format(obj=source.name, player=player.name), exceptions=[player])
        except AttributeError:
            source.emit(self.emit_string.format(obj=source.name, player=player.name))
        # TODO: Implement appropriate changes to world database
        super(ChangeAttribute, self).trigger()

class RemoveAttribute(db.Event):
    """
    Class for scripted events which remove a custom attribute from an object
    """
    def __init__(self, name, emit, send=None, owner=None, disruptive=False):
        with locks.authority_of(locks.SYSTEM):
            self.emit_string = emit
            self.send_string = send
            self.disruptive = disruptive
        super(RemoveAttribute, self).__init__(name, owner=owner, disruptive=disruptive)

    def trigger(self, source, player, **kwargs):
        try:
           player.send(self.send_string.format(obj=source.name))
           source.emit(self.emit_string.format(obj=source.name, player=player.name), exceptions=[player])
        except AttributeError:
            source.emit(self.emit_string.format(obj=source.name, player=player.name))
        # TODO: Implement appropriate changes to world database
        super(RemoveAttribute, self).trigger()

disintegrate = SelfDestruct('disintegrate', 'The {obj} disintegrates!')
explode = SelfDestruct('explode', 'The {obj} explodes violently!')
absorb = SelfDestruct('absorb', 'The {obj} glows briefly, and absorbs into {player}',
        send='The {obj} glows bright, and absorbs into you!')
