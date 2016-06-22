from muss import event, locks, db

class CreateObject(event.VisibleEvent):
    """
    Class for scripted events which cause the creation of a new object.
    Strings passed as emit and send parameters are formatted with the created
      object's name substituted for '{created_obj}', in addition to the usual.
    """
    def __init__(self, name, obj_name, obj_type, emit=None, send=None, disruptive=False, exempt=None):
        emit = emit.format(created_obj=obj_name)
        send = send.format(created_obj=obj_name)
        super(CreateObject, self).__init__(name, emit=emit,
                send=send, owner=owner, disruptive=disruptive, exempt=exempt)
        self.obj_name = obj_name
#        try:
#            mod_name, class_name = obj_type.rsplit(".", 1)
#        except ValueError:
#            raise utils.UserError("Object type should be of the form "
#                                  "module.Class")
#        try:
#            module = importlib.import_module(mod_name)
#            object_class = getattr(module, class_name)
#        except ImportError:
#            raise utils.UserError("I don't know of this module: "
#                                  "{}".format(mod_name))
#        except AttributeError:
#            raise utils.UserError("{} doesn't have this class: "
#                                  "{}".format(mod_name, class_name))
#        self.obj_type = object_class
         self.obj_type = obj_type

    def trigger(self, source, player, **kwargs):
        db.store(self.obj_type(self.obj_name, owner=player, location=player.location))
        super(CreateObject, self).trigger()

class SelfDestruct(event.VisibleEvent):
    """
    Class for scripted events which destroy the object to which they are registered
    """
    def __init__(self, name, emit=None, send=None, exempt=None):
        super(SelfDestruct, self).__init__(name, emit=emit,
                send=send, owner=owner, disruptive=True, exempt=exempt)

    def trigger(self, source, player, **kwargs):
        with locks.authority_of(locks.SYSTEM):
            source.destroy()
        super(SelfDestruct, self).trigger(source, player)

class ApplyAttribute(event.VisibleEvent):
    """
    Class for scripted events which apply a custom attribute to an object
    """
    def __init__(self, name, emit=None, send=None, disruptive=False, exempt=None):
        super(ApplyAttribute, self).__init__(name, emit=emit,
                send=send, owner=owner, disruptive=disruptive, exempt=exempt)

    def trigger(self, source, player, **kwargs):
        # TODO: Implement appropriate changes to world database
        super(ApplyAttribute, self).trigger()

class ChangeAttribute(event.VisibleEvent):
    """
    Class for scripted events which modify a custom attribute on an object
    """
    def __init__(self, name, emit=None, send=None, disruptive=False, exempt=None):
        super(ChangeAttribute, self).__init__(name, emit=emit,
                send=send, owner=owner, disruptive=disruptive, exempt=exempt)

    def trigger(self, source, player, **kwargs):
        # TODO: Implement appropriate changes to world database
        super(ChangeAttribute, self).trigger()

class RemoveAttribute(event.VisibleEvent):
    """
    Class for scripted events which remove a custom attribute from an object
    """
    def __init__(self, name, emit=None, send=None, disruptive=False, exempt=None):
        super(RemoveAttribute, self).__init__(name, emit=emit,
                send=send, owner=owner, disruptive=disruptive, exempt=exempt)

    def trigger(self, source, player, **kwargs):
        # TODO: Implement appropriate changes to world database
        super(RemoveAttribute, self).trigger()

class Relocate(event.VisibleEvent):
    """
    Class for scripted events that cause a player to be moved to a new world location
    """
    def __init__(self, name, destination, emit=None, send=None, disruptive=False, exempt=None):
        super(RemoveAttribute, self).__init__(name, emit=emit,
                send=send, owner=owner, disruptive=disruptive, exempt=exempt)
        self.destination = db.get(destination)

    def trigger(self, source, player, **kwargs):
        with locks.authority_of(locks.SYSTEM):
            player.location = self.target
        super(RemoveAttribute, self).trigger()

_muss_script_lib = {
    'disintegrate' : SelfDestruct('disintegrate', emit='The {obj} disintegrates!'),
    'explode' : SelfDestruct('explode', emit='The {obj} explodes violently!'),
    'absorb' : SelfDestruct('absorb',
        emit='The {obj} glows briefly, and absorbs into {player}',
        send='The {obj} glows bright, and absorbs into you!'),
    'disrupt' : event.VisibleEvent('disrupt', send='The {obj} is cursed!', disruptive=True),
    'teleport_to_start' : Relocate('teleport to start', 0, send='A searing white flash and a thunderclap surround you, momentarily dazzling yoru senses. When you recover, you are somewhere else!', emit='With a blinding flash and a clap of thunder, {player} vanishes!', disruptive=True),
    'create_samophlange' : CreateObject('create samoplhange', 'samophlange', db.Object, emit='The {obj} rattles, and a {created_obj} falls out!')
    }
