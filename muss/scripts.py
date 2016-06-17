from muss import db, locks

class CreateObject(db.VisibleEvent):
    """
    Class for scripted events which cause the creation of a new object
    """
    def __init__(self, name, emit=None, send=None, owner=None,
            disruptive=False, exempt=None):
        super(CreateObject, self).__init__(name, emit=emit,
                send=send, owner=owner, disruptive=disruptive, exempt=exempt)

    def trigger(self, source, player, **kwargs):
        # TODO: Implement appropriate changes to world database
        super(CreateObject, self).trigger()

class SelfDestruct(db.VisibleEvent):
    """
    Class for scripted events which destroy the object to which they are registered
    """
    def __init__(self, name, emit=None, send=None, owner=None, exempt=None):
        super(SelfDestruct, self).__init__(name, emit=emit,
                send=send, owner=owner, disruptive=True, exempt=exempt)

    def trigger(self, source, player, **kwargs):
        with locks.authority_of(locks.SYSTEM):
            source.destroy()
        super(SelfDestruct, self).trigger(source, player)

class ApplyAttribute(db.VisibleEvent):
    """
    Class for scripted events which apply a custom attribute to an object
    """
    def __init__(self, name, emit=None, send=None, owner=None,
            disruptive=False, exempt=None):
        super(ApplyAttribute, self).__init__(name, emit=emit,
                send=send, owner=owner, disruptive=disruptive, exempt=exempt)

    def trigger(self, source, player, **kwargs):
        # TODO: Implement appropriate changes to world database
        super(ApplyAttribute, self).trigger()

class ChangeAttribute(db.VisibleEvent):
    """
    Class for scripted events which modify a custom attribute on an object
    """
    def __init__(self, name, emit=None, send=None, owner=None,
            disruptive=False, exempt=None):
        super(ChangeAttribute, self).__init__(name, emit=emit,
                send=send, owner=owner, disruptive=disruptive, exempt=exempt)

    def trigger(self, source, player, **kwargs):
        # TODO: Implement appropriate changes to world database
        super(ChangeAttribute, self).trigger()

class RemoveAttribute(db.VisibleEvent):
    """
    Class for scripted events which remove a custom attribute from an object
    """
    def __init__(self, name, emit=None, send=None, owner=None,
            disruptive=False, exempt=None):
        super(RemoveAttribute, self).__init__(name, emit=emit,
                send=send, owner=owner, disruptive=disruptive, exempt=exempt)

    def trigger(self, source, player, **kwargs):
        # TODO: Implement appropriate changes to world database
        super(RemoveAttribute, self).trigger()

disintegrate = SelfDestruct('disintegrate', emit='The {obj} disintegrates!')
explode = SelfDestruct('explode', emit='The {obj} explodes violently!')
absorb = SelfDestruct('absorb',
        emit='The {obj} glows briefly, and absorbs into {player}',
        send='The {obj} glows bright, and absorbs into you!')
disruptive_curse = db.VisibleEvent('disrupt', send='The {obj} is cursed!', disruptive=True)
