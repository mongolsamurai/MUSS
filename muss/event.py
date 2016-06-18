class Event(Object):
    """
    A class from which to derive scripted events.
    """
    def __init__(self, name, owner=None, disruptive=False, exempt=None):
        super(Event, self).__init__(name, None, owner)
        with locks.authority_of(locks.SYSTEM):
            self.type = 'event'
        self.disruptive = disruptive
        self.name = name
        self.locks.exempt = locks.Is(exempt)

    def trigger(self, source, player, **kwargs):
        if self.disruptive:
            raise CancelExecutionException("Triggered a disruptive event")


class VisibleEvent(Event):
    """
    An event which includes notices to be displayed when triggered
    """
    def __init__(self, name, emit=None, send=None, owner=None,
            disruptive=False, exempt=None):
        if not (emit or send):
            raise utils.UserError("One of emit message or send message is required.")
        super(VisibleEvent, self).__init__(name, owner=owner,
                disruptive=disruptive, exempt=exempt)
        self.emit_string = emit
        self.send_string = send

    def trigger(self, source, player, **kwargs):
        # the logic here goes something like this:
        #   If there's a message for the triggering player, send it,
        #   then emit the world-visible message to every else, if there is one.
        #   If there's not a player message, just emit the world message to everyone.
        try:
           player.send(self.send_string.format(obj=source.name))
        except AttributeError:
            source.emit(self.emit_string.format(obj=source.name, player=player.name))
        else:
            try:
                source.emit(self.emit_string.format(obj=source.name,
                    player=player.name), exceptions=[player])
            except AttributeError:
                pass
        super(VisibleEvent, self).trigger(source, player)


class CancelExecutionException(Exception):
    """
    An exception used in scripted events to disrupt the triggering command.
    """
    def __init__(self, string=""):
        if string:
            self.msg = string

    def __str__(self):
        return self.msg



